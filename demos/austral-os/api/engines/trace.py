"""Backward and forward lot trace plus a thin FSMA 204 lens on the same ledger."""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from db import fetchall, fetchone


def trace_lot(db, lot_id: str) -> dict[str, Any]:
    t0 = perf_counter()
    lot = fetchone(
        db,
        """SELECT l.*, s.name AS sku_name, s.variety, s.origin_country
           FROM lots l JOIN skus s ON s.id = l.sku_id WHERE l.id = ?""",
        (lot_id,),
    )
    if not lot:
        return {"error": "lot_not_found"}
    events = fetchall(db, "SELECT * FROM events WHERE lot_id = ? ORDER BY ts", (lot_id,))
    pallets = fetchall(db, "SELECT * FROM pallets WHERE lot_id = ?", (lot_id,))
    customers = []
    for e in events:
        if e["event_type"] in ("dispatch", "deliver"):
            payload = json.loads(e["payload"] or "{}")
            cid = payload.get("customer_id")
            if cid:
                party = fetchone(db, "SELECT * FROM parties WHERE id = ?", (cid,))
                customers.append(
                    {
                        "customer": (party or {}).get("name"),
                        "city": (party or {}).get("city"),
                        "qty": e["qty_boxes"],
                        "ts": e["ts"],
                        "event": e["event_type"],
                    }
                )
    in_qty = sum(e["qty_boxes"] or 0 for e in events if e["event_type"] in ("receive", "po_open") and e.get("site_id") != "CEDIS-GDL")
    # Mass balance: first receive at home vs remaining + outbound + gaps
    received = sum(
        e["qty_boxes"] or 0
        for e in events
        if e["event_type"] == "receive" and e.get("site_id") in (None, "CEDIS-MEX")
    )
    outbound = sum(e["qty_boxes"] or 0 for e in events if e["event_type"] in ("dispatch", "deliver"))
    on_hand = sum(p["qty_boxes"] for p in pallets if p.get("site_id") != "CEDIS-GDL")
    elapsed_ms = round((perf_counter() - t0) * 1000, 2)
    return {
        "lot": lot,
        "backward": [
            {
                "what": "proveedor / origen",
                "value": lot["origin"],
                "tlc_source": lot.get("tlc_source"),
                "harvest": lot.get("harvest_date"),
                "pack": lot.get("pack_date"),
                "po": lot.get("po_id"),
            }
        ],
        "forward": customers,
        "events": events,
        "pallets": pallets,
        "mass_balance": {
            "recibido": received,
            "en_mano": on_hand,
            "salido": outbound,
            "explicado": on_hand + outbound,
            "recibido_vs_explicado": received - (on_hand + outbound),
        },
        "elapsed_ms": elapsed_ms,
    }


def fsma_view(db, lot_id: str) -> dict[str, Any]:
    """Required-data checklist mapped from warehouse events. Not a legal opinion."""
    tr = trace_lot(db, lot_id)
    lot = tr.get("lot") or {}
    events = tr.get("events") or []
    kdes = [
        ("location_description", bool(lot.get("origin")), "origen del lote / TLC source"),
        ("traceability_lot_code", bool(lot.get("lot_code")), lot.get("lot_code")),
        ("traceability_lot_code_source", bool(lot.get("tlc_source")), lot.get("tlc_source")),
        ("quantity", True, "cajas en cada evento"),
        ("receiving_date", any(e["event_type"] == "receive" for e in events), "eventos receive"),
        ("shipping_date", any(e["event_type"] in ("dispatch", "transfer") for e in events), "eventos dispatch/transfer"),
        ("reference_document", bool(lot.get("po_id")), lot.get("po_id")),
    ]
    missing = [k for k, ok, _ in kdes if not ok]
    return {
        "lot_id": lot_id,
        "disclaimer": "Vista FSMA 204 sobre el mismo libro de custodia. No es un dictamen legal.",
        "kdes": [{"key": k, "present": ok, "note": note} for k, ok, note in kdes],
        "ready": not missing,
        "missing": missing,
        "elapsed_ms": tr.get("elapsed_ms"),
    }


def epcis_shipping(db, lot_id: str) -> dict[str, Any]:
    tr = trace_lot(db, lot_id)
    lot = tr.get("lot") or {}
    dispatches = [e for e in (tr.get("events") or []) if e["event_type"] in ("dispatch", "transfer")]
    events = []
    for e in dispatches:
        events.append(
            {
                "type": "ObjectEvent",
                "eventTime": e["ts"],
                "eventTimeZoneOffset": "-06:00",
                "action": "OBSERVE",
                "bizStep": "shipping",
                "disposition": "in_transit",
                "quantityList": [
                    {
                        "epcClass": f"urn:epc:class:lgtin:376.12345.{lot.get('sku_id', 'sku')}.{lot.get('lot_code')}",
                        "quantity": e["qty_boxes"],
                        "uom": "CS",
                    }
                ],
                "bizLocation": {"id": f"urn:epc:id:sgln:3761234.00000.0"},
                "sourceList": [{"type": "owning_party", "source": "urn:epc:id:sgln:3761234.00000.0"}],
            }
        )
    return {
        "@context": ["https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld"],
        "type": "EPCISDocument",
        "schemaVersion": "2.0",
        "epcisBody": {"eventList": events},
        "disclaimer": "Ejemplo EPCIS 2.0 JSON-LD generado del libro de custodia. Datos sintéticos.",
    }
