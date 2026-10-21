import { useEffect, useState } from "react";
import { api } from "../api";

export function Connector() {
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    api<any>("/api/connector").then(setD);
  }, []);
  if (!d) return null;
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Encima de Siconet y Excel</h1>
        <p className="text-sm text-black/55">{d.note}</p>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {d.files.map((f: any) => (
          <article key={f.name} className="rounded-2xl border border-black/10 bg-white p-4">
            <div className="text-xs text-black/45">{f.status} · {f.rows} filas</div>
            <h2 className="font-semibold">{f.name}</h2>
            <p className="mt-2 text-xs text-black/55">{f.columns.join(" · ")}</p>
          </article>
        ))}
      </div>
      <p className="text-sm">
        Sin mapear todavía: {d.unmapped.join(", ")}. {d.assumption}
      </p>
    </div>
  );
}
