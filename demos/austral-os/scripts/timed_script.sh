#!/usr/bin/env bash
# Timed owner script against a running API (no browser).
set -euo pipefail
base=http://127.0.0.1:8016
t0=$(date +%s%3N)
curl -sf "$base/api/cockpit" >/tmp/cockpit.json
curl -sf "$base/api/losses/LOT-CER-0918" >/tmp/cer.json
curl -sf "$base/api/trace/LOT-CER-0918" >/tmp/traza.json
t1=$(date +%s%3N)
python3 - <<'PY'
import json
c=json.load(open("/tmp/cockpit.json"))
l=json.load(open("/tmp/cer.json"))
t=json.load(open("/tmp/traza.json"))
assert c["missing_boxes"] >= 12
assert any(g.get("segment")=="anden_a_camara" for g in l["gaps"])
assert t["elapsed_ms"] < 1000
print("owner script API path ok", "missing", c["missing_boxes"], "var", c["value_at_risk_72h_mxn"], "trace_ms", t["elapsed_ms"])
PY
echo "wall_ms $((t1-t0))"
# hold must 409
code=$(curl -s -o /tmp/hold.json -w "%{http_code}" -X POST "$base/api/events" -H "Content-Type: application/json" -d '{"event_type":"pick","pallet_id":"PAL-FRE-H","qty_boxes":4}')
test "$code" = "409"
echo "hold 409 ok"
