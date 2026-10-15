from fastapi.testclient import TestClient

from app import TYPESAFE_MODEL, app
from jev_lab.client import TypeSafeError

FIXTURE_KEY = "apikey_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def test_health_does_not_leak_key():
    with TestClient(app) as client:
        r = client.get("/api/health")
    assert r.status_code == 200
    body = r.text
    assert "apikey_" not in body
    data = r.json()
    assert data["ok"] is True
    assert "live" in data
    assert data["model"] == TYPESAFE_MODEL
    assert data["features"]["playground"] is True


def test_offline_fixture_and_policy():
    with TestClient(app) as client:
        r = client.get("/api/fixtures/stripe-outage")
        assert r.status_code == 200
        answers = r.json()["response"]["answers"]
        p = client.post("/api/policy/ticket", json={"answers": answers})
    assert p.status_code == 200
    body = p.json()
    assert body["lane"] == "human"
    assert body["action"] == "escalate_to_human"
    assert body["department"] == "technical"
    assert body["priority"] == "high"


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


def test_judge_requires_a_key():
    with TestClient(app) as client:
        r = client.post("/api/judge", json={"state": "hello"})
    assert r.status_code == 400
    assert "apikey_" not in r.text


def test_judge_redacts_upstream_errors(monkeypatch):
    monkeypatch.setattr("app.load_api_key", lambda: "present-key")

    def boom(*_args, **_kwargs):
        raise TypeSafeError(401, f"rejected {FIXTURE_KEY}")

    monkeypatch.setattr("app.system_one", boom)
    with TestClient(app) as client:
        r = client.post("/api/judge", json={"state": "hello"})
    assert r.status_code == 401
    assert "Live judge failed" in r.text
    assert "apikey_" not in r.text
    assert "[REDACTED]" in r.text


def test_home_run_does_not_mock_a_live_failure(monkeypatch):
    monkeypatch.setattr("app.load_api_key", lambda: "present-key")

    def boom(*_args, **_kwargs):
        raise TypeSafeError(503, "upstream down")

    monkeypatch.setattr("app.system_one", boom)
    with TestClient(app) as client:
        r = client.post(
            "/api/home/run",
            json={"request": "Turn off all the lights", "home_id": "1br"},
        )
    assert r.status_code == 503
    assert "mock" not in r.text
    assert "Live judge failed" in r.text
    body = r.json()
    assert "plan" not in body


def test_home_run_stays_on_mock_without_a_key(monkeypatch):
    monkeypatch.setattr("app.load_api_key", lambda: "")

    def boom(*_args, **_kwargs):
        raise AssertionError("live client should not run without a key")

    monkeypatch.setattr("app.system_one", boom)
    with TestClient(app) as client:
        r = client.post(
            "/api/home/run",
            json={"request": "Turn off all the lights", "home_id": "1br"},
        )
    assert r.status_code == 200
    assert r.json()["source"] == "mock"
