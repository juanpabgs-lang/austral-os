"""Synthetic Sinaloa packer. Fictional ranches, lots and Nogales receivers."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from codes import gtin14
from kdes import validate_record

NOW = "2026-10-20T14:30:00-07:00"
WATERMARK = "Datos sintéticos · Synthetic data · not a real packer"
COMPLIANCE = "2028-07-20"

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS sites (
    id TEXT PRIMARY KEY, name TEXT, kind TEXT, gln TEXT, address TEXT, lat REAL, lon REAL
);
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY, name_es TEXT, name_en TEXT, ftl INTEGER, ftl_category TEXT, gtin14 TEXT
);
CREATE TABLE IF NOT EXISTS lots (
    id TEXT PRIMARY KEY, product_id TEXT, tlc TEXT, tlc_source TEXT, ranch TEXT, field TEXT,
    harvest_date TEXT, cool_date TEXT, pack_date TEXT, qty_cases INTEGER, ftl INTEGER,
    planted_gap TEXT
);
CREATE TABLE IF NOT EXISTS records (
    id TEXT PRIMARY KEY, lot_id TEXT, cte TEXT, data TEXT, complete INTEGER
);
CREATE TABLE IF NOT EXISTS shipments (
    id TEXT PRIMARY KEY, lot_id TEXT, to_party TEXT, to_city TEXT, qty INTEGER,
    ship_datetime TEXT, released INTEGER, gaps TEXT
);
CREATE TABLE IF NOT EXISTS planted (
    id TEXT PRIMARY KEY, title TEXT, lot_id TEXT, cte TEXT, key TEXT, notes TEXT
);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    db = sqlite3.connect(str(path), check_same_thread=False)
    db.row_factory = sqlite3.Row
    return db


def seed(path: str | Path, reset: bool = True) -> None:
    path = Path(path)
    if reset and path.exists():
        try:
            path.unlink()
        except OSError:
            pass
        for suffix in ("-wal", "-shm"):
            extra = Path(str(path) + suffix)
            if extra.exists():
                extra.unlink()
    db = connect(path)
    db.executescript(SCHEMA)

    db.executemany(
        "INSERT INTO meta VALUES (?,?)",
        [
            ("watermark", WATERMARK),
            ("now", NOW),
            ("compliance", COMPLIANCE),
            ("packer", "Empaque Río Mocorito (demo)"),
            ("product", "Norfront Fresh · FSMA 204"),
        ],
    )

    # Fictional packer + two ranches + two Nogales receivers
    sites = [
        ("PACK-RIM", "Empaque Río Mocorito", "packer", "7501234500001", "Guasave, Sinaloa, MX", 25.56, -108.47),
        ("RANCH-A", "Rancho Azul", "farm", "7501234500018", "Campo 12, Guasave, Sinaloa", 25.61, -108.52),
        ("RANCH-B", "Rancho La Palma", "farm", "7501234500025", "Campo 4, Angostura, Sinaloa", 25.37, -108.16),
        ("RCV-NOG1", "Desierto Produce LLC (demo)", "receiver", "0061414100012", "Nogales, AZ, US", 31.34, -110.93),
        ("RCV-NOG2", "Paso del Norte Fresh (demo)", "receiver", "0061414100029", "Nogales, AZ, US", 31.33, -110.94),
    ]
    # Fix GLNs with real check digits
    from codes import gln13

    sites[0] = ("PACK-RIM", sites[0][1], sites[0][2], gln13("750123450000"), sites[0][4], sites[0][5], sites[0][6])
    sites[1] = ("RANCH-A", sites[1][1], sites[1][2], gln13("750123450001"), sites[1][4], sites[1][5], sites[1][6])
    sites[2] = ("RANCH-B", sites[2][1], sites[2][2], gln13("750123450002"), sites[2][4], sites[2][5], sites[2][6])
    db.executemany("INSERT INTO sites VALUES (?,?,?,?,?,?,?)", sites)

    products = [
        ("PR-TOM", "Jitomate Roma", "Roma tomato", 1, "tomatoes", gtin14("1750123450001")),
        ("PR-PEP", "Pimiento bell", "Bell pepper", 1, "peppers", gtin14("1750123450002")),
        ("PR-CUC", "Pepino europeo", "European cucumber", 1, "cucumbers", gtin14("1750123450003")),
        ("PR-ROM", "Lechuga romana", "Romaine lettuce", 1, "leafy greens", gtin14("1750123450004")),
        ("PR-SQU", "Calabaza", "Italian squash", 0, "not on FTL", gtin14("1750123450005")),
        ("PR-GRP", "Uva de mesa", "Table grape", 0, "not on FTL", gtin14("1750123450006")),
    ]
    db.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products)

    def rec(lot_id: str, cte: str, data: dict, ftl: bool = True) -> None:
        gaps = validate_record(cte, data, ftl=ftl)
        db.execute(
            "INSERT INTO records VALUES (?,?,?,?,?)",
            (f"{lot_id}-{cte}", lot_id, cte, json.dumps(data, ensure_ascii=False), 0 if gaps else 1),
        )

    # LOT-TOM-OK — complete Roma tomato
    db.execute(
        "INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "LOT-TOM-OK",
            "PR-TOM",
            "TOM-RIM-20261018-A",
            "Empaque Río Mocorito · GLN " + sites[0][3],
            "Rancho Azul",
            "Lote 12-Norte",
            "2026-10-18",
            "2026-10-18",
            "2026-10-18",
            800,
            1,
            None,
        ),
    )
    rec(
        "LOT-TOM-OK",
        "harvesting",
        {
            "farm_location": "Rancho Azul, Campo 12, Guasave, Sinaloa",
            "field_name": "Lote 12-Norte",
            "commodity": "Roma tomato",
            "quantity": "12,000 kg",
            "harvest_date": "2026-10-18",
            "ref_doc": "Boleta cosecha BC-4412",
        },
    )
    rec(
        "LOT-TOM-OK",
        "cooling",
        {
            "cool_location": "Hidrocooler Empaque Río Mocorito",
            "commodity": "Roma tomato",
            "quantity": "12,000 kg",
            "cool_date": "2026-10-18",
            "farm_location": "Rancho Azul, Campo 12, Guasave, Sinaloa",
        },
    )
    rec(
        "LOT-TOM-OK",
        "initial_packing",
        {
            "commodity": "Roma tomato 25 lb",
            "quantity": "800 cases",
            "pack_location": "Empaque Río Mocorito, Guasave, Sinaloa",
            "pack_date": "2026-10-18",
            "tlc": "TOM-RIM-20261018-A",
            "tlc_source": "Empaque Río Mocorito",
            "ref_doc": "Orden de empaque OP-881",
            "farm_location": "Rancho Azul, Campo 12",
            "harvest_date": "2026-10-18",
        },
    )
    rec(
        "LOT-TOM-OK",
        "shipping",
        {
            "tlc": "TOM-RIM-20261018-A",
            "quantity": "800 cases",
            "to_location": "Desierto Produce LLC, Nogales AZ",
            "from_location": "Empaque Río Mocorito, Guasave",
            "ship_datetime": "2026-10-19T16:40:00-07:00",
            "tlc_source": "Empaque Río Mocorito",
            "ref_doc": "BOL-991 / PO DP-2201",
        },
    )
    db.execute(
        "INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?)",
        ("SH-TOM-1", "LOT-TOM-OK", "Desierto Produce LLC (demo)", "Nogales, AZ", 800, "2026-10-19T16:40:00-07:00", 1, "[]"),
    )

    # LOT-TOM-GAP — missing harvest field name (planted)
    db.execute(
        "INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("LOT-TOM-GAP", "PR-TOM", "TOM-RIM-20261019-B", "Empaque Río Mocorito", "Rancho Azul", None, "2026-10-19", "2026-10-19", "2026-10-19", 400, 1, "field_name"),
    )
    rec(
        "LOT-TOM-GAP",
        "harvesting",
        {
            "farm_location": "Rancho Azul, Guasave, Sinaloa",
            "field_name": "",
            "commodity": "Roma tomato",
            "quantity": "6,000 kg",
            "harvest_date": "2026-10-19",
            "ref_doc": "BC-4418",
        },
    )
    rec(
        "LOT-TOM-GAP",
        "cooling",
        {
            "cool_location": "Hidrocooler Empaque Río Mocorito",
            "commodity": "Roma tomato",
            "quantity": "6,000 kg",
            "cool_date": "2026-10-19",
            "farm_location": "Rancho Azul, Guasave, Sinaloa",
        },
    )
    rec(
        "LOT-TOM-GAP",
        "initial_packing",
        {
            "commodity": "Roma tomato 25 lb",
            "quantity": "400 cases",
            "pack_location": "Empaque Río Mocorito",
            "pack_date": "2026-10-19",
            "tlc": "TOM-RIM-20261019-B",
            "tlc_source": "Empaque Río Mocorito",
            "ref_doc": "OP-890",
            "farm_location": "Rancho Azul",
            "harvest_date": "2026-10-19",
        },
    )
    rec(
        "LOT-TOM-GAP",
        "shipping",
        {
            "tlc": "TOM-RIM-20261019-B",
            "quantity": "400 cases",
            "to_location": "Paso del Norte Fresh, Nogales AZ",
            "from_location": "Empaque Río Mocorito",
            "ship_datetime": "2026-10-20T11:00:00-07:00",
            "tlc_source": "Empaque Río Mocorito",
            "ref_doc": "BOL-1004",
        },
    )
    ship_gaps = validate_record(
        "harvesting",
        {
            "farm_location": "Rancho Azul, Guasave, Sinaloa",
            "field_name": "",
            "commodity": "Roma tomato",
            "quantity": "6,000 kg",
            "harvest_date": "2026-10-19",
            "ref_doc": "BC-4418",
        },
    )
    db.execute(
        "INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?)",
        ("SH-TOM-GAP", "LOT-TOM-GAP", "Paso del Norte Fresh (demo)", "Nogales, AZ", 400, "2026-10-20T11:00:00-07:00", 0, json.dumps(ship_gaps)),
    )

    # LOT-CUC-GAP — missing cooling date
    db.execute(
        "INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("LOT-CUC-GAP", "PR-CUC", "CUC-RIM-20261017-C", "Empaque Río Mocorito", "Rancho La Palma", "Cuadro 4", "2026-10-17", None, "2026-10-17", 360, 1, "cool_date"),
    )
    rec(
        "LOT-CUC-GAP",
        "harvesting",
        {
            "farm_location": "Rancho La Palma, Angostura, Sinaloa",
            "field_name": "Cuadro 4",
            "commodity": "European cucumber",
            "quantity": "5,400 kg",
            "harvest_date": "2026-10-17",
            "ref_doc": "BC-3301",
        },
    )
    rec(
        "LOT-CUC-GAP",
        "cooling",
        {
            "cool_location": "Cuarto frío 2",
            "commodity": "European cucumber",
            "quantity": "5,400 kg",
            "cool_date": "",
            "farm_location": "Rancho La Palma, Angostura, Sinaloa",
        },
    )
    rec(
        "LOT-CUC-GAP",
        "initial_packing",
        {
            "commodity": "European cucumber",
            "quantity": "360 cases",
            "pack_location": "Empaque Río Mocorito",
            "pack_date": "2026-10-17",
            "tlc": "CUC-RIM-20261017-C",
            "tlc_source": "Empaque Río Mocorito",
            "ref_doc": "OP-870",
            "farm_location": "Rancho La Palma",
            "harvest_date": "2026-10-17",
        },
    )
    rec(
        "LOT-CUC-GAP",
        "shipping",
        {
            "tlc": "CUC-RIM-20261017-C",
            "quantity": "360 cases",
            "to_location": "Desierto Produce LLC, Nogales AZ",
            "from_location": "Empaque Río Mocorito",
            "ship_datetime": "2026-10-18T15:00:00-07:00",
            "tlc_source": "Empaque Río Mocorito",
            "ref_doc": "BOL-980",
        },
    )
    db.execute(
        "INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?)",
        (
            "SH-CUC-GAP",
            "LOT-CUC-GAP",
            "Desierto Produce LLC (demo)",
            "Nogales, AZ",
            360,
            "2026-10-18T15:00:00-07:00",
            0,
            json.dumps(validate_record("cooling", {"cool_location": "Cuarto frío 2", "commodity": "European cucumber", "quantity": "5,400 kg", "cool_date": "", "farm_location": "Rancho La Palma"})),
        ),
    )

    # LOT-ROM-OK romaine + a fresh-cut transformation
    db.execute(
        "INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("LOT-ROM-OK", "PR-ROM", "ROM-RIM-20261016-D", "Empaque Río Mocorito", "Rancho La Palma", "Cuadro 1", "2026-10-16", "2026-10-16", "2026-10-16", 200, 1, None),
    )
    rec(
        "LOT-ROM-OK",
        "harvesting",
        {
            "farm_location": "Rancho La Palma, Angostura, Sinaloa",
            "field_name": "Cuadro 1",
            "commodity": "Romaine lettuce",
            "quantity": "3,000 kg",
            "harvest_date": "2026-10-16",
            "ref_doc": "BC-2210",
        },
    )
    rec(
        "LOT-ROM-OK",
        "cooling",
        {
            "cool_location": "Vacuum cooler 1",
            "commodity": "Romaine lettuce",
            "quantity": "3,000 kg",
            "cool_date": "2026-10-16",
            "farm_location": "Rancho La Palma",
        },
    )
    rec(
        "LOT-ROM-OK",
        "initial_packing",
        {
            "commodity": "Romaine 24ct",
            "quantity": "200 cases",
            "pack_location": "Empaque Río Mocorito",
            "pack_date": "2026-10-16",
            "tlc": "ROM-RIM-20261016-D",
            "tlc_source": "Empaque Río Mocorito",
            "ref_doc": "OP-860",
            "farm_location": "Rancho La Palma",
            "harvest_date": "2026-10-16",
        },
    )
    rec(
        "LOT-ROM-OK",
        "transformation",
        {
            "new_tlc": "CUT-ROM-20261016-X",
            "new_quantity": "1,200 clamshells",
            "new_product": "Romaine hearts 3-pack",
            "transform_location": "Sala de corte Empaque Río Mocorito",
            "transform_date": "2026-10-16",
            "tlc_source": "Empaque Río Mocorito",
            "input_tlc": "ROM-RIM-20261016-D",
            "input_quantity": "80 cases Romaine 24ct",
        },
    )
    rec(
        "LOT-ROM-OK",
        "shipping",
        {
            "tlc": "ROM-RIM-20261016-D",
            "quantity": "120 cases",
            "to_location": "Desierto Produce LLC, Nogales AZ",
            "from_location": "Empaque Río Mocorito",
            "ship_datetime": "2026-10-17T04:30:00-07:00",
            "tlc_source": "Empaque Río Mocorito",
            "ref_doc": "BOL-970",
        },
    )
    db.execute(
        "INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?)",
        ("SH-ROM-1", "LOT-ROM-OK", "Desierto Produce LLC (demo)", "Nogales, AZ", 120, "2026-10-17T04:30:00-07:00", 1, "[]"),
    )

    # LOT-PEP-GAP missing TLC source on packing
    db.execute(
        "INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("LOT-PEP-GAP", "PR-PEP", "PEP-RIM-20261015-E", "", "Rancho Azul", "Lote 8", "2026-10-15", "2026-10-15", "2026-10-15", 240, 1, "tlc_source"),
    )
    rec(
        "LOT-PEP-GAP",
        "harvesting",
        {
            "farm_location": "Rancho Azul, Campo 8",
            "field_name": "Lote 8",
            "commodity": "Bell pepper",
            "quantity": "4,000 kg",
            "harvest_date": "2026-10-15",
            "ref_doc": "BC-1988",
        },
    )
    rec(
        "LOT-PEP-GAP",
        "cooling",
        {
            "cool_location": "Cuarto frío 1",
            "commodity": "Bell pepper",
            "quantity": "4,000 kg",
            "cool_date": "2026-10-15",
            "farm_location": "Rancho Azul",
        },
    )
    rec(
        "LOT-PEP-GAP",
        "initial_packing",
        {
            "commodity": "Bell pepper extra large",
            "quantity": "240 cases",
            "pack_location": "Empaque Río Mocorito",
            "pack_date": "2026-10-15",
            "tlc": "PEP-RIM-20261015-E",
            "tlc_source": "",
            "ref_doc": "OP-850",
            "farm_location": "Rancho Azul",
            "harvest_date": "2026-10-15",
        },
    )
    rec(
        "LOT-PEP-GAP",
        "shipping",
        {
            "tlc": "PEP-RIM-20261015-E",
            "quantity": "240 cases",
            "to_location": "Paso del Norte Fresh",
            "from_location": "Empaque Río Mocorito",
            "ship_datetime": "2026-10-16T14:00:00-07:00",
            "tlc_source": "",
            "ref_doc": "BOL-960",
        },
    )
    db.execute(
        "INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?)",
        (
            "SH-PEP-GAP",
            "LOT-PEP-GAP",
            "Paso del Norte Fresh (demo)",
            "Nogales, AZ",
            240,
            "2026-10-16T14:00:00-07:00",
            0,
            json.dumps(validate_record("initial_packing", {"commodity": "Bell pepper extra large", "quantity": "240 cases", "pack_location": "Empaque Río Mocorito", "pack_date": "2026-10-15", "tlc": "PEP-RIM-20261015-E", "tlc_source": "", "ref_doc": "OP-850", "farm_location": "Rancho Azul", "harvest_date": "2026-10-15"})),
        ),
    )

    # Non-FTL grape — complete enough, must NOT block the gate
    db.execute(
        "INSERT INTO lots VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        ("LOT-GRP-OK", "PR-GRP", "GRP-RIM-20261012-G", "Empaque Río Mocorito", "Rancho Azul", "Parral 2", "2026-10-12", "2026-10-12", "2026-10-12", 180, 0, None),
    )
    rec(
        "LOT-GRP-OK",
        "initial_packing",
        {"commodity": "Table grape", "quantity": "180 cases", "pack_location": "Empaque Río Mocorito", "pack_date": "2026-10-12", "tlc": "GRP-RIM-20261012-G", "tlc_source": "Empaque Río Mocorito", "ref_doc": "OP-800", "farm_location": "Rancho Azul", "harvest_date": "2026-10-12"},
        ftl=False,
    )
    rec(
        "LOT-GRP-OK",
        "shipping",
        {"tlc": "GRP-RIM-20261012-G", "quantity": "180 cases", "to_location": "Desierto Produce LLC", "from_location": "Empaque Río Mocorito", "ship_datetime": "2026-10-13T10:00:00-07:00", "tlc_source": "Empaque Río Mocorito", "ref_doc": "BOL-900"},
        ftl=False,
    )
    db.execute(
        "INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?)",
        ("SH-GRP-1", "LOT-GRP-OK", "Desierto Produce LLC (demo)", "Nogales, AZ", 180, "2026-10-13T10:00:00-07:00", 1, "[]"),
    )

    planted = [
        ("P1", "Cosecha sin nombre de predio", "LOT-TOM-GAP", "harvesting", "field_name", "El jitomate no puede salir hasta que el mayordomo nombre el predio."),
        ("P2", "Enfriado sin fecha", "LOT-CUC-GAP", "cooling", "cool_date", "El pepino se enfrió; nadie escribió el día."),
        ("P3", "Empaque sin TLC source", "LOT-PEP-GAP", "initial_packing", "tlc_source", "Hay lote, no hay quién lo asignó."),
        ("P4", "Uva fuera de la FTL no bloquea", "LOT-GRP-OK", "shipping", "", "La uva de mesa no está en la FTL. El gate no la detiene por Subpart S."),
    ]
    db.executemany("INSERT INTO planted VALUES (?,?,?,?,?,?)", planted)
    db.commit()
    db.close()


if __name__ == "__main__":
    seed(Path(__file__).parent / "fsma.db")
    print("seeded", WATERMARK)
