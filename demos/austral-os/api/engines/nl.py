"""On-device Spanish intent parser. Deterministic. No network."""

from __future__ import annotations

import re
from typing import Any


INTENTS = [
    {
        "id": "vence_semana",
        "label": "Qué vence esta semana",
        "patterns": (r"vence", r"por vencer", r"esta semana", r"vida corta", r"se echa"),
        "route": "/embarcar",
    },
    {
        "id": "perdio_anoche",
        "label": "Qué se perdió anoche",
        "patterns": (r"perdi", r"falt", r"anoche", r"nocturn", r"se perdió"),
        "route": "/perdidas",
    },
    {
        "id": "inventario_sku",
        "label": "Cuánto hay de un producto",
        "patterns": (r"cu[aá]nto", r"hay de", r"disponible", r"existencia"),
        "route": "/disponible",
    },
    {
        "id": "traza_lote",
        "label": "Trazar un lote",
        "patterns": (r"traza", r"lote", r"de d[oó]nde", r"a d[oó]nde", r"recall"),
        "route": "/traza",
    },
    {
        "id": "mapa",
        "label": "Dónde está",
        "patterns": (r"d[oó]nde est", r"ubic", r"c[aá]mara", r"mapa"),
        "route": "/mapa",
    },
    {
        "id": "retenciones",
        "label": "Qué está retenido",
        "patterns": (r"reten", r"hold", r"calidad", r"no surt"),
        "route": "/mapa",
    },
]


def parse(question: str) -> dict[str, Any]:
    q = (question or "").lower()
    scored = []
    for intent in INTENTS:
        hits = sum(1 for p in intent["patterns"] if re.search(p, q))
        if hits:
            scored.append((hits, intent))
    scored.sort(key=lambda x: x[0], reverse=True)
    intent = scored[0][1] if scored else {
        "id": "ayuda",
        "label": "Ayuda",
        "route": "/",
    }
    sku_hint = None
    for token in (
        "cereza",
        "uva",
        "arándano",
        "arandano",
        "aguacate",
        "mango",
        "papaya",
        "kiwi",
        "limón",
        "limon",
        "manzana",
        "fresa",
    ):
        if token in q:
            sku_hint = token
            break
    lot_match = re.search(r"(CER|UVA|ARA|AGU|PAP|KIW|LIM|MAN|FRE|MNG)-[A-Z0-9-]+", question or "", re.I)
    return {
        "question": question,
        "intent": intent["id"],
        "label": intent["label"],
        "route": intent["route"],
        "sku_hint": sku_hint,
        "lot_hint": lot_match.group(0) if lot_match else None,
        "engine": "parser determinista en el dispositivo · sin modelo externo",
    }
