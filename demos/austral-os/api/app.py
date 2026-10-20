"""Norfront Fresh · Austral OS demo API (port 8016)."""

from __future__ import annotations

import io
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pydantic import BaseModel, Field

from config import NOW_ISO, PRODUCT_NAME, ROLE_LABELS, TENANT_NAME, WATERMARK
from db import audit, connect, fetchall, fetchone, insert_event, tx
from engines.allocation import available_to_sell, inventory_with_life, match_orders, ship_first
from engines.freshness import chilling_flag, ethylene_conflicts
from engines.loss import all_gaps, classify_lot, private_signals, public_gap
from engines.nl import parse as parse_nl
from engines.route import order_stops
from engines.rules import RuleViolation, apply_event_side_effects, check_event
from engines.trace import epcis_shipping, fsma_view, trace_lot
from seed import seed

DB_FILE = Path(__file__).resolve().parent / "austral.db"
NOW = NOW_ISO


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not DB_FILE.exists():
        seed(DB_FILE)
    yield


app = FastAPI(title=f"{PRODUCT_NAME} · {TENANT_NAME}", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def db():
    return connect(DB_FILE)


def meta(conn) -> dict[str, str]:
    return {r["key"]: r["value"] for r in fetchall(conn, "SELECT key, value FROM meta")}


def actor_from(x_role: str | None, x_actor: str | None) -> tuple[str, str]:
    role = x_role or "gerente"
    if role not in ROLE_LABELS:
        role = "gerente"
    if x_actor:
        return x_actor, role
    row = fetchone(connect(DB_FILE), "SELECT id FROM staff WHERE role = ? LIMIT 1", (role,))
    return (row["id"] if row else "ST-GER"), role


def hours_since(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        then = datetime.fromisoformat(ts)
        now = datetime.fromisoformat(NOW)
        return round((now - then).total_seconds() / 3600.0, 1)
    except ValueError:
        return None


@app.get("/api/meta")
def get_meta():
    conn = db()
    m = meta(conn)
    staff = fetchall(conn, "SELECT id, name, role, shift FROM staff")
    return {
        "product": PRODUCT_NAME,
        "tenant": TENANT_NAME,
        "watermark": WATERMARK,
        "now": NOW,
        "roles": ROLE_LABELS,
        "staff": staff,
        "meta": m,
    }


@app.post("/api/reset")
def reset_demo():
    seed(DB_FILE, reset=True)
    return {"ok": True, "now": NOW, "watermark": WATERMARK}


@app.get("/api/cockpit")
def cockpit():
    conn = db()
    inv = inventory_with_life(conn, NOW)
    gaps = [public_gap(g) for g in all_gaps(conn) if g["qty"] > 0 or g["kind"] in ("extravio", "reclamo_desestimado")]
    missing = [g for g in gaps if g["kind"] in ("faltante", "faltante_proveedor", "merma_no_registrada", "reempaque")]
    missing_boxes = sum(g["qty"] for g in missing)
    missing_value = sum(g.get("value_mxn") or 0 for g in missing)
    at_risk = [p for p in inv if p["freshness"]["band"] in ("critico", "riesgo")]
    var72 = sum(p["qty_boxes"] * p["box_value_mxn"] for p in at_risk)
    counted = [p for p in inv if p.get("last_count_at")]
    # Truth score: 100 minus penalties for unverified, missing, holds unexplained.
    stale = [p for p in inv if hours_since(p.get("last_count_at")) and hours_since(p["last_count_at"]) > 48]
    truth = max(100 - len(missing) * 4 - len(stale) * 2 - (5 if missing_boxes else 0), 62)
    zones = fetchall(conn, "SELECT * FROM zones WHERE site_id='CEDIS-MEX'")
    alerts = _alerts(conn, inv, gaps)
    ship = ship_first(conn, NOW)[:6]
    return {
        "watermark": WATERMARK,
        "now": NOW,
        "truth_score": truth,
        "truth_note": f"{len(counted)} pallets con conteo · {len(stale)} sin verificar >48 h",
        "value_at_risk_72h_mxn": var72,
        "missing_boxes": missing_boxes,
        "missing_value_mxn": missing_value,
        "missing": missing[:8],
        "at_risk_pallets": len(at_risk),
        "temps": [
            {"id": z["id"], "name": z["name"], "set": z["temp_setpoint_c"], "current": z["temp_current_c"]}
            for z in zones
            if z["kind"] in ("camara", "anden")
        ],
        "ship_first": [
            {
                "pallet_id": p["id"],
                "sku": f"{p['sku_name']} {p['variety']}",
                "remaining_days": p["freshness"]["remaining_days"],
                "band": p["freshness"]["band"],
                "qty": p["qty_boxes"],
                "zone": p["zone_name"],
            }
            for p in ship
        ],
        "alerts": alerts,
    }


def _alerts(conn, inv, gaps) -> list[dict[str, Any]]:
    alerts = []
    for g in gaps:
        if g["kind"] in ("faltante", "faltante_proveedor", "merma_no_registrada", "reempaque"):
            alerts.append(
                {
                    "id": f"gap-{g['lot_id']}-{g['segment']}",
                    "severity": "alta" if g["qty"] >= 10 else "media",
                    "kind": g["kind"],
                    "title": g["summary"],
                    "segment": g["segment"],
                    "shift": g.get("shift"),
                    "qty": g["qty"],
                    "lot_id": g["lot_id"],
                    "href": f"/perdidas?lot={g['lot_id']}",
                }
            )
    # compressor
    cam3 = fetchall(
        conn,
        "SELECT * FROM temp_log WHERE zone_id='Z-CAM3' AND temp_c >= 15 ORDER BY ts",
    )
    if cam3:
        alerts.insert(
            0,
            {
                "id": "cam3-compressor",
                "severity": "alta",
                "kind": "abuso_termico",
                "title": "Cámara 3 a 16 °C durante 5 h (19 oct, 02:00–07:00). Aguacate y mango en riesgo.",
                "segment": "almacen",
                "shift": "nocturno",
                "href": "/embarcar",
            },
        )
    occupants_by_zone: dict[str, list] = {}
    for p in inv:
        occupants_by_zone.setdefault(p.get("zone_id") or "", []).append(
            {
                "pallet_id": p["id"],
                "name": f"{p['sku_name']} {p['variety']}",
                "ethylene_prod": p["ethylene_prod"],
                "ethylene_sens": p["ethylene_sens"],
            }
        )
    for zone_id, occ in occupants_by_zone.items():
        for c in ethylene_conflicts(occ):
            alerts.append(
                {
                    "id": f"eth-{c['sensitive_pallet']}",
                    "severity": "media",
                    "kind": "etileno",
                    "title": c["message"],
                    "href": "/mapa",
                    "pallet_id": c["sensitive_pallet"],
                }
            )
    for p in inv:
        flag = chilling_flag(p, p.get("temp_current_c"))
        if flag:
            alerts.append(
                {
                    "id": f"chill-{p['id']}",
                    "severity": "alta",
                    "kind": "frio",
                    "title": flag["message"],
                    "href": "/mapa",
                    "pallet_id": p["id"],
                }
            )
    holds = [p for p in inv if p["hold_status"] != "libre"]
    for p in holds:
        alerts.append(
            {
                "id": f"hold-{p['id']}",
                "severity": "media",
                "kind": "retencion",
                "title": f"{p['sku_name']} {p['variety']} retenido · {p['hold_reason']}",
                "href": "/mapa",
                "pallet_id": p["id"],
            }
        )
    return alerts


@app.get("/api/map")
def warehouse_map():
    conn = db()
    zones = fetchall(conn, "SELECT * FROM zones")
    positions = fetchall(conn, "SELECT * FROM positions")
    inv = inventory_with_life(conn, NOW)
    pallets = []
    for p in inv:
        pallets.append(
            {
                "id": p["id"],
                "sscc": p["sscc"],
                "sku": f"{p['sku_name']} {p['variety']}",
                "lot_code": p["lot_code"],
                "qty": p["qty_boxes"],
                "zone_id": p["zone_id"],
                "position_id": p["position_id"],
                "x": None,
                "y": None,
                "band": p["freshness"]["band"],
                "remaining_days": p["freshness"]["remaining_days"],
                "hold": p["hold_status"],
                "hold_reason": p["hold_reason"],
                "site_id": p["site_id"],
            }
        )
    pos_xy = {r["id"]: r for r in positions}
    for p in pallets:
        loc = pos_xy.get(p["position_id"] or "")
        if loc:
            p["x"] = loc["x"]
            p["y"] = loc["y"]
            p["position_code"] = loc["code"]
    return {"zones": zones, "positions": positions, "pallets": pallets, "now": NOW}


@app.get("/api/inventory")
def inventory():
    conn = db()
    return {"items": inventory_with_life(conn, NOW), "watermark": WATERMARK}


@app.get("/api/available")
def available():
    conn = db()
    rows = available_to_sell(conn, NOW)
    for r in rows:
        r["verified_hours_ago"] = hours_since(r.get("verified"))
    return {"items": rows, "now": NOW, "note": "físico − retenciones − asignado a pedidos abiertos"}


@app.get("/api/ship-first")
def ship_first_view():
    conn = db()
    matches = match_orders(conn, NOW)
    risky = ship_first(conn, NOW)
    stops = []
    for m in matches:
        for a in m["allocated"]:
            stops.append({**a, "order_id": m["order"]["id"], "customer": m["order"]["customer"]})
    route = order_stops(stops)
    return {
        "risky": risky,
        "matches": matches,
        "pick_route": route,
        "now": NOW,
        "formula": "vida restante = life_days − Σ Δt · Q10^((T−Tref)/10) · Q10=2.5 · HB66",
    }


@app.get("/api/losses")
def losses(private: bool = False, x_role: str | None = Header(default=None)):
    conn = db()
    gaps = [public_gap(g) for g in all_gaps(conn)]
    planted = fetchall(conn, "SELECT * FROM planted_cases")
    payload: dict[str, Any] = {
        "gaps": gaps,
        "planted": planted,
        "note": "Atribución por segmento, turno y zona. Proceso, no persona.",
    }
    if private:
        if x_role != "dueno":
            raise HTTPException(403, "La vista privada solo la abre el dueño.")
        payload["signals"] = private_signals(conn)
        payload["label"] = "señal, no acusación · requiere revisión humana"
    return payload


@app.get("/api/losses/{lot_id}")
def loss_lot(lot_id: str):
    conn = db()
    result = classify_lot(conn, lot_id)
    if result.get("error"):
        raise HTTPException(404, result["error"])
    result["gaps"] = [public_gap(g) for g in result["gaps"]]
    # Strip actor names from the public timeline.
    for e in result["events"]:
        e.pop("actor_id", None)
    return result


@app.get("/api/trace/{lot_id}")
def trace(lot_id: str):
    conn = db()
    result = trace_lot(conn, lot_id)
    if result.get("error"):
        raise HTTPException(404, result["error"])
    return result


@app.get("/api/fsma/{lot_id}")
def fsma(lot_id: str):
    return fsma_view(db(), lot_id)


@app.get("/api/epcis/{lot_id}")
def epcis(lot_id: str):
    return epcis_shipping(db(), lot_id)


@app.get("/api/fda-sheet/{lot_id}")
def fda_sheet(lot_id: str):
    conn = db()
    tr = trace_lot(conn, lot_id)
    if tr.get("error"):
        raise HTTPException(404, "lot_not_found")
    wb = Workbook()
    ws = wb.active
    ws.title = "FDA sortable (demo)"
    headers = [
        "Traceability Lot Code",
        "Quantity",
        "Unit of Measure",
        "Product Description",
        "Location Description",
        "CTE",
        "Event Date",
        "Reference Document Type",
        "Reference Document Number",
        "TLC Source",
    ]
    ws.append(headers)
    lot = tr["lot"]
    for e in tr["events"]:
        ws.append(
            [
                lot["lot_code"],
                e.get("qty_boxes"),
                "cases",
                f"{lot['sku_name']} {lot['variety']}",
                e.get("zone_id") or e.get("site_id"),
                e["event_type"],
                e["ts"],
                "PO" if lot.get("po_id") else "",
                lot.get("po_id") or "",
                lot.get("tlc_source") or "",
            ]
        )
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=fda-{lot_id}.xlsx"},
    )


@app.get("/api/lots")
def lots(q: str | None = None):
    conn = db()
    rows = fetchall(
        conn,
        """SELECT l.*, s.name AS sku_name, s.variety
           FROM lots l JOIN skus s ON s.id = l.sku_id ORDER BY l.pack_date DESC""",
    )
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in json.dumps(r, ensure_ascii=False).lower()]
    return {"lots": rows}


