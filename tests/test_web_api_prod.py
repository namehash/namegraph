import os
import sys
from time import time as get_time

import pytest
from fastapi.testclient import TestClient

from generator.domains import Domains

from .helpers import check_inspector_response, check_generator_response, generate_example_names


@pytest.fixture(scope="module")
def prod_test_client():
    Domains.remove_self()
    # TODO override 'generation.wikipedia2vec_path=tests/data/wikipedia2vec.pkl'
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


@pytest.mark.slow
def test_get_namehash(prod_test_client):
    client = prod_test_client
    response = client.get("/?name=[003fda97309fd6aa9d7753dcffa37da8bb964d0fb99eba99d0770e76fc5bac91].eth")

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']


@pytest.mark.slow
def test_prod(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "fire"})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "myfire" in primary


@pytest.mark.execution_timeout(10)
@pytest.mark.slow
def test_prod_long(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "a" * 40000})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])


@pytest.mark.execution_timeout(10)
@pytest.mark.slow
def test_prod_long_get(prod_test_client):
    client = prod_test_client
    response = client.get("/?name=" + 'a' * 40000)

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])


@pytest.mark.execution_timeout(10)
@pytest.mark.slow
def test_prod_inspector_long_post(prod_test_client):
    client = prod_test_client
    response = client.post("/inspector/",
                           json={'label': "miinibaashkiminasiganibiitoosijiganibadagwiingweshiganibakwezhigan"})

    assert response.status_code == 200

    json = response.json()

    assert 'label' in json
    assert json['tokenizations'] is None


@pytest.mark.execution_timeout(10)
@pytest.mark.slow
def test_prod_inspector_long2_post(prod_test_client):
    client = prod_test_client
    response = client.post("/inspector/", json={'label': 'a' * 40000})

    assert response.status_code == 200

    json = response.json()
    assert 'label' in json
    assert json['tokenizations'] is None


