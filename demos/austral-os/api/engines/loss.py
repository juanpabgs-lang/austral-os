"""Compare quantities along the custody chain and classify the gap.

Segments: po → recibido → almacenado → surtido → cargado → entregado,
plus reempaque and transito. A found pallet is an extravío, not a loss.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from db import fetchall, fetchone

SEGMENTS = (
    "po_a_recibido",
    "anden_a_camara",
    "reempaque",
    "almacen",
    "transito",
    "surtido_a_cargado",
    "cargado_a_entregado",
    "entregado",
)


def _events(db, lot_id: str | None = None) -> list[dict[str, Any]]:
    if lot_id:
        return fetchall(db, "SELECT * FROM events WHERE lot_id = ? ORDER BY ts", (lot_id,))
    return fetchall(db, "SELECT * FROM events ORDER BY ts")


def classify_lot(db, lot_id: str) -> dict[str, Any]:
    lot = fetchone(
        db,
        """SELECT l.*, s.name AS sku_name, s.variety, s.box_value_mxn, p.name AS supplier
           FROM lots l JOIN skus s ON s.id = l.sku_id
           LEFT JOIN parties p ON p.id = l.supplier_id
           WHERE l.id = ?""",
        (lot_id,),
    )
    if not lot:
        return {"error": "lot_not_found", "lot_id": lot_id}

    evs = _events(db, lot_id)
    po = sum(e["qty_boxes"] or 0 for e in evs if e["event_type"] == "po_open")
    received_home = sum(
        e["qty_boxes"] or 0
        for e in evs
        if e["event_type"] == "receive" and e.get("site_id") in (None, "CEDIS-MEX")
    )
    # Transfers into GDL are a later receive of the same lot.
    received_gdl = sum(
        e["qty_boxes"] or 0
        for e in evs
        if e["event_type"] == "receive" and e.get("site_id") == "CEDIS-GDL"
    )
    putaway = sum(e["qty_boxes"] or 0 for e in evs if e["event_type"] == "putaway")
    picked = sum(e["qty_boxes"] or 0 for e in evs if e["event_type"] == "pick")
    loaded = sum(e["qty_boxes"] or 0 for e in evs if e["event_type"] == "load")
    delivered = sum(e["qty_boxes"] or 0 for e in evs if e["event_type"] == "deliver")
    transferred = sum(e["qty_boxes"] or 0 for e in evs if e["event_type"] == "transfer")
    dumped = sum(e["qty_boxes"] or 0 for e in evs if e["event_type"] == "dump")

    on_hand = fetchone(
        db,
        "SELECT COALESCE(SUM(qty_boxes),0) AS q FROM pallets WHERE lot_id = ?",
        (lot_id,),
    )
    on_hand_qty = int(on_hand["q"] if on_hand else 0)

    repack = [e for e in evs if e["event_type"] == "repack"]
    counts = [e for e in evs if e["event_type"] == "count"]

    gaps: list[dict[str, Any]] = []

    if po and received_home and received_home < po:
        ev = next(e for e in evs if e["event_type"] == "receive")
        gaps.append(
            _gap(
                "po_a_recibido",
                "faltante_proveedor",
                po - received_home,
                ev,
                f"PO {po} cajas, recibido {received_home}.",
            )
        )

    if received_home and putaway and putaway < received_home and not transferred:
        # First putaway after receive, typically andén → cámara.
        put_evs = [e for e in evs if e["event_type"] == "putaway"]
        ev = put_evs[0]
        if ev.get("payload") and '"from_zone": "Z-ANDEN"' in (ev.get("payload") or ""):
            gaps.append(
                _gap(
                    "anden_a_camara",
                    "faltante",
                    received_home - putaway,
                    ev,
                    f"Recibido {received_home}, acomodado {putaway}.",
                )
            )

    for e in repack:
        import json

        payload = json.loads(e["payload"] or "{}")
        qin = payload.get("qty_in") or 0
        qout = payload.get("qty_out") or e["qty_boxes"] or 0
        if qin > qout:
            gaps.append(
                _gap(
                    "reempaque",
                    "reempaque",
                    qin - qout,
                    e,
                    f"Reempaque {qin} → {qout} (rendimiento {payload.get('yield_pct')}%).",
                )
            )

    for e in counts:
        import json

        payload = json.loads(e["payload"] or "{}")
        if payload.get("not_loss") or payload.get("classification") == "extravio":
            gaps.append(
                _gap(
                    "almacen",
                    "extravio",
                    0,
                    e,
                    "Pallet localizado en otra zona. No es pérdida.",
                    extra={"found_zone": payload.get("found_zone"), "expected_zone": payload.get("expected_zone")},
                )
            )
        elif payload.get("unrecorded_dump"):
            expected = payload.get("expected") or 0
            actual = e["qty_boxes"] or 0
            gaps.append(
                _gap(
                    "almacen",
                    "merma_no_registrada",
                    expected - actual,
                    e,
                    f"Conteo {actual} contra esperado {expected}. No hay evento de merma.",
                )
            )

    if transferred and received_gdl and received_gdl < transferred:
        ev = next(e for e in evs if e["event_type"] == "receive" and e.get("site_id") == "CEDIS-GDL")
        gaps.append(
            _gap(
                "transito",
                "faltante",
                transferred - received_gdl,
                ev,
                f"Traspaso {transferred}, recibido en destino {received_gdl}.",
            )
        )

    if loaded and delivered and delivered < loaded:
        ev = next(e for e in evs if e["event_type"] == "deliver")
        gaps.append(
            _gap(
                "cargado_a_entregado",
                "faltante",
                loaded - delivered,
                ev,
                f"Cargado {loaded}, entregado {delivered}.",
            )
        )

    for e in evs:
        if e["event_type"] != "deliver":
            continue
        import json

        payload = json.loads(e["payload"] or "{}")
        if payload.get("claim_status") == "desestimado":
            gaps.append(
                _gap(
                    "entregado",
                    "reclamo_desestimado",
                    0,
                    e,
                    "Reclamo del cliente desestimado: escaneo de carga y POD coinciden.",
                    extra={"claimed_short": payload.get("claimed_short")},
                )
            )

    value = lot["box_value_mxn"]
    for g in gaps:
        g["value_mxn"] = g["qty"] * value
        g["sku_name"] = lot["sku_name"]
        g["variety"] = lot["variety"]
        g["lot_code"] = lot["lot_code"]
        g["supplier"] = lot["supplier"]

    chain = {
        "po": po,
        "recibido": received_home,
        "almacenado": putaway,
        "en_mano": on_hand_qty,
        "surtido": picked,
        "cargado": loaded,
        "entregado": delivered,
        "traspaso": transferred,
        "recibido_destino": received_gdl,
        "merma_registrada": dumped,
    }
    return {
        "lot": lot,
        "chain": chain,
        "gaps": gaps,
        "events": evs,
        "on_hand": on_hand_qty,
    }


def _gap(segment: str, kind: str, qty: int, ev: dict, summary: str, extra: dict | None = None) -> dict:
    return {
        "segment": segment,
        "kind": kind,
        "qty": qty,
        "shift": ev.get("shift"),
        "zone_id": ev.get("zone_id"),
        "site_id": ev.get("site_id"),
        "ts": ev.get("ts"),
        "actor_id": ev.get("actor_id"),
        "pallet_id": ev.get("pallet_id"),
        "lot_id": ev.get("lot_id"),
        "summary": summary,
        **(extra or {}),
    }


def all_gaps(db) -> list[dict[str, Any]]:
    lots = fetchall(db, "SELECT id FROM lots")
    out: list[dict[str, Any]] = []
    for lot in lots:
        result = classify_lot(db, lot["id"])
        for g in result.get("gaps", []):
            g["lot_id"] = lot["id"]
            out.append(g)
    out.sort(key=lambda g: g.get("ts") or "", reverse=True)
    return out


def public_gap(g: dict[str, Any]) -> dict[str, Any]:
    """Strip individual identity. Process, not person."""
    return {k: v for k, v in g.items() if k != "actor_id"}


def private_signals(db) -> list[dict[str, Any]]:
    """Owner-only. Labelled señal, no acusación. Human review required."""
    gaps = all_gaps(db)
    by_actor: dict[str, list] = defaultdict(list)
    for g in gaps:
        if g.get("actor_id") and g["kind"] in ("faltante", "merma_no_registrada"):
            by_actor[g["actor_id"]].append(g)
    staff = {s["id"]: s for s in fetchall(db, "SELECT * FROM staff")}
    signals = []
    for actor_id, items in by_actor.items():
        person = staff.get(actor_id, {"name": actor_id, "role": "?", "shift": "?"})
        qty = sum(i["qty"] for i in items)
        signals.append(
            {
                "label": "señal, no acusación",
                "review": "requiere revisión humana",
                "staff_id": actor_id,
                "staff_name": person["name"],
                "role": person["role"],
                "shift": person["shift"],
                "gap_count": len(items),
                "qty": qty,
                "segments": sorted({i["segment"] for i in items}),
                "cases": [public_gap(i) for i in items],
            }
        )
    signals.sort(key=lambda s: s["qty"], reverse=True)
    return signals
