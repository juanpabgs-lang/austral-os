"""Required KDEs per produce-relevant CTE. Citations are 21 CFR Part 1 Subpart S.

Wording is condensed for software. The eCFR is authoritative.
"""

from __future__ import annotations

from typing import Any

# who_keeps: the firm that performs the CTE
# send_on: must provide these to the next covered entity (packer / receiver)

KDE_TABLE: list[dict[str, Any]] = [
    # Harvesting — 21 CFR 1.1325(a)
    {"cte": "harvesting", "key": "farm_location", "cite": "§1.1325(a)", "who_keeps": "harvester", "send_on": True, "label": "Location description of the farm"},
    {"cte": "harvesting", "key": "field_name", "cite": "§1.1325(a)", "who_keeps": "harvester", "send_on": True, "label": "Name of the field or growing area"},
    {"cte": "harvesting", "key": "commodity", "cite": "§1.1325(a)", "who_keeps": "harvester", "send_on": True, "label": "Commodity"},
    {"cte": "harvesting", "key": "quantity", "cite": "§1.1325(a)", "who_keeps": "harvester", "send_on": True, "label": "Quantity and unit of measure"},
    {"cte": "harvesting", "key": "harvest_date", "cite": "§1.1325(a)", "who_keeps": "harvester", "send_on": True, "label": "Date of harvesting"},
    {"cte": "harvesting", "key": "ref_doc", "cite": "§1.1325(a)", "who_keeps": "harvester", "send_on": True, "label": "Reference document type and number (if used)"},
    # Cooling — 21 CFR 1.1325(b)
    {"cte": "cooling", "key": "cool_location", "cite": "§1.1325(b)", "who_keeps": "cooler", "send_on": True, "label": "Location description where cooling occurred"},
    {"cte": "cooling", "key": "commodity", "cite": "§1.1325(b)", "who_keeps": "cooler", "send_on": True, "label": "Commodity"},
    {"cte": "cooling", "key": "quantity", "cite": "§1.1325(b)", "who_keeps": "cooler", "send_on": True, "label": "Quantity and unit of measure"},
    {"cte": "cooling", "key": "cool_date", "cite": "§1.1325(b)", "who_keeps": "cooler", "send_on": True, "label": "Date of cooling"},
    {"cte": "cooling", "key": "farm_location", "cite": "§1.1325(b)", "who_keeps": "cooler", "send_on": True, "label": "Location description of the farm where harvested"},
    # Initial packing — 21 CFR 1.1330
    {"cte": "initial_packing", "key": "commodity", "cite": "§1.1330", "who_keeps": "initial_packer", "send_on": True, "label": "Commodity / product description"},
    {"cte": "initial_packing", "key": "quantity", "cite": "§1.1330", "who_keeps": "initial_packer", "send_on": True, "label": "Quantity and unit of measure"},
    {"cte": "initial_packing", "key": "pack_location", "cite": "§1.1330", "who_keeps": "initial_packer", "send_on": True, "label": "Location description where the food was packed"},
    {"cte": "initial_packing", "key": "pack_date", "cite": "§1.1330", "who_keeps": "initial_packer", "send_on": True, "label": "Date of initial packing"},
    {"cte": "initial_packing", "key": "tlc", "cite": "§1.1330 / §1.1320", "who_keeps": "initial_packer", "send_on": True, "label": "Traceability lot code (assigned here)"},
    {"cte": "initial_packing", "key": "tlc_source", "cite": "§1.1330", "who_keeps": "initial_packer", "send_on": True, "label": "Traceability lot code source (or source reference)"},
    {"cte": "initial_packing", "key": "ref_doc", "cite": "§1.1330", "who_keeps": "initial_packer", "send_on": True, "label": "Reference document type and number"},
    {"cte": "initial_packing", "key": "farm_location", "cite": "§1.1330", "who_keeps": "initial_packer", "send_on": False, "label": "Location description of the farm (produce)"},
    {"cte": "initial_packing", "key": "harvest_date", "cite": "§1.1330", "who_keeps": "initial_packer", "send_on": False, "label": "Date of harvesting (if received from harvester)"},
    # Shipping — 21 CFR 1.1340
    {"cte": "shipping", "key": "tlc", "cite": "§1.1340", "who_keeps": "shipper", "send_on": True, "label": "Traceability lot code"},
    {"cte": "shipping", "key": "quantity", "cite": "§1.1340", "who_keeps": "shipper", "send_on": True, "label": "Quantity and unit of measure"},
    {"cte": "shipping", "key": "to_location", "cite": "§1.1340", "who_keeps": "shipper", "send_on": True, "label": "Location description of the immediate subsequent recipient"},
    {"cte": "shipping", "key": "from_location", "cite": "§1.1340", "who_keeps": "shipper", "send_on": True, "label": "Location description from which the food was shipped"},
    {"cte": "shipping", "key": "ship_datetime", "cite": "§1.1340", "who_keeps": "shipper", "send_on": True, "label": "Date and time the food was shipped"},
    {"cte": "shipping", "key": "tlc_source", "cite": "§1.1340", "who_keeps": "shipper", "send_on": True, "label": "Location description of the TLC source (or source reference)"},
    {"cte": "shipping", "key": "ref_doc", "cite": "§1.1340", "who_keeps": "shipper", "send_on": True, "label": "Reference document type and number"},
    # Receiving — 21 CFR 1.1345
    {"cte": "receiving", "key": "tlc", "cite": "§1.1345", "who_keeps": "receiver", "send_on": False, "label": "Traceability lot code"},
    {"cte": "receiving", "key": "quantity", "cite": "§1.1345", "who_keeps": "receiver", "send_on": False, "label": "Quantity and unit of measure"},
    {"cte": "receiving", "key": "from_location", "cite": "§1.1345", "who_keeps": "receiver", "send_on": False, "label": "Location description from which the food was received"},
    {"cte": "receiving", "key": "to_location", "cite": "§1.1345", "who_keeps": "receiver", "send_on": False, "label": "Location description where the food was received"},
    {"cte": "receiving", "key": "receive_datetime", "cite": "§1.1345", "who_keeps": "receiver", "send_on": False, "label": "Date and time the food was received"},
    {"cte": "receiving", "key": "tlc_source", "cite": "§1.1345", "who_keeps": "receiver", "send_on": False, "label": "Location description of the TLC source (or source reference)"},
    {"cte": "receiving", "key": "ref_doc", "cite": "§1.1345", "who_keeps": "receiver", "send_on": False, "label": "Reference document type and number"},
    # Transformation — 21 CFR 1.1350 (fresh-cut)
    {"cte": "transformation", "key": "new_tlc", "cite": "§1.1350", "who_keeps": "transformer", "send_on": True, "label": "New traceability lot code"},
    {"cte": "transformation", "key": "new_quantity", "cite": "§1.1350", "who_keeps": "transformer", "send_on": True, "label": "Quantity and UoM of food produced"},
    {"cte": "transformation", "key": "new_product", "cite": "§1.1350", "who_keeps": "transformer", "send_on": True, "label": "Product description of food produced"},
    {"cte": "transformation", "key": "transform_location", "cite": "§1.1350", "who_keeps": "transformer", "send_on": True, "label": "Location description where transformation occurred"},
    {"cte": "transformation", "key": "transform_date", "cite": "§1.1350", "who_keeps": "transformer", "send_on": True, "label": "Date the transformation was completed"},
    {"cte": "transformation", "key": "tlc_source", "cite": "§1.1350", "who_keeps": "transformer", "send_on": True, "label": "TLC source of the new lot (or source reference)"},
    {"cte": "transformation", "key": "input_tlc", "cite": "§1.1350", "who_keeps": "transformer", "send_on": False, "label": "TLC of food used"},
    {"cte": "transformation", "key": "input_quantity", "cite": "§1.1350", "who_keeps": "transformer", "send_on": False, "label": "Quantity and product description of food used"},
]


def required_keys(cte: str) -> list[str]:
    return [r["key"] for r in KDE_TABLE if r["cte"] == cte]


def validate_record(cte: str, data: dict[str, Any], ftl: bool = True) -> list[dict[str, str]]:
    """Return missing KDEs. Non-FTL foods are not required to keep Subpart S records."""
    if not ftl:
        return []
    gaps = []
    for row in KDE_TABLE:
        if row["cte"] != cte:
            continue
        val = data.get(row["key"])
        if val is None or val == "" or val == []:
            gaps.append(
                {
                    "cte": cte,
                    "key": row["key"],
                    "cite": row["cite"],
                    "label": row["label"],
                    "send_on": row["send_on"],
                }
            )
    return gaps
