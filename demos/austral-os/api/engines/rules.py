"""Warehouse rules checked on every mutating event."""

from __future__ import annotations

import json
from typing import Any

from db import fetchone


class RuleViolation(Exception):
    def __init__(self, code: str, message: str, http: int = 409):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http = http


def check_event(db, event_type: str, payload: dict[str, Any], pallet: dict[str, Any] | None) -> None:
    if event_type in ("pick", "load") and pallet:
        if pallet.get("hold_status") and pallet["hold_status"] != "libre":
            raise RuleViolation(
                "HOLD_BLOCKS_PICK",
                f"Pallet {pallet.get('sscc')} está en retención ({pallet.get('hold_reason')}). No se surte.",
            )
    if event_type == "dump":
        rule = fetchone(db, "SELECT * FROM rules WHERE code = 'DUMP_NEEDS_PHOTO'")
        if rule and rule["active"]:
            if not payload.get("photo_id"):
                raise RuleViolation("DUMP_NEEDS_PHOTO", "La merma requiere foto adjunta.")
            if not payload.get("supervisor_id"):
                raise RuleViolation("DUMP_NEEDS_PHOTO", "La merma requiere aprobación de supervisor.")


def apply_event_side_effects(db, event_type: str, body: dict[str, Any], ts: str) -> None:
    pallet_id = body.get("pallet_id")
    qty = body.get("qty_boxes")
    if event_type == "putaway" and pallet_id:
        db.execute(
            "UPDATE pallets SET zone_id=?, position_id=?, last_moved_at=? WHERE id=?",
            (body.get("zone_id"), body.get("position_id"), ts, pallet_id),
        )
    elif event_type == "move" and pallet_id:
        db.execute(
            "UPDATE pallets SET zone_id=?, position_id=?, last_moved_at=? WHERE id=?",
            (body.get("zone_id"), body.get("position_id"), ts, pallet_id),
        )
    elif event_type == "count" and pallet_id and qty is not None:
        db.execute(
            "UPDATE pallets SET qty_boxes=?, last_count_at=? WHERE id=?",
            (qty, ts, pallet_id),
        )
    elif event_type == "hold" and pallet_id:
        db.execute(
            "UPDATE pallets SET hold_status='retenido', hold_reason=? WHERE id=?",
            (body.get("reason") or body.get("hold_reason"), pallet_id),
        )
    elif event_type == "release" and pallet_id:
        db.execute(
            "UPDATE pallets SET hold_status='libre', hold_reason=NULL WHERE id=?",
            (pallet_id,),
        )
    elif event_type == "pick" and pallet_id and qty:
        db.execute(
            "UPDATE pallets SET qty_boxes = qty_boxes - ? WHERE id=?",
            (qty, pallet_id),
        )
    elif event_type == "dump" and pallet_id and qty:
        db.execute(
            "UPDATE pallets SET qty_boxes = qty_boxes - ? WHERE id=?",
            (qty, pallet_id),
        )
    elif event_type == "repack" and pallet_id:
        payload = body.get("payload") or {}
        if isinstance(payload, str):
            payload = json.loads(payload)
        qout = payload.get("qty_out") or qty
        if qout is not None:
            db.execute("UPDATE pallets SET qty_boxes=? WHERE id=?", (qout, pallet_id))
