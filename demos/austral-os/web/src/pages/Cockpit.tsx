import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, mxn } from "../api";

type Alert = { id: string; severity: string; kind: string; title: string; href?: string; qty?: number; shift?: string; segment?: string };
type CockpitData = {
  truth_score: number;
  truth_note: string;
  value_at_risk_72h_mxn: number;
  missing_boxes: number;
  missing_value_mxn: number;
  missing: { summary: string; lot_id: string; qty: number; segment: string; shift: string }[];
  at_risk_pallets: number;
  temps: { id: string; name: string; set: number; current: number }[];
  ship_first: { sku: string; remaining_days: number; band: string; qty: number; zone: string }[];
  alerts: Alert[];
  watermark: string;
};

export function Cockpit() {
  const [d, setD] = useState<CockpitData | null>(null);
  useEffect(() => {
    api<CockpitData>("/api/cockpit").then(setD);
  }, []);
  if (!d) return <p className="text-sm text-black/50">Cargando cabina…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">La verdad del almacén</h1>
        <p className="mt-1 text-sm text-black/55">Lo que hay, dónde, de qué lote, qué tan fresco y qué sale primero.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-4">
        <Stat label="Score de verdad" value={`${d.truth_score}`} hint={d.truth_note} />
        <Stat label="Valor en riesgo 72 h" value={mxn(d.value_at_risk_72h_mxn)} hint={`${d.at_risk_pallets} pallets en banda crítica o de riesgo`} />
        <Stat
          label="Cajas faltantes"
          value={String(d.missing_boxes)}
          hint={`${mxn(d.missing_value_mxn)} · atribuidas a un segmento`}
          accent
        />
        <Stat label="Alertas abiertas" value={String(d.alerts.length)} hint="De la alerta a la evidencia, dos clics" />
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-black/50">Temperaturas</h2>
        <div className="grid gap-2 md:grid-cols-4">
          {d.temps.map((t) => {
            const hot = Math.abs(t.current - t.set) >= 3;
            return (
              <div key={t.id} className={`rounded-2xl border p-3 ${hot ? "border-ink bg-ink text-white" : "border-black/10 bg-white"}`}>
                <div className="text-xs opacity-60">{t.name}</div>
                <div className="text-2xl font-semibold">
                  {t.current}° <span className="text-sm font-normal opacity-60">set {t.set}°</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-black/10 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-black/50">Faltantes</h2>
            <Link to="/perdidas" className="text-xs underline">
              Ver cadena
            </Link>
          </div>
          <ul className="space-y-2">
            {d.missing.map((m, i) => (
              <li key={i}>
                <Link to={`/perdidas?lot=${m.lot_id}`} className="block rounded-xl bg-paper px-3 py-2 hover:bg-warm">
                  <div className="text-sm font-medium">{m.summary}</div>
                  <div className="text-[11px] text-black/50">
                    {m.qty} cajas · {m.segment} · turno {m.shift}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        </section>
        <section className="rounded-2xl border border-black/10 bg-white p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-black/50">Sale primero</h2>
            <Link to="/embarcar" className="text-xs underline">
              FEFO y pedidos
            </Link>
          </div>
          <ul className="space-y-2">
            {d.ship_first.map((s, i) => (
              <li key={i} className="flex items-center justify-between rounded-xl bg-paper px-3 py-2">
                <div>
                  <div className="text-sm font-medium">{s.sku}</div>
                  <div className="text-[11px] text-black/50">
                    {s.zone} · {s.qty} cajas
                  </div>
                </div>
                <Band band={s.band} days={s.remaining_days} />
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wider text-black/50">Alertas</h2>
        <div className="grid gap-2 md:grid-cols-2">
          {d.alerts.map((a) => (
            <Link
              key={a.id}
              to={a.href || "/"}
              className="rounded-2xl border border-black/10 bg-white p-3 hover:border-ink"
            >
              <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider">
                <span className={`h-2 w-2 rounded-full ${a.severity === "alta" ? "bg-ink" : "bg-mint"}`} />
                {a.kind} {a.shift ? `· ${a.shift}` : ""}
              </div>
              <div className="mt-1 text-sm">{a.title}</div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value, hint, accent }: { label: string; value: string; hint: string; accent?: boolean }) {
  return (
    <div className={`rounded-2xl border p-4 ${accent ? "border-ink bg-ink text-white" : "border-black/10 bg-white"}`}>
      <div className="text-[11px] uppercase tracking-wider opacity-60">{label}</div>
      <div className="mt-1 text-3xl font-semibold tracking-tight">{value}</div>
      <div className="mt-1 text-xs opacity-60">{hint}</div>
    </div>
  );
}

export function Band({ band, days }: { band: string; days: number }) {
  const colors: Record<string, string> = {
    critico: "bg-ink text-white",
    riesgo: "bg-ink/80 text-white",
    vigilar: "bg-warm text-ink",
    ok: "bg-mint/40 text-ink",
  };
  return <span className={`rounded-full px-2 py-0.5 text-[11px] ${colors[band] || "bg-black/10"}`}>{days.toFixed(1)} d · {band}</span>;
}
