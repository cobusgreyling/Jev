from jev_lab.policy import composite_score, confidence_route, noul_decision, ticket_policy


def test_noul_lanes():
    assert noul_decision(0.9) == "yes"
    assert noul_decision(0.1) == "no"
    assert noul_decision(0.5) == "review"


def test_confidence_lanes():
    assert confidence_route(0.95) == "act"
    assert confidence_route(0.6) == "confirm"
    assert confidence_route(0.2) == "human"


def test_composite_weights():
    assert composite_score([(1.0, 1.0), (0.0, 1.0)]) == 0.5
    assert composite_score([]) == 0.0


def test_ticket_policy_escalates_on_low_confidence():
    answers = {
        "department": {
            "choice": "technical",
            "confidence": 0.2,
            "probabilities": {"technical": 0.4, "billing": 0.3, "sales": 0.3},
        },
        "frustration": {"score": 0.1},
        "is_urgent": {"noul": 0.1},
    }
    out = ticket_policy(answers)
    assert out["lane"] == "human"
    assert out["action"] == "escalate_to_human"


def test_ticket_policy_routes_when_confident_and_urgent():
    answers = {
        "department": {"choice": "technical", "confidence": 0.9},
        "frustration": {"score": 1.0},
        "is_urgent": {"noul": 0.97},
    }
    out = ticket_policy(answers)
    assert out["action"] == "route_technical"
    assert out["priority"] == "high"
