from argparse import ArgumentParser
from typing import Optional
import requests
import time
import tqdm


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
    return response['related_collections'], response['metadata']['processing_time_ms']


def search_with_latency(
        query: str,
        limit: int,
        name_diversity_ratio: Optional[float],
        max_per_type: Optional[int],
        limit_names: Optional[int],
        host: str = 'localhost',
        port: int = 8000,
):
    results, latency = search_by_all(
        query,
        limit,
        name_diversity_ratio,
        max_per_type,
        limit_names,
        host=host,
        port=port
    )
    titles = [hit['title'] for hit in results]
    return titles, latency


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('queries', nargs='+', help='queries')
    parser.add_argument('--limit', type=int, default=10, help='limit')
    parser.add_argument('--names_limits', type=int, nargs='+', default=[15, 50, 100], help='names limits')
    parser.add_argument('--host', type=str, default='localhost', help='host')
    parser.add_argument('--port', type=int, default=8000, help='port')
    args = parser.parse_args()

    identifiers = '🟩🔴🔵🟢🟡🟠🟣🟤'

    if len(args.names_limits) > len(identifiers) - 1:
        raise ValueError(f'Too many names limits, can only support up to {len(identifiers) - 1}')

    names_limits = [None] + args.names_limits

    for query in tqdm.tqdm(args.queries):
        print(f'<h1>{query}</h1>')

        none, none_latency = search_with_latency(query, args.limit, None, None, None, host=args.host, port=args.port)
        names_cover = [
            search_with_latency(query, args.limit, 0.5, None, limit, host=args.host, port=args.port)
            for limit in names_limits
        ]
        names_cover_stayed = [len(res) - len(set(res) - set(none)) for (res, _) in names_cover]

        same = all([
            res == names_cover[0][0]
            for (res, _) in names_cover
        ])
        print(f'<h2>{"same" if same else "impacted"}</h2>')

        print('<table>')
        print(f'<tr><th width="15%">none {none_latency:.3f}ms</th>', end='')
        for limit, identifier, (_, latency) in zip(names_limits, identifiers, names_cover):
            print(f'<th width="10%">names-cover {limit} {identifier} {latency:.3f}ms</th>', end='')
        print(f'<th>empty</th></tr>')

        for i, none_ in enumerate(none):
            modifiers = ''.join([
                identifier
                for identifier, (res, _) in zip(identifiers, names_cover)
                if none_ not in res
            ])

            print(f'<tr><td>{none_}{modifiers}</td>', end='')
            for stayed, (res, _) in zip(names_cover_stayed, names_cover):
                style = 'style="border-top: solid black;"' if i == stayed else ''
                print(f'<td {style}>{res[i]}</td>', end='')
            print('<td></td></tr>')

        print('</table>')
