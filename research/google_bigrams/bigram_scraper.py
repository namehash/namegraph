import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

import heapq
import gzip
import csv
import pickle
import argparse
import logging
from pathlib import Path
from time import perf_counter
from typing import Literal


str_logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(str_logging_format)

file_handler = logging.FileHandler("ngrams.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def get_file_urls(ngram_type: Literal['unigram', 'bigram']) -> list[str]:
    if ngram_type == 'unigram':
        url = Config.unigram['main_url']
    elif ngram_type == 'bigram':
        url = Config.bigram['main_url']
    else:
        raise ValueError(f'Unexpected arg: ngram_type={ngram_type}')
    r = requests.get(url)
    bs = BeautifulSoup(r.text, features="html.parser")
    return list(filter(
        lambda s: s.startswith('http://storage.googleapis.com/books/ngrams/books/') and s[-3:] == '.gz',
        [a.get('href') for a in bs.find_all('a')]
    ))


def get_ngrams(
        ngram_type: Literal['unigram', 'ngram'],
        top_n: int,
        continue_from_saved: bool,
        output_filepath: Path,
        save_freq: int
) -> Path:
    """Consecutively download files from Google ngram api and save top top_n ngrams with counts to file."""

    global state

    logger.info('Fetching file urls...')
    file_urls = get_file_urls(ngram_type)
    n_files = len(file_urls)
    logger.info(f'File urls fetched. Number of files: {n_files}')

    if continue_from_saved:
        ngram_priority_queue, init_file_idx = state.load(ngram_type)
        file_urls = file_urls[init_file_idx:]
        while len(ngram_priority_queue) > top_n:
            heapq.heappop(ngram_priority_queue)
    else:
        ngram_priority_queue = []
        init_file_idx = 0

    def parse_line(line: str) -> tuple[str, int]:
        """Returns (ngram, match_count) tuple from line."""
        split_line = line.split(sep='\t')
        return split_line[0], sum(map(lambda tup: int(tup.split(',')[1]), split_line[1:]))


    def contains_punctuation_mark(ngram: str) -> bool:
        return '.' in ngram or ',' in ngram or "'" in ngram or '"' in ngram or '-' in ngram or \
               ':' in ngram or ';' in ngram or '(' in ngram or ')' in ngram


    def process_file(url: str):
        """Go through the whole file url and add n-grams to priority queue."""
        nonlocal ngram_priority_queue
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            for line in gzip.open(response.raw):
                text_line = line.decode('utf-8')
                ngram, match_count = parse_line(text_line)
                if contains_punctuation_mark(ngram) or ('_' in ngram and '_START_' not in ngram):
                    continue
                if len(ngram_priority_queue) < top_n:
                    heapq.heappush(ngram_priority_queue, (match_count, ngram))
                elif match_count > ngram_priority_queue[0][0]:
                    heapq.heappushpop(ngram_priority_queue, (match_count, ngram))


    for i, file_url in tqdm(enumerate(file_urls), desc='files progress', colour='cyan',
                            initial=init_file_idx, total=n_files):
        filename = file_url.rsplit('/')[-1]
        logger.info(f'Downloading and processing file {filename} ...')
        t0 = perf_counter()
        try:
            process_file(file_url)
        except Exception:
            logger.exception(f'Error occurred while processing file {filename}. Skipping ...\n')
        else:
            t1 = perf_counter()
            logger.info(f'File {filename} processed. Queue length: {len(ngram_priority_queue)}. '
                        f'Time elapsed: {t1 - t0:.5} seconds.\n')
            if i % save_freq == 0:
                state.save(ngram_priority_queue, ngram_type, next_file_idx=init_file_idx+i+1)

    logger.info('Processing files ended.\n')

    logger.info(f'Sorting {len(ngram_priority_queue)} n-grams ...')
    sorted_ngrams = sorted(ngram_priority_queue, key=lambda x: x[0], reverse=True)
    logger.info(f'N-grams sorted.')

    logger.info(f'Saving n-grams ...')
    with open(output_filepath, 'w', encoding='utf-8', newline='') as output_file:
        writer = csv.writer(output_file)
        for count, ngram_str in sorted_ngrams:
            writer.writerow([ngram_str, count])
    logger.info(f'N-grams saved.')

    state.clear(ngram_type)

    return output_filepath


#########################################################


def get_path(path_str: str) -> Path:
    if Path(path_str).resolve().parent.exists():
        return Path(path_str).resolve()
    else:
        raise ValueError("Provide filepath with existing parent directory.")


class State:
    def __init__(self):
        self.type2path = {
            'unigram': Config.unigram['state_path'],
            'bigram': Config.bigram['state_path']
        }

    def is_state_saved(self, ngram_type: Literal['unigram', 'bigram']) -> bool:
        return self.type2path[ngram_type].is_file()


    def clear(self, ngram_type: Literal['unigram', 'bigram']):
        self.type2path[ngram_type].unlink()

    def load(self, ngram_type: Literal['unigram', 'bigram']) -> tuple[list[tuple[int, str]], int]:
        """Returns a tuple (queue, next_file_idx)"""
        with open(self.type2path[ngram_type], 'rb') as file:
            state_dict: dict = pickle.load(file)
            logger.warning(f"State loaded ({ngram_type}). "
                           f"Queue length: {len(state_dict['queue'])}. Next file idx: {state_dict['next_file_idx']}.")
            return state_dict['queue'], state_dict['next_file_idx']

    def save(
            self,
            queue: list[tuple[int, str]],
            ngram_type: Literal['unigram', 'bigram'],
            next_file_idx: int):
        with open(self.type2path[ngram_type], 'wb') as file:
            state_dict = dict()
            state_dict['queue'] = queue
            state_dict['next_file_idx'] = next_file_idx
            logger.info("Saving state...")
            pickle.dump(state_dict, file, protocol=pickle.HIGHEST_PROTOCOL)
            logger.info(f'State saved ({ngram_type}). Queue length: {len(queue)}. Next file idx: {next_file_idx}.')


class Config:
    unigram = {
        'main_url': 'http://storage.googleapis.com/books/ngrams/books/20200217/eng/eng-1-ngrams_exports.html',
        'state_path': Path().cwd().resolve() / '.state1.pickle'
    }
    bigram = {
        'main_url': 'http://storage.googleapis.com/books/ngrams/books/20200217/eng/eng-2-ngrams_exports.html',
        'state_path': Path().cwd().resolve() / '.state2.pickle'
    }


state = State()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download ngrams from Google Ngram Viewer API and save top_n (by count) of them to a csv file.'
    )

    parser.add_argument('ngram_type', choices=['unigram', 'bigram'], help='which n-grams to download')

    parser.add_argument('-n', '--top_n', type=int, required=True, help='number of n-grams to store and save')
    parser.add_argument('-c', '--continue_from_saved', action='store_true', default=None,
                        help='continue processing from saved state; if not specified continues if the state is saved')
    parser.add_argument('-o', '--output', type=str, default=None, help='output file name or path')
    parser.add_argument('-s', '--save_freq', type=int, default=10,
                        help='s=?; save queue state every s file processed')

    args = parser.parse_args()

    continue_from_saved = args.continue_from_saved \
        if args.continue_from_saved is not None else state.is_state_saved(args.ngram_type)
    if continue_from_saved and not state.is_state_saved(args.ngram_type):
        raise ValueError("Cannot continue processing: no state file")
    output_filepath = get_path(args.output) if args.output is not None else f'{args.ngram_type}s.csv'


    logger.info('##### START #####')
    logger.info(
        f'Running:\nget_ngrams(\n'
        f'\tngram_type="{args.ngram_type}"\n'
        f'\ttop_n={args.top_n},\n'
        f'\tcontinue_from_saved={continue_from_saved}\n'
        f'\toutput_filepath="{output_filepath}"\n'
        f'\tsave_freq={args.save_freq}\n)')

    res = get_ngrams(
        ngram_type=args.ngram_type,
        top_n=args.top_n,
        continue_from_saved=continue_from_saved,
        output_filepath=output_filepath,
        save_freq=args.save_freq
    )

    logger.info(f'Output saved to "{res}".')
    logger.info('#####  END  #####\n')
