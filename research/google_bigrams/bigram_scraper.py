import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

import heapq
import gzip
import csv
from io import BytesIO
import logging
from time import perf_counter
from typing import Iterator


str_logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(str_logging_format)

file_handler = logging.FileHandler("bigrams.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def get_file_urls() -> list[str]:
    r = requests.get(Config.google_bigrams_url)
    bs = BeautifulSoup(r.text, features="html.parser")
    return list(filter(
        lambda s: s.startswith('http://storage.googleapis.com/books/ngrams/books/') and s[-3:] == '.gz',
        [a.get('href') for a in bs.find_all('a')]
    ))


def download_and_extract(file_urls: list[str]) -> Iterator[tuple[str, str]]:
    for url in file_urls:
        filename = url.rsplit('/')[-1]
        response = requests.get(url, stream=True)
        decompressed_content = gzip.GzipFile(fileobj=BytesIO(response.content))
        str_content = decompressed_content.read().decode('utf-8')
        yield str_content, filename


def get_bigrams(top_n: int, output_filename='bigrams.csv') -> str:
    """Consecutively download files from Google bigram api and save top N bigrams with counts to file."""

    logger.info('Fetching file urls...')
    file_urls = get_file_urls()
    n_files = len(file_urls)
    logger.info(f'File urls fetched. Number of files: {n_files}')

    bigram_priority_queue = []


    def parse_line(line: str) -> tuple[str, int]:
        """Returns (bigram, match_count) tuple from line."""
        split_line = line.split(sep='\t')
        return split_line[0], sum(map(lambda tup: int(tup.split(',')[1]), split_line[1:]))


    def is_pos_tagged(bigram: str) -> bool:
        return '_NOUN' in bigram or '_VERB' in bigram or '_ADJ' in bigram or '_ADV' in bigram or '_PRON' in bigram or \
                '_DET' in bigram or '_ADP' in bigram or '_NUM' in bigram or '_CONJ' in bigram or '_PRT' in bigram or \
                '_X' in bigram

    def contains_punctuation_mark(bigram: str) -> bool:
        return '.' in bigram or ',' in bigram or "'" in bigram or '"' in bigram or ':' in bigram


    def process_file(content: str):
        """Go through the whole file content and add bigrams to priority queue."""
        nonlocal bigram_priority_queue
        lines = content.splitlines()
        for line in tqdm(lines, position=1, desc='lines progress', colour='cyan'):
            bigram, match_count = parse_line(line)
            if is_pos_tagged(bigram) or contains_punctuation_mark(bigram):
                continue
            if len(bigram_priority_queue) < top_n:
                heapq.heappush(bigram_priority_queue, (match_count, bigram))
            elif match_count > bigram_priority_queue[0][0]:
                heapq.heappushpop(bigram_priority_queue, (match_count, bigram))


    for file_content, filename in tqdm(download_and_extract(file_urls), total=n_files,
                                       position=0, desc='files progress', colour='green'):
        logger.info(f'Processing file {filename} ...')
        t0 = perf_counter()
        process_file(file_content)
        t1 = perf_counter()
        logger.info(f'File {filename} processed. Time elapsed: {t1-t0:.5} seconds.\n')

    logger.info('Processing files ended.\n')

    logger.info(f'Sorting {top_n} bigrams ...')
    sorted_bigrams = sorted(bigram_priority_queue, key=lambda x: x[0], reverse=True)
    logger.info(f'Bigrams sorted.')

    logger.info(f'Saving bigrams ...')
    with open(output_filename, 'w', encoding='utf-8', newline='') as output_file:
        writer = csv.writer(output_file)
        for count, bigram_str in sorted_bigrams:
            writer.writerow([bigram_str, count])
    logger.info(f'Bigrams saved.')

    return output_filename


class Config:
    google_bigrams_url = 'http://storage.googleapis.com/books/ngrams/books/20200217/eng/eng-2-ngrams_exports.html'


if __name__ == '__main__':
    logger.info('##### START #####')

    get_bigrams(top_n=100_000_000)

    logger.info('#####  END  #####\n')
