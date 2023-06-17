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
    parser.add_argument('--limit_names', type=int, default=50, help='limit names')
    parser.add_argument('--host', type=str, default='localhost', help='host')
    parser.add_argument('--port', type=int, default=8000, help='port')
    parser.add_argument('--repeats', type=int, default=5, help='repeats')
    args = parser.parse_args()

    all_none_latencies = []
    all_names_cover_latencies = []
    all_types_cover_latencies = []
    all_combined_latencies = []

    all_none_tooks = []
    all_names_cover_tooks = []
    all_types_cover_tooks = []
    all_combined_tooks = []

    for query in tqdm.tqdm(args.queries):
        print(f'<h1>{query}</h1>')

        none_latencies = []
        names_cover_latencies = []
        types_cover_latencies = []
        combined_latencies = []

        none_tooks = []
        names_cover_tooks = []
        types_cover_tooks = []
        combined_tooks = []

        for _ in range(args.repeats):
            none, none_latency, none_took = \
                search_with_latency(query, args.limit, None, None, args.limit_names, host=args.host, port=args.port)
            names_cover, names_cover_latency, names_cover_took = \
                search_with_latency(query, args.limit, 0.5, None, args.limit_names, host=args.host, port=args.port)
            types_cover, types_cover_latency, types_cover_took = \
                search_with_latency(query, args.limit, None, 3, args.limit_names, host=args.host, port=args.port)
            combined, combined_latency, combined_took = \
                search_with_latency(query, args.limit, 0.5, 3, args.limit_names, host=args.host, port=args.port)

            none_latencies.append(none_latency)
            names_cover_latencies.append(names_cover_latency)
            types_cover_latencies.append(types_cover_latency)
            combined_latencies.append(combined_latency)

            none_tooks.append(none_took)
            names_cover_tooks.append(names_cover_took)
            types_cover_tooks.append(types_cover_took)
            combined_tooks.append(combined_took)

        all_none_latencies.extend(none_latencies)
        all_names_cover_latencies.extend(names_cover_latencies)
        all_types_cover_latencies.extend(types_cover_latencies)
        all_combined_latencies.extend(combined_latencies)

        all_none_tooks.extend(none_tooks)
        all_names_cover_tooks.extend(names_cover_tooks)
        all_types_cover_tooks.extend(types_cover_tooks)
        all_combined_tooks.extend(combined_tooks)

        same = none == names_cover == types_cover == combined
        print(f'<h2>{"same" if same else "diversified"}</h2>')

        names_cover_stayed = len(names_cover) - len(set(names_cover) - set(none))
        types_cover_stayed = len(types_cover) - len(set(types_cover) - set(none))
        combined_stayed = len(combined) - len(set(combined) - set(none))

        print('<table>')
        print(f'<tr><th width="15%">none '
              f'{np.mean(none_latencies):.3f} ± {np.std(none_latencies):.1f}ms'
              f' | took {np.mean(none_tooks):.3f} ± {np.std(none_tooks):.1f}ms</th>')
        print(f'<th width="15%">names-cover 🔴 '
              f'{np.mean(names_cover_latencies):.3f} ± {np.std(names_cover_latencies):.1f}ms'
              f' | took {np.mean(names_cover_tooks):.3f} ± {np.std(names_cover_tooks):.1f}ms</th>')
        print(f'<th width="15%">types-cover 🔵 '
              f'{np.mean(types_cover_latencies):.3f} ± {np.std(types_cover_latencies):.1f}ms'
              f' | took {np.mean(types_cover_tooks):.3f} ± {np.std(types_cover_tooks):.1f}ms</th>')
        print(f'<th width="15%">all 🟢 '
              f'{np.mean(combined_latencies):.3f} ± {np.std(combined_latencies):.1f}ms'
              f' | took {np.mean(combined_tooks):.3f} ± {np.std(combined_tooks):.1f}ms</th>')
        print(f'<th>empty</th></tr>')

        for i, (none_, names_cover_, types_cover_, combined_) in enumerate(zip(none, names_cover, types_cover, combined)):
            modifiers = [
                '🔴' if none_ not in names_cover else '',
                '🔵' if none_ not in types_cover else '',
                '🟢' if none_ not in combined else '',
            ]
            modifiers_str = ''.join(modifiers)

            names_cover_style = 'style="border-top: solid black;"' if i == names_cover_stayed else ''
            types_cover_style = 'style="border-top: solid black;"' if i == types_cover_stayed else ''
            combined_style = 'style="border-top: solid black;"' if i == combined_stayed else ''

            print(
                f'<tr>'
                f'<td>{none_}{modifiers_str}</td>'
                f'<td {names_cover_style}>{names_cover_}</td>'
                f'<td {types_cover_style}>{types_cover_}</td>'
                f'<td {combined_style}>{combined_}</td>'
                f'<td></td></tr>'
            )
            print()
        print('</table>')

    print(f'<h2>all times aggregated</h2>')
    print('<table>')
    print(f'<tr><th width="15%">none '
            f'{np.mean(all_none_latencies):.3f} ± {np.std(all_none_latencies):.1f}ms'
            f' | took {np.mean(all_none_tooks):.3f} ± {np.std(all_none_tooks):.1f}ms</th>')
    print(f'<th width="15%">names-cover 🔴 '
            f'{np.mean(all_names_cover_latencies):.3f} ± {np.std(all_names_cover_latencies):.1f}ms'
            f' | took {np.mean(all_names_cover_tooks):.3f} ± {np.std(all_names_cover_tooks):.1f}ms</th>')
    print(f'<th width="15%">types-cover 🔵 '
            f'{np.mean(all_types_cover_latencies):.3f} ± {np.std(all_types_cover_latencies):.1f}ms'
            f' | took {np.mean(all_types_cover_tooks):.3f} ± {np.std(all_types_cover_tooks):.1f}ms</th>')
    print(f'<th width="15%">all 🟢 '
            f'{np.mean(all_combined_latencies):.3f} ± {np.std(all_combined_latencies):.1f}ms'
            f' | took {np.mean(all_combined_tooks):.3f} ± {np.std(all_combined_tooks):.1f}ms</th>')
    print(f'<th>empty</th></tr>')
    print('</table>')
