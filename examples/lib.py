"""Shared helpers for the progressive examples."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jev_lab.client import load_api_key, system_one  # noqa: E402


def live() -> bool:
    return "--live" in sys.argv and bool(load_api_key())


def load_fixture(name: str) -> dict[str, Any]:
    path = ROOT / "data" / "fixtures" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def judge(state: Any, questions: dict[str, Any], fixture: str = "stripe-outage") -> dict[str, Any]:
    if live():
        return system_one(state, questions)
    data = load_fixture(fixture)
    return data["response"]
