import { NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  Bell,
  ClipboardList,
  LayoutDashboard,
  Map as MapIcon,
  PackageSearch,
  ScanLine,
  Scale,
  Settings2,
  Ship,
  Sparkles,
  FileSpreadsheet,
  Plug,
  Play,
  RotateCcw,
} from "lucide-react";
import { api, currentRole, setRole } from "./api";
import { Cockpit } from "./pages/Cockpit";
import { WarehouseMap } from "./pages/Map";
import { ShipFirst } from "./pages/ShipFirst";
import { Losses } from "./pages/Losses";
import { Trace } from "./pages/Trace";
import { Paperwork } from "./pages/Paperwork";
import { Available } from "./pages/Available";
import { Rules } from "./pages/Rules";
import { Captura } from "./pages/Captura";
import { Connector } from "./pages/Connector";
import { Assistant } from "./pages/Assistant";
import { GoLive } from "./pages/GoLive";

const NAV = [
  { to: "/", label: "Cabina", icon: LayoutDashboard },
  { to: "/mapa", label: "Mapa", icon: MapIcon },
  { to: "/embarcar", label: "Embarcar", icon: Ship },
  { to: "/perdidas", label: "Pérdidas", icon: Scale },
  { to: "/traza", label: "Traza", icon: PackageSearch },
  { to: "/disponible", label: "A la venta", icon: Bell },
  { to: "/papeleria", label: "Papelería", icon: ClipboardList },
  { to: "/captura", label: "Captura", icon: ScanLine },
  { to: "/reglas", label: "Reglas", icon: Settings2 },
  { to: "/arrancar", label: "Arrancar", icon: Play },
  { to: "/siconet", label: "Siconet", icon: Plug },
  { to: "/asistente", label: "Preguntar", icon: Sparkles },
];

type Meta = {
  tenant: string;
  product: string;
  watermark: string;
  now: string;
  roles: Record<string, string>;
};

type Step = { id: string; route: string; title: string; say: string };

export function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [role, setRoleState] = useState(currentRole());
  const [present, setPresent] = useState(false);
  const [steps, setSteps] = useState<Step[]>([]);
  const [step, setStep] = useState(0);
  const nav = useNavigate();
  const loc = useLocation();

  useEffect(() => {
    api<Meta>("/api/meta").then(setMeta);
    api<{ steps: Step[] }>("/api/presentation").then((d) => setSteps(d.steps));
  }, []);

  const handheld = loc.pathname.startsWith("/captura");

  function changeRole(r: string) {
    setRole(r);
    setRoleState(r);
  }

  async function resetDemo() {
    await api("/api/reset", { method: "POST" });
    window.location.href = "/";
  }

  function goStep(i: number) {
    const s = steps[i];
    if (!s) return;
    setStep(i);
    nav(s.route);
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="sticky top-0 z-30 border-b border-black/10 bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-ink text-mint grid place-items-center font-semibold">N</div>
            <div>
              <div className="text-sm font-semibold tracking-tight">{meta?.product ?? "Norfront Fresh"}</div>
              <div className="text-[11px] text-black/55">{meta?.tenant}</div>
            </div>
          </div>
          <div className="hidden items-center gap-2 text-[11px] text-black/50 md:flex">
            <span className="rounded-full bg-black/5 px-2 py-0.5">{meta?.watermark}</span>
            <span>ahora {meta?.now?.slice(0, 16).replace("T", " ")}</span>
          </div>
          <div className="flex items-center gap-2">
            <select
              className="rounded-full border border-black/15 bg-white px-3 py-1.5 text-xs"
              value={role}
              onChange={(e) => changeRole(e.target.value)}
            >
              {Object.entries(meta?.roles ?? { dueno: "Dueño" }).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
            <button
              onClick={() => {
                setPresent((p) => !p);
                if (!present && steps[0]) goStep(0);
              }}
              className="rounded-full border border-black/15 px-3 py-1.5 text-xs"
            >
              Presentar
            </button>
            <button onClick={resetDemo} className="inline-flex items-center gap-1 rounded-full bg-ink px-3 py-1.5 text-xs text-white">
              <RotateCcw size={12} /> Reiniciar demo
            </button>
          </div>
        </div>
        {!handheld && (
          <nav className="mx-auto flex max-w-[1400px] gap-1 overflow-x-auto px-3 pb-2">
            {NAV.map((n) => {
              const Icon = n.icon;
              return (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.to === "/"}
                  className={({ isActive }) =>
                    `flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1.5 text-xs ${
                      isActive ? "bg-ink text-white" : "text-black/70 hover:bg-black/5"
                    }`
                  }
                >
                  <Icon size={13} /> {n.label}
                </NavLink>
              );
            })}
            {role === "dueno" && (
              <NavLink
                to="/privado"
                className={({ isActive }) =>
                  `flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1.5 text-xs ${
                    isActive ? "bg-ink text-white" : "text-black/70 hover:bg-black/5"
                  }`
                }
              >
                <FileSpreadsheet size={13} /> Privado
              </NavLink>
            )}
          </nav>
        )}
      </header>

      <main className={`mx-auto ${handheld ? "max-w-md px-3 py-3" : "max-w-[1400px] px-4 py-6"}`}>
        <Routes>
          <Route path="/" element={<Cockpit />} />
          <Route path="/mapa" element={<WarehouseMap />} />
          <Route path="/embarcar" element={<ShipFirst />} />
          <Route path="/perdidas" element={<Losses privateView={false} />} />
          <Route path="/privado" element={<Losses privateView />} />
          <Route path="/traza" element={<Trace />} />
          <Route path="/papeleria" element={<Paperwork />} />
          <Route path="/disponible" element={<Available />} />
          <Route path="/reglas" element={<Rules role={role} />} />
          <Route path="/captura" element={<Captura />} />
          <Route path="/siconet" element={<Connector />} />
          <Route path="/asistente" element={<Assistant />} />
          <Route path="/arrancar" element={<GoLive />} />
        </Routes>
      </main>

      {present && steps[step] && (
        <div className="fixed bottom-4 left-1/2 z-40 w-[min(720px,92vw)] -translate-x-1/2 rounded-2xl border border-black/10 bg-ink p-4 text-white shadow-2xl">
          <div className="text-[11px] uppercase tracking-widest text-mint">
            Paso {step + 1} / {steps.length}
          </div>
          <div className="mt-1 text-lg font-semibold">{steps[step].title}</div>
          <p className="mt-1 text-sm text-white/75">{steps[step].say}</p>
          <div className="mt-3 flex justify-between">
            <button className="text-xs text-white/70" onClick={() => setPresent(false)}>
              Cerrar
            </button>
            <div className="flex gap-2">
              <button className="rounded-full bg-white/10 px-3 py-1 text-xs" disabled={step === 0} onClick={() => goStep(step - 1)}>
                Anterior
              </button>
              <button
                className="rounded-full bg-mint px-3 py-1 text-xs text-ink"
                onClick={() => goStep(Math.min(step + 1, steps.length - 1))}
              >
                Siguiente
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