@app.get("/api/rules")
def rules():
    conn = db()
    return {
        "rules": fetchall(conn, "SELECT * FROM rules ORDER BY code"),
        "changes": fetchall(
            conn,
            """SELECT c.*, r.title FROM rule_changes c JOIN rules r ON r.id = c.rule_id ORDER BY c.ts DESC""",
        ),
        "audit": fetchall(conn, "SELECT * FROM audit ORDER BY id DESC LIMIT 80"),
    }


class RulePatch(BaseModel):
    active: bool
    actor_id: str = "ST-GER"
    role: str = "gerente"


@app.post("/api/rules/{rule_id}")
def patch_rule(rule_id: str, body: RulePatch, x_role: str | None = Header(default=None)):
    role = x_role or body.role
    if role != "dueno":
        raise HTTPException(403, "Ninguna regla de almacén cambia sin aprobación del dueño.")
    conn = db()
    rule = fetchone(conn, "SELECT * FROM rules WHERE id = ?", (rule_id,))
    if not rule:
        raise HTTPException(404, "rule_not_found")
    with tx(conn):
        conn.execute(
            "INSERT INTO rule_changes (rule_id, ts, actor_id, action, before_json, after_json, approved_by) VALUES (?,?,?,?,?,?,?)",
            (
                rule_id,
                NOW,
                body.actor_id,
                "toggle",
                json.dumps({"active": rule["active"]}),
                json.dumps({"active": int(body.active)}),
                body.actor_id,
            ),
        )
        conn.execute(
            "UPDATE rules SET active=?, approved_by=?, approved_at=?, version=version+1 WHERE id=?",
            (int(body.active), body.actor_id, NOW, rule_id),
        )
        audit(conn, ts=NOW, actor_id=body.actor_id, role=role, action="rule.change", entity="rule", entity_id=rule_id)
    return {"ok": True}


