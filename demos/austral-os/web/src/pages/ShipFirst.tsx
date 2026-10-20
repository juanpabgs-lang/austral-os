import { useEffect, useState } from "react";
import { api } from "../api";
import { Band } from "./Cockpit";

type Match = {
  order: { id: string; customer: string; qty_boxes: number; min_shelf_days: number; due_date: string; notes: string };
  allocated: { pallet_id: string; lot_code: string; qty: number; remaining_days: number; band: string; reason: string; zone_name: string; position_code: string }[];
  rejected: { reason: string; remaining_days: number }[];
  short_by: number;
  ok: boolean;
};

export function ShipFirst() {
  const [data, setData] = useState<{ matches: Match[]; pick_route: { order_id: string; customer: string; position_code: string; zone_name: string; qty: number; lot_code: string }[]; formula: string } | null>(null);
  useEffect(() => {
    api<NonNullable<typeof data>>("/api/ship-first").then(setData);
  }, []);
  if (!data) return <p className="text-sm text-black/50">Calculando FEFO…</p>;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Qué sale primero</h1>
        <p className="text-sm text-black/55">Lotes en riesgo emparejados a pedidos según la vida mínima del cliente. {data.formula}</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {data.matches.map((m) => (
          <article key={m.order.id} className="rounded-2xl border border-black/10 bg-white p-4">
            <div className="flex items-start justify-between">
              <div>
                <div className="text-xs text-black/45">{m.order.id} · entrega {m.order.due_date}</div>
                <div className="text-lg font-semibold">{m.order.customer}</div>
                <div className="text-sm text-black/60">
                  {m.order.qty_boxes} cajas · mínimo {m.order.min_shelf_days} días
                </div>
              </div>
              <span className={`rounded-full px-2 py-0.5 text-[11px] ${m.ok ? "bg-mint/50" : "bg-ink text-white"}`}>
                {m.ok ? "cubierto" : `faltan ${m.short_by}`}
              </span>
            </div>
            {m.order.notes && <p className="mt-2 text-xs text-black/50">{m.order.notes}</p>}
            <ul className="mt-3 space-y-2">
              {m.allocated.map((a) => (
                <li key={a.pallet_id} className="rounded-xl bg-paper px-3 py-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{a.lot_code} · {a.qty} cjs</span>
                    <Band band={a.band} days={a.remaining_days} />
                  </div>
                  <div className="text-[11px] text-black/50">
                    {a.zone_name} {a.position_code} · {a.reason}
                  </div>
                </li>
              ))}
              {m.rejected.slice(0, 2).map((r, i) => (
                <li key={i} className="text-[11px] text-black/45">
                  Rechazado: {r.reason}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
      <section className="rounded-2xl border border-black/10 bg-white p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-black/50">Lista de surtido con ruta</h2>
        <ol className="mt-3 space-y-1">
          {data.pick_route.map((s, i) => (
            <li key={i} className="flex gap-3 text-sm">
              <span className="w-6 font-semibold">{i + 1}</span>
              <span>
                {s.zone_name} {s.position_code} · {s.lot_code} · {s.qty} cjs → {s.customer}
              </span>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
