import { useEffect, useState } from "react";
import { copy } from "../i18n/copy";

type T = (typeof copy)["es"];

export function Gate({ t }: { t: T }) {
  const [ships, setShips] = useState<any[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const load = () => fetch("/api/shipments").then((r) => r.json()).then((d) => setShips(d.shipments));
  useEffect(() => {
    load();
  }, []);

  async function release(id: string) {
    const r = await fetch("/api/gate/release", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ shipment_id: id }) });
    const j = await r.json();
    if (!r.ok) {
      setMsg(`${t.gateBlock}: ${(j.detail?.gaps || []).map((g: any) => g.label).join(" · ")}`);
    } else {
      setMsg(t.gateOk);
    }
    load();
  }

  async function fix(lotId: string, cte: string, key: string) {
    await fetch("/api/records/fix", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lot_id: lotId, cte, key, value: key === "cool_date" ? "2026-10-17" : key === "tlc_source" ? "Empaque Río Mocorito" : "Lote 12-Norte" }),
    });
    load();
    setMsg(t.fix);
  }

  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">{t.gate}</h1>
      {msg && <p className="rounded-xl bg-warm bg-black/5 p-3 text-sm">{msg}</p>}
      {ships.map((s) => (
        <article key={s.id} className="rounded-2xl border border-black/10 bg-white p-4">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-xs text-black/45">{s.id} · {s.ftl ? "FTL" : "fuera de FTL"}</div>
              <div className="text-lg font-semibold">{s.name_es} → {s.to_party}</div>
              <div className="text-sm text-black/55">{s.qty} cajas · {s.tlc}</div>
            </div>
            <span className={`rounded-full px-2 py-0.5 text-[11px] ${s.released ? "bg-mint/50" : "bg-ink text-white"}`}>
              {s.released ? t.gateOk : t.gateBlock}
            </span>
          </div>
          {!!s.gaps?.length && (
            <ul className="mt-2 text-sm">
              {s.gaps.map((g: any, i: number) => (
                <li key={i} className="flex items-center justify-between">
                  <span>{g.label} · {g.cite}</span>
                  <button className="text-xs underline" onClick={() => fix(s.lot_id, g.cte, g.key)}>
                    {t.fix}
                  </button>
                </li>
              ))}
            </ul>
          )}
          <button onClick={() => release(s.id)} className="mt-3 rounded-full bg-ink px-3 py-1.5 text-xs text-white">
            Release
          </button>
        </article>
      ))}
    </div>
  );
}