class EventIn(BaseModel):
    client_uuid: str | None = None
    ts: str | None = None
    device_ts: str | None = None
    event_type: str
    site_id: str | None = None
    zone_id: str | None = None
    pallet_id: str | None = None
    lot_id: str | None = None
    sku_id: str | None = None
    qty_boxes: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncIn(BaseModel):
    events: list[EventIn]
    actor_id: str | None = None
    role: str | None = None
    shift: str | None = None


def _ingest_one(conn, ev: EventIn, actor_id: str, role: str, shift: str | None) -> dict[str, Any]:
    pallet = fetchone(conn, "SELECT * FROM pallets WHERE id = ?", (ev.pallet_id,)) if ev.pallet_id else None
    payload = dict(ev.payload or {})
    try:
        check_event(conn, ev.event_type, payload, pallet)
    except RuleViolation as exc:
        raise HTTPException(exc.http, detail={"code": exc.code, "message": exc.message}) from exc
    ts = ev.ts or ev.device_ts or NOW
    eid, inserted = insert_event(
        conn,
        client_uuid=ev.client_uuid or str(uuid.uuid4()),
        ts=ts,
        device_ts=ev.device_ts or ts,
        actor_id=actor_id,
        role=role,
        shift=shift,
        event_type=ev.event_type,
        site_id=ev.site_id,
        zone_id=ev.zone_id,
        pallet_id=ev.pallet_id,
        lot_id=ev.lot_id or (pallet or {}).get("lot_id"),
        sku_id=ev.sku_id,
        qty_boxes=ev.qty_boxes,
        payload=payload,
    )
    if inserted:
        apply_event_side_effects(
            conn,
            ev.event_type,
            {
                "pallet_id": ev.pallet_id,
                "zone_id": ev.zone_id,
                "position_id": payload.get("position_id"),
                "qty_boxes": ev.qty_boxes,
                "reason": payload.get("reason"),
                "payload": payload,
            },
            ts,
        )
        audit(conn, ts=ts, actor_id=actor_id, role=role, action=f"event.{ev.event_type}", entity="event", entity_id=str(eid))
    return {"id": eid, "inserted": inserted, "client_uuid": ev.client_uuid}


