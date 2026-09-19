from fastapi.testclient import TestClient

from app import app


def test_home_page_and_bootstrap():
    with TestClient(app) as client:
        page = client.get("/home")
        assert page.status_code == 200
        assert "Decision Trace" in page.text
        assert "apikey_" not in page.text
        boot = client.get("/api/home/bootstrap")
    assert boot.status_code == 200
    data = boot.json()
    assert "1br" in data["houses"]
    assert data["houses"]["1br"]["rooms"]


def test_turn_off_all_lights_via_api():
    with TestClient(app) as client:
        r = client.post(
            "/api/home/run",
            json={"request": "Turn off all the lights", "home_id": "1br"},
        )
    assert r.status_code == 200
    body = r.json()
    assert "apikey_" not in r.text
    assert body["plan"]["kind"] == "command"
    kitchen = next(
        d
        for room in body["house"]["rooms"]
        for d in room["devices"]
        if d["id"] == "kitchen_light"
    )
    assert kitchen["on"] is False
    used = {row["id"] for row in body["trace"] if row["used"]}
    assert "action.light" in used
    assert "action.lock" not in used


def test_general_and_split():
    with TestClient(app) as client:
        general = client.post(
            "/api/home/run",
            json={"request": "Who won the World Series in 1989?"},
        )
        split = client.post(
            "/api/home/split",
            json={"request": "Turn off the kitchen lights and lock the office door"},
        )
    assert general.json()["plan"]["kind"] == "general"
    assert "Athletics" in general.json()["reply"]
    assert len(split.json()["commands"]) >= 2
