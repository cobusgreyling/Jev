"""Thin HTTP client for POST /v1/systemone.

The official SDK is ``typesafe-sdk``. This module stays dependency-light so the
lab, tests, and examples can run from the pinned requirements alone.

Auth matches the TypeScript harness: ``TYPESAFE_API_KEY``, ``JEV_API_KEY``,
then ``~/.config/typesafe/api_key``, then ``~/.typesafe/api_key``.
``TYPESAFE_KEY_FILE`` replaces that file list. ``TYPESAFE_OFFLINE=1`` forces
the lab onto fixtures.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from jev_lab.redact import contains_secret, redact_secrets, redact_string

DEFAULT_BASE_URL = "https://api.typesafe.ai"
DEFAULT_MODEL = "jev-1.13.0"


class TypeSafeError(RuntimeError):
    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"TypeSafe API {status_code}: {body}")


def _key_files() -> list[Path]:
    override = os.getenv("TYPESAFE_KEY_FILE", "").strip()
    if override:
        return [Path(override)]
    home = Path.home()
    return [
        home / ".config" / "typesafe" / "api_key",
        home / ".typesafe" / "api_key",
    ]


def _read_key_file(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def load_api_key() -> str:
    if os.getenv("TYPESAFE_OFFLINE", "").strip().lower() in {"1", "true", "yes"}:
        return ""
    for name in ("TYPESAFE_API_KEY", "JEV_API_KEY"):
        env = os.getenv(name, "").strip()
        if env:
            return env
    for path in _key_files():
        found = _read_key_file(path)
        if found:
            return found
    return ""


def _chosen_model(model: str | None) -> str:
    picked = (model or os.getenv("TYPESAFE_MODEL") or DEFAULT_MODEL).strip()
    return picked or DEFAULT_MODEL


def system_one(
    state: Any,
    questions: dict[str, Any],
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 30.0,
    retries: int = 3,
    transport: httpx.BaseTransport | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    key = (api_key if api_key is not None else load_api_key()).strip()
    if not key:
        raise TypeSafeError(
            401,
            "No TypeSafe API key. Set TYPESAFE_API_KEY or JEV_API_KEY, or write ~/.config/typesafe/api_key (mode 600).",
        )

    url = (base_url or os.getenv("TYPESAFE_BASE_URL", DEFAULT_BASE_URL)).rstrip("/")
    payload = {
        "state": redact_secrets(state),
        "model": _chosen_model(model),
        "questions": questions,
    }
    encoded = json.dumps(payload)
    if contains_secret(encoded):
        raise TypeSafeError(400, "Refusing to send state that still looks like it contains a secret.")

    last_error: TypeSafeError | None = None
    with httpx.Client(timeout=timeout, transport=transport) as client:
        for attempt in range(retries + 1):
            try:
                response = client.post(
                    f"{url}/v1/systemone",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            except httpx.RequestError as exc:
                raise TypeSafeError(502, f"upstream request failed: {redact_string(str(exc))[:200]}") from exc

            if response.status_code in {429, 529}:
                retry_after = response.headers.get("retry-after", "")
                try:
                    parsed = float(retry_after) if retry_after else 0.0
                except ValueError:
                    parsed = 0.0
                wait = parsed if parsed > 0 else 0.25 * 2**attempt
                detail = redact_string(response.text)[:400] or "rate limited"
                last_error = TypeSafeError(response.status_code, detail)
                if attempt < retries:
                    sleep(wait)
                    continue
                break

            if response.status_code >= 400:
                last_error = TypeSafeError(response.status_code, redact_string(response.text)[:400])
                if response.status_code >= 500 and attempt < retries:
                    sleep(0.25 * 2**attempt)
                    continue
                raise last_error

            try:
                data = response.json()
            except ValueError as exc:
                snippet = redact_string(response.text)[:200]
                raise TypeSafeError(
                    response.status_code,
                    f"TypeSafe API returned non-JSON: {snippet}",
                ) from exc
            if not isinstance(data.get("answers"), dict):
                raise TypeSafeError(response.status_code, "TypeSafe API response missing answers.")
            return data

    raise last_error or TypeSafeError(429, "TypeSafe API rate limited after retries.")
