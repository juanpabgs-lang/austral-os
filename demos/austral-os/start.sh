#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/api"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
fi
.venv/bin/python -c "from seed import seed; seed()"
.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8016 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT
cd "$ROOT/web"
if [ ! -d node_modules ]; then
  npm install
fi
npm run dev
