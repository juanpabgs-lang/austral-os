import { useState } from "react";

const STEPS = [
  {
    t: "Importar Siconet y Excel",
    d: "Tres archivos: existencias, pedidos, órdenes de compra. El conector mapea columnas. Nada de Austral real entra aquí — esto es el ensayo.",
  },
  {
    t: "Conteo inicial por cámara",
    d: "Cada pallet existente recibe un SSCC y una posición. Cámara 1, 2, 3, andén. Un turno. El score de verdad arranca cuando el conteo cierra.",
  },
  {
    t: "Primer turno en vivo",
    d: "Recibir, acomodar, surtir. Offline en cámara, sync en el andén. Las reglas del dueño ya están prendidas.",
  },
];

export function GoLive() {
  const [i, setI] = useState(0);
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">¿Qué tan rápido se prende?</h1>
        <p className="text-sm text-black/55">Tres pasos. Hardware y etiquetas están en el plan de arranque del informe.</p>
      </div>
      <ol className="space-y-3">
        {STEPS.map((s, idx) => (
          <li
            key={s.t}
            className={`rounded-2xl border p-4 ${idx === i ? "border-ink bg-ink text-white" : "border-black/10 bg-white"}`}
          >
            <div className="text-xs uppercase tracking-wider opacity-60">Paso {idx + 1}</div>
            <div className="text-xl font-semibold">{s.t}</div>
            <p className="mt-1 text-sm opacity-80">{s.d}</p>
          </li>
        ))}
      </ol>
      <div className="flex gap-2">
        <button className="rounded-full border border-black/15 px-4 py-2 text-sm" onClick={() => setI(Math.max(0, i - 1))}>
          Atrás
        </button>
        <button className="rounded-full bg-mint px-4 py-2 text-sm text-ink" onClick={() => setI(Math.min(2, i + 1))}>
          Siguiente
        </button>
      </div>
    </div>
  );
}
