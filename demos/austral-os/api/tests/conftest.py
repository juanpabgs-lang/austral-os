from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from seed import seed  # noqa: E402
from app import DB_FILE  # noqa: E402

# Ensure the API process-level db exists for TestClient tests.
if not DB_FILE.exists():
    seed(DB_FILE)
