import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { copy, type Lang } from "./i18n/copy";
import { Ready } from "./pages/Ready";
import { Pack } from "./pages/Pack";
import { Gate } from "./pages/Gate";
import { Trace } from "./pages/Trace";
import { Fda } from "./pages/Fda";
import { Recall } from "./pages/Recall";
import { Plan } from "./pages/Plan";
import { Buyer } from "./pages/Buyer";
import { Insure } from "./pages/Insure";

export function App() {
  const [lang, setLang] = useState<Lang>((localStorage.getItem("nf-lang") as Lang) || "es");
  const t = copy[lang];
  const nav = useNavigate();
  const [steps, setSteps] = useState<{ id: string; route: string; title_es: string; title_en: string }[]>([]);
  const [present, setPresent] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    fetch("/api/presentation")
      .then((r) => r.json())
      .then((d) => setSteps(d.steps));
  }, []);

  const links = [
    ["/", t.ready],
    ["/empaque", t.pack],
    ["/anden", t.gate],
    ["/traza", t.trace],
    ["/fda", t.fda],
    ["/retiro", t.recall],
    ["/plan", t.plan],
    ["/comprador", t.buyer],
    ["/seguro", t.insure],
  ] as const;

  return (
    <div className="min-h-screen bg-paper">
      <header className="sticky top-0 z-20 border-b border-black/10 bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div>
            <div className="text-sm font-semibold">{t.product}</div>
            <div className="text-[11px] text-black/50">{t.tenant} · {t.watermark}</div>
          </div>
          <div className="flex gap-2">
            <button className="rounded-full border border-black/15 px-3 py-1 text-xs" onClick={() => { const n = lang === "es" ? "en" : "es"; setLang(n); localStorage.setItem("nf-lang", n); }}>
              {lang === "es" ? "EN" : "ES"}
            </button>
            <button className="rounded-full border border-black/15 px-3 py-1 text-xs" onClick={() => { setPresent(true); if (steps[0]) nav(steps[0].route); }}>
              {t.present}
            </button>
            <button className="rounded-full bg-ink px-3 py-1 text-xs text-white" onClick={async () => { await fetch("/api/reset", { method: "POST" }); location.assign(import.meta.env.BASE_URL); }}>
              {t.reset}
            </button>
          </div>
        </div>
        <nav className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-3 pb-2">
          {links.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `rounded-full px-3 py-1.5 text-xs ${isActive ? "bg-ink text-white" : "text-black/70"}`}>
              {label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Ready t={t} />} />
          <Route path="/empaque" element={<Pack t={t} />} />
          <Route path="/anden" element={<Gate t={t} />} />
          <Route path="/traza" element={<Trace t={t} />} />
          <Route path="/fda" element={<Fda t={t} />} />
          <Route path="/retiro" element={<Recall t={t} />} />
          <Route path="/plan" element={<Plan t={t} />} />
          <Route path="/comprador" element={<Buyer t={t} />} />
          <Route path="/seguro" element={<Insure t={t} />} />
        </Routes>
      </main>
      {present && steps[step] && (
        <div className="fixed bottom-4 left-1/2 w-[min(640px,92vw)] -translate-x-1/2 rounded-2xl bg-ink p-4 text-white">
          <div className="text-[11px] text-mint">{step + 1}/{steps.length}</div>
          <div className="font-semibold">{lang === "es" ? steps[step].title_es : steps[step].title_en}</div>
          <div className="mt-2 flex justify-end gap-2">
            <button className="text-xs" onClick={() => setPresent(false)}>×</button>
            <button className="rounded-full bg-mint px-3 py-1 text-xs text-ink" onClick={() => { const i = Math.min(step + 1, steps.length - 1); setStep(i); nav(steps[i].route); }}>→</button>
          </div>
        </div>
      )}
    </div>
  );
}
