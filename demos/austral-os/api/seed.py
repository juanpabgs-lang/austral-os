"""Synthetic seed with a planted answer key.

All names, lots, POs and staff are fictional. The watermark
"Datos sintéticos" is stored in meta and shown on every screen.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from config import NOW_ISO, PRODUCT_NAME, TENANT_NAME, WATERMARK
from db import audit, connect, init_db, insert_event, tx

NOW = NOW_ISO


def uid(prefix: str, *parts: str) -> str:
    raw = "-".join(parts) if parts else prefix
    return f"{prefix}-{raw}"


def ev(kind: str, *parts: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"norfront-fresh/{kind}/{'/'.join(parts)}"))


def seed(path: str | Path | None = None, reset: bool = True) -> None:
    db = connect(path)
    if reset:
        db.executescript(
            """
            PRAGMA foreign_keys = OFF;
            SELECT name FROM sqlite_master WHERE type='table';
            """
        )
        tables = [
            r[0]
            for r in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        for t in tables:
            db.execute(f"DROP TABLE IF EXISTS {t}")
        db.commit()
    init_db(db)

    with tx(db):
        _meta(db)
        _sites(db)
        _staff(db)
        _parties(db)
        _skus(db)
        _rules(db)
        _pos_and_lots(db)
        _pallets_and_history(db)
        _orders(db)
        _temps(db)
        _planted(db)
        _documents(db)
    db.close()


def _meta(db) -> None:
    for k, v in {
        "product": PRODUCT_NAME,
        "tenant": TENANT_NAME,
        "watermark": WATERMARK,
        "now": NOW,
        "seed_version": "2026-10-20.v2",
        "disclaimer": "Demo con datos sintéticos. No usar como inventario real.",
    }.items():
        db.execute("INSERT INTO meta (key, value) VALUES (?, ?)", (k, v))


def _sites(db) -> None:
    db.execute(
        "INSERT INTO sites VALUES (?,?,?,?)",
        ("CEDIS-MEX", "CEDIS Principal", "cedis", "Ciudad de México"),
    )
    db.execute(
        "INSERT INTO sites VALUES (?,?,?,?)",
        ("CEDIS-GDL", "CEDIS Satélite Guadalajara", "satelite", "Guadalajara"),
    )
    zones = [
        # id, site, name, kind, set, current, rh, x, y, w, h
        ("Z-ANDEN", "CEDIS-MEX", "Andén refrigerado", "anden", 8.0, 8.2, 85, 20, 20, 260, 70),
        ("Z-CAM1", "CEDIS-MEX", "Cámara 1 · fruta de clima templado", "camara", 0.5, 0.6, 92, 20, 110, 200, 160),
        ("Z-CAM2", "CEDIS-MEX", "Cámara 2 · berries y cereza", "camara", 0.0, 0.2, 93, 240, 110, 200, 160),
        ("Z-CAM3", "CEDIS-MEX", "Cámara 3 · tropical", "camara", 10.0, 10.4, 90, 460, 110, 200, 160),
        ("Z-SECO", "CEDIS-MEX", "Almacén seco / empaque", "seco", 18.0, 19.0, 55, 20, 290, 260, 80),
        ("Z-TRANSITO", "CEDIS-MEX", "En tránsito a GDL", "transito", 7.0, 7.0, 85, 460, 290, 200, 80),
        ("Z-GDL", "CEDIS-GDL", "Cámara GDL", "camara", 2.0, 2.1, 90, 20, 20, 200, 120),
    ]
    for z in zones:
        db.execute(
            "INSERT INTO zones VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            z,
        )
    # Positions: a simple rack grid per cold room.
    layouts = {
        "Z-ANDEN": [(f"AND-{i:02d}", 40 + i * 36, 40) for i in range(1, 7)],
        "Z-CAM1": [((r, c), 40 + c * 36, 130 + r * 36) for r in range(4) for c in range(5)],
        "Z-CAM2": [((r, c), 260 + c * 36, 130 + r * 36) for r in range(4) for c in range(5)],
        "Z-CAM3": [((r, c), 480 + c * 36, 130 + r * 36) for r in range(4) for c in range(5)],
        "Z-SECO": [(f"SEC-{i:02d}", 40 + i * 36, 320) for i in range(1, 6)],
        "Z-TRANSITO": [(f"TR-{i:02d}", 480 + i * 36, 320) for i in range(1, 4)],
        "Z-GDL": [((r, c), 40 + c * 36, 40 + r * 36) for r in range(3) for c in range(4)],
    }
    for zone_id, cells in layouts.items():
        for item in cells:
            if zone_id in ("Z-ANDEN", "Z-SECO", "Z-TRANSITO"):
                code, x, y = item
            else:
                (r, c), x, y = item
                prefix = zone_id.split("-")[1]
                code = f"{prefix}-R{r+1}C{c+1}"
            pid = f"P-{zone_id}-{code}"
            db.execute(
                "INSERT INTO positions VALUES (?,?,?,?,?)",
                (pid, zone_id, code, x, y),
            )


def _staff(db) -> None:
    staff = [
        ("ST-DUENO", "Héctor Solís", "dueno", "matutino"),
        ("ST-GER", "Marisol Peña", "gerente", "matutino"),
        ("ST-SUP-M", "Iván Cabrera", "supervisor", "matutino"),
        ("ST-SUP-V", "Rebeca Núñez", "supervisor", "vespertino"),
        ("ST-SUP-N", "Óscar Ledesma", "supervisor", "nocturno"),
        ("ST-ALM-M1", "Paola Ríos", "almacenista", "matutino"),
        ("ST-ALM-M2", "Diego Arce", "almacenista", "matutino"),
        ("ST-ALM-V1", "Lucía Beltrán", "almacenista", "vespertino"),
        ("ST-ALM-N1", "Andrés Molina", "almacenista", "nocturno"),
        ("ST-ALM-N2", "Karina Soto", "almacenista", "nocturno"),
        ("ST-VEN", "Camila Herrera", "ventas", "matutino"),
        ("ST-CAL", "Fernanda Ortiz", "calidad", "matutino"),
    ]
    for row in staff:
        db.execute("INSERT INTO staff VALUES (?,?,?,?,1)", row)


def _parties(db) -> None:
    parties = [
        ("SUP-ANDES", "supplier", "Andes Pacífico SpA", "Valparaíso", "CL", None),
        ("SUP-CUSCO", "supplier", "Valle del Cusco SAC", "Ica", "PE", None),
        ("SUP-YAKIMA", "supplier", "Yakima Ridge Packers", "Yakima", "US", None),
        ("SUP-MICHO", "supplier", "Huerta Alta Michoacán", "Uruapan", "MX", None),
        ("SUP-BERRIES", "supplier", "Costa Berry Coop", "Watsonville", "US", None),
        ("CUS-VALLE", "customer", "Super Valle", "Toluca", "MX", 5),
        ("CUS-NORTE", "customer", "Mercado Norte", "Monterrey", "MX", 4),
        ("CUS-CADI", "customer", "CADI Central", "CDMX", "MX", 3),
        ("CUS-COSTA", "customer", "Costa Fresca Retail", "Veracruz", "MX", 7),
        ("CUS-HORECA", "customer", "Grupo Horeca Bajío", "León", "MX", 4),
        ("CAR-FRIO", "carrier", "FrioRuta Logística", "CDMX", "MX", None),
    ]
    db.executemany("INSERT INTO parties VALUES (?,?,?,?,?,?)", parties)


def _skus(db) -> None:
    # Temps and lives from USDA HB66 / UC Davis Produce Facts (approx., labelled in UI).
    skus = [
        ("SKU-MANZ-GAL", "Manzana", "Gala", "US", "templado", -0.5, 0.5, 90, 95, 90, -1.5, 0, None, "high", "low", 280, 80),
        ("SKU-MANZ-FUJ", "Manzana", "Fuji", "US", "templado", -0.5, 0.5, 90, 95, 120, -1.5, 0, None, "high", "low", 300, 80),
        ("SKU-PERA-PACK", "Pera", "Packham", "CL", "templado", -1.0, 0.0, 90, 95, 90, -1.6, 0, None, "high", "high", 320, 70),
        ("SKU-UVA-RED", "Uva de mesa", "Red Globe", "PE", "templado", -0.5, 0.0, 90, 95, 56, -2.1, 0, None, "very_low", "low", 420, 60),
        ("SKU-UVA-THOM", "Uva de mesa", "Thompson", "CL", "templado", -0.5, 0.0, 90, 95, 56, -2.1, 0, None, "very_low", "low", 400, 60),
        ("SKU-CER-BING", "Cereza", "Bing", "US", "berry", -1.0, 0.0, 90, 95, 21, -1.8, 0, None, "very_low", "low", 780, 40),
        ("SKU-ARA-DUKE", "Arándano", "Duke", "PE", "berry", -0.5, 0.0, 90, 95, 21, -1.3, 0, None, "low", "low", 620, 80),
        ("SKU-FRE-ALB", "Fresa", "Albion", "US", "berry", 0.0, 0.5, 90, 95, 7, -0.8, 0, None, "low", "low", 540, 80),
        ("SKU-KIWI-HAY", "Kiwi", "Hayward", "CL", "templado", -0.5, 0.5, 90, 95, 90, -1.5, 0, None, "low", "high", 360, 70),
        ("SKU-DUR-ELEG", "Durazno", "Elegant Lady", "US", "hueso", -0.5, 0.0, 90, 95, 21, -0.9, 1, 0.0, "high", "high", 340, 60),
        ("SKU-AGU-HASS", "Aguacate", "Hass", "MX", "tropical", 5.0, 12.0, 85, 90, 28, -0.3, 1, 5.0, "high", "high", 480, 50),
        ("SKU-MAN-ATA", "Mango", "Ataulfo", "MX", "tropical", 10.0, 13.0, 85, 90, 21, -1.0, 1, 10.0, "moderate", "moderate", 300, 60),
        ("SKU-PAP-MAR", "Papaya", "Maradol", "MX", "tropical", 10.0, 13.0, 85, 90, 14, -0.9, 1, 7.0, "moderate", "moderate", 220, 50),
        ("SKU-LIM-PERS", "Limón persa", "Tahití", "MX", "citrico", 9.0, 10.0, 85, 90, 42, -1.4, 1, 7.5, "very_low", "moderate", 180, 80),
        ("SKU-NAR-VAL", "Naranja", "Valencia", "MX", "citrico", 3.0, 8.0, 85, 90, 56, -0.8, 1, 3.0, "very_low", "moderate", 160, 80),
        ("SKU-PLA-CAV", "Plátano", "Cavendish", "MX", "tropical", 13.0, 14.0, 90, 95, 21, -0.8, 1, 13.0, "moderate", "high", 140, 80),
        ("SKU-PIN-MD2", "Piña", "MD-2", "MX", "tropical", 7.0, 13.0, 85, 90, 21, -1.0, 1, 7.0, "low", "low", 200, 40),
        ("SKU-FRAM-TUL", "Frambuesa", "Tulameen", "MX", "berry", -0.5, 0.0, 90, 95, 5, -0.9, 0, None, "low", "low", 700, 80),
        ("SKU-ZAR-CHE", "Zarzamora", "Chester", "MX", "berry", -0.5, 0.5, 90, 95, 7, -0.8, 0, None, "low", "low", 640, 80),
        ("SKU-UVA-CRI", "Uva de mesa", "Crimson", "CL", "templado", -0.5, 0.0, 90, 95, 56, -2.1, 0, None, "very_low", "low", 410, 60),
        ("SKU-MANZ-GRA", "Manzana", "Granny Smith", "US", "templado", -0.5, 0.5, 90, 95, 120, -1.5, 0, None, "high", "low", 290, 80),
        ("SKU-PERA-BART", "Pera", "Bartlett", "US", "templado", -1.0, 0.5, 90, 95, 60, -1.6, 0, None, "high", "high", 310, 70),
        ("SKU-CIR-ANG", "Ciruela", "Angeleno", "US", "hueso", -0.5, 0.0, 90, 95, 28, -0.8, 1, 0.0, "moderate", "high", 300, 70),
        ("SKU-NEC-SUM", "Nectarina", "Summer Bright", "US", "hueso", -0.5, 0.0, 90, 95, 21, -0.9, 1, 0.0, "high", "high", 330, 60),
        ("SKU-MAND-W", "Mandarina", "W. Murcott", "MX", "citrico", 4.0, 8.0, 90, 95, 28, -1.0, 1, 3.0, "very_low", "moderate", 190, 80),
        ("SKU-TOR-RUB", "Toronja", "Ruby Red", "MX", "citrico", 10.0, 15.0, 85, 90, 42, -1.0, 1, 10.0, "very_low", "moderate", 170, 70),
        ("SKU-COC-VER", "Coco verde", "Enano", "MX", "tropical", 12.0, 16.0, 80, 85, 14, -0.9, 1, 12.0, "very_low", "low", 90, 40),
        ("SKU-GUA-PER", "Guayaba", "Pera", "MX", "tropical", 5.0, 10.0, 85, 90, 21, -1.0, 1, 5.0, "moderate", "high", 160, 60),
        ("SKU-HIG-BRN", "Higo", "Brown Turkey", "MX", "hueso", -0.5, 0.0, 85, 90, 7, -2.4, 0, None, "moderate", "high", 520, 50),
        ("SKU-MEL-CAN", "Melón", "Cantaloupe", "MX", "melon", 2.0, 5.0, 85, 90, 14, -1.2, 1, 2.0, "high", "moderate", 210, 40),
        ("SKU-SAN-HON", "Sandía", "Jubilee", "MX", "melon", 10.0, 15.0, 85, 90, 14, -0.4, 1, 10.0, "very_low", "low", 150, 20),
        ("SKU-UVA-JAM", "Uva de mesa", "Autumn Royal", "CL", "templado", -0.5, 0.0, 90, 95, 50, -2.1, 0, None, "very_low", "low", 430, 60),
        ("SKU-ARA-BIL", "Arándano", "Biloxi", "MX", "berry", -0.5, 0.0, 90, 95, 18, -1.3, 0, None, "low", "low", 600, 80),
        ("SKU-CER-LAP", "Cereza", "Lapins", "US", "berry", -1.0, 0.0, 90, 95, 21, -1.8, 0, None, "very_low", "low", 800, 40),
        ("SKU-KIWI-GOL", "Kiwi", "Gold", "CL", "templado", 0.0, 0.5, 90, 95, 60, -1.5, 0, None, "low", "high", 390, 70),
        ("SKU-MAN-HAD", "Mango", "Haden", "MX", "tropical", 12.0, 13.0, 85, 90, 21, -1.0, 1, 10.0, "moderate", "moderate", 280, 60),
        ("SKU-AGU-CRE", "Aguacate", "Criollo", "MX", "tropical", 8.0, 12.0, 85, 90, 14, -0.3, 1, 8.0, "high", "high", 400, 50),
        ("SKU-LIM-COL", "Lima colima", "Mexicana", "MX", "citrico", 9.0, 10.0, 85, 90, 28, -1.4, 1, 7.5, "very_low", "moderate", 170, 80),
        ("SKU-NAR-NJL", "Naranja", "Navel", "US", "citrico", 3.0, 8.0, 85, 90, 56, -0.8, 1, 3.0, "very_low", "moderate", 200, 80),
        ("SKU-PERA-FOR", "Pera", "Forelle", "CL", "templado", -1.0, 0.0, 90, 95, 70, -1.6, 0, None, "high", "high", 340, 70),
        ("SKU-MANZ-PIN", "Manzana", "Pink Lady", "US", "templado", -0.5, 0.5, 90, 95, 120, -1.5, 0, None, "high", "low", 330, 80),
        ("SKU-UVA-SUG", "Uva de mesa", "Sugarone", "PE", "templado", -0.5, 0.0, 90, 95, 45, -2.1, 0, None, "very_low", "low", 440, 60),
        ("SKU-FRE-MON", "Fresa", "Monterey", "MX", "berry", 0.0, 0.5, 90, 95, 7, -0.8, 0, None, "low", "low", 520, 80),
        ("SKU-PAP-HAW", "Papaya", "Hawaiian", "MX", "tropical", 7.0, 13.0, 85, 90, 12, -0.9, 1, 7.0, "moderate", "moderate", 240, 50),
        ("SKU-DUR-RICH", "Durazno", "Rich Lady", "US", "hueso", -0.5, 0.0, 90, 95, 18, -0.9, 1, 0.0, "high", "high", 350, 60),
    ]
    db.executemany(
        """INSERT INTO skus VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        skus,
    )


