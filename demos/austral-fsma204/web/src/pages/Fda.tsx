import { copy } from "../i18n/copy";
type T = (typeof copy)["es"];

export function Fda({ t }: { t: T }) {
  return (
    <div className="space-y-4">
      <h1 className="text-3xl font-semibold">{t.fda}</h1>
      <p className="text-sm text-black/55">21 CFR 1.1455 · hoja ordenable en 24 horas. Plantilla de demostración.</p>
      <a
        className="inline-block rounded-full bg-ink px-4 py-2 text-sm text-white"
        href={import.meta.env.VITE_STATIC === "1" ? `${import.meta.env.BASE_URL}files/fda/LOT-TOM-OK.xlsx` : "/api/fda-sheet/LOT-TOM-OK"}
      >
        Descargar / Download · LOT-TOM-OK
      </a>
      <a
        className="ml-2 inline-block rounded-full border border-black/15 px-4 py-2 text-sm"
        href={import.meta.env.VITE_STATIC === "1" ? `${import.meta.env.BASE_URL}files/epcis/LOT-TOM-OK.json` : "/api/epcis/LOT-TOM-OK"}
        target="_blank"
      >
        EPCIS 2.0
      </a>
    </div>
  );
}
