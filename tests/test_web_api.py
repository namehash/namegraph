import os
import sys

import pytest
from fastapi.testclient import TestClient

from generator.domains import Domains

from helpers import check_inspector_response


@pytest.fixture(scope="module")
def test_test_client():
    Domains.remove_self()
    os.environ['CONFIG_NAME'] = 'test_config'
    # import web_api
    if 'web_api' not in sys.modules:
        import web_api
    else:
        import web_api
        import importlib
        importlib.reload(web_api)
    client = TestClient(web_api.app)
    client.get("/?name=aaa.eth")
    return client


def test_read_main(test_test_client):
    client = test_test_client
    response = client.post("/", json={"name": "fire"})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "discharge" in primary


def test_get(test_test_client):
    client = test_test_client
    response = client.get("/?name=firę")

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "secondary"])

    primary = json['primary']
    assert "discharge" in primary


def test_inspector_fast(test_test_client):
    name = 'cat'
    response = test_test_client.post('/inspector/', json={'name': name})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(name, json)


@pytest.mark.xfail
def test_inspector_negative_score(test_test_client):
    name = 'fourscoreandsevenyearsagoourfathersbroughtforthonthiscontinentanewnationconceivedinlibertyanddedicatedtothepropositionthatallmenarecreatedequalnowweareengagedinagreatcivilwartestingwhetherthatnationoranynationsoconceivedandsodedicatedcanlongendurewearemetonagreatbattlefieldofthatwarwehavecometodedicateaportionofthatfieldasafinalrestingplaceforthosewhoheregavetheirlivesthatthatnationmightliveitisaltogetherfittingandproperthatweshoulddothisbutinalargersensewecannotdedicatewecannotconsecratewecannothallowthisgroundthebravemenlivinganddeadwhostruggledherehaveconsecrateditfaraboveourpoorpowertoaddordetracttheworldwilllittlenotenorlongrememberwhatwesayherebutitcanneverforgetwhattheydidhereitisforusthelivingrathertobededicatedheretotheunfinishedworkwhichtheywhofoughtherehavethusfarsonoblyadvanceditisratherforustobeherededicatedtothegreattaskremainingbeforeusthatfromthesehonoreddeadwetakeincreaseddevotiontothatcauseforwhichtheyheregavethelastfullmeasureofdevotionthatweherehighlyresolvethatthesedeadshallnothavediedinvainthatthisnationundergodshallhaveanewbirthoffreedomandthatgovernmentofthepeoplebythepeopleforthepeopleshallnotperishfromtheearth.eth'
    response = test_test_client.post('/inspector/', json={'name': name})
    assert response.status_code == 200
    check_inspector_response(name, response.json())
