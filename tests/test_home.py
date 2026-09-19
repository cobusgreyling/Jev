from jev_lab.home import (
    apply_plan,
    build_questions,
    clone_home,
    mock_answers,
    plan,
    split_request,
)


def _judge(request: str, home_id: str = "1br", speaking_to: str | None = None):
    home = clone_home(home_id)
    questions = build_questions(home)
    answers = mock_answers(request, home, speaking_to, questions)
    return home, questions, answers, plan(answers, home, speaking_to)


def test_fanout_asks_every_action_upfront():
    home = clone_home("1br")
    questions = build_questions(home)
    for kind in ("light", "fan", "speaker", "thermostat", "appliance", "lock"):
        assert f"action.{kind}" in questions
    assert questions["category"]["type"] == "choice"
    assert questions["is_compound"]["type"] == "noul"


def test_turn_off_all_lights():
    home, _, _, planned = _judge("Turn off all the lights")
    assert planned["kind"] == "command"
    assert planned["action"] == "turn_off"
    assert planned["type"] == "light"
    ids = {t["id"] for t in planned["targets"]}
    assert "living_room_overhead" in ids
    assert "kitchen_light" in ids
    assert "action.light" in planned["used"]
    assert "action.lock" not in planned["used"]
    result = apply_plan(home, planned)
    assert result["status"] == "ok"
    kitchen = next(d for r in home["rooms"] for d in r["devices"] if d["id"] == "kitchen_light")
    assert kitchen["on"] is False


def test_living_room_lights_specific():
    _, _, _, planned = _judge("Turn on the living room lights")
    assert planned["kind"] == "command"
    assert planned["type"] == "light"
    rooms = {t["room"] for t in planned["targets"]}
    assert rooms == {"living_room"}


def test_world_series_is_general():
    _, _, _, planned = _judge("Who won the World Series in 1989?")
    assert planned["kind"] == "general"
    assert planned["used"] == ["category"]


def test_compound_request():
    parts = split_request("Turn off the kitchen lights and lock the office door")
    assert len(parts) >= 2
    _, _, _, planned = _judge("Turn off the kitchen lights and lock the office door")
    assert planned["kind"] == "compound"


def test_outside_music_unavailable_in_1br():
    _, _, _, planned = _judge("Let's get some outside music going", "1br")
    assert planned["kind"] == "unavailable"


def test_outside_music_available_in_family_home():
    _, _, _, planned = _judge("Let's get some outside music going", "family")
    assert planned["kind"] == "command"
    assert planned["type"] == "speaker"
    assert any(t["id"] == "patio_speakers" for t in planned["targets"])


def test_status_question():
    home, _, _, planned = _judge("Is the kitchen light on?")
    assert planned["kind"] == "status"
    result = apply_plan(home, planned)
    assert result["status"] == "ok"
    assert "Kitchen Lights" in result["message"]


def test_unlock_confirms_when_confidence_low(monkeypatch):
    home = clone_home("1br")
    questions = build_questions(home)
    answers = mock_answers("Unlock the office door", home, None, questions)
    answers["action.lock"]["confidence"] = 0.4
    answers["category"]["confidence"] = 0.4
    planned = plan(answers, home, None)
    assert planned["kind"] == "command"
    assert planned["needs_confirm"] is True
    blocked = apply_plan(home, planned)
    assert blocked["status"] == "confirm"
    locked = next(d for r in home["rooms"] for d in r["devices"] if d["id"] == "office_lock")
    assert locked["locked"] is True
    applied = apply_plan(home, planned, force=True)
    assert applied["status"] == "ok"
    assert locked["locked"] is False
