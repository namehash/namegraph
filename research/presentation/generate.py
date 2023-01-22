import collections
import sys
import os
import argparse

from generator.domains import Domains
from fastapi.testclient import TestClient


# TODO position of first appearance
# TODO 

def prod_test_client(config):
    Domains.remove_self()
    os.environ['CONFIG_NAME'] = config
    # TODO lower generator log verbosity
    if 'web_api' not in sys.modules:
        import web_api
    else:
        import web_api
        import importlib
        importlib.reload(web_api)
    client = TestClient(web_api.app)
    client.get("/?name=aaa.eth")
    return client


def request_generator_client(name, override=None):
    data = {
        'name': name,
        'metadata': True,
        'min_suggestions': 100,
        'max_suggestions': 100,
        "min_primary_fraction": 0.1,
        "params": {
            'conservative': False,
            'country': 'pl'
        }
    }
    if override:
        data.update(override)
    return client.post('/', json=data)


import requests


def request_generator_http(host, name, override=None):
    data = {
        'name': name,
        'metadata': True,
        'min_suggestions': 100,
        'max_suggestions': 100,
        "min_primary_fraction": 0.1,
        "params": {
            'conservative': False,
            'country': 'pl'
        }
    }
    if override:
        data.update(override)
    return requests.post(host, json=data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Presents suggestions for set of names for each generator.')
    parser.add_argument('--host', default='http://127.0.0.1:8000', help='host with name generator web apo')
    parser.add_argument('-c', '--config', default=None, choices=['prod_config', 'test_config'],
                        help=f'config name, if None then host is used')
    parser.add_argument('-o', '--output', default='test_generators.html', help='path to output HTML file')
    args = parser.parse_args()

    print('Creating client...')
    if args.config:
        client = prod_test_client(args.config)
        request_fn = request_generator_client
    else:
        request_fn = lambda name, override: request_generator_http(args.host, name, override)

    input_names = ['fire', 'funny', 'funnyshit', 'funnyshitass', 'funnyshitshit', 'lightwalker', 'josiahadams',
                   'kwrobel', 'krzysztofwrobel', 'pikachu', 'mickey', 'adoreyoureyes', 'face', 'theman', 'goog',
                   'billycorgan', '[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91]', 'a' * 101,
                   'dogcat', 'firepower', 'tubeyou', 'fireworks', 'hacker', 'firecar', '😊😊😊', 'anarchy',
                   'prayforukraine', 'krakowdragon', 'fiftysix', 'あかまい', '💛', 'asd', 'bartek', 'hongkong', 'hongkonger',
                   'tyler', 'asdfasdfasdf3453212345', 'nineinchnails', 'krakow', 'joebiden', 'europeanunion',
                   'rogerfederer', 'suzuki', 'pirates', 'doge', 'ethcorner', 'google', 'apple', '001',
                   'stop-doing-fake-bids-its-honestly-lame-my-guy', 'kfcsogood', 'wallet', 'الأبيض', 'porno', 'sex',
                   'slutwife', 'god', 'imexpensive', 'htaccess', 'nike', '€80000', 'starbucks', 'ukraine', '٠٠٩',
                   'sony', 'kevin', 'discord', 'monaco', 'market', 'sportsbet', 'volodymyrzelensky', 'coffee', 'gold',
                   'hodl', 'yeezy', 'brantly', 'jeezy', 'vitalik', 'exampleregistration', 'pyme', 'avalanche', 'messy',
                   'messi', 'kingmessi', 'abc', 'testing', 'superman', 'facebook', 'test', 'namehash', 'testb']

    f = open(args.output, 'w')

    f.write('''<style>
section {
    display: flex;
}
.g100 ol {
    list-style-type: none;
    padding: 0;
}
div {
    padding: 10px;
    flex-shrink: 0;
}
.all100 {
    flex-basis: 600px;
}
</style>''')

    stats = collections.defaultdict(list)
    mrr = collections.defaultdict(list)
    first_position = collections.defaultdict(list)
    all_positions = collections.defaultdict(list)
    for input_name in input_names:
        f.write(f'<h1>{input_name}</h1>')

        f.write(f'<section>')

        # START INSTANT
        instant_r = request_fn(input_name, {
            'min_suggestions': 3,
            'max_suggestions': 3,
            "min_primary_fraction": 1.0,
            "params": {
                'conservative': True,
                'country': 'pl'
            }}).json()
        print(instant_r)
        f.write(f'<div>')
        f.write(f'<h2>instant</h2>')
        f.write(f'<ol>')
        for s in instant_r:
            generators = []
            for strategy in s['metadata']['applied_strategies']:
                for processor in strategy:
                    if 'Generator' in processor:
                        generators.append(processor.replace('Generator', ''))
            f.write(f'<li>{s["name"].replace(".eth", "")} ({", ".join(generators)})</li>')
        f.write(f'</ol>')
        f.write(f'</div>')
        # END INSTANT

        # START NAME other ideas
        name_r = request_fn(input_name, {
            'min_suggestions': 5,
            'max_suggestions': 5,
            "min_primary_fraction": 0.1,
            "params": {
                'conservative': True,
                'country': 'pl'
            }}).json()

        f.write(f'<div>')
        f.write(f'<h2>/name</h2>')
        f.write(f'<ol>')
        for s in name_r:
            generators = []
            for strategy in s['metadata']['applied_strategies']:
                for processor in strategy:
                    if 'Generator' in processor:
                        generators.append(processor.replace('Generator', ''))
            f.write(f'<li>{s["name"].replace(".eth", "")} ({", ".join(generators)})</li>')
        f.write(f'</ol>')
        f.write(f'</div>')
        # END NAME

        # START 100
        name_r = request_fn(input_name, {
            'min_suggestions': 100,
            'max_suggestions': 100,
            "min_primary_fraction": 0.1,
            "params": {
                'conservative': False,
                'country': 'pl'
            }}).json()

        generated = len(name_r)

        f.write(f'<div class="all100">')
        f.write(f'<h2>100 ideas generated</h2>')
        f.write(f'<p>')
        for data in name_r:
            f.write(f'{data["name"].replace(".eth", "")} ')
        f.write(f'</p>')
        f.write(f'</div>')

        generators = collections.defaultdict(list)
        for i, s in enumerate(name_r):
            for strategy in s['metadata']['applied_strategies']:
                for processor in strategy:
                    if 'Generator' in processor:
                        generator_name = processor.replace('Generator', '')
                        generators[generator_name].append((s["name"], i))

        for generator_name, names in sorted(generators.items()):
            stats[generator_name].append(len(names) / generated)
            f.write(f'<div class="g100">')
            f.write(f'<h3>{generator_name} {(100 * len(names) / generated):.2f}%</h3>')
            f.write(f'<ol>')

            mrr[generator_name].append(1 / (names[0][1] + 1))
            first_position[generator_name].append(names[0][1] + 1)
            positions = []
            for name, i in names:
                f.write(f'<li>{i + 1}. {name.replace(".eth", "")}</li>')
                positions.append(i + 1)
            f.write(f'</ol>')
            all_positions[generator_name].append(positions)

            f.write(f'</div>')
        # END 100

        f.write(f'</section>')

    f.write(f'<h1>Mean share</h1>')
    for generator_name, values in sorted(stats.items(), key=lambda x: sum(x[1]), reverse=True):
        f.write(f'<p>{(100 * sum(values) / len(input_names)):.2f}% {generator_name}</p>')

    f.write(f'<h1>MRR</h1>')
    for generator_name, values in sorted(mrr.items(), key=lambda x: sum(x[1]), reverse=True):
        f.write(f'<p>{(sum(values) / len(input_names)):.2f} {generator_name}</p>')

    f.write(f'<h1>First position</h1>')
    for generator_name, values in sorted(first_position.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=False):
        f.write(f'<p>{(sum(values) / len(values)):.2f} {generator_name}</p>')

    f.write(f'<h1>MAP</h1>')
    maps = []
    for generator_name, positions_lists in all_positions.items():
        map = []
        for positions in positions_lists:
            ap = []
            for i, position in enumerate(positions):
                ap.append((i + 1) / position)
            map.append(sum(ap) / len(ap))
        maps.append((sum(map) / len(input_names), generator_name))

    for map, generator_name in sorted(maps, reverse=True):
        f.write(f'<p>{map:.2f} {generator_name}</p>')

    f.write(f'<h1>MAP /map</h1>')
    maps = []
    for generator_name, positions_lists in all_positions.items():
        map = []
        for positions in positions_lists:
            ap = []
            for i, position in enumerate(positions):
                ap.append((i + 1) / position)
            map.append(sum(ap) / len(ap))
        maps.append((sum(map) / len(map), generator_name))

    for map, generator_name in sorted(maps, reverse=True):
        f.write(f'<p>{map:.2f} {generator_name}</p>')