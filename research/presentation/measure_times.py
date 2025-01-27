import collections
import sys
import os
import argparse
import time

import numpy as np
from tqdm import tqdm

from namegraph.domains import Domains
from fastapi.testclient import TestClient


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
    client.get("/?name=aaa")
    return client


def request_generator_client(name, override=None):
    data = {
        'label': name,
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
    # time.sleep(0.1)
    data = {
        'label': name,
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

    input_labels = ['fire', 'funny', 'funnyshit', 'funnyshitass', 'funnyshitshit', 'lightwalker', 'josiahadams',
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
span.i {
    color: grey;
}
</style>''')

    stats = collections.defaultdict(list)
    mrr = collections.defaultdict(list)
    first_position = collections.defaultdict(list)
    all_positions = collections.defaultdict(list)
    times = collections.defaultdict(list)

    request_times = collections.defaultdict(list)
    generators = {}

    # input_labels = input_labels[:10]
    for i in range(10):
        for input_label in tqdm(input_labels):
            # START INSTANT
            start_time = time.time()
            instant_r = request_fn(input_label, {
                'min_suggestions': 3,
                'max_suggestions': 3,
                "min_primary_fraction": 1.0,
                "params": {
                    'country': 'pl',
                    'mode': 'instant'
                }}).json()
            request_time = time.time() - start_time
            request_times['instant'].append(request_time)
            times[(input_label, 'instant')].append(request_time)

            # START NAME other ideas
            start_time = time.time()
            name_r = request_fn(input_label, {
                'min_suggestions': 5,
                'max_suggestions': 5,
                "min_primary_fraction": 0.1,
                "params": {
                    'country': 'pl',
                    'mode': 'domain_detail'
                }}).json()
            request_time = time.time() - start_time
            request_times['top5'].append(request_time)
            times[(input_label, 'top5')].append(request_time)

            # START 100
            start_time = time.time()
            name_r = request_fn(input_label, {
                'min_suggestions': 100,
                'max_suggestions': 100,
                "min_primary_fraction": 0.1,
                "params": {
                    'country': 'pl'
                }}).json()
            request_time = time.time() - start_time
            request_times['100'].append(request_time)
            times[(input_label, '100')].append(request_time)

            name_generators = set()
            for i, s in enumerate(name_r):
                for strategy in s['metadata']['applied_strategies']:
                    for processor in strategy:
                        if 'Generator' in processor:
                            generator_name = processor.replace('Generator', '')
                            name_generators.add(generator_name)
            generators[(input_label, '100')] = list(sorted(name_generators))

    f.write(f'<h1>Average times</h1>')
    for mode, values in request_times.items():
        f.write(
            f'<p>{mode}: avg {(1000 * sum(values) / len(values)):.2f} ms, median {1000 * np.median(values):.2f} ms</p>')

    f.write(f'<h1>Times</h1>')
    for (name, mode), values in sorted(times.items(), reverse=True, key=lambda x: np.std(x[1])):
        avg = np.mean(values)
        median = np.median(values)
        std = np.std(values)
        values_str = ', '.join([f'{1000 * x:.2f}' for x in values])
        try:
            gen_str = ', '.join(generators[(name, mode)])
        except:
            gen_str = ''
        f.write(
            f'<p>{name} {mode} - avg: {1000 * avg:.2f} ms, median: {1000 * median:.2f} ms, std: {1000 * std:.2f} ms, ({values_str}) - {gen_str}</p>')
