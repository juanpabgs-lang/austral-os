# Decision memo — Norfront Fresh

Date: 20 Oct 2026. Drives both demos. Update when research notes land; decisions below are already coded.

## Differentiation thesis

Norfront Fresh is **not** a produce ERP and **not** a FSMA network. It is a **custody layer** that sits on Siconet/Excel (and later Famous, Produce Pro or a packhouse MES):

1. Capture happens in the work, including **offline in the cold room**.
2. Inventory is a **projection of an append-only event ledger**.
3. Every gap is attributed to a **segment, shift and zone** (process, not person).
4. The same events write the **FSMA 204 record** when the food is for the US.

What incumbents actually are, on public evidence (see `notes/02_incumbents.md` when it lands):

| Vendor | What it is | Gap vs this thesis |
| --- | --- | --- |
| Siconet | Mexican cloud ERP for comercializadoras (facturación, almacén, embarques, liquidación) | Inventory module exists; no public offline cold-room capture or segment-level loss attribution |
| Famous | On-prem Oracle produce ERP, grower accounting | Heavy, custom quote, not a 3-shift overlay |
| Prophet | Name collision: Epicor Prophet 21 is a distribution ERP, not a produce WMS | Wrong tool if that is the "Prophet" people mean |
| RedLine | PTI labels + MyProduce / packing; FSMA is the founder's centre of gravity | Partner for labels; we should not rebuild print-pack-ship |
| iTrade / ReposiTrak / FoodLogiQ | Buyer-side networks | Partner or export into; do not compete as a network first |
| Agriful | Ambiguous — confirm in notes | Do not pitch against a name we cannot point to |

**The single capability none of them sell well to a Mexican importer-distributor:** store-and-forward capture in a metal cold room + "this box went missing between the dock and Cámara 2 on the night shift" + an owner-only theft signal that is not an accusation.

Confidence: medium until the incumbent matrix is filled. High that Siconet does not do this — it is an ERP, and Austral already has it.

## The one thing to show

**De la alerta a la evidencia en dos clics.**

Script: cabina → faltante de cereza → 12 cajas, segmento andén→cámara, turno nocturno, línea de tiempo. Then the hold that actually blocks a pick (409). Then "cámara fría · sin señal".

That is the demo. Everything else is support.

## Who first

1. **Austral** — design partner, already inside, father asked "how fast can we switch it on". Not a logo. Founding-partner terms, not secrecy.
2. **Mr Lucky (Grupo U)** — 10 Nov, Irapuato. Lettuce, tomato, spinach, celery, fresh-cut: **on the FTL**. Ships through Laredo. The FSMA demo is for them, not for Austral.
3. **Divine Flavor** — Nogales hub. Peppers, tomatoes, cucumbers, melons are FTL; squash and grapes are not. Door is the grower group in Sinaloa/Sonora, one capture at the shed.
4. **Sunview** — table grapes, **not on the FTL**. Do not lead with FSMA 204. Cold-storage inventory only, later.

## Persona scripts and acceptance

| Persona | 5-minute script | Pass if |
| --- | --- | --- |
| Dueño (40 años) | Cabina → cereza → mapa → arrancar | "Sé qué hay, dónde, de qué lote, qué tan fresco, qué sale primero." Alert → evidence ≤ 2 clicks. |
| Gerente de ventas ("inventario sagrado") | Disponible para vender | Every number has "verificado hace N h". Holds and allocations are subtracted. |
| Almacenista nocturno, guantes | `/captura` | Targets ≥ 56 px. Offline queue. Sync at the door, no duplicates. |
| Ops / inocuidad Mr Lucky | Hold 409 + traza + hoja FDA | Held pallet cannot be picked. Lot back/forward < 1 s. |
| Receptor US (Nogales) | FSMA gate | Truck does not leave with a missing KDE. Packet is PDF/CSV/EPCIS. |
| Experto FSMA | Tabla KDE + plantados | Every planted gap caught. Non-FTL grapes do not block. |

## Mr Lucky deck → demo map

| Deck promise | Screen |
| --- | --- |
| Cada movimiento, con nombre y hora | `/traza`, `/perdidas` (public view strips the name) |
| Faltantes visibles al momento | `/` → `/perdidas?lot=LOT-CER-0918` |
| Rutas y retenciones | `/embarcar`, `/mapa`, `/captura` (409) |
| Roles, bitácora, el dueño aprueba | selector de rol, `/reglas` |
| Convive con su ERP | `/siconet` |
| Trazabilidad por lote (checklist: not built) | `/traza` — now built |

## Pricing (inference, pending notes/06)

Mexican importer, 1 warehouse, 3 shifts: **setup + hardware** in the low six figures MXN, **monthly** in the mid five figures MXN, hardware-as-a-service for 6–8 handhelds. Grower-packer FSMA: same monthly plus a per-site packing-station kit. Gainshare on shrink only after a 90-day baseline. See switch-on plan in the main report.

## What we will not claim

- No invented shrink percentages.
- No "FSMA applies to Austral" (it does not, if the fruit is sold only in Mexico).
- No SOC 2 / ISO.
- Voice pick code is `crc16-ccitt-candidate` until PTI examples are confirmed.
- GMA/Deloitte $10M recall average is 2011 and not produce-specific; show it with the date.
