import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_secret_scan_clean():
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "secret_scan.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
