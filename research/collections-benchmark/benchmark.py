from argparse import ArgumentParser
from typing import Optional, Callable
from collections import defaultdict
import requests
import tqdm

import numpy as np


HOST = 'localhost'
PORT = 8000

QUERIES = [
    'apple', 'apples', 'bmw', 'hulk', 'marvel', 'characters', 'fruit', 'fruits', 'britney', 'spears',
    'car', 'models', 'cars', 'football', 'players', 'cristiano', 'ronaldo', 'planets', 'countries',
    'france', 'switzerland', 'vehicles', 'greek', 'gods', 'zeus', 'athena', 'fire', 'pinkfloyd',
]

# TODO to change
COLLECTION_IDS = [
    'Q8882867', 'Q8763100', 'Q925427', 'Q6946014',
]


MEMBERS = [
    'apple', 'apples', 'bmw', 'hulk', 'marvel', 'characters', 'fruit', 'fruits', 'britney', 'spears',
    'ummagumma', 'atom', 'heart', 'football', 'players', 'cristiano', 'ronaldo', 'planets', 'countries',
]

TIME_NAMES = ['latency', 'took', 'communication']

############### SEARCH BY STRING ###############
def find_collections_by_string(
        query: str,
        mode: str,
        max_related_collections: int = 15,
        min_other_collections: int = 0,
        max_other_collections: int = 0,
        max_total_collections: int = 15,
        name_diversity_ratio: float = 0.55,
        max_per_type: int = 3,
        limit_names: int = 10,
):
    data = {
        "query": query,
        "mode": mode,
        "max_related_collections": max_related_collections,
        "min_other_collections": min_other_collections,
        "max_other_collections": max_other_collections,
        "max_total_collections": max_total_collections,
        "name_diversity_ratio": name_diversity_ratio,
        "max_per_type": max_per_type,
        "limit_names": limit_names,
    }
    return requests.post(
        f'http://{HOST}:{PORT}/find_collections_by_string',
        json=data,
    ).json()


def find_collections_by_string_instant_search(query: str):
    return find_collections_by_string(query=query, mode='instant')


def find_collections_by_string_domain_detail_search(query: str):
    return find_collections_by_string(
        query=query, mode='domain_detail', max_related_collections=3, min_other_collections=3,
        max_other_collections=3, max_total_collections=6
    )


############### SEARCH BY COLLECTION ###############
def find_collections_by_collection(collection_id: str):
    data = {
        "collection_id": collection_id,
        "max_related_collections": 10,
        "min_other_collections": 0,
        "max_other_collections": 0,
        "max_total_collections": 10,
        "name_diversity_ratio": 0.5,
        "max_per_type": 5,
        "limit_names": 10,
        "sort_order": "AI-LTR",
        "offset": 0,
    }
    return requests.post(
        f'http://{HOST}:{PORT}/find_collections_by_collection',
        json=data,
    ).json()


############### SEARCH BY MEMBER ###############
def count_collections_by_member(label: str):
    data = {"label": label}
    return requests.post(
        f'http://{HOST}:{PORT}/count_collections_by_member',
        json=data,
    ).json()


def find_collections_by_member(
        label: str,
        mode: str,
        max_results: int = 100,
        limit_names: int = 10,
        sort_order: str = 'AI-LTR',
        offset: int = 0,
):
    data = {
        "label": label,
        "mode": mode,
        "max_results": max_results,
        "limit_names": limit_names,
        "sort_order": sort_order,
        "offset": offset,
    }
    return requests.post(
        f'http://{HOST}:{PORT}/find_collections_by_member',
        json=data,
    ).json()


def find_collections_by_member_instant(label: str):
    return find_collections_by_member(label=label, mode='instant')


def find_collections_by_member_domain_detail(label: str):
    return find_collections_by_member(label=label, mode='domain_detail')


############### UTILS ###############
def extract_times(response) -> dict[str, float]:
    return {
        'latency': response['metadata']['processing_time_ms'],
        'took': response['metadata']['elasticsearch_processing_time_ms'],
        'communication': response['metadata']['elasticsearch_communication_time_ms'],
    }


def stats_string(x: list) -> str:
    if any([elem is None for elem in x]):
        return 'N/A'
    return f'{np.mean(x):.3f} ± {np.std(x):.1f}'


def aggregate_stats(times: dict[str, dict[str, list[float]]]) -> dict[str, list[float]]:
    aggregated_times = defaultdict(list)
    for subtimes in times.values():
        for key, value in subtimes.items():
            aggregated_times[key].extend(value)
    return aggregated_times


def collect_times(call_fn: Callable, queries: list[str], repeats: int) -> dict[str, dict[str, list[float]]]:
    times = {query: defaultdict(list) for query in queries}
    for _ in tqdm.tqdm(range(repeats), desc='repeats'):
        for query in tqdm.tqdm(queries, desc='queries'):
            response = call_fn(query)
            extracted_times = extract_times(response)
            for key, value in extracted_times.items():
                times[query][key].append(value)
    return times


def benchmark_report(times: dict[str, dict[str, list[float]]]):
    print('<table max-width="30%">')
    print('<tr><th width="10%">query</th>'
          + ''.join([f'<th width="10%">{name} (ms)</th>' for name in TIME_NAMES]) + '</tr>')

    for query, subtimes in times.items():
        time_strings = {name: stats_string(subtimes[name]) for name in TIME_NAMES}
        print(f'<tr><td><b>{query}</b></td>'
              + ''.join([f'<td>{time_strings[name]}</td>' for name in TIME_NAMES]) + '</tr>')

    aggregated_times = aggregate_stats(times)
    aggregated_time_strings = {name: stats_string(aggregated_times[name]) for name in TIME_NAMES}
    print(f'<tr><td><b>OVERALL</b></td>'
          + ''.join([f'<td><b>{aggregated_time_strings[name]}</b></td>' for name in TIME_NAMES]) + '</tr>')
    print('</table>')


if __name__ == '__main__':
    parser = ArgumentParser(description='Benchmark the NameGenerator collections search API')
    parser.add_argument('--host', type=str, default='localhost', help='host')
    parser.add_argument('--port', type=int, default=8000, help='port')
    parser.add_argument('--repeats', type=int, default=15, help='repeats')
    args = parser.parse_args()

    HOST = args.host
    PORT = args.port

    print(f'<h1>find_collections_by_string (instant)</h1>')
    times = collect_times(find_collections_by_string_instant_search, QUERIES, args.repeats)
    benchmark_report(times)

    print(f'<h1>find_collections_by_string (domain detail)</h1>')
    times = collect_times(find_collections_by_member_domain_detail, QUERIES, args.repeats)
    benchmark_report(times)

    print(f'<h1>find_collections_by_collection</h1>')
    times = collect_times(find_collections_by_collection, COLLECTION_IDS, args.repeats)
    benchmark_report(times)

    print(f'<h1>count_collections_by_member</h1>')
    times = collect_times(count_collections_by_member, MEMBERS, args.repeats)
    benchmark_report(times)

    print(f'<h1>find_collections_by_member (instant)</h1>')
    times = collect_times(find_collections_by_member_instant, MEMBERS, args.repeats)
    benchmark_report(times)
