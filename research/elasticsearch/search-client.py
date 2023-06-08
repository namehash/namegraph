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
    parser.add_argument('--limit_names', type=int, default=50, help='limit names')
    parser.add_argument('--host', type=str, default='localhost', help='host')
    parser.add_argument('--port', type=int, default=8000, help='port')
    args = parser.parse_args()

    for query in tqdm.tqdm(args.queries):
        print(f'<h1>{query}</h1>')

        none, none_latency = \
            search_with_latency(query, args.limit, None, None, None, host=args.host, port=args.port)
        names_cover, names_cover_latency = \
            search_with_latency(query, args.limit, 0.5, None, args.limit_names, host=args.host, port=args.port)
        types_cover, types_cover_latency = \
            search_with_latency(query, args.limit, None, 3, args.limit_names, host=args.host, port=args.port)
        combined, combined_latency = \
            search_with_latency(query, args.limit, 0.5, 3, args.limit_names, host=args.host, port=args.port)

        same = none == names_cover == types_cover == combined
        print(f'<h2>{"same" if same else "diversified"}</h2>')

        names_cover_stayed = len(names_cover) - len(set(names_cover) - set(none))
        types_cover_stayed = len(types_cover) - len(set(types_cover) - set(none))
        combined_stayed = len(combined) - len(set(combined) - set(none))

        print('<table>')
        print(f'<tr><th width="15%">none {none_latency:.3f}ms</th>'
              f'<th width="15%">names-cover 🔴 {names_cover_latency:.3f}ms</th>'
              f'<th width="15%">types-cover 🔵 {types_cover_latency:.3f}ms</th>'
              f'<th width="15%">all 🟢 {combined_latency:.3f}ms</th>'
              f'<th>empty</th></tr>')

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
