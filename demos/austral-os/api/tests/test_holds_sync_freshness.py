from __future__ import annotations

import sys
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402
from config import NOW_ISO  # noqa: E402
from engines.freshness import q10_factor, remaining_life  # noqa: E402
from engines.trace import trace_lot  # noqa: E402
from db import connect  # noqa: E402


client = TestClient(app)


def test_held_pallet_cannot_be_picked():
    r = client.post(
        "/api/events",
        json={
            "event_type": "pick",
            "pallet_id": "PAL-FRE-H",
            "qty_boxes": 4,
            "payload": {},
        },
        headers={"X-Role": "almacenista"},
    )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "HOLD_BLOCKS_PICK"


def test_dump_requires_photo_and_supervisor():
    r = client.post(
        "/api/events",
        json={"event_type": "dump", "pallet_id": "PAL-PAP-A", "qty_boxes": 2, "payload": {}},
        headers={"X-Role": "almacenista"},
    )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "DUMP_NEEDS_PHOTO"


def test_twenty_offline_events_dedupe():
    run = uuid.uuid4().hex
    events = []
    for i in range(20):
        events.append(
            {
                "client_uuid": f"offline-count-{run}-{i:02d}",
                "device_ts": NOW_ISO,
                "event_type": "count",
                "zone_id": "Z-CAM2",
                "qty_boxes": 1,
                "payload": {"seq": i},
            }
        )
    first = client.post("/api/sync", json={"events": events, "shift": "matutino"})
    assert first.status_code == 200
    assert first.json()["inserted"] == 20
    second = client.post("/api/sync", json={"events": events, "shift": "matutino"})
    assert second.json()["inserted"] == 0
    assert second.json()["duplicates"] == 20


def test_rule_change_requires_owner():
    r = client.post("/api/rules/R-HOLD-BLOCK", json={"active": False}, headers={"X-Role": "gerente"})
    assert r.status_code == 403
    ok = client.post("/api/rules/R-HOLD-BLOCK", json={"active": True, "actor_id": "ST-DUENO"}, headers={"X-Role": "dueno"})
    assert ok.status_code == 200


def test_private_losses_forbidden_to_sales():
    r = client.get("/api/losses?private=true", headers={"X-Role": "ventas"})
    assert r.status_code == 403


def test_q10_warms_faster():
    cool = remaining_life(
        life_days=28,
        received_at="2026-10-10T10:00:00-06:00",
        now="2026-10-20T14:30:00-06:00",
        t_min=5,
        t_max=12,
        baseline_temp=8.5,
    )
    hot = remaining_life(
        life_days=28,
        received_at="2026-10-10T10:00:00-06:00",
        now="2026-10-20T14:30:00-06:00",
        t_min=5,
        t_max=12,
        exposures=[
            {"ts": "2026-10-10T10:00:00-06:00", "temp_c": 8.5},
            {"ts": "2026-10-19T02:00:00-06:00", "temp_c": 16.0},
            {"ts": "2026-10-19T07:00:00-06:00", "temp_c": 10.4},
        ],
    )
    assert hot["equivalent_days"] > cool["equivalent_days"]
    assert q10_factor(16, 8.5) > 1


def test_trace_is_fast_and_has_mass_balance():
    # Use the already-seeded app db
    from app import DB_FILE

    conn = connect(DB_FILE)
    tr = trace_lot(conn, "LOT-CER-0918")
    assert tr["elapsed_ms"] < 1000
    assert "recibido" in tr["mass_balance"]
    assert tr["lot"]["lot_code"] == "CER-BING-20261018"


def test_cockpit_and_ask():
    c = client.get("/api/cockpit")
    assert c.status_code == 200
    body = c.json()
    assert body["missing_boxes"] >= 12
    assert body["truth_score"] >= 60
    a = client.post("/api/ask", json={"q": "¿qué se perdió anoche?"})
    assert a.json()["intent"] == "perdio_anoche"
    assert a.json()["items"]
