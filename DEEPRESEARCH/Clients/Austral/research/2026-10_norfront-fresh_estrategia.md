# Norfront Fresh — strategy for Austral, Mr Lucky and the Mexico–US produce corridor

**20 October 2026.** Written for Mateo. English summary first, Spanish (MX) after. Every factual sentence has a source. Inferences are marked `[Inference]`. Synthetic demos contain no Austral records.

Companion files: `00_decision-memo.md`, `notes/`, `OPEN_QUESTIONS.md`.

---

## English summary

**The door.** Sign Austral as a *design partner*, not as the brand. The first paid logo that looks like the company you want to be is **Mr Lucky (Grupo U)** — Irapuato, FTL vegetables, a plant, six DCs, Laredo. Meeting around 10 November, four days after FDA’s 6 November public meeting on lot-level traceability. Divine Flavor is the hub play (Nogales + Sinaloa/Sonora growers). Sunview is grapes: not on the Food Traceability List; do not lead with FSMA.

**The one thing to show.** From an inventory alert to *where in the chain it happened* in two clicks — segment, shift, zone, evidence — with capture that works in a cold room that has no Wi-Fi. That is what Austral’s father and sales manager will recognise, and what Mr Lucky’s ops lead can test with a held pallet that the API will not pick.

**Who pays, and what.** `[Inference]` A one-warehouse Mexican importer: implementation plus 6–8 cold-rated handhelds in the low six figures MXN; software in the mid five figures MXN per month. A grower-packer adding FSMA 204: same monthly, plus a packing-station kit. Take a 90-day shrink baseline before any gainshare. Public list prices for Famous, RedLine and Siconet were **NOT FOUND**; ReposiTrak publishes supplier-network economics in its filings (see notes/06 when complete).

**Beat or partner.** Overlay Siconet, do not replace it. Partner RedLine for PTI print if the customer already has it. Export KDEs into iTrade / ReposiTrak / FoodLogiQ when a US buyer demands a network. Do not start a traceability *network*. Do not rebuild Famous.

**Tailwind.** FSMA 204 enforcement cannot begin before **20 July 2028** (Pub. L. 119-37). The rule still covers Mr Lucky’s lettuce, tomato, cucumber, pepper and fresh-cut. Walmart’s PTI case-label mandate has been in force since 1 November 2013. Mexican retailers (Walmex, Chedraui) currently buy on GFSI and SENASICA more than on Subpart S — sell them shrink and mock-recall time, not “FDA will fine you.”

**At scale.** A vertical OS for fresh produce: warehouse truth in Mexico, lot records at the border, then a thin network only when buyers require it. Analogues are Toast / Procore (land at one site, expand) not IBM Food Trust (a consortium that faded).

**Keep it secret?** No. Traceability is a network good. Offer Austral a founding-partner window (pricing, veto on a named competitor for 12 months, no press without them). Secrecy and “sell it to everyone” are the same product with different contracts.

**Where you are wrong.** (1) FSMA 204 does not apply to fruit Austral imports and sells only in Mexico. (2) Do not name the product Austral OS. (3) RedLine’s site saying “July 26th, 2028” is almost certainly a typo for 20 July. (4) Celery, cabbage, garlic, corn, carrot, frozen vegetables and table grapes are not on the FTL; pitching FSMA there is a credibility kill. (5) You do not yet have SOC 2. (6) The September scan test failed on radio, not on software — hardware and labels are half the switch-on plan.

---

## 1. El mercado y el problema

México es el primer o segundo proveedor de varios productos de la Food Traceability List que entran a Estados Unidos: jitomate, pimiento, pepino, pepino, melón, mango, hierbas. Las cifras oficiales de volumen y valor 2024/2025 están en SIAP/SADER, USDA FAS GAIN y GATS; se transcriben en `notes/03_market-mexico-us.md` cuando el stream cierre. El corredor relevante para esta tesis es **Sinaloa/Sonora → Nogales**, **Bajío → Laredo** y **el importador de fruta templada hacia el mercado interno** (el oficio de Austral).

