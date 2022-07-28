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
    label: str,
    tokenization: bool,
    limit_confusables: bool,
    truncate_chars_output: int,
    disable_char_analysis: bool,
):
    durations = []
    response_size = None
    for _ in range(5):
        start = get_time()
        resp = client.post('/inspector/', json={
            'label': label,
            'tokenization': tokenization,
            'limit_confusables': limit_confusables,
            'truncate_chars_output': truncate_chars_output,
            'disable_char_analysis': disable_char_analysis,
            })
        duration = get_time() - start
        durations.append(duration)
        assert resp.status_code == 200

        response_size = len(resp.text)
    
    return np.mean(durations), response_size


default_results = []
no_tokenization_results = []
limit_confusables_results = []
truncate_chars_output_results = []
disable_char_analysis_results = []
no_tokenization_limit_confusables_results = []
no_tokenization_truncate_chars_output_results = []

lengths = range(10_000, 40_001, 10_000)

print('Running tests...')
for l in tqdm(lengths):
    name = 'a' * l + '.eth'
    default_results.append(                              run_test(name, True,  False, None, False))
    no_tokenization_results.append(                      run_test(name, False, False, None, False))
    limit_confusables_results.append(                    run_test(name, True,  True,  None, False))
    truncate_chars_output_results.append(                run_test(name, True,  False, 0,    False))
    disable_char_analysis_results.append(                run_test(name, True,  False, None, True))
    no_tokenization_limit_confusables_results.append(    run_test(name, False, True,  None, False))
    no_tokenization_truncate_chars_output_results.append(run_test(name, False, False, 0,    False))


print('Drawing plots...')


plt.clf()
plt.plot(lengths, [r[0] for r in default_results])
plt.title('Duration - default')
plt.savefig(THIS_DIR / 'duration_default.png')

plt.clf()
plt.plot(lengths, [r[0] for r in no_tokenization_results])
plt.title('Duration - no tokenization')
plt.savefig(THIS_DIR / 'duration_no_tokenization.png')

plt.clf()
plt.plot(lengths, [r[0] for r in limit_confusables_results])
plt.title('Duration - limit confusables')
plt.savefig(THIS_DIR / 'duration_limit_confusables.png')

plt.clf()
plt.plot(lengths, [r[0] for r in truncate_chars_output_results])
plt.title('Duration - truncate chars output')
plt.savefig(THIS_DIR / 'duration_truncate_chars_output.png')

plt.clf()
plt.plot(lengths, [r[0] for r in disable_char_analysis_results])
plt.title('Duration - disable char analysis')
plt.savefig(THIS_DIR / 'duration_disable_char_analysis.png')

plt.clf()
plt.plot(lengths, [r[0] for r in no_tokenization_limit_confusables_results])
plt.title('Duration - no tokenization limit confusables')
plt.savefig(THIS_DIR / 'duration_no_tokenization_limit_confusables.png')

plt.clf()
plt.plot(lengths, [r[0] for r in no_tokenization_truncate_chars_output_results])
plt.title('Duration - no tokenization truncate chars output')
plt.savefig(THIS_DIR / 'duration_no_tokenization_truncate_chars_output.png')


plt.clf()
plt.plot(lengths, [r[1] for r in default_results])
plt.title('Size - default')
plt.savefig(THIS_DIR / 'size_default.png')

plt.clf()
plt.plot(lengths, [r[1] for r in no_tokenization_results])
plt.title('Size - no tokenization')
plt.savefig(THIS_DIR / 'size_no_tokenization.png')

plt.clf()
plt.plot(lengths, [r[1] for r in limit_confusables_results])
plt.title('Size - limit confusables')
plt.savefig(THIS_DIR / 'size_limit_confusables.png')

plt.clf()
plt.plot(lengths, [r[1] for r in truncate_chars_output_results])
plt.title('Size - truncate chars output')
plt.savefig(THIS_DIR / 'size_truncate_chars_output.png')

plt.clf()
plt.plot(lengths, [r[1] for r in disable_char_analysis_results])
plt.title('Size - disable char analysis')
plt.savefig(THIS_DIR / 'size_disable_char_analysis.png')

plt.clf()
plt.plot(lengths, [r[1] for r in no_tokenization_limit_confusables_results])
plt.title('Size - no tokenization limit confusables')
plt.savefig(THIS_DIR / 'size_no_tokenization_limit_confusables.png')

plt.clf()
plt.plot(lengths, [r[1] for r in no_tokenization_truncate_chars_output_results])
plt.title('Size - no tokenization truncate chars output')
plt.savefig(THIS_DIR / 'size_no_tokenization_truncate_chars_output.png')


print('Done')
