import { useEffect, useState } from "react";
import { api, downloadHref } from "../api";

export function Paperwork() {
  const [docs, setDocs] = useState<any[]>([]);
  useEffect(() => {
    api<{ documents: any[] }>("/api/documents").then((d) => setDocs(d.documents));
  }, []);
  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">El papeleo se escribe solo</h1>
          <p className="text-sm text-black/55">Recepción, reclamo, remisión, Carta Porte, POD. Siconet timbra el CFDI; esto arma la hoja.</p>
        </div>
        <a className="rounded-full bg-ink px-3 py-2 text-xs text-white" href={downloadHref("/api/documents/siconet.csv", "files/siconet.csv")}>
          Exportar a Siconet
        </a>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {docs.map((d) => (
          <article key={d.id} className="rounded-2xl border border-black/10 bg-white p-4">
            <div className="text-[11px] uppercase tracking-wider text-black/45">{d.kind}</div>
            <h2 className="text-lg font-semibold">{d.title}</h2>
            <pre className="mt-2 overflow-auto text-xs text-black/70">{JSON.stringify(d.body, null, 2)}</pre>
          </article>
        ))}
      </div>
    </div>
  );
}