El problema que Austral ya describió, y que no es exclusivo de ellos:

- Nadie confía en el inventario. Las cajas se pierden y no se sabe en qué eslabón.
- Los registros viven en papel, Excel, Siconet, Teams, correo, radio y memoria.
- Una prueba de escaneo en septiembre se cayó **porque no hay Wi‑Fi en las cámaras** (dato del brief; el modelo de terminal y el vendor son NOT FOUND).
- El gerente de ventas llama al inventario “sagrado”. El dueño, con más de 40 años en el oficio, preguntó qué tan rápido se prende.

Eso no es un problema de “hace falta un ERP”. Austral ya tiene Siconet: ERP en la nube para comercializadoras de perecederos, Zapopan, Jalisco, fundado en 2005, con módulos de almacén, embarques, facturación (Carta Porte / CFDI), tesorería y liquidación a agricultores ([siconet.com.mx](https://www.siconet.com.mx/), consultado 2026-10-20). El hueco es **la captura en el piso y la atribución del faltante**.

Pérdida y merma: el estudio del Banco Mundial *Pérdidas y desperdicios de alimentos en México* (2017) y las series de FAO/SEMARNAT documentan pérdida alta en frutas y hortalizas en la distribución. Un porcentaje puntual “típico” de merma de un comercializador mexicano de fruta **no está publicado de forma usable**; no lo inventamos. La literatura de *inventory record inaccuracy* (DeHoratius & Raman, 2008, *Management Science*) sí establece que la inexactitud de existencias es la norma, no la excepción, en retail. `[Inference]` Un comercializador que no cuenta a ciegas por turno está operando a ciegas.

## 2. Cómo corre un almacén de produce que sí funciona

Práctica, no software (fuentes: USDA Agriculture Handbook 66, 2016; UC Davis Postharvest Technology Center; WERC DC Measures; PACA para reclamos a proveedor):

- Recepción con temperatura de pulpa y, si aplica, inspección USDA / reclamo PACA en tiempo.
- Ubicación por **compatibilidad de temperatura y etileno**, no por “dónde cabe”. Manzana y pera son altos productores de etileno; kiwi, lechuga y brócoli son sensibles (HB66 / UC Davis Produce Facts).
- **FEFO**, no FIFO, cuando la vida restante diverge (un lote abusado térmicamente no es el más viejo en calendario).
- Conteos cíclicos ABC y **conteo ciego al cambio de turno**.
- Producto retenido **segregado y bloqueado** en el sistema, no solo con un papel en el pallet.
- Captura en cámara: access points *dentro* del cuarto, o terminales store-and-forward. El Wi‑Fi falla en paneles aislados de metal. Equipos de freezer (Zebra MC9300/CK65 y equivalentes) tienen rango de temperatura publicado; los precios de revendedor se anotan en `notes/05`.
- RFID en produce fresco: el agua y el metal degradan UHF. Auburn RFID Lab y GS1 lo documentan. `[Inference]` No es la primera inversión de un CEDIS mexicano de tamaño medio. Primero código de barras y disciplina de evento.

El motor de frescura del demo usa las temperaturas de HB66 y un Q10 = 2.5 (Kader / postcosecha). La fórmula se muestra en pantalla y se etiqueta como inferencia.

## 3. Incumbentes: vencer o asociarse

| Firma | Jugada |
| --- | --- |
| **Siconet** | Convivir. Importar existencias / OC / pedidos. Ellos timbran el CFDI y la Carta Porte. Nosotros escribimos la hoja de datos y el libro de custodia. |
| **Famous** | No reemplazar. Si un cliente US ya vive ahí, conectar el ledger. On-prem Oracle, cotización a la medida (Software Advice / SelectHub; precio de lista NOT FOUND). |
| **Prophet** | Confirmar de qué producto hablan. Epicor Prophet 21 es un ERP de distribución, no un WMS de fruta. No pelear contra un nombre ambiguo. |
| **Agriful** | Identidad no confirmada en fuentes primarias al momento de escribir. No citar en una junta. |
| **RedLine** | Asociarse en etiquetas PTI / Print Pack Ship. Todd Baggett, Santa Clara, fundó la compañía en 1997 y copreside el PTI Technology Working Group. El centro de su discurso 2025–2026 es FSMA 204. Su sitio escribe “Enforcement Begins July 26th, 2028” — la ley dice **20 de julio**. Tratarlo como aliado, no como enemigo, y no copiar la fecha. |
| **Produce Pro, Silo, dProduce Man, FreshByte** | ERPs/WMS de produce US. Mismo patrón: overlay, no rip-and-replace. |
| **iTradeNetwork, ReposiTrak, FoodLogiQ/Trustwell, iFoodDS** | Redes del *comprador* US. Exportar KDEs / EPCIS. No lanzar “la red mexicana” en 2026. |
| **TOMRA, Unitec, MAF, Reemoon** | Línea de empaque. El lote nace ahí; el software de clasificación no es un libro de custodia. Integrar después. |

`[Inference]` La capacidad que nadie les vende bien a un importador mexicano de un solo CEDIS es la que está en el memo: captura offline + faltante por segmento/turno + overlay.

## 4. La puerta y la única cosa

Ver `00_decision-memo.md`. En una frase: **Austral enseña el producto; Mr Lucky lo convierte en compañía; Divine Flavor lo lleva al empaque.**

La única cosa: *de la alerta a la evidencia en dos clics*, con la red apagada.

## 5. A quién firmar y cómo

**Austral (diseño).** El padre ya preguntó por el encendido. El gerente de ventas preguntó si se guarda o se vende. Respuesta en §11. Condiciones `[Inference]`: 90 días de piloto en una cámara y el andén; precio de socio fundador; ellos no son el logo en la home; veto de 12 meses sobre un competidor nombrado; ninguna nota de prensa sin su sí.

**Mr Lucky / Grupo U.** Hechos públicos (mrlucky.com.mx, consultado 2026-10-20): planta en Irapuato; CEDIS en CDMX, Monterrey, Guadalajara, Cancún, Irapuato y Laredo, TX; lechugas, apio, brócoli, coliflor, espinaca, jitomates, mini pepino, precortado y congelado; orgánico CCOF/USDA. El catálogo muestra prefijo UPC 796631 y vidas de anaquel (iceberg 14 días, apio 2–3 semanas, corona de brócoli 20 días). **En la FTL:** lechugas de hoja, espinaca, jitomate, pepino, precortado. **Fuera:** apio, brócoli, coliflor, ajo, col, elote, zanahoria, chícharo, congelado. La junta ~10 nov es cuatro días después de la reunión pública de FDA (6 nov 2026, FR 2026-20720). Llevar el demo de FSMA y el de almacén. No prometer cumplimiento legal.

**Divine Flavor.** Nogales AZ, 2007. Pimiento, jitomate, pepino, calabaza, melón, uva. Growers públicos: Hortifresh, Viva Orgánica, Grupo Chaparral, Campaña Agricultores (Culiacán), Grupo Alta (Sonora). Puertos: Nogales (~80 %), Otay Mesa, McAllen. La puerta es **un empaque, muchos ranchos**, no el importador solo.

**Sunview Vineyards.** Delano, CA. Uva de mesa. La uva **no está en la FTL**. OSHA 300A 2025 lista ~1,437 empleados. Estimaciones de ingreso ($68 M–$250 M) discrepan — no usar ninguna. Si se abre, vender frío y traza comercial, no Subpart S.

## 6. Precio

Precios de lista de Famous, Produce Pro, RedLine PTI Lite y Siconet: **NOT FOUND** en páginas públicas al 20 oct 2026. ReposiTrak (NYSE: TRAK) publica ingresos y número de nodos en 10-K/10-Q; transcribir en notes/06.

Ancla de valor `[Inference]`, aritmética, no un resultado:

- Si un comercializador factura MXN 500 M y la merma + faltante no registrado es 2 % de ventas, un punto porcentual vale MXN 5 M al año.
- Un piloto que recupere *una décima* de punto (MXN 500 mil) paga un software de MXN 40–80 mil al mes y el hardware.
- No afirmar que el piloto recupera eso. Medir 90 días.

Recomendación de empaque comercial `[Inference]`:

| Perfil | Setup | Mensual | Hardware |
| --- | --- | --- | --- |
| Importador, 1 CEDIS, 3 turnos | MXN 180–350 k (mapeo Siconet, conteo inicial, reglas) | MXN 45–75 k | 6–8 handhelds freezer-rate + 2 impresoras; renta o compra |
| Empaque FSMA, 1 planta | MXN 220–400 k (plan §1.1315, estaciones, etiquetas) | MXN 55–90 k | 2 estaciones de empaque + 1 andén |

Riesgo de cada uno: el primero se muere si el Wi‑Fi (o el store-and-forward) falla otra vez; el segundo se muere si FDA recorta KDEs en 2027 y el comprador deja de preguntar.

## 7. FSMA 204 y los retailers

- **Fecha de cumplimiento:** 20 julio 2028. FDA lo propuso el 7 agosto 2025; Pub. L. 119-37 (Continuing Appropriations Act, 2026) impide exigir antes. Reunión pública sobre trazabilidad a nivel de lote: 6 noviembre 2026 (Federal Register 2026-20720). Guía borrador de discreción de aplicación para pequeños retailers y restaurantes: 9 octubre 2026.
- **Qué cubre (FTL produce):** pepinos, hierbas, leafy greens (fresco y corte), melones, pimientos, germinados, jitomates, frutas tropicales de árbol *con exclusiones* (aguacate, cítricos, plátano, piña y otras), y frutas/verduras precortadas. Fuente: página FTL de FDA, consultada 2026-10-20.
- **Qué no cubre:** uva de mesa, manzana, pera, cereza, arándano entero, kiwi, durazno, cítricos, aguacate, plátano, piña, calabaza, apio, brócoli, col, elote, ajo, zanahoria, congelados. Un empaque de uva o un importador de manzana no “está en FSMA 204” por vender fruta.
- **Quién guarda qué:** 21 CFR 1.1325 (cosecha y enfriado, y lo que hay que mandar al empaque inicial), 1.1330 (empaque inicial: aquí nace el TLC), 1.1340 (envío), 1.1345 (recibo), 1.1350 (transformación), 1.1315 (plan), 1.1320 (quién puede asignar un código nuevo), 1.1455 (retención 2 años, 24 horas, hoja electrónica ordenable).
- **Walmart US:** exigencia de etiqueta PTI de caja vigente desde el 1 nov 2013 (comunicado Walmart / PTI). IBM Food Trust para leafy greens (2018–2019) no es, en 2026, el estándar de facto; no vender “están en blockchain”.
- **México:** NOM-251-SSA1-2009 es higiene; no es Subpart S. SENASICA SRRC y certificados fitosanitarios *sí* generan rastro en el andén de un importador. GFSI (PrimusGFS, GLOBALG.A.P. IFA v6, SQF, BRCGS) exige trazabilidad y simulacros de retiro — eso sí aplica a Mr Lucky y a Divine hoy, no en 2028.

## 8. La compañía a escala

`[Inference]` Tres capas, en este orden:

1. **Ledger de custodia** (lo que está construido): evento → inventario, pérdida, FEFO, documentos.
2. **Lente FSMA** sobre el mismo ledger para quien exporta a EUA.
3. **Red** solo cuando un comprador la exige (export a ReposiTrak / iTrade / EPCIS), no como producto de lanzamiento.

El patrón es Toast o Procore: un sitio, un turno, luego el segundo CEDIS. No IBM Food Trust. Frubana y Jüsto enseñan que “OS del food en LatAm” se estrella cuando se financia distribución en lugar de software.

Comparables de *traceability software* cotizados: ReposiTrak (TRAK) es el único número limpio; el resto es privado o se vendió (FoodLogiQ → Trustwell). Transcribir múltiplos cuando notes/06 cierre. No inventar valuación.

## 9. ¿Lo guardamos o lo vendemos?

Pregunta del gerente de ventas de Austral. Respuesta:

La traza solo vale si el siguiente eslabón puede leer el lote. Un sistema secreto es un Excel con mejor tipo de letra. Lo que sí se puede guardar es **la ventaja de 12 meses**: precio de socio, capacidad de decir que no a un competidor nombrado, y control de la historia pública.

Tres contratos, un producto: diseño (Austral), planta (Mr Lucky), empaque (Divine).

## 10. Dónde estamos mal

1. FSMA no cubre el negocio doméstico de Austral ni la uva de Sunview.
2. El producto no se llama Austral OS. Se llama Norfront Fresh. El tenant es el cliente.
3. “July 26, 2028” en RedLine no es la ley.
4. Vender FSMA sobre apio, col, ajo o uva destruye credibilidad en la primera junta.
5. No hay SOC 2 ni ISO. Las *claims rules* de Norfront lo prohíben.
6. El piloto de septiembre falló por radio. Sin handhelds de frío y etiquetas que se peguen a 0 °C, el software es teatro.
7. Atribuir un faltante a una persona, en México, es un problema laboral y de LFPDPPP. Por eso la vista pública es proceso y la privada dice “señal, no acusación”.
8. El VPC del demo es un CRC-16 candidato, no un certificado PTI. Decirlo en la junta.

## 11. Plan de encendido en Austral

**Supuestos** (en `demos/austral-os/ASSUMPTIONS.md`): forma del CEDIS, columnas de Siconet, términos de Dafne (A9, CLAM, line order) y el modelo de terminal de septiembre son desconocidos. No se inventaron.

### Hardware y etiquetas `[Inference]` de rangos de revendedor 2025–2026, a confirmar

| Ítem | Cantidad | Rango USD | Nota |
| --- | --- | --- | --- |
| Handheld freezer-rate (Zebra MC3300/MC9300 o Honeywell CK65 cold) | 6 | 1,400–2,400 c/u | O tablet rugerizada + anillo si el presupuesto aprieta |
| Impresora de escritorio (ZD421 / PC42) | 2 | 400–700 | Andén y empaque |
| Stock freezer / all-temp, 1,000 etiquetas | 10 millar | 40–90 / millar | Adhesivo que aguante condensación |
| AP en cámara (opcional, fase 2) | 3 | 200–400 | No es el plan A; el plan A es offline |

### Línea base (semana 0, antes de prender)

- 10 días de: cajas recibidas vs acomodadas vs surtidas vs embarcadas, por SKU, a mano.
- Conteos ciegos de las tres cámaras, un turno.
- Lista de faltantes y reclamos de los últimos 60 días (rangos, no records reales en ningún modelo).
- Métrica piloto: *inventory truth score* (pallets verificados < 48 h), cajas faltantes atribuidas a un segmento, tiempo alerta→evidencia, pick bloqueado en retención.

### Fases

1. **Días 1–10.** Mapear Siconet/Excel. Reglas del dueño. Etiquetar pallets existentes (paso 2 del wizard).
2. **Días 11–25.** Un turno, Cámara 2 + andén. Offline obligatorio. No se apaga Siconet.
3. **Días 26–45.** Tres turnos. FEFO en un SKU de vida corta (cereza / berry).
4. **Días 46–90.** Segunda cámara. Vista privada solo el dueño. Decisión de seguir o no, con números, no con sentimiento.

## 12. Preparación Mr Lucky (~10 nov 2026)

**Antes de entrar**

- El 6 nov FDA habla de trazabilidad a nivel de lote. Leer el docket esa noche. Si recortan KDEs, el pitch no cambia: el gate y el simulacro siguen sirviendo a PrimusGFS / al receptor de Laredo.
- Llevar dos laptops. La demo corre sin red. Video de respaldo (este repo, walkthrough).
- Personas en la sala `[Inference]`: operaciones de planta, inocuidad, y quien manda a Laredo. No solo “innovación”.

**Guion 20 minutos**

1. Tres frases: cada movimiento con hora; el faltante se ve ahora; una retención no se surte.
2. Demo almacén (5 min): alerta → cereza → 409 en fresa → offline.
3. Demo FSMA (5 min): empaque sin predio no imprime; camión con hueco no sale; hoja FDA; simulacro de un clic.
4. Pregunta que ellos deben hacer: “¿esto convive con lo que ya tenemos?” Sí. Overlay.
5. Lo que no se dice: plazos de cumplimiento, “les bajamos la merma X %”, nombres de otros clientes, SOC 2.

**Objeciones**

- “Ya tenemos Primus y etiquetas.” El simulacro de hoy tarda horas y el lote se arma en Excel. Esto lo deja en minutos y no deja salir el camión.
- “FSMA es en 2028.” H-E-B y Walmart no esperan a FDA para pedir PTI y un paquete de embarque. Además el 2028 es la fecha *más temprana* de enforcement, no un horizonte cómodo.
- “¿Se lo van a vender a todos?” Socio de diseño ahora, no exclusividad eterna. Ver §9.

**Materiales en la mesa:** esta nota, el memo, los dos READMEs, el deck de Mateo con el ítem 3 del checklist ya construido.

---

## Sources (load-bearing)

- [S1] FDA Food Traceability List — https://www.fda.gov/food/food-safety-modernization-act-fsma/food-traceability-list — accessed 2026-10-20
- [S2] FDA FSMA Final Rule on Requirements for Additional Traceability Records (Subpart S) — eCFR 21 CFR 1.1300–1.1465 — accessed 2026-10-20
- [S3] Pub. L. 119-37, Continuing Appropriations Act, 2026 (no enforcement of the Food Traceability Rule before 20 Jul 2028)
- [S4] Federal Register 2026-20720, FDA public meeting on lot-level traceability, 6 Nov 2026
- [S5] FDA draft enforcement-discretion guidance for small retailers and restaurants, 9 Oct 2026
- [S6] Siconet — https://www.siconet.com.mx/ — accessed 2026-10-20
- [S7] Mr Lucky / Grupo U — https://www.mrlucky.com.mx/ — accessed 2026-10-20
- [S8] Divine Flavor — company site / grower pages — accessed 2026-10-20
- [S9] USDA Agriculture Handbook 66 (2016), The Commercial Storage of Fruits, Vegetables, and Florist and Nursery Stocks
- [S10] UC Davis Postharvest Technology Center, Produce Facts
- [S11] Walmart PTI case-label requirement, effective 1 Nov 2013 (Walmart supplier communications / PTI)
- [S12] Produce Traceability Initiative — https://www.producetraceability.org/ — accessed 2026-10-20
- [S13] GS1 General Specifications, check-digit algorithm; GS1 EPCIS 2.0
- [S14] GMA / Deloitte, Recall Execution Effectiveness, 2011 (USD 10 M average *direct* cost; not produce-specific)
- [S15] World Bank, *Pérdidas y desperdicios de alimentos en México*, 2017
- [S16] DeHoratius & Raman, “Inventory Record Inaccuracy”, *Management Science*, 2008
- [S17] RedLine Solutions — company site / “Produce Traceability Integrity” (Todd Baggett) — accessed 2026-10-20. Date conflict: site “July 26th, 2028” vs [S3].
- [S18] SAT, Complemento Carta Porte 3.1, Guía de llenado (Anexo 20) — version and mandate dates to be confirmed in notes/07
- [S19] NOM-251-SSA1-2009, prácticas de higiene — not a lot-level traceability rule
- [S20] Norfront public claims rules (internal): no guarantees, no invented metrics, no client names without permission, LFPDPPP

Streams 01–07 will add quote-level ledgers under `notes/`. Where a number is still **NOT FOUND**, it stays NOT FOUND.
