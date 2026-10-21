"""Demo clock, branding and synthetic-data watermark.

Assumptions live here so a real Austral dump can replace the seed
without touching engines. See ASSUMPTIONS.md in the demo root.
"""

from __future__ import annotations

PRODUCT_NAME = "Norfront Fresh"
TENANT_NAME = "Austral Trading (demo)"
WATERMARK = "Datos sintéticos · no son registros de Austral Trading"
TIMEZONE = "America/Mexico_City"

# Frozen "now" so screenshots, tests and the live shift stay aligned.
NOW_ISO = "2026-10-20T14:30:00-06:00"
HISTORY_DAYS = 60

API_HOST = "127.0.0.1"
API_PORT = 8016

DB_PATH = "austral.db"

ROLES = (
    "dueno",
    "gerente",
    "supervisor",
    "almacenista",
    "ventas",
    "calidad",
)

ROLE_LABELS = {
    "dueno": "Dueño",
    "gerente": "Gerente de almacén",
    "supervisor": "Supervisor de turno",
    "almacenista": "Almacenista",
    "ventas": "Ventas",
    "calidad": "Calidad",
}

SHIFTS = {
    "matutino": ("06:00", "14:00"),
    "vespertino": ("14:00", "22:00"),
    "nocturno": ("22:00", "06:00"),
}
