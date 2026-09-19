import os
import sys
from pathlib import Path

os.environ["TYPESAFE_OFFLINE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
