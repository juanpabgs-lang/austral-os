type Ship = {
  id: string;
  lot_id: string;
  released: number;
  gaps: { cte: string; key: string; label?: string; cite?: string }[];
};

type Snap = {
  gets: Record<string, unknown>;
  packEmpty: unknown;
  packOk: unknown;
};

/** Published copy of the packer demo. Screens and the gate story run from a snapshot, with no server. */
export function installStaticFetch() {
  const orig = window.fetch.bind(window);
  let snapPromise: Promise<Snap> | null = null;
  let ships: Ship[] | null = null;

  function load() {
    if (!snapPromise) {
      snapPromise = orig(`${import.meta.env.BASE_URL}snapshot.json`).then((r) => r.json());
    }
    return snapPromise;
  }

  function jsonResponse(status: number, body: unknown) {
    return new Response(JSON.stringify(body), {
      status,
      headers: { "content-type": "application/json" },
    });
  }

  async function shipments() {
    const snap = await load();
    if (!ships) {
      const body = snap.gets["/api/shipments"] as { shipments: Ship[] };
      ships = structuredClone(body.shipments);
    }
    return ships;
  }

  window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const raw = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const path = raw.startsWith("http") ? new URL(raw).pathname : raw;
    if (!path.startsWith("/api/")) return orig(input, init);

    const snap = await load();
    const method = (init?.method || "GET").toUpperCase();

    if (method === "GET") {
      if (path === "/api/shipments") return jsonResponse(200, { shipments: await shipments() });
      if (path in snap.gets) return jsonResponse(200, snap.gets[path]);
      return jsonResponse(404, { detail: `Sin dato estático para ${path}` });
    }

    if (path === "/api/reset") {
      ships = null;
      return jsonResponse(200, { ok: true });
    }

    if (path === "/api/records/fix") {
      const body = JSON.parse(String(init?.body || "{}")) as { lot_id: string; cte: string; key: string };
      for (const ship of await shipments()) {
        if (ship.lot_id !== body.lot_id) continue;
        ship.gaps = (ship.gaps || []).filter((g) => !(g.cte === body.cte && g.key === body.key));
      }
      return jsonResponse(200, { ok: true });
    }

    if (path === "/api/gate/release") {
      const body = JSON.parse(String(init?.body || "{}")) as { shipment_id: string };
      const ship = (await shipments()).find((s) => s.id === body.shipment_id);
      if (ship && ship.gaps?.length) return jsonResponse(409, { detail: { gaps: ship.gaps } });
      if (ship) ship.released = 1;
      return jsonResponse(200, { ok: true, released: true });
    }

    if (path === "/api/pack") {
      const body = JSON.parse(String(init?.body || "{}")) as { field?: string };
      if (!body.field || !String(body.field).trim()) return jsonResponse(409, snap.packEmpty);
      return jsonResponse(200, snap.packOk);
    }

    return jsonResponse(404, { detail: "static" });
  };
}
