import { useEffect, useState } from "react";
import { copy } from "../i18n/copy";
type T = (typeof copy)["es"];

export function Buyer({ t }: { t: T }) {
  const [d, setD] = useState<any>(null);
  useEffect(() => {
    fetch("/api/buyer-pack").then((r) => r.json()).then(setD);
  }, []);
  if (!d) return null;
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">{t.buyer}</h1>
      <p className="text-sm text-black/55">{d.buyer}</p>
      <ul className="list-disc pl-5 text-sm">
        {d.items.map((i: string) => (
          <li key={i}>{i}</li>
        ))}
      </ul>
    </div>
  );
}
