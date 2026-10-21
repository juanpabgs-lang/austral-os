import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api";

type Gap = { segment: string; kind: string; qty: number; shift?: string; summary: string; lot_id: string; value_mxn?: number; sku_name?: string };
type Signal = { label: string; review: string; staff_name: string; shift: string; qty: number; gap_count: number; segments: string[] };

export function Losses({ privateView }: { privateView: boolean }) {
  const [params] = useSearchParams();
  const lot = params.get("lot");
  const [gaps, setGaps] = useState<Gap[]>([]);
  const [signals, setSignals] = useState<Signal[] | null>(null);
  const [detail, setDetail] = useState<{ chain: Record<string, number>; events: { ts: string; event_type: string; qty_boxes: number; zone_id: string; shift: string }[]; lot: { lot_code: string; sku_name: string; variety: string } } | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const q = privateView ? "/api/losses?private=true" : "/api/losses";
    api<{ gaps: Gap[]; signals?: Signal[] }>(q)
      .then((d) => {
        setGaps(d.gaps);
        setSignals(d.signals || null);
      })
      .catch((e) => setErr(String(e.message)));
  }, [privateView]);

  useEffect(() => {
    if (!lot) return;
    api<NonNullable<typeof detail>>(`/api/losses/${lot}`).then(setDetail);
  }, [lot]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">{privateView ? "Vista privada del dueño" : "Dónde se pierde"}</h1>
        <p className="text-sm text-black/55">
          {privateView
            ? "Señal, no acusación. Toda atribución a una persona exige revisión humana."
            : "PO → recibido → almacenado → surtido → cargado → entregado. Segmento, turno y zona. Proceso, no persona."}
        </p>
      </div>
      {err && <p className="rounded-xl bg-ink px-3 py-2 text-sm text-white">{err}</p>}
      {privateView && signals && (
        <div className="grid gap-3 md:grid-cols-2">
          {signals.map((s) => (
            <div key={s.staff_name} className="rounded-2xl border border-black/10 bg-white p-4">
              <div className="text-[11px] uppercase tracking-wider text-black/45">{s.label}</div>
              <div className="text-lg font-semibold">{s.staff_name}</div>
              <div className="text-sm text-black/60">
                {s.qty} cajas en {s.gap_count} huecos · turno {s.shift} · {s.segments.join(", ")}
              </div>
              <div className="mt-2 text-xs text-black/50">{s.review}</div>
            </div>
          ))}
        </div>
      )}
      <div className="grid gap-6 lg:grid-cols-2">
        <ul className="space-y-2">
          {gaps.map((g, i) => (
            <li key={i}>
              <a href={`/perdidas?lot=${g.lot_id}`} className="block rounded-2xl border border-black/10 bg-white p-3 hover:border-ink">
                <div className="text-[11px] uppercase tracking-wider text-black/45">
                  {g.kind} · {g.segment} · {g.shift}
                </div>
                <div className="text-sm font-medium">{g.summary}</div>
                <div className="text-xs text-black/50">
                  {g.sku_name} · {g.qty} cajas
                </div>
              </a>
            </li>
          ))}
        </ul>
        {detail && (
          <article className="rounded-2xl border border-black/10 bg-white p-4">
            <div className="text-xs text-black/45">Cadena de custodia</div>
            <h2 className="text-xl font-semibold">
              {detail.lot.sku_name} {detail.lot.variety} · {detail.lot.lot_code}
            </h2>
            <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
              {Object.entries(detail.chain).map(([k, v]) => (
                <div key={k} className="rounded-xl bg-paper p-2">
                  <div className="text-lg font-semibold">{v}</div>
                  <div className="text-black/50">{k}</div>
                </div>
              ))}
            </div>
            <ol className="mt-4 space-y-1 text-sm">
              {detail.events.map((e, i) => (
                <li key={i} className="flex justify-between gap-3 border-b border-black/5 py-1">
                  <span>
                    {e.event_type} · {e.zone_id || "—"} · {e.shift}
                  </span>
                  <span className="text-black/50">
                    {e.qty_boxes ?? ""} · {e.ts.slice(5, 16).replace("T", " ")}
                  </span>
                </li>
              ))}
            </ol>
          </article>
        )}
      </div>
    </div>
  );
}
