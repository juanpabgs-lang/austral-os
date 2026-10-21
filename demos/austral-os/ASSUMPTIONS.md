# Assumptions (replace without code changes)

These stand in for inputs Mateo can send. They live in `api/config.py` and `api/seed.py`.

1. **Warehouse shape.** CEDIS Principal CDMX: refrigerated dock, three cold rooms (templado / berries / tropical), dry pack room. Satellite CEDIS Guadalajara so a transfer exists. Not Austral's real layout.
2. **Siconet columns.** `SKU, Descripcion, Lote, Cantidad, Almacen, Valor` and two more files for orders and POs. Real headers unknown.
3. **Dafne terms.** `A9`, `CLAM`, `line order`, `three rules left` are listed as unmapped on `/siconet`. Not invented.
4. **September scan test.** Assumed failure mode is "no Wi-Fi in the cold rooms" (from the brief). Device model unknown.
5. **PTI / incoming barcodes.** Incoming pallets get synthetic SSCC-18. Whether Austral already prints PTI is unknown.
6. **Staff, suppliers, customers.** All fictional. Super Valle, Mercado Norte, CADI Central, Costa Fresca, Grupo Horeca Bajío.
7. **Now.** Frozen at `2026-10-20T14:30:00-06:00` so screenshots stay still.
8. **Carta Porte.** We generate a data sheet. Siconet stamps the CFDI. Complemento version assumed 3.1 until the technical notes land.
9. **Freshness.** USDA HB66 temperatures and a Q10 of 2.5. Formula shown in the UI and labelled as inference.
10. **Product name.** UI says **Norfront Fresh**, tenant **Austral Trading (demo)**. Both are config.

Do not put real Austral records in this repo or into any model.
