import os
import sys

import pytest
from fastapi.testclient import TestClient

from generator.domains import Domains

from helpers import check_inspector_response


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


@pytest.mark.timeout(10)
@pytest.mark.slow
def test_prod_long(prod_test_client):
    client = prod_test_client
    response = client.post("/", json={"name": "a" * 40000})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])


@pytest.mark.timeout(10)
@pytest.mark.slow
def test_prod_long_get(prod_test_client):
    client = prod_test_client
    response = client.get("/?name=" + 'a' * 40000)

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])


@pytest.mark.timeout(10)
@pytest.mark.slow
def test_prod_inspector_long_post(prod_test_client):
    client = prod_test_client
    response = client.post("/inspector/",
                           json={"name": "miinibaashkiminasiganibiitoosijiganibadagwiingweshiganibakwezhigan"})

    assert response.status_code == 200

    json = response.json()

    assert 'name' in json
    assert len(json['tokenizations']) == 0


@pytest.mark.timeout(10)
@pytest.mark.slow
def test_prod_inspector_long2_post(prod_test_client):
    client = prod_test_client
    response = client.post("/inspector/", json={"name": "a" * 40000})

    assert response.status_code == 200

    json = response.json()
    assert 'name' in json
    assert len(json['tokenizations']) == 0


@pytest.mark.slow
def test_inspector_basic(prod_test_client):
    name = 'cat'
    response = prod_test_client.post('/inspector/', json={'name': name})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(name, json)

    assert json['word_length'] == 1
    assert json['all_class'] == 'simple_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert 0 < json['probability']
    assert json['any_classes'] == ['simple_letter']
    assert json['all_unicodeblock'] == 'BASIC_LATIN'
    assert json['ens_is_valid_name']
    assert json['ens_nameprep'] == name
    assert json['idna_encode'] == name
    assert 0 < json['score']

    # order of the returned characters must match input name
    for char, name_char in zip(json['chars'], name):
        assert char['script'] == 'Latin'
        assert char['name'] == f'LATIN SMALL LETTER {name_char.upper()}'
        assert char['char_class'] == 'simple_letter'
        assert char['unicodedata_category'] == 'Ll'
        assert char['unicodeblock'] == 'BASIC_LATIN'
        assert char['confusables'] == []

    tokenization = sorted(json['tokenizations'], key=lambda t: t['probability'])[-1]
    tok = tokenization['tokens'][0]
    assert tok['token'] == name
    assert tok['length'] == len(name)
    assert tok['pos'] == 'NOUN'
    assert tok['lemma'] == name


@pytest.mark.slow
def test_inspector_special(prod_test_client):
    name = 'żółć'
    response = prod_test_client.post('/inspector/', json={'name': name})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(name, json)

    assert json['word_length'] == 0
    assert json['all_class'] == 'any_letter'
    assert json['all_script'] == 'Latin'
    assert json['any_scripts'] == ['Latin']
    assert json['probability'] == 0
    assert json['any_classes'] == ['any_letter']
    assert json['all_unicodeblock'] is None
    assert json['ens_is_valid_name']
    assert json['ens_nameprep'] == name
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
