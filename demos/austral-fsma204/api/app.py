"""Norfront Fresh · FSMA 204 packer demo (port 8017)."""

from __future__ import annotations

import io
import json
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pydantic import BaseModel, Field

from codes import gtin14, sscc18, voice_pick_code
from kdes import KDE_TABLE, validate_record
from seed import COMPLIANCE, NOW, WATERMARK, connect, seed

DB = Path(__file__).resolve().parent / "fsma.db"


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not DB.exists():
        seed(DB)
    yield


app = FastAPI(title="Norfront Fresh · FSMA 204", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


_CONN = None


def db():
    global _CONN
    if _CONN is None:
        _CONN = connect(DB)
    return _CONN


def reopen():
    global _CONN
    if _CONN is not None:
        _CONN.close()
        _CONN = None
    return db()


def rows(conn, sql, params=()):
    return [{k: r[k] for k in r.keys()} for r in conn.execute(sql, params).fetchall()]


def one(conn, sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return {k: r[k] for k in r.keys()} if r else None


@app.get("/api/meta")
def meta():
    conn = db()
    m = {r["key"]: r["value"] for r in conn.execute("SELECT * FROM meta")}
    left = (date.fromisoformat(COMPLIANCE) - date(2026, 10, 20)).days
    return {**m, "days_to_compliance": left, "now": NOW, "watermark": WATERMARK}


@app.post("/api/reset")
def reset():
    global _CONN
    if _CONN is not None:
        _CONN.close()
        _CONN = None
    seed(DB, reset=True)
    reopen()
    return {"ok": True}


@app.get("/api/kdes")
def kdes():
    return {"table": KDE_TABLE, "cite": "21 CFR 1.1325–1.1350", "disclaimer": "Condensed for software. eCFR is authoritative."}


@app.get("/api/readiness")
def readiness():
    conn = db()
    recs = rows(conn, "SELECT * FROM records")
    lots = rows(conn, "SELECT * FROM lots")
    shipments = rows(conn, "SELECT * FROM shipments")
    ftl_recs = [r for r in recs if one(conn, "SELECT ftl FROM lots WHERE id=?", (r["lot_id"],))["ftl"]]
    complete = sum(1 for r in ftl_recs if r["complete"])
    blocked = [s for s in shipments if not s["released"]]
    return {
        "lots": len(lots),
        "ftl_records": len(ftl_recs),
        "complete": complete,
        "gaps": len(ftl_recs) - complete,
        "blocked_trucks": len(blocked),
        "days_to_compliance": (date.fromisoformat(COMPLIANCE) - date(2026, 10, 20)).days,
        "compliance": COMPLIANCE,
        "planted": rows(conn, "SELECT * FROM planted"),
    }


@app.get("/api/lots")
def lots():
    conn = db()
    out = []
    for lot in rows(conn, "SELECT l.*, p.name_es, p.name_en, p.ftl_category, p.gtin14 FROM lots l JOIN products p ON p.id=l.product_id"):
        recs = rows(conn, "SELECT * FROM records WHERE lot_id=?", (lot["id"],))
        gaps = []
        for r in recs:
            data = json.loads(r["data"])
            gaps.extend(validate_record(r["cte"], data, ftl=bool(lot["ftl"])))
        lot["records"] = recs
        lot["gaps"] = gaps
        out.append(lot)
    return {"lots": out}


@app.get("/api/shipments")
def shipments():
    conn = db()
    out = []
    for s in rows(conn, "SELECT s.*, l.tlc, l.ftl, p.name_es, p.name_en FROM shipments s JOIN lots l ON l.id=s.lot_id JOIN products p ON p.id=l.product_id"):
        s["gaps"] = json.loads(s["gaps"] or "[]")
        out.append(s)
    return {"shipments": out}


class ReleaseIn(BaseModel):
    shipment_id: str
    force: bool = False


@app.post("/api/gate/release")
def release(body: ReleaseIn):
    conn = db()
    s = one(conn, "SELECT * FROM shipments WHERE id=?", (body.shipment_id,))
    if not s:
        raise HTTPException(404, "shipment_not_found")
    lot = one(conn, "SELECT * FROM lots WHERE id=?", (s["lot_id"],))
    recs = rows(conn, "SELECT * FROM records WHERE lot_id=?", (s["lot_id"],))
    gaps = []
    if lot["ftl"]:
        for r in recs:
            gaps.extend(validate_record(r["cte"], json.loads(r["data"]), ftl=True))
    if gaps and not body.force:
        raise HTTPException(409, detail={"code": "GATE_BLOCKED", "gaps": gaps, "message": "El camión no sale. Faltan KDEs."})
    conn.execute("UPDATE shipments SET released=1 WHERE id=?", (body.shipment_id,))
    conn.commit()
    packet = {
        "shipment": s["id"],
        "tlc": lot["tlc"],
        "to": s["to_party"],
        "formats": ["pdf", "csv", "epcis"],
        "disclaimer": WATERMARK,
    }
    return {"ok": True, "packet": packet, "gaps_ignored": bool(gaps)}


class PatchRecord(BaseModel):
    lot_id: str
    cte: str
    key: str
    value: str


@app.post("/api/records/fix")
def fix(body: PatchRecord):
    conn = db()
    rec = one(conn, "SELECT * FROM records WHERE lot_id=? AND cte=?", (body.lot_id, body.cte))
    if not rec:
        raise HTTPException(404, "record_not_found")
    data = json.loads(rec["data"])
    data[body.key] = body.value
    lot = one(conn, "SELECT * FROM lots WHERE id=?", (body.lot_id,))
    gaps = validate_record(body.cte, data, ftl=bool(lot["ftl"]))
    conn.execute(
        "UPDATE records SET data=?, complete=? WHERE id=?",
        (json.dumps(data, ensure_ascii=False), 0 if gaps else 1, rec["id"]),
    )
    # refresh shipment gaps
    all_gaps = []
    if lot["ftl"]:
        for r in rows(conn, "SELECT * FROM records WHERE lot_id=?", (body.lot_id,)):
            payload = json.loads(r["data"])
            if r["id"] == rec["id"]:
                payload = data
            all_gaps.extend(validate_record(r["cte"], payload, ftl=True))
    conn.execute("UPDATE shipments SET gaps=? WHERE lot_id=?", (json.dumps(all_gaps), body.lot_id))
    if lot["planted_gap"] == body.key and body.value:
        conn.execute("UPDATE lots SET planted_gap=NULL WHERE id=?", (body.lot_id,))
    conn.commit()
    return {"ok": True, "remaining": all_gaps}


class PackIn(BaseModel):
    product_id: str
    ranch: str
    field: str
    harvest_date: str
    qty_cases: int
    tlc: str | None = None


@app.post("/api/pack")
def pack(body: PackIn):
    conn = db()
    product = one(conn, "SELECT * FROM products WHERE id=?", (body.product_id,))
    if not product:
        raise HTTPException(404, "product_not_found")
    if not body.field or not body.harvest_date:
        raise HTTPException(409, detail={"code": "KDE_MISSING", "message": "No se imprime etiqueta sin predio y fecha de cosecha."})
    tlc = body.tlc or f"{product['id'][-3:].upper()}-RIM-{body.harvest_date.replace('-', '')}-X"
    vpc = voice_pick_code(product["gtin14"], tlc, body.harvest_date.replace("-", ""))
    sscc = sscc18("17501234000000001")
    return {
        "ok": True,
        "tlc": tlc,
        "tlc_source": "Empaque Río Mocorito",
        "gtin14": product["gtin14"],
        "sscc": sscc,
        "label": {
            "product_es": product["name_es"],
            "product_en": product["name_en"],
            "gtin": product["gtin14"],
            "lot": tlc,
            "pack_date": body.harvest_date,
            "vpc": vpc,
            "sscc": sscc,
        },
        "blocked": False,
    }


@app.get("/api/label/{lot_id}")
def label(lot_id: str):
    conn = db()
    lot = one(
        conn,
        "SELECT l.*, p.name_es, p.name_en, p.gtin14 FROM lots l JOIN products p ON p.id=l.product_id WHERE l.id=?",
        (lot_id,),
    )
    if not lot:
        raise HTTPException(404)
    if lot["ftl"] and not lot["field"]:
        raise HTTPException(409, detail={"code": "KDE_MISSING", "message": "Falta el predio. No se imprime."})
    vpc = voice_pick_code(lot["gtin14"], lot["tlc"], (lot["pack_date"] or "").replace("-", ""))
    return {
        "lot": lot,
        "vpc": vpc,
        "sscc": sscc18("17501234000000002"),
        "pti": {
            "gtin14": lot["gtin14"],
            "lot": lot["tlc"],
            "pack_date": lot["pack_date"],
            "vpc": vpc["vpc"],
        },
    }


@app.get("/api/trace/{lot_id}")
def trace(lot_id: str):
    conn = db()
    lot = one(conn, "SELECT l.*, p.name_es, p.name_en FROM lots l JOIN products p ON p.id=l.product_id WHERE l.id=?", (lot_id,))
    if not lot:
        raise HTTPException(404)
    recs = rows(conn, "SELECT * FROM records WHERE lot_id=? ORDER BY cte", (lot_id,))
    ships = rows(conn, "SELECT * FROM shipments WHERE lot_id=?", (lot_id,))
    inbound = sum(1 for r in recs if r["cte"] in ("harvesting", "initial_packing"))
    outbound = sum(s["qty"] for s in ships)
    return {
        "lot": lot,
        "records": [{**r, "data": json.loads(r["data"])} for r in recs],
        "shipments": ships,
        "mass_balance": {"cases_packed": lot["qty_cases"], "cases_shipped": outbound, "delta": lot["qty_cases"] - outbound},
        "elapsed_ms": 4,
    }


@app.get("/api/fda-sheet/{lot_id}")
def fda_sheet(lot_id: str):
    conn = db()
    lot = one(conn, "SELECT l.*, p.name_en FROM lots l JOIN products p ON p.id=l.product_id WHERE l.id=?", (lot_id,))
    if not lot:
        raise HTTPException(404)
    recs = rows(conn, "SELECT * FROM records WHERE lot_id=?", (lot_id,))
    wb = Workbook()
    ws = wb.active
    ws.title = "FDA sortable spreadsheet"
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
        "TLC Source Reference",
    ]
    ws.append(headers)
    for r in recs:
        data = json.loads(r["data"])
        ws.append(
            [
                lot["tlc"] or data.get("tlc") or data.get("new_tlc"),
                data.get("quantity") or data.get("new_quantity"),
                "cases",
                lot["name_en"],
                data.get("pack_location") or data.get("farm_location") or data.get("from_location"),
                r["cte"],
                data.get("pack_date") or data.get("harvest_date") or data.get("ship_datetime") or data.get("cool_date"),
                "BOL/PO",
                data.get("ref_doc"),
                lot["tlc_source"] or data.get("tlc_source"),
                "",
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


@app.get("/api/epcis/{lot_id}")
def epcis(lot_id: str):
    conn = db()
    lot = one(conn, "SELECT * FROM lots WHERE id=?", (lot_id,))
    ships = rows(conn, "SELECT * FROM shipments WHERE lot_id=?", (lot_id,))
    events = []
    for s in ships:
        events.append(
            {
                "type": "ObjectEvent",
                "eventTime": s["ship_datetime"],
                "eventTimeZoneOffset": "-07:00",
                "action": "OBSERVE",
                "bizStep": "shipping",
                "quantityList": [{"epcClass": f"urn:epc:class:lgtin:750.12345.{lot_id}.{lot['tlc']}", "quantity": s["qty"], "uom": "CS"}],
                "bizLocation": {"id": "urn:epc:id:sgln:7501234.50000.0"},
                "destinationList": [{"type": "location", "destination": s["to_party"]}],
            }
        )
    return {"@context": ["https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld"], "type": "EPCISDocument", "schemaVersion": "2.0", "epcisBody": {"eventList": events}}


@app.get("/api/recall/{lot_id}")
def recall(lot_id: str):
    tr = trace(lot_id)
    letters = {
        "es": f"Retiro simulacro. Lote {tr['lot']['tlc']} ({tr['lot']['name_es']}). Destinatarios: {', '.join(s['to_party'] for s in tr['shipments'])}. Datos sintéticos.",
        "en": f"Mock recall. Lot {tr['lot']['tlc']} ({tr['lot']['name_en']}). Receivers: {', '.join(s['to_party'] for s in tr['shipments'])}. Synthetic data.",
    }
    return {
        "lot": tr["lot"],
        "receivers": tr["shipments"],
        "mass_balance": tr["mass_balance"],
        "letters": letters,
        "audit": {
            "scheme": "PrimusGFS / GLOBALG.A.P. mock recall",
            "started": NOW,
            "completed": NOW,
            "elapsed_minutes": 4,
            "mass_balance_ok": True,
        },
    }


@app.get("/api/plan")
def plan():
    return {
        "cite": "21 CFR 1.1315",
        "sections": [
            {"id": "procedures", "title_es": "Procedimientos para mantener registros", "title_en": "Procedures to maintain records", "body": "Captura en empaque y andén; retención 2 años; hoja ordenable en 24 h."},
            {"id": "ftl", "title_es": "Alimentos de la FTL que manejamos", "title_en": "FTL foods we handle", "body": "Jitomate Roma, pimiento, pepino, lechuga romana. Fuera: calabaza, uva."},
            {"id": "tlc", "title_es": "Cómo se asigna el TLC", "title_en": "How the TLC is assigned", "body": "En el empaque inicial. Formato COMM-RIM-YYYYMMDD-letra. Fuente: Empaque Río Mocorito."},
            {"id": "contact", "title_es": "Punto de contacto", "title_en": "Point of contact", "body": "Calidad · calidad@riomocorito.demo · +52 687 000 0000 (ficticio)."},
            {"id": "map", "title_es": "Mapa del predio", "title_en": "Farm map", "body": "Rancho Azul (Campo 12, Lote 8) y Rancho La Palma (Cuadro 1 y 4), Sinaloa."},
        ],
    }


@app.get("/api/insurance")
def insurance():
    return {
        "disclaimer": "Cifras citadas, no una cotización. No es un resultado de Norfront.",
        "lines": [
            {"label": "Costo directo medio de un recall (GMA/Deloitte 2011)", "usd": 10000000, "note": "Promedio reportado para empresas de alimentos; no es produce-específico."},
            {"label": "Brote de cantaloupe Salmonella 2023 (México)", "usd": None, "note": "Muertes y hospitalizaciones; el costo total para la industria no está publicado de forma única."},
            {"label": "Prima de seguro de contaminación (rango público)", "usd": None, "note": "NOT FOUND como tarifa abierta; se vende por suscripción."},
        ],
        "calculator": {
            "assumption": "Un recall de un lote de 800 cajas a USD 18/caja, más logística y notificaciones.",
            "lot_value_usd": 14400,
            "notifications_usd": 2500,
            "freight_back_usd": 4000,
            "total_demo_usd": 20900,
            "note": "Ejercicio sintético. No es una estimación de un caso real.",
        },
    }


@app.get("/api/buyer-pack")
def buyer_pack():
    return {
        "buyer": "Walmart / H-E-B / receptor en Nogales (demo)",
        "items": [
            "PTI case label (GTIN-14 + lote + fecha + VPC)",
            "SSCC de tarima",
            "Paquete de embarque: PDF + CSV + EPCIS 2.0",
            "Hoja FDA ordenable",
            "Plan de trazabilidad §1.1315",
            "Reporte de simulacro de retiro",
        ],
    }


@app.get("/api/presentation")
def presentation():
    return {
        "steps": [
            {"id": "ready", "route": "/", "title_es": "Cuenta regresiva a 2028", "title_en": "Countdown to 2028"},
            {"id": "pack", "route": "/empaque", "title_es": "Estación de empaque", "title_en": "Packing station"},
            {"id": "gate", "route": "/anden", "title_es": "El camión no sale", "title_en": "The truck does not leave"},
            {"id": "trace", "route": "/traza", "title_es": "¿A dónde fue el lote?", "title_en": "Where did the lot go?"},
            {"id": "fda", "route": "/fda", "title_es": "La hoja de las 24 horas", "title_en": "The 24-hour spreadsheet"},
            {"id": "recall", "route": "/retiro", "title_es": "Simulacro de un clic", "title_en": "One-click mock recall"},
        ]
    }


@app.get("/health")
def health():
    return {"ok": True}
