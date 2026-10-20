import { useEffect, useState } from "react";
import { api, mxn } from "../api";

export function Available() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => {
    api<{ items: any[] }>("/api/available").then((d) => setItems(d.items));
  }, []);
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Disponible para vender</h1>
        <p className="text-sm text-black/55">Físico menos retenciones menos lo ya prometido. Cada cifra dice hace cuántas horas se verificó.</p>
      </div>
      <div className="overflow-auto rounded-2xl border border-black/10 bg-white">
        <table className="w-full text-left text-sm">
          <thead className="text-[11px] uppercase tracking-wider text-black/45">
            <tr>
              <th className="px-3 py-2">Producto</th>
              <th>Físico</th>
              <th>Retenido</th>
              <th>Asignado</th>
              <th>A la venta</th>
              <th>Valor</th>
              <th>Verificado</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.sku_id} className="border-t border-black/5">
                <td className="px-3 py-2 font-medium">
                  {r.sku_name} {r.variety}
                </td>
                <td>{r.physical}</td>
                <td>{r.on_hold}</td>
                <td>{r.allocated}</td>
                <td className="font-semibold">{r.available}</td>
                <td>{mxn(r.value_mxn)}</td>
                <td className="text-xs text-black/50">hace {r.verified_hours_ago ?? "—"} h</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
