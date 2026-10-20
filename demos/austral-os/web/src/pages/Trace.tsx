import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";

type Lot = { id: string; lot_code: string; sku_name: string; variety: string };

export function Trace() {
  const [params, setParams] = useSearchParams();
  const [lots, setLots] = useState<Lot[]>([]);
  const [lotId, setLotId] = useState(params.get("lot") || "LOT-CER-0918");
  const [tr, setTr] = useState<any>(null);
  const [fsma, setFsma] = useState<any>(null);

  useEffect(() => {
    api<{ lots: Lot[] }>("/api/lots").then((d) => setLots(d.lots));
  }, []);
  useEffect(() => {
    if (!lotId) return;
    setParams({ lot: lotId });
    api(`/api/trace/${lotId}`).then(setTr);
    api(`/api/fsma/${lotId}`).then(setFsma);
  }, [lotId]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Traza y recall</h1>
        <p className="text-sm text-black/55">Atrás y adelante sobre el mismo libro. La hoja FDA y el EPCIS salen de aquí.</p>
      </div>
      <select className="rounded-full border border-black/15 bg-white px-3 py-2 text-sm" value={lotId} onChange={(e) => setLotId(e.target.value)}>
        {lots.map((l) => (
          <option key={l.id} value={l.id}>
            {l.sku_name} {l.variety} · {l.lot_code}
          </option>
        ))}
      </select>
      {tr && (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border border-black/10 bg-white p-4 lg:col-span-2">
            <div className="text-xs text-black/45">{tr.elapsed_ms} ms</div>
            <h2 className="text-xl font-semibold">
              {tr.lot.sku_name} {tr.lot.variety}
            </h2>
            <p className="text-sm text-black/55">
              Origen {tr.lot.origin} · TLC {tr.lot.lot_code} · fuente {tr.lot.tlc_source}
            </p>
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-xs uppercase tracking-wider text-black/45">Atrás</h3>
                {tr.backward.map((b: any, i: number) => (
                  <p key={i} className="mt-1 text-sm">
                    {b.value} · cosecha {b.harvest} · empaque {b.pack}
                  </p>
                ))}
              </div>
              <div>
                <h3 className="text-xs uppercase tracking-wider text-black/45">Adelante</h3>
                {tr.forward.length === 0 && <p className="text-sm text-black/45">Sin salidas a cliente todavía.</p>}
                {tr.forward.map((f: any, i: number) => (
                  <p key={i} className="mt-1 text-sm">
                    {f.customer} · {f.qty} cajas · {f.event}
                  </p>
                ))}
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <a className="rounded-full bg-ink px-3 py-1.5 text-xs text-white" href={`/api/fda-sheet/${lotId}`}>
                Hoja FDA
              </a>
              <a className="rounded-full border border-black/15 px-3 py-1.5 text-xs" href={`/api/epcis/${lotId}`} target="_blank">
                EPCIS 2.0
              </a>
            </div>
          </div>
          <div className="rounded-2xl border border-black/10 bg-white p-4">
            <h3 className="text-xs uppercase tracking-wider text-black/45">Balance de masas</h3>
            {tr.mass_balance &&
              Object.entries(tr.mass_balance).map(([k, v]) => (
                <div key={k} className="mt-2 flex justify-between text-sm">
                  <span className="text-black/55">{k}</span>
                  <span className="font-medium">{String(v)}</span>
                </div>
              ))}
            {fsma && (
              <div className="mt-4">
                <h3 className="text-xs uppercase tracking-wider text-black/45">Vista FSMA 204</h3>
                <p className="mt-1 text-[11px] text-black/45">{fsma.disclaimer}</p>
                <ul className="mt-2 space-y-1 text-sm">
                  {fsma.kdes.map((k: any) => (
                    <li key={k.key} className="flex justify-between">
                      <span>{k.key}</span>
                      <span>{k.present ? "sí" : "falta"}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
