"""Code owns the workflow. Jev returns typed probabilities; this module acts."""

from __future__ import annotations

from typing import Any, Literal

NoulLane = Literal["yes", "no", "review"]
RouteLane = Literal["act", "confirm", "human"]


def noul_decision(
    noul: float,
    *,
    yes_at: float = 0.7,
    no_at: float = 0.3,
) -> NoulLane:
    if noul >= yes_at:
        return "yes"
    if noul <= no_at:
        return "no"
    return "review"


def confidence_route(
    confidence: float,
    *,
    act_at: float = 0.8,
    confirm_at: float = 0.5,
) -> RouteLane:
    if confidence >= act_at:
        return "act"
    if confidence >= confirm_at:
        return "confirm"
    return "human"


def composite_score(parts: list[tuple[float, float]]) -> float:
    """Weighted mean of (value, weight) pairs. Values should be 0–1."""
    total_w = sum(weight for _, weight in parts)
    if total_w <= 0:
        return 0.0
    return sum(value * weight for value, weight in parts) / total_w


def ticket_policy(
    answers: dict[str, Any],
    *,
    act_at: float = 0.8,
    confirm_at: float = 0.5,
    urgent_at: float = 0.7,
    angry_at: float = 1.5,
) -> dict[str, Any]:
    """Compose Choice + Score + Noul into one support-ticket action.

    Stakes live here, not in the model:
    - low confidence → human
    - high urgency or high frustration → priority
    - otherwise route to the chosen department
    """
    department = answers.get("department") or {}
    frustration = answers.get("frustration") or {}
    urgent = answers.get("is_urgent") or {}

    choice = department.get("choice")
    confidence = float(department.get("confidence") or 0.0)
    noul = float(urgent.get("noul") or 0.0)
    score = float(frustration.get("score") or 0.0)

    lane = confidence_route(confidence, act_at=act_at, confirm_at=confirm_at)
    priority = "high" if noul >= urgent_at or score >= angry_at else "normal"

    if lane == "human":
        action = "escalate_to_human"
    elif lane == "confirm":
        action = f"confirm_then_route_{choice or 'unknown'}"
    else:
        action = f"route_{choice or 'unknown'}"

    return {
        "action": action,
        "lane": lane,
        "department": choice,
        "priority": priority,
        "confidence": round(confidence, 4),
        "urgency_noul": round(noul, 4),
        "frustration_score": round(score, 4),
        "thresholds": {
            "act_at": act_at,
            "confirm_at": confirm_at,
            "urgent_at": urgent_at,
            "angry_at": angry_at,
        },
    }
