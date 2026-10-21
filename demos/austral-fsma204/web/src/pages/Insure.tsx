import { useEffect, useState } from "react";
import { copy } from "../i18n/copy";
type T = (typeof copy)["es"];

export function Insure({ t }: { t: T }) {
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    fetch("/api/insurance").then((r) => r.json()).then(setD);
  }, []);
  if (!d) return null;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">{t.insure}</h1>
      <p className="text-xs text-black/50">{d.disclaimer}</p>
      {d.lines.map((l: any) => (
        <div key={l.label} className="rounded-2xl border border-black/10 bg-white p-3">
          <div className="font-medium">{l.label}</div>
          <div className="text-sm text-black/60">{l.note} {l.usd ? `· USD ${l.usd.toLocaleString()}` : ""}</div>
        </div>
      ))}
      <div className="rounded-2xl bg-ink p-4 text-white">
        <div className="text-xs text-mint">demo</div>
        <div className="text-2xl font-semibold">USD {d.calculator.total_demo_usd.toLocaleString()}</div>
        <p className="text-sm opacity-70">{d.calculator.note}</p>
      </div>
    </div>
  );
}
