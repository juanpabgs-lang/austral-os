import { useEffect, useState } from "react";
import { api } from "../api";
import { Band } from "./Cockpit";

type Zone = { id: string; name: string; kind: string; x: number; y: number; w: number; h: number; temp_current_c: number; site_id: string };
type Pallet = {
  id: string;
  sscc: string;
  sku: string;
  lot_code: string;
  qty: number;
  zone_id: string;
  x: number | null;
  y: number | null;
  band: string;
  remaining_days: number;
  hold: string;
  hold_reason: string | null;
  position_code?: string;
  site_id: string;
};

export function WarehouseMap() {
  const [data, setData] = useState<{ zones: Zone[]; pallets: Pallet[] } | null>(null);
  const [sel, setSel] = useState<Pallet | null>(null);
  const [route, setRoute] = useState<{ x: number; y: number }[]>([]);
  useEffect(() => {
    api<{ zones: Zone[]; pallets: Pallet[] }>("/api/map").then(setData);
    api<{ pick_route: { position_code?: string; zone_id: string }[] }>("/api/ship-first").then((d) => {
      // route overlay fetched with map coords after both load — handled below
      void d;
    });
  }, []);
  useEffect(() => {
    if (!data) return;
    api<{ pick_route: { pallet_id: string }[] }>("/api/ship-first").then((d) => {
      const pts = d.pick_route
        .map((s) => data.pallets.find((p) => p.id === s.pallet_id))
        .filter((p): p is Pallet => !!p && p.x != null && p.y != null)
        .map((p) => ({ x: p.x as number, y: p.y as number }));
      setRoute(pts);
    });
  }, [data]);
  if (!data) return <p className="text-sm text-black/50">Cargando mapa…</p>;
  const zones = data.zones.filter((z) => z.site_id === "CEDIS-MEX");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Mapa en vivo</h1>
        <p className="text-sm text-black/55">Color por frescura. La línea es la ruta FEFO del turno.</p>
      </div>
      <div className="overflow-auto rounded-2xl border border-black/10 bg-white p-4">
        <svg viewBox="0 0 700 400" className="h-[520px] w-full min-w-[700px]">
          {zones.map((z) => (
            <g key={z.id}>
              <rect x={z.x} y={z.y} width={z.w} height={z.h} rx={12} fill="#F1F1F1" stroke="#111" strokeOpacity={0.15} />
              <text x={z.x + 10} y={z.y + 18} fontSize={10} fill="#111" fillOpacity={0.55}>
                {z.name} · {z.temp_current_c}°C
              </text>
            </g>
          ))}
          {route.length > 1 && (
            <polyline
              fill="none"
              stroke="#00FE99"
              strokeWidth={3}
              points={route.map((p) => `${p.x + 10},${p.y + 10}`).join(" ")}
            />
          )}
          {data.pallets
            .filter((p) => p.x != null)
            .map((p) => (
              <g key={p.id} onClick={() => setSel(p)} style={{ cursor: "pointer" }}>
                <rect
                  x={p.x as number}
                  y={p.y as number}
                  width={22}
                  height={18}
                  rx={4}
                  fill={p.hold !== "libre" ? "#111" : bandFill(p.band)}
                  stroke="#111"
                  strokeWidth={sel?.id === p.id ? 2 : 0.6}
                />
              </g>
            ))}
        </svg>
        <div className="mt-2 flex gap-3 text-[11px] text-black/55">
          <span className="inline-flex items-center gap-1"><i className="inline-block h-3 w-3 rounded-sm bg-[#00FE99]" /> ok</span>
          <span className="inline-flex items-center gap-1"><i className="inline-block h-3 w-3 rounded-sm bg-[#C4B89A]" /> vigilar</span>
          <span className="inline-flex items-center gap-1"><i className="inline-block h-3 w-3 rounded-sm bg-[#4A4A4A]" /> riesgo</span>
          <span className="inline-flex items-center gap-1"><i className="inline-block h-3 w-3 rounded-sm bg-[#111]" /> retención</span>
        </div>
      </div>
      {sel && (
        <div className="rounded-2xl border border-black/10 bg-white p-4">
          <div className="text-xs text-black/45">{sel.sscc}</div>
          <div className="text-lg font-semibold">{sel.sku}</div>
          <div className="mt-1 flex items-center gap-2 text-sm">
            <Band band={sel.band} days={sel.remaining_days} />
            <span>{sel.qty} cajas · {sel.position_code}</span>
          </div>
          {sel.hold !== "libre" && <p className="mt-2 text-sm">Retenido: {sel.hold_reason}</p>}
          <p className="mt-1 text-xs text-black/50">Lote {sel.lot_code}</p>
        </div>
      )}
    </div>
  );
}

function bandFill(band: string) {
  if (band === "ok") return "#00FE99";
  if (band === "vigilar") return "#C4B89A";
  if (band === "riesgo") return "#4A4A4A";
  return "#111111";
}
