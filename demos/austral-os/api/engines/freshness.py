"""Remaining shelf life from USDA Handbook 66 setpoints plus Q10 acceleration.

Sources (cited in the research notes, implemented here as a closed table):
- USDA Agriculture Handbook 66 (2016) recommended storage temperatures
  and approximate storage life.
- Q10 ≈ 2.0–3.0 for produce respiration (Kader; typically 2.5 used here).

Formula (inference, labelled as such in the UI):
    remaining_days = life_days - equivalent_days_elapsed
    equivalent_days_elapsed = Σ Δt_days * Q10 ** ((T - T_ref) / 10)
    T_ref = midpoint of the recommended range.
Chilling-injury flag if a chilling-sensitive commodity sits below its threshold.
Ethylene flag if a high-sensitivity SKU shares a zone with a high producer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

Q10 = 2.5


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


def hours_between(a: str, b: str) -> float:
    return (parse_ts(b) - parse_ts(a)).total_seconds() / 3600.0


def q10_factor(temp_c: float, t_ref: float, q10: float = Q10) -> float:
    return q10 ** ((temp_c - t_ref) / 10.0)


def remaining_life(
    *,
    life_days: int,
    received_at: str,
    now: str,
    t_min: float,
    t_max: float,
    exposures: list[dict[str, Any]] | None = None,
    baseline_temp: float | None = None,
) -> dict[str, Any]:
    t_ref = (t_min + t_max) / 2.0
    start = parse_ts(received_at)
    end = parse_ts(now)
    calendar_days = max((end - start).total_seconds() / 86400.0, 0.0)

    equivalent = 0.0
    if exposures:
        ordered = sorted(exposures, key=lambda e: e["ts"])
        for i, sample in enumerate(ordered):
            if i + 1 < len(ordered):
                dt_days = hours_between(sample["ts"], ordered[i + 1]["ts"]) / 24.0
            else:
                dt_days = hours_between(sample["ts"], now) / 24.0
            if dt_days < 0:
                continue
            equivalent += dt_days * q10_factor(float(sample["temp_c"]), t_ref)
    else:
        t = baseline_temp if baseline_temp is not None else t_ref
        equivalent = calendar_days * q10_factor(t, t_ref)

    remaining = max(life_days - equivalent, 0.0)
    pct = 0.0 if life_days <= 0 else remaining / life_days
    if remaining <= 2:
        band = "critico"
    elif remaining <= 5:
        band = "riesgo"
    elif remaining <= 10:
        band = "vigilar"
    else:
        band = "ok"
    return {
        "life_days": life_days,
        "calendar_days": round(calendar_days, 2),
        "equivalent_days": round(equivalent, 2),
        "remaining_days": round(remaining, 2),
        "pct": round(pct, 3),
        "band": band,
        "t_ref_c": t_ref,
        "q10": Q10,
        "formula": "life_days - Σ Δt * Q10**((T-Tref)/10)",
    }


def chilling_flag(sku: dict[str, Any], current_temp: float | None) -> dict[str, Any] | None:
    if not sku.get("chilling_sensitive") or current_temp is None:
        return None
    threshold = sku.get("chilling_threshold_c")
    if threshold is None:
        return None
    if current_temp < float(threshold):
        return {
            "kind": "chilling",
            "temp_c": current_temp,
            "threshold_c": threshold,
            "message": (
                f"{sku.get('name') or sku.get('sku_name') or 'Producto'} es sensible al frío; {current_temp} °C está "
                f"por debajo de {threshold} °C."
            ),
        }
    return None


def ethylene_conflicts(occupants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    producers = [o for o in occupants if o.get("ethylene_prod") in ("high", "very_high")]
    sensitive = [o for o in occupants if o.get("ethylene_sens") in ("high",)]
    out: list[dict[str, Any]] = []
    for s in sensitive:
        for p in producers:
            if s["pallet_id"] == p["pallet_id"]:
                continue
            out.append(
                {
                    "kind": "ethylene",
                    "sensitive_pallet": s["pallet_id"],
                    "sensitive_sku": s["name"],
                    "producer_pallet": p["pallet_id"],
                    "producer_sku": p["name"],
                    "message": (
                        f"{s['name']} (sensible al etileno) comparte zona con "
                        f"{p['name']} (productor {p['ethylene_prod']})."
                    ),
                }
            )
    return out
