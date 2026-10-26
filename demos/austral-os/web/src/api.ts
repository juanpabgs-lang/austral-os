import { staticResponse } from "./staticDemo";

export const ROLE_KEY = "nf-role";

export function currentRole(): string {
  return localStorage.getItem(ROLE_KEY) || "dueno";
}

export function setRole(role: string) {
  localStorage.setItem(ROLE_KEY, role);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("X-Role", currentRole());
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const res =
    import.meta.env.VITE_STATIC === "1"
      ? await staticResponse(path, { ...init, headers })
      : await fetch(path, { ...init, headers });
  if (!res.ok) {
    let detail: unknown = res.statusText;
    try {
      detail = await res.json();
    } catch {
      /* ignore */
    }
    const err = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    (err as Error & { status: number; detail: unknown }).status = res.status;
    (err as Error & { status: number; detail: unknown }).detail = detail;
    throw err;
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json() as Promise<T>;
  return res as unknown as T;
}

export function downloadHref(livePath: string, filePath: string) {
  if (import.meta.env.VITE_STATIC === "1") return `${import.meta.env.BASE_URL}${filePath}`;
  return livePath;
}

export const mxn = (n: number) =>
  new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(n);
