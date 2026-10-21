import { useEffect, useState } from "react";
import Dexie from "dexie";
import { api } from "../api";

type OutboxRow = {
  id?: number;
  client_uuid: string;
  event_type: string;
  pallet_id?: string;
  qty_boxes?: number;
  zone_id?: string;
  payload: Record<string, unknown>;
  device_ts: string;
};

class Outbox extends Dexie {
  events!: Dexie.Table<OutboxRow, number>;
  constructor() {
    super("norfront-fresh-outbox");
    this.version(1).stores({ events: "++id,client_uuid" });
  }
}
const db = new Outbox();

const TASKS = [
  { id: "scan-cer", label: "Contar cereza Cámara 2", event_type: "count", pallet_id: "PAL-CER-B", zone_id: "Z-CAM2", qty_boxes: 54 },
  { id: "scan-fre", label: "Intentar surtir fresa retenida", event_type: "pick", pallet_id: "PAL-FRE-H", zone_id: "Z-CAM2", qty_boxes: 4 },
  { id: "scan-lim", label: "Mover limón a Cámara 3", event_type: "move", pallet_id: "PAL-LIM-A", zone_id: "Z-CAM3", qty_boxes: 90 },
  { id: "scan-kiw", label: "Separar kiwi de manzana", event_type: "move", pallet_id: "PAL-KIW-A", zone_id: "Z-CAM2", qty_boxes: 70 },
];

export function Captura() {
  const [offline, setOffline] = useState(true);
  const [queue, setQueue] = useState<OutboxRow[]>([]);
  const [log, setLog] = useState<string[]>([]);
  const [scan, setScan] = useState("");

  async function refresh() {
    setQueue(await db.events.toArray());
  }
  useEffect(() => {
    refresh();
  }, []);

  async function enqueue(t: (typeof TASKS)[0]) {
    const row: OutboxRow = {
      client_uuid: crypto.randomUUID(),
      event_type: t.event_type,
      pallet_id: t.pallet_id,
      qty_boxes: t.qty_boxes,
      zone_id: t.zone_id,
      payload: { task: t.id, photo_id: t.event_type === "dump" ? "cam" : undefined },
      device_ts: new Date().toISOString(),
    };
    await db.events.add(row);
    setLog((l) => [`en cola · ${t.label}`, ...l]);
    refresh();
  }

  async function syncDoor() {
    const rows = await db.events.toArray();
    if (!rows.length) {
      setLog((l) => ["nada que sincronizar", ...l]);
      return;
    }
    try {
      const res = await api<{ inserted: number; duplicates: number; results: { inserted: boolean }[] }>("/api/sync", {
        method: "POST",
        body: JSON.stringify({
          shift: "matutino",
          events: rows.map((r) => ({
            client_uuid: r.client_uuid,
            device_ts: r.device_ts,
            event_type: r.event_type,
            pallet_id: r.pallet_id,
            qty_boxes: r.qty_boxes,
            zone_id: r.zone_id,
            payload: r.payload,
          })),
        }),
      });
      await db.events.clear();
      setLog((l) => [`sync en el andén · ${res.inserted} nuevos · ${res.duplicates} duplicados`, ...l]);
      refresh();
    } catch (e: any) {
      setLog((l) => [`bloqueado · ${e.message}`, ...l]);
    }
  }

  function onScan(e: React.FormEvent) {
    e.preventDefault();
    const hit = TASKS.find((t) => scan.includes("000131") || t.pallet_id.includes(scan.toUpperCase()) || scan.toLowerCase().includes("fresa"));
    if (scan.includes("000131") || /fresa|fre/i.test(scan)) {
      enqueue(TASKS[1]);
    } else if (hit) {
      enqueue(hit);
    } else {
      setLog((l) => [`escaneo ${scan} · sin tarea`, ...l]);
    }
    setScan("");
  }

  return (
    <div className="space-y-4 pb-24">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Captura</h1>
          <p className="text-xs text-black/55">Botones grandes para guantes. Sin Wi‑Fi en cámara.</p>
        </div>
        <button
          onClick={() => setOffline((o) => !o)}
          className={`rounded-full px-3 py-2 text-xs ${offline ? "bg-ink text-mint" : "bg-mint text-ink"}`}
        >
          {offline ? "cámara fría · sin señal" : "en el andén · en línea"}
        </button>
      </div>
      <form onSubmit={onScan} className="flex gap-2">
        <input
          value={scan}
          onChange={(e) => setScan(e.target.value)}
          placeholder="Escanear SSCC o lote"
          className="tap-lg flex-1 rounded-2xl border border-black/15 bg-white px-4 text-base"
        />
        <button className="tap-lg rounded-2xl bg-ink px-4 text-white">OK</button>
      </form>
      <div className="grid gap-2">
        {TASKS.map((t) => (
          <button
            key={t.id}
            onClick={() => enqueue(t)}
            className="tap-xl rounded-2xl border border-black/10 bg-white px-4 text-left text-base font-medium"
          >
            {t.label}
            <div className="text-xs font-normal text-black/45">
              {t.event_type} · {t.pallet_id}
            </div>
          </button>
        ))}
      </div>
      <div className="rounded-2xl bg-warm p-3 text-sm">
        Cola offline: {queue.length} eventos. Se mandan al cruzar el andén. El servidor no duplica.
      </div>
      <button onClick={syncDoor} className="tap-xl w-full rounded-2xl bg-mint text-base font-semibold text-ink">
        Sincronizar en el andén
      </button>
      <ul className="space-y-1 text-xs text-black/60">
        {log.map((l, i) => (
          <li key={i}>{l}</li>
        ))}
      </ul>
    </div>
  );
}
