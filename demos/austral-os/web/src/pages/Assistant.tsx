import { useState } from "react";
import { api } from "../api";

const SUGGESTIONS = ["¿qué vence esta semana?", "¿qué se perdió anoche?", "¿cuánto hay de cereza?", "¿qué está retenido?"];

export function Assistant() {
  const [q, setQ] = useState("");
  const [a, setA] = useState<any>(null);
  async function ask(text: string) {
    setQ(text);
    setA(await api<any>("/api/ask", { method: "POST", body: JSON.stringify({ q: text }) }));
  }
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Pregúntale a Austral</h1>
        <p className="text-sm text-black/55">Parser en el dispositivo. Sin modelo externo, sin red.</p>
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(q);
        }}
        className="flex gap-2"
      >
        <input className="flex-1 rounded-full border border-black/15 bg-white px-4 py-3" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Escribe en español…" />
        <button className="rounded-full bg-ink px-4 text-sm text-white">Preguntar</button>
      </form>
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => ask(s)} className="rounded-full bg-white px-3 py-1 text-xs ring-1 ring-black/10">
            {s}
          </button>
        ))}
      </div>
      {a && (
        <div className="rounded-2xl border border-black/10 bg-white p-4">
          <div className="text-xs text-black/45">
            {a.engine} · {a.intent} → {a.route}
          </div>
          <h2 className="text-lg font-semibold">{a.label}</h2>
          <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(a.items ?? a, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