@app.post("/api/events")
def post_event(body: EventIn, x_role: str | None = Header(default=None), x_actor: str | None = Header(default=None)):
    actor, role = actor_from(x_role, x_actor)
    conn = db()
    with tx(conn):
        result = _ingest_one(conn, body, actor, role, body.payload.get("shift") if body.payload else None)
    return result


@app.post("/api/sync")
def sync(body: SyncIn, x_role: str | None = Header(default=None), x_actor: str | None = Header(default=None)):
    actor, role = actor_from(x_role, body.role or x_actor)
    conn = db()
    results = []
    with tx(conn):
        for ev in body.events:
            results.append(_ingest_one(conn, ev, body.actor_id or actor, role, body.shift))
    inserted = sum(1 for r in results if r["inserted"])
    return {"ok": True, "received": len(results), "inserted": inserted, "duplicates": len(results) - inserted, "results": results}


@app.get("/api/documents")
def documents(kind: str | None = None):
    conn = db()
    if kind:
        rows = fetchall(conn, "SELECT * FROM documents WHERE kind = ? ORDER BY created_at DESC", (kind,))
    else:
        rows = fetchall(conn, "SELECT * FROM documents ORDER BY created_at DESC")
    for r in rows:
        try:
            r["body"] = json.loads(r["body"])
        except json.JSONDecodeError:
            pass
    return {"documents": rows}


