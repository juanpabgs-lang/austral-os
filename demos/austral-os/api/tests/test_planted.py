"""Every planted case is found and classified. No person named in the public view."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db import connect, init_db  # noqa: E402
from engines.loss import all_gaps, classify_lot, private_signals, public_gap  # noqa: E402
from seed import seed  # noqa: E402


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "t.db"
    seed(path)
    conn = connect(path)
    yield conn
    conn.close()


def _gap(db, case_kind: str, lot_id: str):
    result = classify_lot(db, lot_id)
    hits = [g for g in result["gaps"] if g["kind"] == case_kind]
    assert hits, f"expected {case_kind} on {lot_id}, got {[g['kind'] for g in result['gaps']]}"
    return hits[0]


def test_cherry_night_dock_to_room(db):
    g = _gap(db, "faltante", "LOT-CER-0918")
    assert g["segment"] == "anden_a_camara"
    assert g["shift"] == "nocturno"
    assert g["qty"] == 12


def test_peru_grape_short_ship(db):
    g = _gap(db, "faltante_proveedor", "LOT-UVA-1016")
    assert g["segment"] == "po_a_recibido"
    assert g["qty"] == 24


def test_blueberry_repack_yield(db):
    g = _gap(db, "reempaque", "LOT-ARA-1012")
    assert g["qty"] == 12
    assert g["shift"] == "vespertino"


def test_mango_misplaced_not_loss(db):
    g = _gap(db, "extravio", "LOT-MNG-1011")
    assert g["qty"] == 0
    assert g.get("found_zone") == "Z-CAM1"


def test_avocado_in_transit(db):
    g = _gap(db, "faltante", "LOT-AGU-TRN")
    assert g["segment"] == "transito"
    assert g["qty"] == 4


def test_customer_claim_disproved(db):
    g = _gap(db, "reclamo_desestimado", "LOT-CER-0918")
    assert g["qty"] == 0
    assert g["segment"] == "entregado"


def test_unrecorded_papaya_dump(db):
    g = _gap(db, "merma_no_registrada", "LOT-PAP-1008")
    assert g["qty"] == 10
    assert g["segment"] == "almacen"


def test_public_view_has_no_actor_id(db):
    for g in all_gaps(db):
        pub = public_gap(g)
        assert "actor_id" not in pub


def test_private_signals_are_labelled(db):
    signals = private_signals(db)
    assert signals
    for s in signals:
        assert s["label"] == "señal, no acusación"
        assert s["review"] == "requiere revisión humana"
        assert "staff_name" in s
