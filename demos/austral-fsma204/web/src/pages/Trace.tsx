import { useEffect, useState } from "react";
import { copy } from "../i18n/copy";

type T = (typeof copy)["es"];

export function Trace({ t }: { t: T }) {
  const [lots, setLots] = useState<any[]>([]);
  const [id, setId] = useState("LOT-TOM-OK");
  const [tr, setTr] = useState<any>(null);
  useEffect(() => {
    fetch("/api/lots").then((r) => r.json()).then((d) => setLots(d.lots));
  }, []);
  useEffect(() => {
    fetch(`/api/trace/${id}`).then((r) => r.json()).then(setTr);
  }, [id]);
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">{t.trace}</h1>
      <select className="rounded-full border border-black/15 bg-white px-3 py-2 text-sm" value={id} onChange={(e) => setId(e.target.value)}>
        {lots.map((l) => (
          <option key={l.id} value={l.id}>{l.name_es} · {l.tlc}</option>
        ))}
      </select>
      {tr && (
        <div className="rounded-2xl border border-black/10 bg-white p-4">
          <div className="text-xs text-black/45">{tr.elapsed_ms} ms</div>
          <h2 className="text-xl font-semibold">{tr.lot.name_es} · {tr.lot.tlc}</h2>
          <p className="text-sm">{tr.lot.ranch} / {tr.lot.field} · cosecha {tr.lot.harvest_date}</p>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="rounded-xl bg-paper p-2"><div className="text-lg font-semibold">{tr.mass_balance.cases_packed}</div>packed</div>
            <div className="rounded-xl bg-paper p-2"><div className="text-lg font-semibold">{tr.mass_balance.cases_shipped}</div>shipped</div>
            <div className="rounded-xl bg-paper p-2"><div className="text-lg font-semibold">{tr.mass_balance.delta}</div>delta</div>
          </div>
          <ol className="mt-4 space-y-1 text-sm">
            {tr.records.map((r: any) => (
              <li key={r.id}>{r.cte} · {r.complete ? "ok" : "gap"}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
