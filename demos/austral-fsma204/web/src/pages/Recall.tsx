import { useState } from "react";
import { copy } from "../i18n/copy";
type T = (typeof copy)["es"];

export function Recall({ t }: { t: T }) {
  const [d, setD] = useState<any>(null);
  async function run() {
    setD(await (await fetch("/api/recall/LOT-TOM-OK")).json());
  }
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">{t.recall}</h1>
      <button onClick={run} className="rounded-full bg-mint px-4 py-2 text-sm font-semibold text-ink">{t.mock}</button>
      {d && (
        <div className="space-y-3">
          <p className="text-sm">{d.letters.es}</p>
          <p className="text-sm text-black/60">{d.letters.en}</p>
          <pre className="rounded-2xl bg-white p-3 text-xs">{JSON.stringify(d.audit, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
