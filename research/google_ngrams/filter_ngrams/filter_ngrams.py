import pandas as pd
import nltk
from tqdm import tqdm

import csv
import argparse
import logging
from pathlib import Path
from time import perf_counter


str_logging_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(str_logging_format)
file_handler = logging.FileHandler("filter_ngrams.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def get_nothumans_token_set(nothumans: list[str]) -> set[str]:
    stop_words = set(nltk.corpus.stopwords.words('english'))
    nothumans_tokens = set()
    for name in tqdm(nothumans, desc='nothumans tokenization', colour='cyan'):
        tokens = nltk.tokenize.word_tokenize(name)
        tokens = list(filter(lambda x: len(x) > 2 and x.lower() not in stop_words, tokens))
        nothumans_tokens.update(tokens)
    return nothumans_tokens


def filter_ngrams(
        input_ngrams_path: Path,
        nothumans_path: Path,
        humans_path: Path,
        output_path: Path,
        humans_min_qrank: int,
        nothumans_min_qrank: int
) -> Path:
    logger.info("Reading ngrams...")
    ngrams_df = pd.read_csv(input_ngrams_path, header=None, names=['ngram', 'count'],
                            dtype={'ngram': str, 'count': int})

    csv_dtype_dict = {'itemid': str, 'qrank': int, 'name': str}

    # logger.info("Reading humans...")
    # humans = pd.read_csv(humans_path, header=None, names=['itemid', 'qrank', 'name'])
    # humans = humans[humans['qrank'] >= humans_min_qrank]

    logger.info("Reading nothumans...")
    nothumans_df = pd.read_csv(nothumans_path, header=None, names=['itemid', 'qrank', 'name'], dtype=csv_dtype_dict)
    nothumans_df = nothumans_df[nothumans_df['qrank'] >= nothumans_min_qrank]
    logger.info("Tokenizing nothumans...")
    nothumans_tokens = get_nothumans_token_set(list(map(str, nothumans_df['name'].tolist())))

    # todo: count popular names % in nothumans (before)

    # todo: read ngrams line by line and save matched lines to output file

    # todo: count popular names % in nothumans (after)

    return output_path


def get_path(path_str: str) -> Path:
    if Path(path_str).resolve().parent.exists():
        return Path(path_str).resolve()
    else:
        raise ValueError("Provide filepath with existing parent directory.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filter n-grams from a csv file.')

    parser.add_argument('ngram_type', choices=['unigram', 'bigram'], help='which n-grams to filter')

    parser.add_argument('-n', '--ngrams', type=str, default=None, help='input ngram file name or path')
    parser.add_argument('--nothumans', type=str, default=None, help='nothumans (proper nouns) file name or path')
    parser.add_argument('--humans', type=str, default=None, help='human (names) file name or path')
    parser.add_argument('-o', '--output', type=str, default=None, help='output file name or path')

    parser.add_argument('--humans_min_qrank', type=int, default=500, help='trim humans below this qrank')
    parser.add_argument('--nothumans_min_qrank', type=int, default=1000, help='trim nothumans below this qrank')

    args = parser.parse_args()

    ngrams_filepath = get_path(
        args.ngrams) if args.ngrams is not None else Path().cwd() / 'data' / f'{args.ngram_type}s.csv'
    assert ngrams_filepath.is_file(), f'N-gram file {ngrams_filepath} does not exist.'

    nothumans_filepath = get_path(
        args.nothumans) if args.nothumans is not None else Path().cwd() / 'data' / f'nothumans.csv'
    assert nothumans_filepath.is_file(), f'Proper nouns file {nothumans_filepath} does not exist.'

    humans_filepath = get_path(args.humans) if args.humans is not None else Path().cwd() / 'data' / f'humans.csv'
    assert humans_filepath.is_file(), f'Humans file {humans_filepath} does not exist.'

    output_filepath = get_path(args.output) if args.output is not None else f'{args.ngram_type}s_filtered.csv'

    logger.info('##### START #####')

    res = filter_ngrams(
        input_ngrams_path=ngrams_filepath,
        nothumans_path=nothumans_filepath,
        humans_path=humans_filepath,
        output_path=output_filepath,
        humans_min_qrank=args.humans_min_qrank,
        nothumans_min_qrank=args.nothumans_min_qrank
    )

    logger.info(f'Output saved to "{res}".')
    logger.info('#####  END  #####\n')

# todo: Ile procent popularnych imion zostaje usuniętych
# todo: jeśli weźmiemy pod uwagę tokeny z nothumans powyżej qrank X.

# python filter_ngrams.py unigram --humans_min_qrank 500 --nothumans_min_qrank 1000
