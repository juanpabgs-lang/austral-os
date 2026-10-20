import { useEffect, useState } from "react";
import { copy } from "../i18n/copy";
type T = (typeof copy)["es"];

export function Plan({ t }: { t: T }) {
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    fetch("/api/plan").then((r) => r.json()).then(setD);
  }, []);
  if (!d) return null;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">{t.plan} · {d.cite}</h1>
      {d.sections.map((s: any) => (
        <article key={s.id} className="rounded-2xl border border-black/10 bg-white p-4">
          <h2 className="font-semibold">{s.title_es} / {s.title_en}</h2>
          <p className="text-sm text-black/65">{s.body}</p>
        </article>
      ))}
    </div>
  );
}
