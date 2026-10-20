# Norfront Fresh · Austral OS (demo)

Inventario verdadero, traza por lote y decisiones de salida para un comercializador de fruta fresca. Datos **sintéticos**. Puerto web **5176**, API **8016**. Español (México).

No son registros de Austral Trading.

## Arrancar

```bash
# Linux / macOS
./start.sh

# Windows
./start.ps1
```

Abre http://127.0.0.1:5176

Requisitos: Python 3.12+, Node 20+.

Manual:

```bash
cd api && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -c "from seed import seed; seed()"
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8016

cd ../web && npm install && npm run dev
```

`Reiniciar demo` vuelve a sembrar el libro de custodia.

## Presentar (5 minutos, dueño)

1. Cabina: score de verdad, cajas faltantes, valor en riesgo 72 h.
2. Clic en el faltante de cereza → segmento **andén → cámara**, turno **nocturno**, 12 cajas, línea de tiempo.
3. Mapa: Cámara 3 caliente, kiwi junto a manzana, limón demasiado frío, fresa retenida (negro).
4. Embarcar: aguacate expuesto → Horeca (3 días). Costa Fresca pide 7 y no toma ese lote. Lista FEFO con ruta.
5. Captura: modo «cámara fría · sin señal», intentar surtir la fresa → el API responde 409. Sync en el andén, sin duplicados.
6. Traza del lote de cereza: atrás al huerto, adelante a Super Valle, hoja FDA y EPCIS.
7. Papelería y Arrancar: la respuesta a «¿qué tan rápido se prende?».

Modo **Presentar** recorre esos pasos. La demo corre en una laptop; la captura queda en IndexedDB si no hay red.

## Promesas del deck de Mr Lucky → pantalla

| Promesa del deck | Dónde se ve |
| --- | --- |
| Cada movimiento, con nombre y hora | Traza / Pérdidas · eventos con `ts`, turno y rol. La vista pública no nombra personas. |
| Faltantes visibles al momento | Cabina → Pérdidas, dos clics al segmento |
| Rutas de surtido | Embarcar + línea en el mapa |
| Retenciones que bloquean | Captura / API `HOLD_BLOCKS_PICK` (409) |
| Roles, bitácora, el dueño aprueba reglas | Selector de rol, `/reglas` |
| Convive con su ERP | `/siconet` y CSV de existencias |
| Trazabilidad por lote | `/traza` (el ítem 3 del checklist del deck) |

## Qué está plantado (llave de respuestas)

El motor de pérdidas tiene que clasificar exactamente esto (lo cubre `pytest`):

1. Cereza, 12 cajas, andén → cámara, turno nocturno.
2. Uva Red Globe Perú, 24 cajas, faltante de proveedor.
3. Arándano, merma de reempaque 80 → 68.
4. Mango extraviado en Cámara 1 (no es pérdida).
5. Aguacate, 4 cajas en tránsito a GDL.
6. Reclamo de Super Valle desestimado con evidencia de carga.
7. Papaya, 10 cajas de merma no registrada.
8. Cámara 3 a 16 °C × 5 h; aguacate/mango en riesgo.
9. Kiwi junto a manzana (etileno).
10. Limón persa demasiado frío.
11. Fresa retenida: el pick no pasa.

## Pruebas

```bash
cd api && .venv/bin/pytest -q
cd ../web && npm run build
```

## Principios visibles en la UI

- Una captura, dos resultados (inventario + vista FSMA).
- Proceso, no persona.
- Datos sintéticos, sin llamadas a un modelo externo.
- Listo para enseñarse en un almacén sin Wi‑Fi.
