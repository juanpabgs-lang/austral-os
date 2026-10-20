"""Pick-route order: zone walking order then rack code."""

from __future__ import annotations

from typing import Any

ZONE_ORDER = ["Z-CAM2", "Z-CAM1", "Z-CAM3", "Z-SECO", "Z-ANDEN", "Z-GDL"]


def order_stops(stops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(s: dict[str, Any]) -> tuple:
        z = s.get("zone_id") or ""
        zo = ZONE_ORDER.index(z) if z in ZONE_ORDER else 99
        return (zo, s.get("position_code") or "", s.get("pallet_id") or "")

    return sorted(stops, key=key)
