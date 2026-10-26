type Snap = {
  gets: Record<string, unknown>;
  asks: Record<string, unknown>;
  hold: unknown;
};

let snapPromise: Promise<Snap> | null = null;
let rules: { rules: { id: string; active: number; version: number }[]; audit: Record<string, unknown>[] } | null = null;
const seen = new Set<string>();

function load(): Promise<Snap> {
  if (!snapPromise) {
    snapPromise = fetch(`${import.meta.env.BASE_URL}snapshot.json`)
      .then((r) => r.json())
      .then((s: Snap) => {
        rules = structuredClone(s.gets["/api/rules"]) as NonNullable<typeof rules>;
        return s;
      });
  }
  return snapPromise;
}

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/** Published copy of the demo. Reads a snapshot taken from the API so the screens work without a server. */
export async function staticResponse(path: string, init: RequestInit = {}): Promise<Response> {
  const snap = await load();
  const method = (init.method || "GET").toUpperCase();
  const role = new Headers(init.headers).get("X-Role") || "dueno";

  if (method === "GET") {
    if (path === "/api/rules" || path.startsWith("/api/rules?")) return jsonResponse(200, rules);
    if (path in snap.gets) return jsonResponse(200, snap.gets[path]);
    const bare = path.split("?")[0];
    if (bare in snap.gets) return jsonResponse(200, snap.gets[bare]);
    return jsonResponse(404, { detail: `Sin dato estático para ${path}` });
  }

  if (path === "/api/reset") {
    snapPromise = null;
    rules = null;
    seen.clear();
    return jsonResponse(200, { ok: true });
  }

  if (path === "/api/ask") {
    const q = JSON.parse(String(init.body || "{}")).q as string;
    return jsonResponse(200, snap.asks[q] || snap.asks._default);
  }

  if (path === "/api/sync") {
    const events = (JSON.parse(String(init.body || "{}")).events || []) as {
      client_uuid?: string;
      event_type?: string;
      pallet_id?: string;
    }[];
    if (events.some((e) => e.event_type === "pick" && e.pallet_id === "PAL-FRE-H")) {
      return jsonResponse(409, snap.hold);
    }
    let inserted = 0;
    let duplicates = 0;
    const results = events.map((e) => {
      const id = e.client_uuid || crypto.randomUUID();
      if (seen.has(id)) {
        duplicates += 1;
        return { inserted: false, client_uuid: id };
      }
      seen.add(id);
      inserted += 1;
      return { inserted: true, client_uuid: id };
    });
    return jsonResponse(200, { ok: true, received: events.length, inserted, duplicates, results });
  }

  if (path.startsWith("/api/rules/")) {
    if (role !== "dueno") {
      return jsonResponse(403, { detail: "Ninguna regla de almacén cambia sin aprobación del dueño." });
    }
    const id = path.split("/").pop();
    const active = Boolean(JSON.parse(String(init.body || "{}")).active);
    const rule = rules?.rules.find((r) => r.id === id);
    if (!rule || !rules) return jsonResponse(404, { detail: "rule_not_found" });
    rule.active = active ? 1 : 0;
    rule.version = (rule.version || 1) + 1;
    rules.audit = [
      {
        id: `local-${Date.now()}`,
        action: "rule.change",
        entity: "rule",
        entity_id: id,
        ts: new Date().toISOString(),
        role,
      },
      ...rules.audit,
    ];
    return jsonResponse(200, { ok: true });
  }

  return jsonResponse(404, { detail: "static" });
}
