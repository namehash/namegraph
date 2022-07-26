import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path
from time import time as get_time
from tqdm import tqdm

from generator.domains import Domains
from fastapi.testclient import TestClient


THIS_DIR = Path(__file__).parent
PROJECT_DIR = THIS_DIR.parent.parent

os.chdir(PROJECT_DIR)


def create_client():
    Domains.remove_self()
    os.environ['CONFIG_NAME'] = 'prod_config'
    if 'web_api' not in sys.modules:
        import web_api
    else:
        import web_api
        import importlib
        importlib.reload(web_api)
    client = TestClient(web_api.app)
    client.get("/?name=aaa.eth")
    return client


print('Creating client...')
client = create_client()


def run_test(
    name: str,
    score: bool,
    limit_confusables: bool,
    disable_chars_output: bool,
    disable_char_analysis: bool,
):
    durations = []
    response_size = None
    for _ in range(5):
        start = get_time()
        resp = client.post('/inspector/', json={
            'name': name,
            'score': score,
            'limit_confusables': limit_confusables,
            'disable_chars_output': disable_chars_output,
            'disable_char_analysis': disable_char_analysis,
            })
        duration = get_time() - start
        durations.append(duration)
        assert resp.status_code == 200

        response_size = len(resp.text)
    
    return np.mean(durations), response_size


default_results = []
no_score_results = []
limit_confusables_results = []
disable_chars_output_results = []
disable_char_analysis_results = []
no_score_limit_confusables_results = []
no_score_disable_chars_output_results = []

lengths = range(10_000, 40_001, 10_000)

print('Running tests...')
for l in tqdm(lengths):
    name = 'a' * l + '.eth'
    default_results.append(                       run_test(name, True,  False, False, False))
    no_score_results.append(                      run_test(name, False, False, False, False))
    limit_confusables_results.append(             run_test(name, True,  True,  False, False))
    disable_chars_output_results.append(          run_test(name, True,  False, True,  False))
    disable_char_analysis_results.append(         run_test(name, True,  False, False, True))
    no_score_limit_confusables_results.append(    run_test(name, False, True,  False, False))
    no_score_disable_chars_output_results.append( run_test(name, False, False, True,  False))


print('Drawing plots...')


plt.clf()
plt.plot(lengths, [r[0] for r in default_results], label='default')
plt.plot(lengths, [r[0] for r in no_score_results], label='no score')
plt.plot(lengths, [r[0] for r in limit_confusables_results], label='limit confusables')
plt.plot(lengths, [r[0] for r in disable_chars_output_results], label='disable chars output')
plt.plot(lengths, [r[0] for r in disable_char_analysis_results], label='disable char analysis')
plt.plot(lengths, [r[0] for r in no_score_limit_confusables_results], label='no score limit confusables')
plt.plot(lengths, [r[0] for r in no_score_disable_chars_output_results], label='no score disable chars output')
plt.legend()
plt.title('Duration')
plt.savefig(THIS_DIR / 'duration.png')


plt.clf()
plt.plot(lengths, [r[1] for r in default_results], label='default')
plt.plot(lengths, [r[1] for r in no_score_results], label='no score')
plt.plot(lengths, [r[1] for r in limit_confusables_results], label='limit confusables')
plt.plot(lengths, [r[1] for r in disable_chars_output_results], label='disable chars output')
plt.plot(lengths, [r[1] for r in disable_char_analysis_results], label='disable char analysis')
plt.plot(lengths, [r[1] for r in no_score_limit_confusables_results], label='no score limit confusables')
plt.plot(lengths, [r[1] for r in no_score_disable_chars_output_results], label='no score disable chars output')
plt.legend()
plt.title('Response size')
plt.savefig(THIS_DIR / 'response_size.png')


print('Done')
