from argparse import ArgumentParser
import requests
import time
import tqdm


def request_generator_http(query: str, limit: int, diversify_mode: str):
    data = {
        "query": query,
        "limit": limit,
        "diversify_mode": diversify_mode
    }
    return requests.post('http://localhost:8000/collections/featured', json=data).json()


def search_by_all(query: str, limit: int, diversify_mode: str):
    return request_generator_http(query, limit, diversify_mode)


def search_with_latency(query: str, limit: int, diversify_mode: str):
    t0 = time.time()
    results = [hit['title'] for hit in search_by_all(query, limit, diversify_mode)]
    return results, time.time() - t0


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('queries', nargs='+', help='queries')
    parser.add_argument('--limit', type=int, default=10, help='limit')
    args = parser.parse_args()

    for query in tqdm.tqdm(args.queries):
        print(f'<h1>{query}</h1>')

        all_collections = [hit['title'] for hit in search_by_all(query, args.limit * 3, 'none')]
        none, none_latency = search_with_latency(query, args.limit, 'none')
        names_cover, names_cover_latency = search_with_latency(query, args.limit, 'names-cover')
        types_cover, types_cover_latency = search_with_latency(query, args.limit, 'types-cover')
        combined, combined_latency = search_with_latency(query, args.limit, 'all')

        same = none == names_cover == types_cover == combined
        print(f'<h2>{"same" if same else "diversified"}</h2>')

        print(' '.join(all_collections))

        names_cover_stayed = len(names_cover) - len(set(names_cover) - set(none))
        types_cover_stayed = len(types_cover) - len(set(types_cover) - set(none))
        combined_stayed = len(combined) - len(set(combined) - set(none))

        print('<table>')
        print(f'<tr><th width="15%">none {none_latency:.3f}s</th>'
              f'<th width="15%">names-cover 🔴 {names_cover_latency:.3f}s</th>'
              f'<th width="15%">types-cover 🔵 {types_cover_latency:.3f}s</th>'
              f'<th width="15%">all 🟢 {combined_latency:.3f}s</th>'
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
