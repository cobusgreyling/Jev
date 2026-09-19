#!/usr/bin/env python3
"""Fail if a TypeSafe-shaped key or other secrets appear in tracked files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = [
    re.compile(r"apikey_[0-9a-f]{20,}", re.I),
    re.compile(r"TYPESAFE_API_KEY\s*=\s*['\"]?apikey_", re.I),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"xai-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
]


def tracked_files() -> list[Path]:
    try:
        raw = subprocess.check_output(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            text=True,
        )
        names = [n for n in raw.split("\0") if n]
    except (subprocess.CalledProcessError, FileNotFoundError):
        names = [
            str(p.relative_to(ROOT))
            for p in ROOT.rglob("*")
            if p.is_file() and ".venv" not in p.parts and ".git" not in p.parts
        ]
    skip_suffix = {".jpg", ".png", ".webp", ".gif", ".mp4", ".pyc"}
    out: list[Path] = []
    for name in names:
        path = ROOT / name
        if any(part in {".venv", ".git", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.lower() in skip_suffix:
            continue
        if name.endswith("scripts/secret_scan.py"):
            continue
        out.append(path)
    return out


def main() -> int:
    hits: list[str] = []
    for path in tracked_files():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in PATTERNS:
            if pattern.search(text):
                hits.append(f"{path.relative_to(ROOT)} matches {pattern.pattern}")
    if hits:
        print("secret-scan FAILED:")
        for hit in hits:
            print(" ", hit)
        return 1
    print("secret-scan OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
