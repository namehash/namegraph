from fastapi.testclient import TestClient

from web_api import app

client = TestClient(app)

def test_read_main():
    response = client.post("/", json={"name": "fire"})

    assert response.status_code == 200

    json = response.json()
    assert sorted(list(json.keys())) == sorted(["advertised", "primary", "random", "secondary"])

    primary = json['primary']
    assert "fire" in primary