@pytest.mark.slow
def test_inspector_basic(prod_test_client):
    label = 'cat'
    response = prod_test_client.post('/inspector/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)

    assert json['word_count'] == 1
    assert json['all_class'] == 'simple_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert 0 < json['probability']
    assert json['any_classes'] == ['simple_letter']
    assert json['all_unicodeblock'] == 'BASIC_LATIN'
    assert json['ens_is_valid_name']
    assert json['ens_nameprep'] == label
    assert json['idna_encode'] == label
    assert 0 < json['score']

    # order of the returned characters must match input name
    for char, name_char in zip(json['chars'], label):
        assert char['script'] == 'Latin'
        assert char['name'] == f'LATIN SMALL LETTER {name_char.upper()}'
        assert char['char_class'] == 'simple_letter'
        assert char['unicodedata_category'] == 'Ll'
        assert char['unicodeblock'] == 'BASIC_LATIN'
        assert char['confusables'] == []

    tokenization = sorted(json['tokenizations'], key=lambda t: t['probability'])[-1]
    tok = tokenization['tokens'][0]
    assert tok['token'] == label
    assert tok['length'] == len(label)
    assert tok['pos'] == 'NOUN'
    assert tok['lemma'] == label


@pytest.mark.slow
def test_inspector_special(prod_test_client):
    label = 'żółć'
    response = prod_test_client.post('/inspector/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)

    assert json['word_count'] == 0
    assert json['all_class'] == 'any_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert json['probability'] == 0
    assert json['any_classes'] == ['any_letter']
    assert json['all_unicodeblock'] is None
    assert json['ens_is_valid_name']
    assert json['ens_nameprep'] == label
    assert json['idna_encode'] == 'xn--kda4b0koi'
    assert 0 < json['score']

    # order of the returned characters must match input name
    for char, canonical_char in zip(json['chars'], 'zolc'):
        assert char['script'] == 'Latin'
        assert char['name'].startswith(f'LATIN SMALL LETTER {canonical_char.upper()}')
        assert char['char_class'] == 'any_letter'
        assert char['unicodedata_category'] == 'Ll'
        assert char['unicodeblock'] == 'LATIN_EXTENDED_A' or char['unicodeblock'] == 'LATIN_EXTENDED_LETTER'

        found_canonical_in_confusables = False
        for conf_list in char['confusables']:
            for conf in conf_list:
                found_canonical_in_confusables |= conf['char'] == canonical_char
        assert found_canonical_in_confusables

    assert json['tokenizations'] == []


@pytest.mark.slow
@pytest.mark.parametrize(
    'label',
    [
        'dbque.eth\n',
        '🇪🇹is🦇🔊💲.eth',
        'iwant\U0001faf5.eth',
        'iwant\\U0001faf5.eth',
        'iwant\\\\U0001faf5.eth',
        'iwant🫵.eth',
        'ЁЯй╖ЁЯй╖ЁЯй╖.eth',
        'ЁЯлиЁЯлиЁЯли.eth',
        'ЁЯй╡ЁЯй╡ЁЯй╡ЁЯй╡ЁЯй╡.eth',
        'ЁЯй╢ЁЯй╢ЁЯй╢ЁЯй╢ЁЯй╢.eth',
        'ЁЯй╖ЁЯй╖ЁЯй╖ЁЯй╖ЁЯй╖.eth',
        'ЁЯй╡ЁЯй╡ЁЯй╡.eth',
        'ЁЯй╢ЁЯй╢ЁЯй╢.eth',
    ]
)
def test_inspector_special_cases(prod_test_client, label):
    response = prod_test_client.post('/inspector/', json={'label': label})
    assert response.status_code == 200
    check_inspector_response(label, response.json())


@pytest.mark.slow
@pytest.mark.parametrize(
    'label',
    [
        '🩶🩶🩶🩶🩶.eth',
        '🫨🫨🫨.eth',
        '🩷🩷🩷.eth',
        '🩶🩶🩶🩶🩶.eth',
        'i🩷u.eth',
    ]
)
def test_inspector_invalid_script(prod_test_client, label):
    response = prod_test_client.post('/inspector/', json={'label': label})
    assert response.status_code == 200
    check_inspector_response(label, response.json())


@pytest.mark.slow
def test_inspector_stress(prod_test_client):
    client = prod_test_client
    max_duration = 2
    for label in generate_example_names(400):
        start = get_time()
        response = client.post('/inspector/', json={'label': label})
        duration = get_time() - start
        assert response.status_code == 200, f'{label} failed with {response.status_code}'
        assert duration < max_duration, f'Time exceeded on {label}'
        check_inspector_response(label, response.json())


@pytest.mark.slow
def test_generator_stress(prod_test_client):
    client = prod_test_client
    max_duration = 2
    for name in generate_example_names(400):
        start = get_time()
        response = client.post('/', json={'name': name})
        duration = get_time() - start
        assert response.status_code == 200, f'{name} failed with {response.status_code}'
        assert duration < max_duration, f'Time exceeded on {name}'
        check_generator_response(response.json())


@pytest.mark.slow
def test_inspector_no_tokenization(prod_test_client):
    label = 'cat'
    response = prod_test_client.post('/inspector/', json={'label': label, 'tokenization': False})
    assert response.status_code == 200
    json = response.json()
    print(json)
    check_inspector_response(label, json, tokenization=False)

    assert json['word_count'] is None
    assert json['all_class'] == 'simple_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert json['probability'] is None or 0 < json['probability']
    assert json['any_classes'] == ['simple_letter']
    assert json['all_unicodeblock'] == 'BASIC_LATIN'
    assert json['ens_is_valid_name']
    assert json['ens_nameprep'] == label
    assert json['idna_encode'] == label
    assert 0 <= json['score'] <= 1

    # order of the returned characters must match input name
    for char, name_char in zip(json['chars'], label):
        assert char['script'] == 'Latin'
        assert char['name'] == f'LATIN SMALL LETTER {name_char.upper()}'
        assert char['char_class'] == 'simple_letter'
        assert char['unicodedata_category'] == 'Ll'
        assert char['unicodeblock'] == 'BASIC_LATIN'
        assert char['confusables'] == []

    assert json['tokenizations'] is None


@pytest.mark.slow
def test_inspector_limit_confusables(prod_test_client):
    label = 'ącat'
    response = prod_test_client.post('/inspector/', json={'label': label, 'limit_confusables': True})
    assert response.status_code == 200
    json = response.json()
    print(json)
    check_inspector_response(label, json, limit_confusables=True)

    assert json['word_count'] == 0
    assert json['all_class'] is None
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert 0 < json['probability']
    assert sorted(json['any_classes']) == ['any_letter', 'simple_letter']
    assert json['all_unicodeblock'] is None
    assert json['ens_is_valid_name']
    assert json['ens_nameprep'] == label
    assert json['idna_encode'] == 'xn--cat-hpa'
    assert json['score'] >= 0

    assert len(json['chars'][0]['confusables']) == 1

    tokenization = sorted(json['tokenizations'], key=lambda t: t['probability'])[-1]
    tok = tokenization['tokens'][0]
    assert tok['token'] == ''


@pytest.mark.slow
def test_inspector_disable_chars_output(prod_test_client):
    label = 'cat'
    response = prod_test_client.post('/inspector/', json={'label': label, 'truncate_chars_output': 0})
    assert response.status_code == 200
    json = response.json()
    print(json)
    check_inspector_response(label, json, truncate_chars_output=0)

    assert json['word_count'] == 1
    assert json['all_class'] == 'simple_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert 0 < json['probability']
    assert json['any_classes'] == ['simple_letter']
    assert json['all_unicodeblock'] == 'BASIC_LATIN'
    assert json['ens_is_valid_name']
    assert json['ens_nameprep'] == label
    assert json['idna_encode'] == label
    assert json['score'] >= 0

    assert len(json['chars']) == 0

    tokenization = sorted(json['tokenizations'], key=lambda t: t['probability'])[-1]
    tok = tokenization['tokens'][0]
    assert tok['token'] == label
    assert tok['length'] == len(label)
    assert tok['pos'] == 'NOUN'
    assert tok['lemma'] == label


@pytest.mark.slow
def test_inspector_disable_char_analysis(prod_test_client):
    label = 'cat'
    response = prod_test_client.post('/inspector/', json={'label': label, 'disable_char_analysis': True})
    assert response.status_code == 200
    json = response.json()
    print(json)
    check_inspector_response(label, json, disable_char_analysis=True)

    assert json['word_count'] == 1
    assert json['all_class'] is None
    assert json['all_script'] is None
    assert json['any_scripts'] is None
    assert 0 < json['probability']
    assert json['any_classes'] is None
    assert json['all_unicodeblock'] is None
    assert json['ens_is_valid_name']
    assert json['ens_nameprep'] == label
    assert json['idna_encode'] == label
    assert json['score'] is None

    assert json['chars'] is None

    tokenization = sorted(json['tokenizations'], key=lambda t: t['probability'])[-1]
    tok = tokenization['tokens'][0]
    assert tok['token'] == label
    assert tok['length'] == len(label)
    assert tok['pos'] == 'NOUN'
    assert tok['lemma'] == label


@pytest.mark.slow
def test_inspector_disable_pos_lemma(prod_test_client):
    label = 'cat'
    response = prod_test_client.post('/inspector/', json={'label': label, 'pos_lemma': False})
    assert response.status_code == 200
    json = response.json()
    print(json)
    check_inspector_response(label, json, pos_lemma=False)

    assert json['word_count'] == 1
    assert json['all_class'] == 'simple_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert 0 < json['probability']
    assert json['any_classes'] == ['simple_letter']
    assert json['all_unicodeblock'] == 'BASIC_LATIN'
    assert json['ens_is_valid_name']
    assert json['ens_nameprep'] == label
    assert json['idna_encode'] == label
    assert json['score'] >= 0

    assert len(json['chars']) == 3

    tokenization = sorted(json['tokenizations'], key=lambda t: t['probability'])[-1]
    tok = tokenization['tokens'][0]
    assert tok['token'] == label
    assert tok['length'] == len(label)
    assert tok['pos'] is None
    assert tok['lemma'] is None
