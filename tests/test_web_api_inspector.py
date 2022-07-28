import os

import pytest
from fastapi.testclient import TestClient

import web_api_inspector

from .helpers import check_inspector_response


@pytest.fixture(scope="module")
def test_test_client():
    os.environ['CONFIG_NAME'] = 'test_config'

    client = TestClient(web_api_inspector.app)
    client.get("/?name=aaa.eth")
    return client


def test_inspector_fast(test_test_client):
    label = 'cat'
    response = test_test_client.post('/inspector/', json={'label': label})
    assert response.status_code == 200
    json = response.json()

    check_inspector_response(label, json)


def test_inspector_negative_score(test_test_client):
    label = 'fourscoreandsevenyearsagoourfathersbroughtforthonthiscontinentanewnationconceivedinlibertyanddedicatedtothepropositionthatallmenarecreatedequalnowweareengagedinagreatcivilwartestingwhetherthatnationoranynationsoconceivedandsodedicatedcanlongendurewearemetonagreatbattlefieldofthatwarwehavecometodedicateaportionofthatfieldasafinalrestingplaceforthosewhoheregavetheirlivesthatthatnationmightliveitisaltogetherfittingandproperthatweshoulddothisbutinalargersensewecannotdedicatewecannotconsecratewecannothallowthisgroundthebravemenlivinganddeadwhostruggledherehaveconsecrateditfaraboveourpoorpowertoaddordetracttheworldwilllittlenotenorlongrememberwhatwesayherebutitcanneverforgetwhattheydidhereitisforusthelivingrathertobededicatedheretotheunfinishedworkwhichtheywhofoughtherehavethusfarsonoblyadvanceditisratherforustobeherededicatedtothegreattaskremainingbeforeusthatfromthesehonoreddeadwetakeincreaseddevotiontothatcauseforwhichtheyheregavethelastfullmeasureofdevotionthatweherehighlyresolvethatthesedeadshallnothavediedinvainthatthisnationundergodshallhaveanewbirthoffreedomandthatgovernmentofthepeoplebythepeopleforthepeopleshallnotperishfromtheearth.eth'
    response = test_test_client.post('/inspector/', json={'label': label})
    assert response.status_code == 200
    check_inspector_response(label, response.json())
