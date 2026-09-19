#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

# Local key file is optional and never committed.
if [[ -z "${TYPESAFE_API_KEY:-}" && -f "${HOME}/.typesafe/api_key" ]]; then
  export TYPESAFE_API_KEY
  TYPESAFE_API_KEY="$(tr -d '[:space:]' < "${HOME}/.typesafe/api_key")"
fi

echo "Jev Showcase → http://127.0.0.1:${PORT:-7872}"
echo "Offline tabs work with no key. Optional live: set TYPESAFE_API_KEY in .env"
exec python app.py
