"""Strip credentials before they are sent to TypeSafe or shown in the lab.

Same shapes as ``packages/js/src/redact.ts``.
"""

from __future__ import annotations

import re
from typing import Any

REDACTED = "[REDACTED]"

_SECRET_PATTERNS = [
    re.compile(r"apikey_[0-9a-f]+_[0-9a-f]+", re.I),
    re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bxai-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-+/=]+\b", re.I),
    re.compile(
        r"\b(TYPESAFE_API_KEY|JEV_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY|XAI_API_KEY)\s*[=:]\s*\S+",
        re.I,
    ),
    re.compile(r"\b(api[_-]?key|secret|token|password)\s*[=:]\s*[^\s'\"]{8,}", re.I),
]

_SECRET_KEY = re.compile(r"key|token|secret|password|authorization|credential", re.I)


def redact_string(value: str) -> str:
    out = value
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub(REDACTED, out)
    return out


def redact_secrets(value: Any) -> Any:
    if isinstance(value, str):
        return redact_string(value)
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if isinstance(key, str) and isinstance(item, str) and _SECRET_KEY.search(key):
                redacted[key] = REDACTED
            else:
                redacted[key] = redact_secrets(item)
        return redacted
    return value


def contains_secret(haystack: str) -> bool:
    return any(pattern.search(haystack) for pattern in _SECRET_PATTERNS)