def _rules(db) -> None:
    rules = [
        (
            "R-HOLD-BLOCK",
            "HOLD_BLOCKS_PICK",
            "Un pallet en retención no se surte",
            "Calidad o inspección pueden retener un pallet. El API rechaza pick y load mientras hold_status != libre.",
            1,
            0,
            0,
        ),
        (
            "R-DUMP-PHOTO",
            "DUMP_NEEDS_PHOTO",
            "Merma requiere foto y supervisor",
            "Toda merma (dump) exige foto adjunta y aprobación de supervisor de turno.",
            1,
            1,
            1,
        ),
        (
            "R-BLIND-COUNT",
            "BLIND_COUNT_SHIFT",
            "Conteo ciego al cambio de turno",
            "Al cierre de cada turno se abre un conteo ciego por cámara. El almacenista no ve el sistema.",
            1,
            0,
            0,
        ),
        (
            "R-ETHYLENE",
            "NO_ETHYLENE_MIX",
            "No mezclar productores de etileno con sensibles",
            "Kiwi, lechuga y brócoli no se ubican junto a manzana, pera o aguacate.",
            1,
            0,
            0,
        ),
        (
            "R-CHILL",
            "CHILLING_ZONE",
            "Cítricos y tropicales fuera de Cámara 1",
            "Producto sensible al frío no se almacena por debajo de su umbral.",
            1,
            0,
            0,
        ),
        (
            "R-SYNC-DOOR",
            "SYNC_AT_DOOR",
            "Sincronizar al salir de cámara",
            "Los eventos offline se envían al cruzar el andén. El servidor deduplica por UUID.",
            1,
            0,
            0,
        ),
    ]
    for r in rules:
        db.execute(
            """INSERT INTO rules (id, code, title, body, active, requires_photo, requires_supervisor, approved_by, approved_at, version)
               VALUES (?,?,?,?,?,?,?,?,?,1)""",
            (*r, "ST-DUENO", "2026-09-01T09:00:00-06:00"),
        )
        audit(
            db,
            ts="2026-09-01T09:00:00-06:00",
            actor_id="ST-DUENO",
            role="dueno",
            action="rule.approve",
            entity="rule",
            entity_id=r[0],
            detail=r[2],
        )


