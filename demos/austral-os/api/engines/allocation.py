"""Match at-risk lots to open orders by customer min shelf life (FEFO)."""

from __future__ import annotations

from typing import Any

from db import fetchall, fetchone
from engines.freshness import remaining_life


def _exposures(db, zone_id: str | None) -> list[dict[str, Any]]:
    if not zone_id:
        return []
    return fetchall(
        db,
        "SELECT ts, temp_c FROM temp_log WHERE zone_id = ? ORDER BY ts",
        (zone_id,),
    )


def pallet_freshness(db, pallet: dict[str, Any], sku: dict[str, Any], now: str) -> dict[str, Any]:
    zone = fetchone(db, "SELECT * FROM zones WHERE id = ?", (pallet.get("zone_id"),)) if pallet.get("zone_id") else None
    exposures = _exposures(db, pallet.get("zone_id"))
    life = remaining_life(
        life_days=sku["life_days"],
        received_at=pallet["received_at"],
        now=now,
        t_min=sku["temp_min_c"],
        t_max=sku["temp_max_c"],
        exposures=exposures,
        baseline_temp=(zone or {}).get("temp_current_c"),
    )
    return life


def inventory_with_life(db, now: str) -> list[dict[str, Any]]:
    rows = fetchall(
        db,
        """
        SELECT p.*, l.lot_code, l.origin, l.pack_date, l.sku_id,
               s.name AS sku_name, s.variety, s.origin_country, s.temp_min_c, s.temp_max_c,
               s.life_days, s.chilling_sensitive, s.chilling_threshold_c,
               s.ethylene_prod, s.ethylene_sens, s.box_value_mxn,
               z.name AS zone_name, z.temp_current_c, z.kind AS zone_kind,
               pos.code AS position_code
        FROM pallets p
        JOIN lots l ON l.id = p.lot_id
        JOIN skus s ON s.id = l.sku_id
        LEFT JOIN zones z ON z.id = p.zone_id
        LEFT JOIN positions pos ON pos.id = p.position_id
        ORDER BY s.name, p.received_at
        """,
    )
    out = []
    for r in rows:
        life = pallet_freshness(db, r, r, now)
        r = dict(r)
        r["freshness"] = life
        r["available"] = 0 if r["hold_status"] != "libre" else r["qty_boxes"]
        out.append(r)
    return out


def match_orders(db, now: str) -> list[dict[str, Any]]:
    inv = inventory_with_life(db, now)
    orders = fetchall(
        db,
        """SELECT o.*, p.name AS customer, p.city AS customer_city
           FROM sales_orders o JOIN parties p ON p.id = o.customer_id
           WHERE o.status = 'abierta' ORDER BY o.due_date""",
    )
    matches = []
    reserved: dict[str, int] = {}
    for order in orders:
        candidates = [
            p
            for p in inv
            if p["sku_id"] == order["sku_id"] and p["hold_status"] == "libre" and p["qty_boxes"] > reserved.get(p["id"], 0)
        ]
        # FEFO: shortest remaining life first, but must meet min_shelf_days.
        candidates.sort(key=lambda p: p["freshness"]["remaining_days"])
        need = order["qty_boxes"]
        chosen = []
        rejected = []
        for p in candidates:
            rem = p["freshness"]["remaining_days"]
            free = p["qty_boxes"] - reserved.get(p["id"], 0)
            if rem < order["min_shelf_days"]:
                rejected.append(
                    {
                        "pallet_id": p["id"],
                        "sscc": p["sscc"],
                        "remaining_days": rem,
                        "reason": f"vida {rem} d < mínimo del cliente {order['min_shelf_days']} d",
                    }
                )
                continue
            take = min(free, need)
            if take <= 0:
                continue
            reserved[p["id"]] = reserved.get(p["id"], 0) + take
            need -= take
            why = "FEFO · lote más corto que aún cumple el mínimo del cliente"
            if p["freshness"]["band"] in ("critico", "riesgo"):
                why = "lote en riesgo térmico emparejado a pedido de vida corta"
            chosen.append(
                {
                    "pallet_id": p["id"],
                    "sscc": p["sscc"],
                    "lot_code": p["lot_code"],
                    "zone_id": p["zone_id"],
                    "zone_name": p["zone_name"],
                    "position_code": p["position_code"],
                    "qty": take,
                    "remaining_days": rem,
                    "band": p["freshness"]["band"],
                    "reason": why,
                }
            )
            if need <= 0:
                break
        matches.append(
            {
                "order": order,
                "allocated": chosen,
                "short_by": max(need, 0),
                "rejected": rejected,
                "ok": need <= 0,
            }
        )
    return matches


def ship_first(db, now: str) -> list[dict[str, Any]]:
    inv = inventory_with_life(db, now)
    risky = [p for p in inv if p["freshness"]["band"] in ("critico", "riesgo", "vigilar")]
    risky.sort(key=lambda p: p["freshness"]["remaining_days"])
    return risky


def available_to_sell(db, now: str) -> list[dict[str, Any]]:
    inv = inventory_with_life(db, now)
    orders = fetchall(db, "SELECT sku_id, SUM(qty_boxes) AS q FROM sales_orders WHERE status='abierta' GROUP BY sku_id")
    reserved = {o["sku_id"]: o["q"] for o in orders}
    by_sku: dict[str, dict[str, Any]] = {}
    for p in inv:
        key = p["sku_id"]
        bucket = by_sku.setdefault(
            key,
            {
                "sku_id": key,
                "sku_name": p["sku_name"],
                "variety": p["variety"],
                "physical": 0,
                "on_hold": 0,
                "allocated": reserved.get(key, 0),
                "available": 0,
                "oldest_count": None,
                "value_mxn": 0,
                "lots": [],
            },
        )
        bucket["physical"] += p["qty_boxes"]
        bucket["value_mxn"] += p["qty_boxes"] * p["box_value_mxn"]
        if p["hold_status"] != "libre":
            bucket["on_hold"] += p["qty_boxes"]
        if p["last_count_at"]:
            if bucket["oldest_count"] is None or p["last_count_at"] < bucket["oldest_count"]:
                bucket["oldest_count"] = p["last_count_at"]
        bucket["lots"].append(
            {
                "lot_code": p["lot_code"],
                "qty": p["qty_boxes"],
                "hold": p["hold_status"],
                "remaining_days": p["freshness"]["remaining_days"],
                "verified_at": p["last_count_at"],
            }
        )
    for b in by_sku.values():
        b["available"] = max(b["physical"] - b["on_hold"] - b["allocated"], 0)
        b["verified"] = b["oldest_count"]
    return sorted(by_sku.values(), key=lambda x: x["sku_name"])
