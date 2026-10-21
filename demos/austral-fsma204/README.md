# Norfront Fresh · FSMA 204 packer demo

Fictional Sinaloa packer. English and Spanish. Ports **5177 / 8017**. Synthetic data.

The cheapest insurance policy: lot codes at packing, a gate that will not release a truck with missing KDEs, and the FDA sortable spreadsheet on demand.

## Run

```bash
./start.sh
# http://127.0.0.1:5177
```

## Present (5 minutes)

1. Readiness: countdown to 20 Jul 2028, planted gaps.
2. Packing station: try to print without a field name — blocked. Fill the field — PTI + VPC + SSCC.
3. Gate: tomato truck with no field name is held. Fix inline. Release sends PDF/CSV/EPCIS.
4. Trace the good Roma lot in milliseconds.
5. Download the FDA sheet. One-click mock recall (EN/ES letters + mass balance).
6. Plan §1.1315, buyer pack, insurance calculator (cited, labelled).

## Acceptance

`cd api && pytest -q` proves the KDE table, every planted gap, gate 409, GS1 check digits, stable VPC, non-FTL grapes do not block, and a fix-then-release path.

`node scripts/check-i18n.mjs` proves ES/EN key parity.