@app.get("/api/documents/siconet.csv")
def siconet_export():
    conn = db()
    inv = inventory_with_life(conn, NOW)
    buf = io.StringIO()
    buf.write("sku,variedad,lote,sscc,cajas,zona,posicion,retencion,valor_mxn,verificado\n")
    for p in inv:
        buf.write(
            ",".join(
                [
                    p["sku_name"],
                    p["variety"],
                    p["lot_code"],
                    p["sscc"],
                    str(p["qty_boxes"]),
                    p.get("zone_name") or "",
                    p.get("position_code") or "",
                    p["hold_status"],
                    str(p["qty_boxes"] * p["box_value_mxn"]),
                    p.get("last_count_at") or "",
                ]
            )
            + "\n"
        )
    data = io.BytesIO(buf.getvalue().encode("utf-8"))
    return StreamingResponse(
        data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=siconet-inventario.csv"},
    )


class AskIn(BaseModel):
    q: str


@app.post("/api/ask")
def ask(body: AskIn):
    parsed = parse_nl(body.q)
    conn = db()
    extra: dict[str, Any] = {}
    if parsed["intent"] == "vence_semana":
        extra["items"] = [
            {
                "sku": f"{p['sku_name']} {p['variety']}",
                "remaining_days": p["freshness"]["remaining_days"],
                "qty": p["qty_boxes"],
            }
            for p in ship_first(conn, NOW)[:8]
        ]
    elif parsed["intent"] == "perdio_anoche":
        extra["items"] = [
            public_gap(g)
            for g in all_gaps(conn)
            if g.get("shift") == "nocturno" and g["qty"] > 0
        ]
    elif parsed["intent"] == "inventario_sku":
        extra["items"] = available_to_sell(conn, NOW)
    elif parsed["intent"] == "retenciones":
        extra["items"] = [p for p in inventory_with_life(conn, NOW) if p["hold_status"] != "libre"]
    return {**parsed, **extra}


