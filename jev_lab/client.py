"""Thin HTTP client for POST /v1/systemone.

The official SDK is `typesafe-sdk`. This module stays dependency-light so the
lab, tests, and examples can run from `requirements.txt` alone.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-latest"


class TypeSafeError(RuntimeError):
    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"TypeSafe API {status_code}: {body}")


def load_api_key() -> str:
    env = os.getenv("TYPESAFE_API_KEY", "").strip()
    if env:
        return env
    path = Path.home() / ".typesafe" / "api_key"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return ""


def system_one(
    state: Any,
    questions: dict[str, Any],
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    key = (api_key if api_key is not None else load_api_key()).strip()
    if not key:
        raise TypeSafeError(
            401,
            "TYPESAFE_API_KEY is not set. Use offline fixtures, or set the key in .env",
        )

    url = (base_url or os.getenv("TYPESAFE_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
    payload = {
        "state": state,
        "model": model or os.getenv("TYPESAFE_MODEL", DEFAULT_MODEL),
        "questions": questions,
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{url}/v1/systemone",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.RequestError as exc:
        raise TypeSafeError(502, f"upstream request failed: {exc}") from exc

    if response.status_code >= 400:
        raise TypeSafeError(response.status_code, response.text[:800])
    return response.json()
