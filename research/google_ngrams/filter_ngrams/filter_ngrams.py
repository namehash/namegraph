import pandas as pd
import numpy as np
from tqdm import tqdm

import csv
import argparse
import logging
from pathlib import Path
from collections import defaultdict

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


def filter_ngrams(
        input_ngrams_path: Path,
        nothumans_path: Path,
        humans_path: Path,
        output_path: Path,
        humans_min_qrank: int,
        nothumans_min_qrank: int,
        popular_humans_top_n: int
) -> Path:
    ngrams_dtype = {'ngram': str, 'count': np.uint64}
    wikidata_dtype = {'itemid': str, 'qrank': np.uint64, 'name': str}

    logger.debug("Reading ngrams...")
    ngrams_df = pd.read_csv(input_ngrams_path, header=None, names=['ngram', 'count'], dtype=ngrams_dtype)

    logger.debug("Reading humans...")
    humans_df = pd.read_csv(humans_path, header=None, names=['itemid', 'qrank', 'name'], dtype=wikidata_dtype)
    humans_df = humans_df[humans_df['qrank'] >= humans_min_qrank]

    logger.debug("Reading nothumans...")
    nothumans_df = pd.read_csv(nothumans_path, header=None, names=['itemid', 'qrank', 'name'], dtype=wikidata_dtype)
    nothumans_df = nothumans_df[nothumans_df['qrank'] >= nothumans_min_qrank]

    logger.debug("Converting dataframes to lists...")
    ngrams_list = [(str(ngram), int(count)) for ngram, count in zip(ngrams_df['ngram'], ngrams_df['count'])]
    humans_list = [(str(name), int(qrank)) for name, qrank in zip(humans_df['name'], humans_df['qrank'])]
    nothumans_list = [(str(name), int(qrank)) for name, qrank in zip(nothumans_df['name'], nothumans_df['qrank'])]

    logger.debug("Tokenizing lists...")
    # humans_tokens = get_token_set(humans_list, min_length=2)
    popular_humans_tokens = get_token_set(humans_list[:popular_humans_top_n], min_length=2)
    # nothumans_tokens = get_token_set(nothumans_list, min_length=3)

    logger.info("Counting popular names % in ngrams [before] ...")
    count_before = count_human_names_in_ngrams(ngrams_list, popular_humans_tokens)
    logger.info(f'Popular names in ngrams:\t{count_before} /\t{len(ngrams_list)} [before]')

    # filter_basic(ngrams_list, nothumans_tokens, output_path)
    filter_qrank_weighted_counts(ngrams_list, humans_list, nothumans_list, output_path, k=0.9)

    logger.debug("Reading filtered ngrams...")
    filtered_ngrams_df = pd.read_csv(output_path, header=None, names=['ngram', 'count'], dtype=ngrams_dtype)
    filtered_ngrams_list = [
        (str(ngram), int(count)) for ngram, count in zip(filtered_ngrams_df['ngram'], filtered_ngrams_df['count'])
    ]
    logger.info("Counting popular names % in filtered ngrams [after] ...")
    count_after = count_human_names_in_ngrams(filtered_ngrams_list, popular_humans_tokens)
    logger.info(f'Popular names in ngrams:\t{count_after} /\t{len(filtered_ngrams_list)} [after]')
    logger.info(f'--- Deleted {100 * (1. - count_after / count_before):.4}% of popular names ---')
    logger.info(f'--- Deleted {100 * (1. - len(filtered_ngrams_list) / len(ngrams_list)):.4}% of rows ---')

    return output_path


def filter_basic(ngrams_list: list[tuple[str, int]], nothumans_tokens: set[str], output_path: Path):
    logger.info("Chosen method: basic filtering")

    def is_name(ngram: str) -> bool:
        nonlocal nothumans_tokens
        tokens = ngram.split()
        for token in tokens:
            if token.istitle() and token not in nothumans_tokens:
                return True
        return False

    logger.debug("Filtering ngrams...")
    with open(output_path, 'w', encoding='utf-8', newline='') as output_file:
        writer = csv.writer(output_file)
        for ngram_str, count in tqdm(ngrams_list, desc='filtering n-grams', colour='magenta'):
            if '_START_' in ngram_str:
                continue
            if not is_name(ngram_str):
                writer.writerow([ngram_str, count])
    logger.debug(f'N-grams saved.')


