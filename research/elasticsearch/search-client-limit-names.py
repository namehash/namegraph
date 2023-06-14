from argparse import ArgumentParser
from typing import Optional
import requests
import time
import tqdm

import numpy as np


def request_generator_http(
        query: str,
        limit: int,
        name_diversity_ratio: Optional[float],
        max_per_type: Optional[int],
        limit_names: Optional[int],
        host: str = 'localhost',
        port: int = 8000,
):
    data = {
        "query": query,
        "max_related_collections": limit,
        "min_other_collections": 0,
        "max_other_collections": 0,
        "max_total_collections": limit,
        "name_diversity_ratio": name_diversity_ratio,
        "max_per_type": max_per_type,
        "limit_names": limit_names,
    }
    return requests.post(
        f'http://{host}:{port}/find_collections_by_string',
        json=data,
    ).json()


def search_by_all(
        query: str,
        limit: int,
        name_diversity_ratio: Optional[float],
        max_per_type: Optional[int],
        limit_names: Optional[int],
        host: str = 'localhost',
        port: int = 8000,
):
    response = request_generator_http(
        query,
        limit,
        name_diversity_ratio,
        max_per_type,
        limit_names,
        host=host,
        port=port,
    )
    return response['related_collections'], \
           response['metadata']['processing_time_ms'], \
           response['metadata']['elasticsearch_processing_time_ms']


def search_with_latency(
        query: str,
        limit: int,
        name_diversity_ratio: Optional[float],
        max_per_type: Optional[int],
        limit_names: Optional[int],
        host: str = 'localhost',
        port: int = 8000,
):
    results, latency, took = search_by_all(
        query,
        limit,
        name_diversity_ratio,
        max_per_type,
        limit_names,
        host=host,
        port=port
    )
    titles = [hit['title'] for hit in results]
    return titles, latency, took


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('queries', nargs='+', help='queries')
    parser.add_argument('--limit', type=int, default=10, help='limit')
    parser.add_argument('--names_limits', type=int, nargs='+', default=[15, 50, 100], help='names limits')
    parser.add_argument('--host', type=str, default='localhost', help='host')
    parser.add_argument('--port', type=int, default=8000, help='port')
    parser.add_argument('--repeats', type=int, default=5, help='repeats')
    args = parser.parse_args()

    identifiers = '🟩🔴🔵🟢🟡🟠🟣🟤'

    if len(args.names_limits) > len(identifiers) - 1:
        raise ValueError(f'Too many names limits, can only support up to {len(identifiers) - 1}')

    names_limits = [None] + args.names_limits

    for query in tqdm.tqdm(args.queries):
        print(f'<h1>{query}</h1>')

        none_latencies = []
        names_covers_latencies = [[] for _ in names_limits]

        none_tooks = []
        names_covers_tooks = [[] for _ in names_limits]

        for _ in range(args.repeats):
            none, none_latency, none_took \
                = search_with_latency(query, args.limit, None, None, None, host=args.host, port=args.port)
            names_cover = [
                search_with_latency(query, args.limit, 0.5, None, limit, host=args.host, port=args.port)
                for limit in names_limits
            ]
            none_latencies.append(none_latency)
            none_tooks.append(none_took)
            for i, (_, latency, took) in enumerate(names_cover):
                names_covers_latencies[i].append(latency)
                names_covers_tooks[i].append(took)


        names_cover_stayed = [len(res) - len(set(res) - set(none)) for (res, _, _) in names_cover]

        same = all([
            res == names_cover[0][0]
            for (res, _, _) in names_cover
        ])
        print(f'<h2>{"same" if same else "impacted"}</h2>')

        print('<table>')
        print(f'<tr><th width="15%">none {np.mean(none_latencies):.3f} ± {np.std(none_latencies):.1f}ms</th>', end='')
        for limit, identifier, latencies, tooks in zip(names_limits, identifiers, names_covers_latencies, names_covers_tooks):
            latency = np.mean(latencies)
            latency_std = np.std(latencies)
            took = np.mean(tooks)
            took_std = np.std(tooks)
            print(f'<th width="10%">names-cover {limit} {identifier} {latency:.3f} ± {latency_std:.1f}ms '
                  f'| took {took:.3f} ± {took_std:.1f}ms</th>', end='')
        print(f'<th>empty</th></tr>')

        for i, none_ in enumerate(none):
            modifiers = ''.join([
                identifier
                for identifier, (res, _, _) in zip(identifiers, names_cover)
                if none_ not in res
            ])

            print(f'<tr><td>{none_}{modifiers}</td>', end='')
            for stayed, (res, _, _) in zip(names_cover_stayed, names_cover):
                style = 'style="border-top: solid black;"' if i == stayed else ''
                print(f'<td {style}>{res[i]}</td>', end='')
            print('<td></td></tr>')

        print('</table>')
