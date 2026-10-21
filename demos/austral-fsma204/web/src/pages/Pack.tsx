import { useState } from "react";
import { copy } from "../i18n/copy";

type T = (typeof copy)["es"];

export function Pack({ t }: { t: T }) {
  const [field, setField] = useState("");
  const [out, setOut] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function print() {
    setErr(null);
    const r = await fetch("/api/pack", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: "PR-TOM",
        ranch: "Rancho Azul",
        field,
        harvest_date: "2026-10-20",
        qty_cases: 40,
      }),
    });
    const j = await r.json();
    if (!r.ok) {
      setErr(j.detail?.message || t.gateBlock);
      setOut(null);
      return;
    }
    setOut(j);
  }

  return (
    <div className="mx-auto max-w-md space-y-4">
      <h1 className="text-2xl font-semibold">{t.pack}</h1>
      <p className="text-sm text-black/55">Offline-first. Sin predio no hay etiqueta PTI.</p>
      <input className="tap-xl w-full rounded-2xl border border-black/15 bg-white px-4" placeholder="Predio / field name" value={field} onChange={(e) => setField(e.target.value)} />
      <button onClick={print} className="tap-xl w-full rounded-2xl bg-mint text-base font-semibold text-ink">
        {t.pack} · PTI + SSCC
      </button>
      {err && <p className="rounded-xl bg-ink p-3 text-sm text-white">{err}</p>}
      {out && (
        <div className="rounded-2xl border-2 border-ink bg-white p-4 font-mono text-sm">
          <div className="text-xs uppercase tracking-wider">PTI case label</div>
          <div className="text-lg font-semibold">{out.label.product_es}</div>
          <div>GTIN {out.label.gtin}</div>
          <div>LOT {out.label.lot}</div>
          <div>
            VPC {out.label.vpc.large}
            <sup>{out.label.vpc.small}</sup> · {out.label.vpc.algorithm}
          </div>
          <div>SSCC {out.sscc}</div>
        </div>
      )}
    </div>
  );
}
