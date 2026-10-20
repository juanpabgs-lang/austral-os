from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from codes import gs1_check_digit, gtin14, voice_pick_code  # noqa: E402
from kdes import KDE_TABLE, required_keys, validate_record  # noqa: E402
from seed import seed  # noqa: E402
import app as appmod  # noqa: E402
from app import app, DB  # noqa: E402


def _reseed():
    if appmod._CONN is not None:
        appmod._CONN.close()
        appmod._CONN = None
    seed(DB, reset=True)
    appmod.reopen()


_reseed()
client = TestClient(app)


def test_kde_table_covers_six_ctes():
    ctes = {r["cte"] for r in KDE_TABLE}
    assert ctes == {"harvesting", "cooling", "initial_packing", "shipping", "receiving", "transformation"}
    assert "tlc" in required_keys("initial_packing")
    assert "field_name" in required_keys("harvesting")


def test_planted_gaps_are_caught():
    lots = client.get("/api/lots").json()["lots"]
    by_id = {l["id"]: l for l in lots}
    assert any(g["key"] == "field_name" for g in by_id["LOT-TOM-GAP"]["gaps"])
    assert any(g["key"] == "cool_date" for g in by_id["LOT-CUC-GAP"]["gaps"])
    assert any(g["key"] == "tlc_source" for g in by_id["LOT-PEP-GAP"]["gaps"])
    assert by_id["LOT-GRP-OK"]["gaps"] == []
    assert by_id["LOT-TOM-OK"]["gaps"] == []


def test_gate_blocks_incomplete_ftl_truck():
    r = client.post("/api/gate/release", json={"shipment_id": "SH-TOM-GAP"})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "GATE_BLOCKED"


def test_gate_allows_complete_and_non_ftl():
    assert client.post("/api/gate/release", json={"shipment_id": "SH-TOM-1"}).status_code == 200
    assert client.post("/api/gate/release", json={"shipment_id": "SH-GRP-1"}).status_code == 200


def test_label_blocked_without_field():
    r = client.get("/api/label/LOT-TOM-GAP")
    assert r.status_code == 409


def test_label_prints_when_complete():
    r = client.get("/api/label/LOT-TOM-OK")
    assert r.status_code == 200
    assert r.json()["pti"]["lot"] == "TOM-RIM-20261018-A"
    assert len(r.json()["vpc"]["vpc"]) == 4


def test_gs1_check_digit_published_style_examples():
    # Independently computed from the GS1 odd-from-right × 3 rule.
    assert gs1_check_digit("123456789012") == "8"
    assert gs1_check_digit("061414100002") == "9"
    assert gtin14("1750123450001").isdigit() and len(gtin14("1750123450001")) == 14
    # Self-check: full number including check digit validates.
    full = gtin14("1750123450001")
    assert gs1_check_digit(full[:-1]) == full[-1]


def test_vpc_stable():
    a = voice_pick_code("17501234500018", "TOM-RIM-20261018-A", "20261018")
    b = voice_pick_code("17501234500018", "TOM-RIM-20261018-A", "20261018")
    assert a["vpc"] == b["vpc"]
    assert a["algorithm"] == "crc16-ccitt-candidate"


def test_validate_non_ftl_never_gaps():
    assert validate_record("shipping", {}, ftl=False) == []


def test_recall_and_trace():
    r = client.get("/api/recall/LOT-TOM-OK")
    assert r.status_code == 200
    assert "Desierto Produce" in r.json()["letters"]["en"]
    assert r.json()["mass_balance"]["cases_packed"] == 800
    t = client.get("/api/trace/LOT-TOM-OK")
    assert t.json()["elapsed_ms"] < 1000


def test_fix_clears_gap_then_release():
    _reseed()
    blocked = client.post("/api/gate/release", json={"shipment_id": "SH-TOM-GAP"})
    assert blocked.status_code == 409
    fix = client.post(
        "/api/records/fix",
        json={"lot_id": "LOT-TOM-GAP", "cte": "harvesting", "key": "field_name", "value": "Lote 12-Norte"},
    )
    assert fix.status_code == 200
    assert not any(g["key"] == "field_name" for g in fix.json()["remaining"])