def _pos_and_lots(db) -> None:
    pos = [
        ("PO-8841", "SUP-YAKIMA", "SKU-CER-BING", 120, "2026-10-18", "recibida"),
        ("PO-8842", "SUP-CUSCO", "SKU-UVA-RED", 200, "2026-10-16", "recibida"),
        ("PO-8843", "SUP-BERRIES", "SKU-ARA-DUKE", 80, "2026-10-12", "recibida"),
        ("PO-8844", "SUP-MICHO", "SKU-AGU-HASS", 100, "2026-10-10", "recibida"),
        ("PO-8845", "SUP-MICHO", "SKU-PAP-MAR", 60, "2026-10-08", "recibida"),
        ("PO-8846", "SUP-ANDES", "SKU-KIWI-HAY", 70, "2026-10-05", "recibida"),
        ("PO-8847", "SUP-MICHO", "SKU-LIM-PERS", 90, "2026-10-06", "recibida"),
        ("PO-8848", "SUP-YAKIMA", "SKU-MANZ-GAL", 160, "2026-09-20", "recibida"),
        ("PO-8849", "SUP-MICHO", "SKU-MAN-ATA", 80, "2026-10-11", "recibida"),
        ("PO-8850", "SUP-BERRIES", "SKU-FRE-ALB", 40, "2026-10-19", "recibida"),
        ("PO-8851", "SUP-ANDES", "SKU-PERA-PACK", 90, "2026-09-28", "recibida"),
        ("PO-8852", "SUP-ANDES", "SKU-UVA-THOM", 120, "2026-10-02", "recibida"),
        ("PO-8853", "SUP-YAKIMA", "SKU-MANZ-FUJ", 140, "2026-09-18", "recibida"),
        ("PO-8854", "SUP-YAKIMA", "SKU-MANZ-PIN", 100, "2026-09-22", "recibida"),
        ("PO-8855", "SUP-CUSCO", "SKU-UVA-SUG", 80, "2026-10-04", "recibida"),
        ("PO-8856", "SUP-MICHO", "SKU-NAR-VAL", 110, "2026-10-01", "recibida"),
        ("PO-8857", "SUP-ANDES", "SKU-KIWI-GOL", 50, "2026-10-07", "recibida"),
        ("PO-8858", "SUP-MICHO", "SKU-MEL-CAN", 40, "2026-10-14", "recibida"),
        ("PO-8859", "SUP-YAKIMA", "SKU-CER-LAP", 60, "2026-10-15", "recibida"),
        ("PO-8860", "SUP-BERRIES", "SKU-ARA-BIL", 70, "2026-10-13", "recibida"),
    ]
    db.executemany("INSERT INTO purchase_orders VALUES (?,?,?,?,?,?)", pos)

    lots = [
        ("LOT-CER-0918", "SKU-CER-BING", "CER-BING-20261018", "Yakima, US", "2026-10-16", "2026-10-17", "PO-8841", "SUP-YAKIMA", "Yakima Ridge Packers"),
        ("LOT-UVA-1016", "SKU-UVA-RED", "UVA-RG-20261014", "Ica, PE", "2026-10-10", "2026-10-12", "PO-8842", "SUP-CUSCO", "Valle del Cusco SAC"),
        ("LOT-ARA-1012", "SKU-ARA-DUKE", "ARA-DUKE-20261010", "Watsonville, US", "2026-10-08", "2026-10-09", "PO-8843", "SUP-BERRIES", "Costa Berry Coop"),
        ("LOT-AGU-1010", "SKU-AGU-HASS", "AGU-HASS-20261008", "Uruapan, MX", "2026-10-07", "2026-10-08", "PO-8844", "SUP-MICHO", "Huerta Alta Michoacán"),
        ("LOT-PAP-1008", "SKU-PAP-MAR", "PAP-MAR-20261006", "Colima, MX", "2026-10-05", "2026-10-06", "PO-8845", "SUP-MICHO", "Huerta Alta Michoacán"),
        ("LOT-KIW-1005", "SKU-KIWI-HAY", "KIW-HAY-20261002", "Valparaíso, CL", "2026-09-28", "2026-10-01", "PO-8846", "SUP-ANDES", "Andes Pacífico SpA"),
        ("LOT-LIM-1006", "SKU-LIM-PERS", "LIM-TAH-20261004", "Martínez de la Torre, MX", "2026-10-02", "2026-10-03", "PO-8847", "SUP-MICHO", "Huerta Alta Michoacán"),
        ("LOT-MAN-0920", "SKU-MANZ-GAL", "MAN-GAL-20260918", "Yakima, US", "2026-09-12", "2026-09-16", "PO-8848", "SUP-YAKIMA", "Yakima Ridge Packers"),
        ("LOT-MNG-1011", "SKU-MAN-ATA", "MNG-ATA-20261009", "Chiapas, MX", "2026-10-08", "2026-10-09", "PO-8849", "SUP-MICHO", "Huerta Alta Michoacán"),
        ("LOT-FRE-1019", "SKU-FRE-ALB", "FRE-ALB-20261018", "Watsonville, US", "2026-10-17", "2026-10-18", "PO-8850", "SUP-BERRIES", "Costa Berry Coop"),
        ("LOT-PER-0928", "SKU-PERA-PACK", "PER-PAC-20260924", "Valparaíso, CL", "2026-09-20", "2026-09-23", "PO-8851", "SUP-ANDES", "Andes Pacífico SpA"),
        ("LOT-UVA-1002", "SKU-UVA-THOM", "UVA-TH-20260928", "Valparaíso, CL", "2026-09-24", "2026-09-27", "PO-8852", "SUP-ANDES", "Andes Pacífico SpA"),
        ("LOT-FUJ-0918", "SKU-MANZ-FUJ", "MAN-FUJ-20260914", "Yakima, US", "2026-09-10", "2026-09-13", "PO-8853", "SUP-YAKIMA", "Yakima Ridge Packers"),
        ("LOT-PIN-0922", "SKU-MANZ-PIN", "MAN-PIN-20260918", "Yakima, US", "2026-09-14", "2026-09-17", "PO-8854", "SUP-YAKIMA", "Yakima Ridge Packers"),
        ("LOT-SUG-1004", "SKU-UVA-SUG", "UVA-SU-20261001", "Ica, PE", "2026-09-26", "2026-09-29", "PO-8855", "SUP-CUSCO", "Valle del Cusco SAC"),
        ("LOT-NAR-1001", "SKU-NAR-VAL", "NAR-VAL-20260928", "Veracruz, MX", "2026-09-26", "2026-09-28", "PO-8856", "SUP-MICHO", "Huerta Alta Michoacán"),
        ("LOT-KIG-1007", "SKU-KIWI-GOL", "KIW-GOL-20261003", "Valparaíso, CL", "2026-09-30", "2026-10-02", "PO-8857", "SUP-ANDES", "Andes Pacífico SpA"),
        ("LOT-MEL-1014", "SKU-MEL-CAN", "MEL-CAN-20261012", "Colima, MX", "2026-10-11", "2026-10-12", "PO-8858", "SUP-MICHO", "Huerta Alta Michoacán"),
        ("LOT-LAP-1015", "SKU-CER-LAP", "CER-LAP-20261013", "Yakima, US", "2026-10-11", "2026-10-12", "PO-8859", "SUP-YAKIMA", "Yakima Ridge Packers"),
        ("LOT-BIL-1013", "SKU-ARA-BIL", "ARA-BIL-20261011", "Jalisco, MX", "2026-10-09", "2026-10-10", "PO-8860", "SUP-BERRIES", "Costa Berry Coop"),
        ("LOT-AGU-TRN", "SKU-AGU-HASS", "AGU-HASS-20261008-T", "Uruapan, MX", "2026-10-07", "2026-10-08", "PO-8844", "SUP-MICHO", "Huerta Alta Michoacán"),
    ]
    db.executemany(
        """INSERT INTO lots (id, sku_id, lot_code, origin, harvest_date, pack_date, po_id, supplier_id, tlc_source)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        lots,
    )


def _put_pallet(db, **kw) -> None:
    db.execute(
        """INSERT INTO pallets (id, sscc, lot_id, qty_boxes, position_id, zone_id, site_id, hold_status, hold_reason, received_at, last_count_at, last_moved_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            kw["id"],
            kw["sscc"],
            kw["lot_id"],
            kw["qty"],
            kw.get("position_id"),
            kw.get("zone_id"),
            kw.get("site_id", "CEDIS-MEX"),
            kw.get("hold", "libre"),
            kw.get("hold_reason"),
            kw["received_at"],
            kw.get("last_count_at"),
            kw.get("last_moved_at"),
        ),
    )


