import { useEffect, useState } from "react";
import { api } from "../api";

export function Rules({ role }: { role: string }) {
  const [data, setData] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    api<any>("/api/rules").then(setData);
  }, []);
  async function toggle(id: string, active: boolean) {
    setMsg(null);
    try {
      await api(`/api/rules/${id}`, { method: "POST", body: JSON.stringify({ active, actor_id: "ST-DUENO" }) });
      api<any>("/api/rules").then(setData);
      setMsg("Regla actualizada. Quedó en la bitácora.");
    } catch (e: any) {
      setMsg(e.message);
    }
  }
  if (!data) return null;
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Reglas y bitácora</h1>
        <p className="text-sm text-black/55">Ninguna regla de almacén cambia sin la aprobación del dueño.</p>
      </div>
      {msg && <p className="rounded-xl bg-warm px-3 py-2 text-sm">{msg}</p>}
      <div className="grid gap-3 md:grid-cols-2">
        {data.rules.map((r: any) => (
          <article key={r.id} className="rounded-2xl border border-black/10 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-xs text-black/45">{r.code} · v{r.version}</div>
                <h2 className="text-lg font-semibold">{r.title}</h2>
                <p className="mt-1 text-sm text-black/65">{r.body}</p>
              </div>
              <button
                disabled={role !== "dueno"}
                onClick={() => toggle(r.id, !r.active)}
                className={`rounded-full px-3 py-1 text-xs ${r.active ? "bg-mint text-ink" : "bg-black/10"} ${role !== "dueno" ? "opacity-50" : ""}`}
              >
                {r.active ? "activa" : "apagada"}
              </button>
            </div>
          </article>
        ))}
      </div>
      <section className="rounded-2xl border border-black/10 bg-white p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-black/50">Bitácora</h2>
        <ul className="mt-2 max-h-72 space-y-1 overflow-auto text-sm">
          {data.audit.map((a: any) => (
            <li key={a.id} className="flex justify-between border-b border-black/5 py-1">
              <span>
                {a.action} · {a.entity} {a.entity_id}
              </span>
              <span className="text-black/45">{a.ts?.slice(5, 16)}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
