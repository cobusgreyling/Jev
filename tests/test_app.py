from fastapi.testclient import TestClient

from app import app


def test_health_does_not_leak_key():
    with TestClient(app) as client:
        r = client.get("/api/health")
    assert r.status_code == 200
    body = r.text
    assert "apikey_" not in body
    data = r.json()
    assert data["ok"] is True
    assert "live" in data
    assert data["features"]["playground"] is True


def test_offline_fixture_and_policy():
    with TestClient(app) as client:
        r = client.get("/api/fixtures/stripe-outage")
        assert r.status_code == 200
        answers = r.json()["response"]["answers"]
        p = client.post("/api/policy/ticket", json={"answers": answers})
    assert p.status_code == 200
    assert p.json()["action"].startswith("route_") or p.json()["lane"] in {
        "act",
        "confirm",
        "human",
    }


def test_cost_endpoint():
    with TestClient(app) as client:
        r = client.post(
            "/api/cost/estimate",
            json={"input_tokens": 1_000_000, "output_tokens": 1000, "questions": 3},
        )
    assert r.status_code == 200
    jev = r.json()["jev"]
    assert jev["output_usd"] == 0.0
    assert jev["input_usd"] == 0.042
