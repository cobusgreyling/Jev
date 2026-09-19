import json
from pathlib import Path

from jev_lab.policy import ticket_policy

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "data" / "fixtures"


def test_fixtures_have_three_primitives():
    names = ["stripe-outage", "jailbreak", "calm-question", "duplicate-charge"]
    for name in names:
        data = json.loads((FIXTURES / f"{name}.json").read_text())
        answers = data["response"]["answers"]
        assert answers["department"]["type"] == "choice"
        assert answers["frustration"]["type"] == "score"
        assert answers["is_urgent"]["type"] == "noul"
        assert 0 <= answers["is_urgent"]["noul"] <= 1
        policy = ticket_policy(answers)
        assert policy["action"]
        assert policy["lane"] in {"act", "confirm", "human"}


def test_no_secrets_in_fixtures():
    for path in FIXTURES.glob("*.json"):
        text = path.read_text()
        assert "apikey_" not in text
        assert "Bearer " not in text
