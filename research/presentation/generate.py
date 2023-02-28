import collections
import sys
import os
import argparse
import time

import numpy as np
import regex
from tqdm import tqdm

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
            'country': 'pl'
        }
    }
    if override:
        data.update(override)
    return requests.post(host, json=data)


def interpretation_str(interpretation):
    try:
        interpretation = interpretation["interpretation"]
        type, lang, feat = interpretation
        return f'{type} {lang} {feat}'
    except KeyError:
        return ''


def write(s: str, keep_time=False, print_wo_time=True, stats=False):
    f.write(s)
    f.write('\n')
    f_current.write(s)
    f_current.write('\n')

    if stats:
        f_current_stats.write(s)
        f_current_stats.write('\n')

    if not keep_time:
        s = regex.sub(r' ?(\d+\.\d+ ms|\(\d+\.\d+ ms\))', '', s)
    if print_wo_time:
        f_current_wo_times.write(s)
        f_current_wo_times.write('\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Presents suggestions for set of names for each generator.')
    parser.add_argument('--host', default='http://127.0.0.1:8000', help='host with name generator web apo')
    parser.add_argument('-c', '--config', default=None, choices=['prod_config_new', 'test_config_new', 'prod_config'],
                        help=f'config name, if None then host is used')
    parser.add_argument('-o', '--output', default='test_generators.html', help='path to output HTML file')
    args = parser.parse_args()

    print('Creating client...')
    if args.config:
        client = prod_test_client(args.config)
        request_fn = request_generator_client
    else:
        request_fn = lambda name, override: request_generator_http(args.host, name, override)

    for name in ['cat', 'ice']:
        request_fn(name, {
            'min_suggestions': 100,
            'max_suggestions': 100,
            "min_primary_fraction": 1.0,
            "params": {
                'country': 'pl'
            }})

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
                   'messi', 'kingmessi', 'abc', 'testing', 'superman', 'facebook', 'test', 'namehash', 'testb',
                   'happypeople', 'muscle', 'billybob', 'quo', 'circleci', 'bitcoinmine', 'poweroutage',
                   'shootingarrowatthesky']

    # 'happypeople', 'muscle', 'billybob' (2 leet in instant), 'quo' (instant 2 flag suggestions)

    f_current = open('research/presentation/reports/current.html', 'w')
    f_current_wo_times = open('research/presentation/reports/current_wo_times.html', 'w')
    f_current_stats = open('research/presentation/reports/current_stats.html', 'w')
    f = open(args.output, 'w')

    write('''<style>
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
span.i {
    color: grey;
}
</style>''')

    stats = collections.defaultdict(list)
    mrr = collections.defaultdict(list)
    first_position = collections.defaultdict(list)
    all_positions = collections.defaultdict(list)
    times = []

    request_times = collections.defaultdict(list)
    for input_name in tqdm(input_names):
        write(f'<h1>{input_name}</h1>')

        write(f'<section>')

        # START INSTANT
        start_time = time.time()
        instant_r = request_fn(input_name, {
            'min_suggestions': 3,
            'max_suggestions': 3,
            "min_primary_fraction": 1.0,
            "params": {
                'country': 'pl',
                'mode': 'instant'
            }}).json()
        request_time = time.time() - start_time
        request_times['instant'].append(request_time)
        times.append((request_time, input_name, 'instant'))
        print(instant_r)
        write(f'<div>')
        write(f'<h2>instant ({request_time * 1000:.2f} ms)</h2>')
        write(f'<ol>')
        for s in instant_r:
            generators = []
            for strategy in s['metadata']['applied_strategies']:
                for processor in strategy:
                    if 'Generator' in processor:
                        generators.append(processor.replace('Generator', ''))
            write(
                f'<li>{s["name"].replace(".eth", "")} <span class="i">({", ".join(generators)}, {interpretation_str(s["metadata"])})</span></li>')
        write(f'</ol>')
        write(f'</div>')
        # END INSTANT

        # START NAME other ideas
        start_time = time.time()
        name_r = request_fn(input_name, {
            'min_suggestions': 5,
            'max_suggestions': 5,
            "min_primary_fraction": 0.1,
            "params": {
                'country': 'pl',
                'mode': 'domain_detail'
            }}).json()
        request_time = time.time() - start_time
        request_times['top5'].append(request_time)
        times.append((request_time, input_name, 'top5'))

        write(f'<div>')
        write(f'<h2>/name ({request_time * 1000:.2f} ms)</h2>')
        write(f'<ol>')
        for s in name_r:
            generators = []
            for strategy in s['metadata']['applied_strategies']:
                for processor in strategy:
                    if 'Generator' in processor:
                        generators.append(processor.replace('Generator', ''))
            write(
                f'<li>{s["name"].replace(".eth", "")} <span class="i">({", ".join(generators)}, {interpretation_str(s["metadata"])})</span></li>')
        write(f'</ol>')
        write(f'</div>')
        # END NAME

        # START 100
        start_time = time.time()
        name_r = request_fn(input_name, {
            'min_suggestions': 100,
            'max_suggestions': 100,
            "min_primary_fraction": 0.1,
            "params": {
                'country': 'pl',
                'mode': 'full'
            }}).json()
        request_time = time.time() - start_time
        request_times['100'].append(request_time)
        times.append((request_time, input_name, '100'))

        generated = len(name_r)

        write(f'<div class="all100">')
        write(f'<h2>100 ideas generated ({request_time * 1000:.2f} ms)</h2>')
        write(f'<p>')
        for data in name_r:
            write(f'{data["name"].replace(".eth", "")} ')
        write(f'</p>')
        write(f'</div>')

        generators = collections.defaultdict(list)
        for i, s in enumerate(name_r):
            for strategy in s['metadata']['applied_strategies']:
                for processor in strategy:
                    if 'Generator' in processor:
                        generator_name = processor.replace('Generator', '')
                        generators[generator_name].append((s["name"], i))

        for generator_name, names in sorted(generators.items()):
            stats[generator_name].append(len(names) / generated)
            write(f'<div class="g100">')
            write(f'<h3>{generator_name} {(100 * len(names) / generated):.2f}%</h3>')
            write(f'<ol>')

            mrr[generator_name].append(1 / (names[0][1] + 1))
            first_position[generator_name].append(names[0][1] + 1)
            positions = []
            for name, i in names:
                write(f'<li>{i + 1}. {name.replace(".eth", "")}</li>')
                positions.append(i + 1)
            write(f'</ol>')
            all_positions[generator_name].append(positions)

            write(f'</div>')
        # END 100

        write(f'</section>')

    write(f'<h1>Average times</h1>', stats=True)
    for mode, values in request_times.items():
        write(
            f'<p>{mode}: avg {(1000 * sum(values) / len(values)):.2f} ms, median {1000 * np.median(values):.2f} ms</p>',
            keep_time=True, stats=True)

    write(f'<h1>Times</h1>')
    for request_time, name, mode in sorted(times, reverse=True):
        write(f'<p>{1000 * request_time:.2f} ms {name} {mode}</p>', print_wo_time=False)

    write(f'<h1>Mean share</h1>', stats=True)
    for generator_name, values in sorted(stats.items(), key=lambda x: sum(x[1]), reverse=True):
        write(f'<p>{(100 * sum(values) / len(input_names)):.2f}% {generator_name}</p>', stats=True)

    write(f'<h1>MRR</h1>', stats=True)
    for generator_name, values in sorted(mrr.items(), key=lambda x: sum(x[1]), reverse=True):
        write(f'<p>{(sum(values) / len(input_names)):.2f} {generator_name}</p>', stats=True)

    write(f'<h1>First position</h1>', stats=True)
    for generator_name, values in sorted(first_position.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=False):
        write(f'<p>{(sum(values) / len(values)):.2f} {generator_name}</p>', stats=True)

    write(f'<h1>MAP</h1>', stats=True)
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
        write(f'<p>{map:.2f} {generator_name}</p>', stats=True)

    write(f'<h1>MAP /map</h1>', stats=True)
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
        write(f'<p>{map:.2f} {generator_name}</p>', stats=True)