def filter_qrank_weighted_counts(
        ngrams_list: list[tuple[str, int]],
        humans_list: list[tuple[str, int]],
        nothumans_list: list[tuple[str, int]],
        output_path: Path,
        k=0.9  # todo: different k
):
    """
    Create token->weighted_count dicts for humans and nothumans weighted by get_name_weight(name_qrank).
    Then, if for at least one of ngram's tokens
        human_dict[token] > k * nothuman_dict[token] holds
    do not inlude this ngram.
    """
    logger.info("Chosen method: qrank-weighted-counts filtering")

    def get_name_weight(name_qrank: int) -> int:  # todo: zmienić / usunąć buckety?
        if name_qrank < 500:
            return 1
        elif name_qrank < 1000:
            return 2
        elif name_qrank < 5000:
            return 4
        elif name_qrank < 10_000:
            return 6
        elif name_qrank < 20_000:
            return 10
        elif name_qrank < 100_000:
            return 20
        else:
            return 40

    humans_tokens_2_rank = defaultdict(lambda: 0)
    for name, qrank in tqdm(humans_list, desc='creating humans dict', colour='cyan'):
        for token in tokenize_name(name, min_length=2):
            humans_tokens_2_rank[token] += get_name_weight(qrank)

    nothumans_tokens_2_rank = defaultdict(lambda: 0)
    for name, qrank in tqdm(nothumans_list, desc='creating nothumans dict', colour='cyan'):
        for token in tokenize_name(name, min_length=3):
            nothumans_tokens_2_rank[token] += get_name_weight(qrank)

    def is_name(ngram: str) -> bool:
        nonlocal humans_tokens_2_rank, nothumans_tokens_2_rank, k
        for ngram_token in ngram.split():
            if humans_tokens_2_rank[ngram_token] > k * nothumans_tokens_2_rank[ngram_token]:
                return True
        return False

    logger.debug("Filtering ngrams...")
    with open(output_path, 'w', encoding='utf-8', newline='') as output_file:
        writer = csv.writer(output_file)
        for ngram_str, count in tqdm(ngrams_list, desc='filtering n-grams', colour='magenta'):
            if '_START_' in ngram_str:
                continue
            if not is_name(ngram_str):
                writer.writerow([ngram_str, count])
    logger.debug(f'N-grams saved.')


def count_human_names_in_ngrams(ngrams_list: list[tuple[str, int]], humans_tokens: set[str]) -> int:
    names_count = 0
    for ngram_str, count in tqdm(ngrams_list, desc='counting names in n-grams', colour='green'):
        if all([ngram_token in humans_tokens for ngram_token in ngram_str.split()]):  # todo: czy to jest dobrze liczone
            names_count += 1
    return names_count


# todo: jak jest pauza, kropka itp. to usunąć z name?
def tokenize_name(name: str, min_length):
    if name[0] == '"' and name[-1] == '"':
        name = name[1:-1]
        name = name.replace(',', '')
    if name.startswith('Category:'):
        name = name[9:]
    tokens = name.split()
    return list(filter(lambda x: len(x) >= min_length, tokens))


def get_token_set(names_list: list[tuple[str, any]], min_length=3) -> set[str]:
    token_set = set()
    for name_tup in names_list:
        token_set.update(tokenize_name(name_tup[0], min_length))
    return token_set


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

    parser.add_argument('--popular_humans_top_n', type=int, default=10_000, help='how many top humans are popular')

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
        nothumans_min_qrank=args.nothumans_min_qrank,
        popular_humans_top_n=args.popular_humans_top_n
    )

    logger.info(f'Output saved to "{res}".')
    logger.info('#####  END  #####\n')

"""
python filter_ngrams.py unigram \
    --humans_min_qrank 1000 \
    --nothumans_min_qrank 4000

python filter_ngrams.py bigram \
    --humans_min_qrank 1000 \
    --nothumans_min_qrank 4000
"""