def _event(db, **kw) -> None:
    insert_event(db, **kw)


def _pallets_and_history(db) -> None:
    # --- 1. Cherries: 120 received night of 18 Oct, 108 put away. 12 missing andén→cámara.
    _put_pallet(
        db,
        id="PAL-CER-A",
        sscc="003761234500000018",
        lot_id="LOT-CER-0918",
        qty=54,
        position_id="P-Z-CAM2-CAM2-R1C1",
        zone_id="Z-CAM2",
        received_at="2026-10-18T23:10:00-06:00",
        last_count_at="2026-10-19T06:20:00-06:00",
        last_moved_at="2026-10-19T00:40:00-06:00",
    )
    _put_pallet(
        db,
        id="PAL-CER-B",
        sscc="003761234500000025",
        lot_id="LOT-CER-0918",
        qty=54,
        position_id="P-Z-CAM2-CAM2-R1C2",
        zone_id="Z-CAM2",
        received_at="2026-10-18T23:12:00-06:00",
        last_count_at="2026-10-19T06:20:00-06:00",
        last_moved_at="2026-10-19T00:55:00-06:00",
    )
    _event(db, client_uuid=ev("po", "8841"), ts="2026-10-10T11:00:00-06:00", event_type="po_open", actor_id="ST-VEN", role="ventas", shift="matutino", site_id="CEDIS-MEX", sku_id="SKU-CER-BING", lot_id="LOT-CER-0918", qty_boxes=120, payload={"po_id": "PO-8841"})
    _event(db, client_uuid=ev("rcv", "cer-a"), ts="2026-10-18T23:10:00-06:00", event_type="receive", actor_id="ST-ALM-N1", role="almacenista", shift="nocturno", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-CER-A", lot_id="LOT-CER-0918", sku_id="SKU-CER-BING", qty_boxes=60, payload={"po_id": "PO-8841", "sscc": "003761234500000018", "temp_pulpa_c": 0.4})
    _event(db, client_uuid=ev("rcv", "cer-b"), ts="2026-10-18T23:12:00-06:00", event_type="receive", actor_id="ST-ALM-N1", role="almacenista", shift="nocturno", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-CER-B", lot_id="LOT-CER-0918", sku_id="SKU-CER-BING", qty_boxes=60, payload={"po_id": "PO-8841", "sscc": "003761234500000025", "temp_pulpa_c": 0.5})
    _event(db, client_uuid=ev("put", "cer-a"), ts="2026-10-19T00:40:00-06:00", event_type="putaway", actor_id="ST-ALM-N2", role="almacenista", shift="nocturno", site_id="CEDIS-MEX", zone_id="Z-CAM2", pallet_id="PAL-CER-A", lot_id="LOT-CER-0918", sku_id="SKU-CER-BING", qty_boxes=54, payload={"from_zone": "Z-ANDEN", "gap": 6})
    _event(db, client_uuid=ev("put", "cer-b"), ts="2026-10-19T00:55:00-06:00", event_type="putaway", actor_id="ST-ALM-N2", role="almacenista", shift="nocturno", site_id="CEDIS-MEX", zone_id="Z-CAM2", pallet_id="PAL-CER-B", lot_id="LOT-CER-0918", sku_id="SKU-CER-BING", qty_boxes=54, payload={"from_zone": "Z-ANDEN", "gap": 6})
    _event(db, client_uuid=ev("cnt", "cer-am"), ts="2026-10-19T06:20:00-06:00", event_type="count", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM2", lot_id="LOT-CER-0918", sku_id="SKU-CER-BING", qty_boxes=108, payload={"expected": 120, "blind": True})

    # Partial pick + load of cherries to Super Valle (48 boxes) — used to disprove customer short claim.
    _event(db, client_uuid=ev("pick", "cer-valle"), ts="2026-10-19T09:15:00-06:00", event_type="pick", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM2", pallet_id="PAL-CER-A", lot_id="LOT-CER-0918", sku_id="SKU-CER-BING", qty_boxes=48, payload={"order_id": "SO-2201", "route": ["Z-CAM2", "Z-ANDEN"]})
    db.execute("UPDATE pallets SET qty_boxes = 6 WHERE id = 'PAL-CER-A'")
    _event(db, client_uuid=ev("load", "cer-valle"), ts="2026-10-19T10:05:00-06:00", event_type="load", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-CER-A", lot_id="LOT-CER-0918", sku_id="SKU-CER-BING", qty_boxes=48, payload={"order_id": "SO-2201", "sscc_scans": 48, "photo_ids": ["pod-cer-001"]})
    _event(db, client_uuid=ev("disp", "cer-valle"), ts="2026-10-19T10:20:00-06:00", event_type="dispatch", actor_id="ST-SUP-M", role="supervisor", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", lot_id="LOT-CER-0918", sku_id="SKU-CER-BING", qty_boxes=48, payload={"order_id": "SO-2201", "customer_id": "CUS-VALLE", "unidad": "FRIO-18"})
    _event(db, client_uuid=ev("pod", "cer-valle"), ts="2026-10-19T13:40:00-06:00", event_type="deliver", actor_id="CAR-FRIO", role="almacenista", shift="matutino", site_id="CEDIS-MEX", lot_id="LOT-CER-0918", sku_id="SKU-CER-BING", qty_boxes=48, payload={"order_id": "SO-2201", "signed_by": "Recepción Super Valle", "claimed_short": 6, "claim_status": "desestimado"})

    # --- 2. Peru Red Globe short-ship: PO 200, received 176.
    _put_pallet(db, id="PAL-UVA-A", sscc="003761234500000032", lot_id="LOT-UVA-1016", qty=88, position_id="P-Z-CAM1-CAM1-R1C1", zone_id="Z-CAM1", received_at="2026-10-16T08:40:00-06:00", last_count_at="2026-10-16T11:00:00-06:00", last_moved_at="2026-10-16T09:10:00-06:00")
    _put_pallet(db, id="PAL-UVA-B", sscc="003761234500000049", lot_id="LOT-UVA-1016", qty=88, position_id="P-Z-CAM1-CAM1-R1C2", zone_id="Z-CAM1", received_at="2026-10-16T08:45:00-06:00", last_count_at="2026-10-16T11:00:00-06:00", last_moved_at="2026-10-16T09:20:00-06:00")
    _event(db, client_uuid=ev("po", "8842"), ts="2026-10-08T10:00:00-06:00", event_type="po_open", actor_id="ST-VEN", role="ventas", sku_id="SKU-UVA-RED", lot_id="LOT-UVA-1016", qty_boxes=200, payload={"po_id": "PO-8842"})
    _event(db, client_uuid=ev("rcv", "uva-a"), ts="2026-10-16T08:40:00-06:00", event_type="receive", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-UVA-A", lot_id="LOT-UVA-1016", sku_id="SKU-UVA-RED", qty_boxes=88, payload={"po_id": "PO-8842", "bol_qty": 200})
    _event(db, client_uuid=ev("rcv", "uva-b"), ts="2026-10-16T08:45:00-06:00", event_type="receive", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-UVA-B", lot_id="LOT-UVA-1016", sku_id="SKU-UVA-RED", qty_boxes=88, payload={"po_id": "PO-8842"})
    _event(db, client_uuid=ev("put", "uva-a"), ts="2026-10-16T09:10:00-06:00", event_type="putaway", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM1", pallet_id="PAL-UVA-A", lot_id="LOT-UVA-1016", sku_id="SKU-UVA-RED", qty_boxes=88, payload={})
    _event(db, client_uuid=ev("put", "uva-b"), ts="2026-10-16T09:20:00-06:00", event_type="putaway", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM1", pallet_id="PAL-UVA-B", lot_id="LOT-UVA-1016", sku_id="SKU-UVA-RED", qty_boxes=88, payload={})

    # --- 3. Blueberry repack yield gap 80 → 68.
    _put_pallet(db, id="PAL-ARA-A", sscc="003761234500000056", lot_id="LOT-ARA-1012", qty=68, position_id="P-Z-CAM2-CAM2-R2C1", zone_id="Z-CAM2", received_at="2026-10-12T07:50:00-06:00", last_count_at="2026-10-13T16:10:00-06:00", last_moved_at="2026-10-13T16:10:00-06:00")
    _event(db, client_uuid=ev("rcv", "ara"), ts="2026-10-12T07:50:00-06:00", event_type="receive", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-ARA-A", lot_id="LOT-ARA-1012", sku_id="SKU-ARA-DUKE", qty_boxes=80, payload={"po_id": "PO-8843"})
    _event(db, client_uuid=ev("put", "ara"), ts="2026-10-12T08:20:00-06:00", event_type="putaway", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM2", pallet_id="PAL-ARA-A", lot_id="LOT-ARA-1012", sku_id="SKU-ARA-DUKE", qty_boxes=80, payload={})
    _event(db, client_uuid=ev("repack", "ara"), ts="2026-10-13T15:40:00-06:00", event_type="repack", actor_id="ST-ALM-V1", role="almacenista", shift="vespertino", site_id="CEDIS-MEX", zone_id="Z-SECO", pallet_id="PAL-ARA-A", lot_id="LOT-ARA-1012", sku_id="SKU-ARA-DUKE", qty_boxes=68, payload={"qty_in": 80, "qty_out": 68, "yield_pct": 85, "reason": "reclasificación clamshell 6 oz"})

    # --- 4. Misplaced mango pallet: physically in CAM1, system said CAM3. Found by count.
    _put_pallet(db, id="PAL-MNG-MIS", sscc="003761234500000063", lot_id="LOT-MNG-1011", qty=40, position_id="P-Z-CAM1-CAM1-R3C4", zone_id="Z-CAM1", received_at="2026-10-11T09:00:00-06:00", last_count_at="2026-10-19T07:10:00-06:00", last_moved_at="2026-10-19T07:10:00-06:00")
    _event(db, client_uuid=ev("rcv", "mng"), ts="2026-10-11T09:00:00-06:00", event_type="receive", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-MNG-MIS", lot_id="LOT-MNG-1011", sku_id="SKU-MAN-ATA", qty_boxes=40, payload={"po_id": "PO-8849"})
    _event(db, client_uuid=ev("put", "mng"), ts="2026-10-11T09:30:00-06:00", event_type="putaway", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM3", pallet_id="PAL-MNG-MIS", lot_id="LOT-MNG-1011", sku_id="SKU-MAN-ATA", qty_boxes=40, payload={})
    _event(db, client_uuid=ev("found", "mng"), ts="2026-10-19T07:10:00-06:00", event_type="count", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM1", pallet_id="PAL-MNG-MIS", lot_id="LOT-MNG-1011", sku_id="SKU-MAN-ATA", qty_boxes=40, payload={"expected_zone": "Z-CAM3", "found_zone": "Z-CAM1", "classification": "extravio", "not_loss": True})
    _event(db, client_uuid=ev("move", "mng"), ts="2026-10-19T07:25:00-06:00", event_type="move", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM1", pallet_id="PAL-MNG-MIS", lot_id="LOT-MNG-1011", sku_id="SKU-MAN-ATA", qty_boxes=40, payload={"from_zone": "Z-CAM3", "to_zone": "Z-CAM1", "reason": "localizado en conteo"})

    # --- 5. In-transit avocado loss CEDIS-MEX → GDL: 40 dispatched, 36 received.
    _put_pallet(db, id="PAL-AGU-TRN", sscc="003761234500000070", lot_id="LOT-AGU-TRN", qty=36, position_id="P-Z-GDL-GDL-R1C1", zone_id="Z-GDL", site_id="CEDIS-GDL", received_at="2026-10-17T16:40:00-06:00", last_count_at="2026-10-17T16:50:00-06:00", last_moved_at="2026-10-17T16:40:00-06:00")
    _event(db, client_uuid=ev("rcv", "agu-trn"), ts="2026-10-10T11:20:00-06:00", event_type="receive", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-AGU-TRN", lot_id="LOT-AGU-TRN", sku_id="SKU-AGU-HASS", qty_boxes=40, payload={"po_id": "PO-8844"})
    _event(db, client_uuid=ev("put", "agu-trn"), ts="2026-10-10T11:50:00-06:00", event_type="putaway", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM3", pallet_id="PAL-AGU-TRN", lot_id="LOT-AGU-TRN", sku_id="SKU-AGU-HASS", qty_boxes=40, payload={})
    _event(db, client_uuid=ev("xfr", "agu"), ts="2026-10-17T05:10:00-06:00", event_type="transfer", actor_id="ST-SUP-N", role="supervisor", shift="nocturno", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-AGU-TRN", lot_id="LOT-AGU-TRN", sku_id="SKU-AGU-HASS", qty_boxes=40, payload={"to_site": "CEDIS-GDL", "unidad": "FRIO-07"})
    _event(db, client_uuid=ev("rcv-gdl", "agu"), ts="2026-10-17T16:40:00-06:00", event_type="receive", actor_id="ST-ALM-M1", role="almacenista", shift="vespertino", site_id="CEDIS-GDL", zone_id="Z-GDL", pallet_id="PAL-AGU-TRN", lot_id="LOT-AGU-TRN", sku_id="SKU-AGU-HASS", qty_boxes=36, payload={"from_site": "CEDIS-MEX", "expected": 40})

    # Remaining avocado in CAM3 (exposed to compressor failure).
    _put_pallet(db, id="PAL-AGU-A", sscc="003761234500000087", lot_id="LOT-AGU-1010", qty=50, position_id="P-Z-CAM3-CAM3-R1C1", zone_id="Z-CAM3", received_at="2026-10-10T10:10:00-06:00", last_count_at="2026-10-19T08:00:00-06:00", last_moved_at="2026-10-10T10:40:00-06:00")
    _event(db, client_uuid=ev("rcv", "agu-a"), ts="2026-10-10T10:10:00-06:00", event_type="receive", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-AGU-A", lot_id="LOT-AGU-1010", sku_id="SKU-AGU-HASS", qty_boxes=50, payload={"po_id": "PO-8844"})
    _event(db, client_uuid=ev("put", "agu-a"), ts="2026-10-10T10:40:00-06:00", event_type="putaway", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM3", pallet_id="PAL-AGU-A", lot_id="LOT-AGU-1010", sku_id="SKU-AGU-HASS", qty_boxes=50, payload={})

    # --- 7. Papaya: 60 received, unrecorded dump of 10 found by cycle count.
    _put_pallet(db, id="PAL-PAP-A", sscc="003761234500000094", lot_id="LOT-PAP-1008", qty=50, position_id="P-Z-CAM3-CAM3-R2C1", zone_id="Z-CAM3", received_at="2026-10-08T08:15:00-06:00", last_count_at="2026-10-18T21:30:00-06:00", last_moved_at="2026-10-08T08:40:00-06:00")
    _event(db, client_uuid=ev("rcv", "pap"), ts="2026-10-08T08:15:00-06:00", event_type="receive", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-PAP-A", lot_id="LOT-PAP-1008", sku_id="SKU-PAP-MAR", qty_boxes=60, payload={"po_id": "PO-8845"})
    _event(db, client_uuid=ev("put", "pap"), ts="2026-10-08T08:40:00-06:00", event_type="putaway", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM3", pallet_id="PAL-PAP-A", lot_id="LOT-PAP-1008", sku_id="SKU-PAP-MAR", qty_boxes=60, payload={})
    _event(db, client_uuid=ev("cnt", "pap"), ts="2026-10-18T21:30:00-06:00", event_type="count", actor_id="ST-ALM-V1", role="almacenista", shift="vespertino", site_id="CEDIS-MEX", zone_id="Z-CAM3", pallet_id="PAL-PAP-A", lot_id="LOT-PAP-1008", sku_id="SKU-PAP-MAR", qty_boxes=50, payload={"expected": 60, "unrecorded_dump": True})

    # --- 9. Kiwi next to apples in CAM1 (ethylene).
    _put_pallet(db, id="PAL-KIW-A", sscc="003761234500000100", lot_id="LOT-KIW-1005", qty=70, position_id="P-Z-CAM1-CAM1-R1C3", zone_id="Z-CAM1", received_at="2026-10-05T09:00:00-06:00", last_count_at="2026-10-15T08:00:00-06:00", last_moved_at="2026-10-05T09:30:00-06:00")
    _event(db, client_uuid=ev("rcv", "kiw"), ts="2026-10-05T09:00:00-06:00", event_type="receive", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-KIW-A", lot_id="LOT-KIW-1005", sku_id="SKU-KIWI-HAY", qty_boxes=70, payload={"po_id": "PO-8846"})
    _event(db, client_uuid=ev("put", "kiw"), ts="2026-10-05T09:30:00-06:00", event_type="putaway", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM1", pallet_id="PAL-KIW-A", lot_id="LOT-KIW-1005", sku_id="SKU-KIWI-HAY", qty_boxes=70, payload={})

    _put_pallet(db, id="PAL-MAN-A", sscc="003761234500000117", lot_id="LOT-MAN-0920", qty=80, position_id="P-Z-CAM1-CAM1-R1C4", zone_id="Z-CAM1", received_at="2026-09-20T08:00:00-06:00", last_count_at="2026-10-10T08:00:00-06:00", last_moved_at="2026-09-20T08:40:00-06:00")
    _event(db, client_uuid=ev("rcv", "man"), ts="2026-09-20T08:00:00-06:00", event_type="receive", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-MAN-A", lot_id="LOT-MAN-0920", sku_id="SKU-MANZ-GAL", qty_boxes=80, payload={"po_id": "PO-8848"})
    _event(db, client_uuid=ev("put", "man"), ts="2026-09-20T08:40:00-06:00", event_type="putaway", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM1", pallet_id="PAL-MAN-A", lot_id="LOT-MAN-0920", sku_id="SKU-MANZ-GAL", qty_boxes=80, payload={})

    # --- 10. Limes stored too cold in CAM1.
    _put_pallet(db, id="PAL-LIM-A", sscc="003761234500000124", lot_id="LOT-LIM-1006", qty=90, position_id="P-Z-CAM1-CAM1-R2C1", zone_id="Z-CAM1", received_at="2026-10-06T10:00:00-06:00", last_count_at="2026-10-12T08:00:00-06:00", last_moved_at="2026-10-06T10:25:00-06:00")
    _event(db, client_uuid=ev("rcv", "lim"), ts="2026-10-06T10:00:00-06:00", event_type="receive", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-LIM-A", lot_id="LOT-LIM-1006", sku_id="SKU-LIM-PERS", qty_boxes=90, payload={"po_id": "PO-8847"})
    _event(db, client_uuid=ev("put", "lim"), ts="2026-10-06T10:25:00-06:00", event_type="putaway", actor_id="ST-ALM-M2", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM1", pallet_id="PAL-LIM-A", lot_id="LOT-LIM-1006", sku_id="SKU-LIM-PERS", qty_boxes=90, payload={"note": "ubicado por espacio, no por compatibilidad"})

    # --- 11. Strawberries on QC hold.
    _put_pallet(db, id="PAL-FRE-H", sscc="003761234500000131", lot_id="LOT-FRE-1019", qty=40, position_id="P-Z-CAM2-CAM2-R3C1", zone_id="Z-CAM2", hold="retenido", hold_reason="Botrytis en 4 clamshells · espera dictamen de calidad", received_at="2026-10-19T07:40:00-06:00", last_count_at="2026-10-19T08:10:00-06:00", last_moved_at="2026-10-19T08:00:00-06:00")
    _event(db, client_uuid=ev("rcv", "fre"), ts="2026-10-19T07:40:00-06:00", event_type="receive", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id="PAL-FRE-H", lot_id="LOT-FRE-1019", sku_id="SKU-FRE-ALB", qty_boxes=40, payload={"po_id": "PO-8850", "temp_pulpa_c": 1.2})
    _event(db, client_uuid=ev("put", "fre"), ts="2026-10-19T08:00:00-06:00", event_type="putaway", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM2", pallet_id="PAL-FRE-H", lot_id="LOT-FRE-1019", sku_id="SKU-FRE-ALB", qty_boxes=40, payload={})
    _event(db, client_uuid=ev("hold", "fre"), ts="2026-10-19T08:25:00-06:00", event_type="hold", actor_id="ST-CAL", role="calidad", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-CAM2", pallet_id="PAL-FRE-H", lot_id="LOT-FRE-1019", sku_id="SKU-FRE-ALB", qty_boxes=40, payload={"reason": "Botrytis en 4 clamshells"})

    # Healthy background stock so the map looks full.
    extras = [
        ("PAL-PER-A", "003761234500000148", "LOT-PER-0928", 70, "P-Z-CAM1-CAM1-R2C2", "Z-CAM1", "2026-09-28T09:00:00-06:00", "SKU-PERA-PACK"),
        ("PAL-THO-A", "003761234500000155", "LOT-UVA-1002", 60, "P-Z-CAM1-CAM1-R2C3", "Z-CAM1", "2026-10-02T10:00:00-06:00", "SKU-UVA-THOM"),
        ("PAL-FUJ-A", "003761234500000162", "LOT-FUJ-0918", 80, "P-Z-CAM1-CAM1-R3C1", "Z-CAM1", "2026-09-18T08:30:00-06:00", "SKU-MANZ-FUJ"),
        ("PAL-PIN-A", "003761234500000179", "LOT-PIN-0922", 70, "P-Z-CAM1-CAM1-R3C2", "Z-CAM1", "2026-09-22T09:10:00-06:00", "SKU-MANZ-PIN"),
        ("PAL-SUG-A", "003761234500000186", "LOT-SUG-1004", 80, "P-Z-CAM2-CAM2-R2C2", "Z-CAM2", "2026-10-04T11:00:00-06:00", "SKU-UVA-SUG"),
        ("PAL-NAR-A", "003761234500000193", "LOT-NAR-1001", 110, "P-Z-CAM3-CAM3-R3C1", "Z-CAM3", "2026-10-01T08:20:00-06:00", "SKU-NAR-VAL"),
        ("PAL-KIG-A", "003761234500000209", "LOT-KIG-1007", 50, "P-Z-CAM1-CAM1-R4C1", "Z-CAM1", "2026-10-07T09:40:00-06:00", "SKU-KIWI-GOL"),
        ("PAL-MEL-A", "003761234500000216", "LOT-MEL-1014", 40, "P-Z-CAM3-CAM3-R3C2", "Z-CAM3", "2026-10-14T10:00:00-06:00", "SKU-MEL-CAN"),
        ("PAL-LAP-A", "003761234500000223", "LOT-LAP-1015", 60, "P-Z-CAM2-CAM2-R1C3", "Z-CAM2", "2026-10-15T07:50:00-06:00", "SKU-CER-LAP"),
        ("PAL-BIL-A", "003761234500000230", "LOT-BIL-1013", 70, "P-Z-CAM2-CAM2-R2C3", "Z-CAM2", "2026-10-13T08:10:00-06:00", "SKU-ARA-BIL"),
        ("PAL-MNG-B", "003761234500000247", "LOT-MNG-1011", 40, "P-Z-CAM3-CAM3-R1C2", "Z-CAM3", "2026-10-11T09:20:00-06:00", "SKU-MAN-ATA"),
    ]
    for pid, sscc, lot, qty, pos, zone, rec, sku in extras:
        _put_pallet(db, id=pid, sscc=sscc, lot_id=lot, qty=qty, position_id=pos, zone_id=zone, received_at=rec, last_count_at=rec, last_moved_at=rec)
        _event(db, client_uuid=ev("rcv", pid), ts=rec, event_type="receive", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id="Z-ANDEN", pallet_id=pid, lot_id=lot, sku_id=sku, qty_boxes=qty, payload={})
        _event(db, client_uuid=ev("put", pid), ts=rec, event_type="putaway", actor_id="ST-ALM-M1", role="almacenista", shift="matutino", site_id="CEDIS-MEX", zone_id=zone, pallet_id=pid, lot_id=lot, sku_id=sku, qty_boxes=qty, payload={})

    # Shift handoffs last 3 days.
    for day, actor, shift in [
        ("2026-10-18T06:00:00-06:00", "ST-SUP-N", "nocturno"),
        ("2026-10-18T14:00:00-06:00", "ST-SUP-M", "matutino"),
        ("2026-10-18T22:00:00-06:00", "ST-SUP-V", "vespertino"),
        ("2026-10-19T06:00:00-06:00", "ST-SUP-N", "nocturno"),
        ("2026-10-19T14:00:00-06:00", "ST-SUP-M", "matutino"),
        ("2026-10-19T22:00:00-06:00", "ST-SUP-V", "vespertino"),
        ("2026-10-20T06:00:00-06:00", "ST-SUP-N", "nocturno"),
    ]:
        _event(db, client_uuid=ev("handoff", day), ts=day, event_type="shift_handoff", actor_id=actor, role="supervisor", shift=shift, site_id="CEDIS-MEX", payload={"blind_count_opened": True})


def _orders(db) -> None:
    orders = [
        ("SO-2201", "CUS-VALLE", "SKU-CER-BING", 48, "2026-10-19", 5, "entregada", "Reclamo de 6 cajas · desestimado con evidencia de carga"),
        ("SO-2208", "CUS-NORTE", "SKU-AGU-HASS", 40, "2026-10-21", 4, "abierta", "Acepta vida restante ≥ 4 días"),
        ("SO-2209", "CUS-HORECA", "SKU-AGU-HASS", 20, "2026-10-21", 3, "abierta", "Horeca, giro rápido"),
        ("SO-2210", "CUS-COSTA", "SKU-MAN-ATA", 30, "2026-10-22", 7, "abierta", "Pide 7 días de vida · no tomar lote expuesto"),
        ("SO-2211", "CUS-CADI", "SKU-MAN-ATA", 24, "2026-10-21", 3, "abierta", "CADI acepta 3 días"),
        ("SO-2212", "CUS-VALLE", "SKU-UVA-RED", 40, "2026-10-22", 5, "abierta", None),
        ("SO-2213", "CUS-NORTE", "SKU-CER-LAP", 20, "2026-10-21", 4, "abierta", None),
        ("SO-2214", "CUS-CADI", "SKU-FRE-ALB", 16, "2026-10-21", 3, "abierta", "Bloqueada: lote en retención"),
        ("SO-2215", "CUS-COSTA", "SKU-KIWI-HAY", 20, "2026-10-25", 10, "abierta", None),
        ("SO-2216", "CUS-HORECA", "SKU-ARA-DUKE", 16, "2026-10-21", 4, "abierta", None),
    ]
    db.executemany("INSERT INTO sales_orders VALUES (?,?,?,?,?,?,?,?)", orders)


def _temps(db) -> None:
    # Baseline hourly-ish samples plus Cámara 3 compressor failure 02:00–07:00 on 19 Oct.
    rows = []
    baselines = {
        "Z-ANDEN": 8.2,
        "Z-CAM1": 0.6,
        "Z-CAM2": 0.2,
        "Z-CAM3": 10.4,
        "Z-SECO": 19.0,
        "Z-GDL": 2.1,
    }
    for zone, t in baselines.items():
        for hour in range(0, 48):
            # 19 Oct 00:00 through 20 Oct 14:00
            day = 19 if hour < 24 else 20
            h = hour if hour < 24 else hour - 24
            if day == 20 and h > 14:
                continue
            temp = t
            if zone == "Z-CAM3" and day == 19 and 2 <= h < 7:
                temp = 16.0
            ts = f"2026-10-{day:02d}T{h:02d}:00:00-06:00"
            rows.append((zone, ts, temp, "sensor"))
    db.executemany("INSERT INTO temp_log (zone_id, ts, temp_c, source) VALUES (?,?,?,?)", rows)


def _planted(db) -> None:
    cases = [
        (
            "CASE-CHERRY-NIGHT",
            "Faltante de cereza en turno nocturno, segmento andén → cámara",
            "faltante",
            "LOT-CER-0918",
            None,
            "anden_a_camara",
            "nocturno",
            12,
            "PO 120, recibido 120, acomodado 108. 12 cajas entre andén y Cámara 2, 18–19 oct, turno nocturno.",
        ),
        (
            "CASE-UVA-SHORTSHIP",
            "Faltante de proveedor · uva Red Globe Perú",
            "faltante_proveedor",
            "LOT-UVA-1016",
            None,
            "po_a_recibido",
            "matutino",
            24,
            "PO 200, recibido 176. Borrador de reclamo a Valle del Cusco SAC.",
        ),
        (
            "CASE-ARA-REPACK",
            "Merma de rendimiento en reempaque de arándano",
            "reempaque",
            "LOT-ARA-1012",
            "PAL-ARA-A",
            "reempaque",
            "vespertino",
            12,
            "80 clamshells in, 68 out, rendimiento 85%.",
        ),
        (
            "CASE-MANGO-MISPLACE",
            "Pallet de mango extraviado, no perdido",
            "extravio",
            "LOT-MNG-1011",
            "PAL-MNG-MIS",
            "almacen",
            "matutino",
            0,
            "Sistema: Cámara 3. Conteo: Cámara 1. Clasificado como extravío.",
        ),
        (
            "CASE-AGU-TRANSIT",
            "Faltante de aguacate en tránsito a GDL",
            "faltante",
            "LOT-AGU-TRN",
            "PAL-AGU-TRN",
            "transito",
            "nocturno",
            4,
            "40 despachadas el 17 oct, 36 recibidas en GDL.",
        ),
        (
            "CASE-CLAIM-FALSE",
            "Reclamo de cliente desestimado con evidencia de carga",
            "reclamo_desestimado",
            "LOT-CER-0918",
            "PAL-CER-A",
            "entregado",
            "matutino",
            0,
            "Super Valle reclamó 6 cajas. Escaneo de carga y POD = 48.",
        ),
        (
            "CASE-PAPAYA-DUMP",
            "Merma de papaya no registrada, hallada en conteo",
            "merma_no_registrada",
            "LOT-PAP-1008",
            "PAL-PAP-A",
            "almacen",
            "vespertino",
            10,
            "Recibido 60, conteo 50, sin evento de merma.",
        ),
        (
            "CASE-CAM3-COMPRESSOR",
            "Falla de compresor Cámara 3 · 16 °C × 5 h",
            "abuso_termico",
            "LOT-AGU-1010",
            "PAL-AGU-A",
            "almacen",
            "nocturno",
            0,
            "19 oct 02:00–07:00. Aguacate y mango Ataulfo en riesgo; se emparejan a pedidos de vida corta.",
        ),
        (
            "CASE-KIWI-ETHYLENE",
            "Kiwi almacenado junto a manzana",
            "etileno",
            "LOT-KIW-1005",
            "PAL-KIW-A",
            "almacen",
            "matutino",
            0,
            "Cámara 1: kiwi Hayward junto a manzana Gala (productor alto de etileno).",
        ),
        (
            "CASE-LIME-CHILL",
            "Limón persa demasiado frío",
            "frio",
            "LOT-LIM-1006",
            "PAL-LIM-A",
            "almacen",
            "matutino",
            0,
            "Cámara 1 a 0.6 °C; umbral de daño por frío del limón ~7.5 °C.",
        ),
        (
            "CASE-HOLD-BLOCK",
            "Pallet de fresa en retención no se puede surtir",
            "retencion",
            "LOT-FRE-1019",
            "PAL-FRE-H",
            "calidad",
            "matutino",
            0,
            "Calidad retuvo por Botrytis. Pick API → 409.",
        ),
    ]
    db.executemany(
        "INSERT INTO planted_cases VALUES (?,?,?,?,?,?,?,?,?)",
        cases,
    )


def _documents(db) -> None:
    docs = [
        (
            "DOC-RECEP-UVA",
            "recepcion",
            "Reporte de recepción PO-8842 · uva Red Globe",
            "2026-10-16T09:30:00-06:00",
            "PO-8842",
            json.dumps(
                {
                    "po": "PO-8842",
                    "sku": "Uva Red Globe",
                    "ordered": 200,
                    "received": 176,
                    "short": 24,
                    "supplier": "Valle del Cusco SAC",
                    "claim_draft": "Se recibieron 176 de 200 cajas del PO-8842. Faltante de 24 cajas. Se adjunta foto de andén y packing list.",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "DOC-RECLAMO-UVA",
            "reclamo_proveedor",
            "Borrador de reclamo · Valle del Cusco SAC",
            "2026-10-16T10:00:00-06:00",
            "PO-8842",
            json.dumps(
                {
                    "to": "Valle del Cusco SAC",
                    "po": "PO-8842",
                    "lot": "UVA-RG-20261014",
                    "ordered": 200,
                    "received": 176,
                    "short": 24,
                    "value_mxn": 24 * 420,
                    "status": "borrador",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "DOC-POD-CER",
            "pod",
            "Prueba de entrega SO-2201 · Super Valle",
            "2026-10-19T13:40:00-06:00",
            "SO-2201",
            json.dumps(
                {
                    "order": "SO-2201",
                    "customer": "Super Valle",
                    "qty": 48,
                    "signed_by": "Recepción Super Valle",
                    "claim": "6 cajas faltantes — desestimado",
                },
                ensure_ascii=False,
            ),
        ),
        (
            "DOC-REMISION-CER",
            "remision",
            "Remisión SO-2201",
            "2026-10-19T10:20:00-06:00",
            "SO-2201",
            json.dumps(
                {"order": "SO-2201", "qty": 48, "sku": "Cereza Bing", "lot": "CER-BING-20261018"},
                ensure_ascii=False,
            ),
        ),
        (
            "DOC-CP-CER",
            "carta_porte",
            "Hoja de datos Carta Porte · SO-2201",
            "2026-10-19T10:20:00-06:00",
            "SO-2201",
            json.dumps(
                {
                    "TranspInternac": "No",
                    "BienesTransp": "01010101",
                    "Descripcion": "Cereza Bing, lote CER-BING-20261018",
                    "Cantidad": 48,
                    "ClaveUnidad": "XBX",
                    "PesoEnKg": 480,
                    "nota": "Siconet timbra el CFDI; Norfront Fresh genera la hoja de datos.",
                },
                ensure_ascii=False,
            ),
        ),
    ]
    db.executemany(
        "INSERT INTO documents (id, kind, title, created_at, related_id, body) VALUES (?,?,?,?,?,?)",
        docs,
    )


if __name__ == "__main__":
    seed()
    print("seeded", WATERMARK)
