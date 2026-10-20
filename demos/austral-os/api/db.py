"""SQLite schema and helpers. Inventory is a projection of the event ledger."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from config import DB_PATH

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sites (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    city TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS zones (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL REFERENCES sites(id),
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    temp_setpoint_c REAL,
    temp_current_c REAL,
    rh INTEGER,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    w INTEGER NOT NULL,
    h INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    zone_id TEXT NOT NULL REFERENCES zones(id),
    code TEXT NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS parties (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    name TEXT NOT NULL,
    city TEXT,
    country TEXT,
    min_shelf_days INTEGER
);

CREATE TABLE IF NOT EXISTS staff (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    shift TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS skus (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    variety TEXT NOT NULL,
    origin_country TEXT NOT NULL,
    category TEXT NOT NULL,
    temp_min_c REAL NOT NULL,
    temp_max_c REAL NOT NULL,
    rh_min INTEGER,
    rh_max INTEGER,
    life_days INTEGER NOT NULL,
    freezing_point_c REAL,
    chilling_sensitive INTEGER NOT NULL DEFAULT 0,
    chilling_threshold_c REAL,
    ethylene_prod TEXT NOT NULL,
    ethylene_sens TEXT NOT NULL,
    box_value_mxn INTEGER NOT NULL,
    boxes_per_pallet INTEGER NOT NULL DEFAULT 80
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL REFERENCES parties(id),
    sku_id TEXT NOT NULL REFERENCES skus(id),
    qty_boxes INTEGER NOT NULL,
    expected_date TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lots (
    id TEXT PRIMARY KEY,
    sku_id TEXT NOT NULL REFERENCES skus(id),
    lot_code TEXT NOT NULL,
    origin TEXT NOT NULL,
    harvest_date TEXT,
    pack_date TEXT,
    po_id TEXT REFERENCES purchase_orders(id),
    supplier_id TEXT REFERENCES parties(id),
    tlc_source TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS pallets (
    id TEXT PRIMARY KEY,
    sscc TEXT NOT NULL UNIQUE,
    lot_id TEXT NOT NULL REFERENCES lots(id),
    qty_boxes INTEGER NOT NULL,
    position_id TEXT REFERENCES positions(id),
    zone_id TEXT REFERENCES zones(id),
    site_id TEXT REFERENCES sites(id),
    hold_status TEXT NOT NULL DEFAULT 'libre',
    hold_reason TEXT,
    received_at TEXT NOT NULL,
    last_count_at TEXT,
    last_moved_at TEXT
);

CREATE TABLE IF NOT EXISTS sales_orders (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES parties(id),
    sku_id TEXT NOT NULL REFERENCES skus(id),
    qty_boxes INTEGER NOT NULL,
    due_date TEXT NOT NULL,
    min_shelf_days INTEGER NOT NULL,
    status TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_uuid TEXT NOT NULL UNIQUE,
    ts TEXT NOT NULL,
    device_ts TEXT,
    actor_id TEXT,
    role TEXT,
    shift TEXT,
    event_type TEXT NOT NULL,
    site_id TEXT,
    zone_id TEXT,
    pallet_id TEXT,
    lot_id TEXT,
    sku_id TEXT,
    qty_boxes INTEGER,
    payload TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_lot ON events(lot_id);
CREATE INDEX IF NOT EXISTS idx_events_pallet ON events(pallet_id);

CREATE TABLE IF NOT EXISTS temp_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id TEXT NOT NULL REFERENCES zones(id),
    ts TEXT NOT NULL,
    temp_c REAL NOT NULL,
    source TEXT NOT NULL DEFAULT 'sensor'
);

CREATE TABLE IF NOT EXISTS rules (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    requires_photo INTEGER NOT NULL DEFAULT 0,
    requires_supervisor INTEGER NOT NULL DEFAULT 0,
    approved_by TEXT,
    approved_at TEXT,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rule_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT NOT NULL REFERENCES rules(id),
    ts TEXT NOT NULL,
    actor_id TEXT,
    action TEXT NOT NULL,
    before_json TEXT,
    after_json TEXT,
    approved_by TEXT
);

CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    actor_id TEXT,
    role TEXT,
    action TEXT NOT NULL,
    entity TEXT,
    entity_id TEXT,
    detail TEXT
);

CREATE TABLE IF NOT EXISTS allocations (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES sales_orders(id),
    pallet_id TEXT NOT NULL REFERENCES pallets(id),
    qty_boxes INTEGER NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    related_id TEXT,
    body TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS planted_cases (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    lot_id TEXT,
    pallet_id TEXT,
    expected_segment TEXT,
    expected_shift TEXT,
    expected_qty INTEGER,
    notes TEXT NOT NULL
);
"""


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    db = sqlite3.connect(str(path or DB_PATH), check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


@contextmanager
def tx(db: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


def init_db(db: sqlite3.Connection) -> None:
    db.executescript(SCHEMA)
    db.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {k: row[k] for k in row.keys()}


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [{k: r[k] for k in r.keys()} for r in rows]


def fetchall(db: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    return rows_to_dicts(db.execute(sql, params).fetchall())


def fetchone(db: sqlite3.Connection, sql: str, params: tuple = ()) -> dict[str, Any] | None:
    return row_to_dict(db.execute(sql, params).fetchone())


def audit(
    db: sqlite3.Connection,
    *,
    ts: str,
    actor_id: str | None,
    role: str | None,
    action: str,
    entity: str | None = None,
    entity_id: str | None = None,
    detail: str | None = None,
) -> None:
    db.execute(
        """INSERT INTO audit (ts, actor_id, role, action, entity, entity_id, detail)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (ts, actor_id, role, action, entity, entity_id, detail),
    )


def insert_event(
    db: sqlite3.Connection,
    *,
    client_uuid: str,
    ts: str,
    event_type: str,
    device_ts: str | None = None,
    actor_id: str | None = None,
    role: str | None = None,
    shift: str | None = None,
    site_id: str | None = None,
    zone_id: str | None = None,
    pallet_id: str | None = None,
    lot_id: str | None = None,
    sku_id: str | None = None,
    qty_boxes: int | None = None,
    payload: dict | None = None,
) -> tuple[int, bool]:
    """Insert an event. Returns (id, inserted). Duplicate client_uuid is a no-op."""
    existing = fetchone(db, "SELECT id FROM events WHERE client_uuid = ?", (client_uuid,))
    if existing:
        return existing["id"], False
    cur = db.execute(
        """INSERT INTO events (
            client_uuid, ts, device_ts, actor_id, role, shift, event_type,
            site_id, zone_id, pallet_id, lot_id, sku_id, qty_boxes, payload
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            client_uuid,
            ts,
            device_ts or ts,
            actor_id,
            role,
            shift,
            event_type,
            site_id,
            zone_id,
            pallet_id,
            lot_id,
            sku_id,
            qty_boxes,
            json.dumps(payload or {}, ensure_ascii=False),
        ),
    )
    return int(cur.lastrowid), True
