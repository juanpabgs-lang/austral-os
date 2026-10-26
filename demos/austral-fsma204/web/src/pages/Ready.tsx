import { useEffect, useState } from "react";
import { copy } from "../i18n/copy";

type T = (typeof copy)["es"];

export function Ready({ t }: { t: T }) {
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    fetch("/api/readiness").then((r) => r.json()).then(setD);
  }, []);
  if (!d) return null;
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-semibold tracking-tight">{t.ready}</h1>
      <p className="text-sm text-black/55">{t.cheapest}</p>
      <div className="grid gap-3 md:grid-cols-4">
        <Card n={d.days_to_compliance} l={t.countdown} dark />
        <Card n={d.blocked_trucks} l={t.blocked} />
        <Card n={d.gaps} l={t.gaps} />
        <Card n={d.complete} l={t.complete} />
      </div>
      <ul className="space-y-2">
        {d.planted.map((p: any) => (
          <li key={p.id} className="rounded-2xl border border-black/10 bg-white p-3">
            <div className="text-xs text-black/45">{p.cte} · {p.key || "FTL"}</div>
            <div className="font-medium">{p.title}</div>
            <p className="text-sm text-black/60">{p.notes}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Card({ n, l, dark }: { n: number; l: string; dark?: boolean }) {
  return (
    <div className={`rounded-2xl border p-4 ${dark ? "border-ink bg-ink text-white" : "border-black/10 bg-white"}`}>
      <div className="text-3xl font-semibold">{n}</div>
      <div className="text-xs opacity-60">{l}</div>
    </div>
  );
}