@app.get("/api/presentation")
def presentation():
    return {
        "steps": [
            {
                "id": "cockpit",
                "route": "/",
                "title": "El dueño ve la verdad del almacén",
                "say": "Inventario sagrado: score, faltantes, valor en riesgo a 72 h, temperaturas.",
            },
            {
                "id": "cherry",
                "route": "/perdidas?lot=LOT-CER-0918",
                "title": "12 cajas de cereza · andén → cámara · turno nocturno",
                "say": "De la alerta a segmento, turno y evidencia en dos clics. Proceso, no persona.",
            },
            {
                "id": "map",
                "route": "/mapa",
                "title": "Mapa en vivo, color por frescura",
                "say": "Cámara 3 caliente, kiwi junto a manzana, limón demasiado frío, fresa retenida.",
            },
            {
                "id": "ship",
                "route": "/embarcar",
                "title": "Qué sale primero",
                "say": "Aguacate expuesto se empareja a Horeca (3 días). Costa Fresca pide 7 · no toma ese lote.",
            },
            {
                "id": "hold",
                "route": "/captura",
                "title": "Retención que sí bloquea",
                "say": "El almacenista escanea la fresa retenida. El API responde 409.",
            },
            {
                "id": "offline",
                "route": "/captura",
                "title": "Cámara fría · sin señal",
                "say": "Los eventos se quedan en el dispositivo y se sincronizan al cruzar el andén, sin duplicados.",
            },
            {
                "id": "trace",
                "route": "/traza?lot=LOT-CER-0918",
                "title": "Trazar un lote en milisegundos",
                "say": "Atrás al huerto, adelante a Super Valle. Hoja FDA y EPCIS del mismo libro.",
            },
            {
                "id": "paper",
                "route": "/papeleria",
                "title": "El papeleo se escribe solo",
                "say": "Recepción, reclamo al proveedor, remisión, Carta Porte, POD, export a Siconet.",
            },
            {
                "id": "golive",
                "route": "/arrancar",
                "title": "¿Qué tan rápido se prende?",
                "say": "Importar Siconet → conteo inicial por cámara → primer turno.",
            },
        ]
    }


@app.get("/api/connector")
def connector():
    return {
        "source": "Siconet / Excel (sintético)",
        "note": "No hay un export real de Austral. Estas columnas son un mapeo supuesto, sustituible.",
        "files": [
            {
                "name": "siconet_existencias.xlsx",
                "columns": ["SKU", "Descripcion", "Lote", "Cantidad", "Almacen", "Valor"],
                "rows": 45,
                "status": "mapeado",
            },
            {
                "name": "siconet_pedidos.xlsx",
                "columns": ["Folio", "Cliente", "SKU", "Cantidad", "FechaPromesa"],
                "rows": 10,
                "status": "mapeado",
            },
            {
                "name": "siconet_oc.xlsx",
                "columns": ["OC", "Proveedor", "SKU", "Cantidad", "FechaETA"],
                "rows": 20,
                "status": "mapeado",
            },
        ],
        "unmapped": ["A9", "CLAM", "line order", "las tres reglas de Dafne"],
        "assumption": "Esos términos viven en ASSUMPTIONS.md hasta que Mateo envíe el significado.",
    }


@app.get("/health")
def health():
    return {"ok": True, "now": NOW}
