import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(root, "../web/src/i18n/copy.ts"), "utf8");
const keys = (lang) => {
  const re = new RegExp(`${lang}:\\s*\\{([\\s\\S]*?)\\n\\s*\\}`, "m");
  const m = src.match(re);
  if (!m) throw new Error(`no block for ${lang}`);
  return [...m[1].matchAll(/^\s*(\w+):/gm)].map((x) => x[1]);
};
const a = new Set(keys("es"));
const b = new Set(keys("en"));
const missingEn = [...a].filter((k) => !b.has(k));
const missingEs = [...b].filter((k) => !a.has(k));
if (missingEn.length || missingEs.length) {
  console.error("i18n gaps", { missingEn, missingEs });
  process.exit(1);
}
console.log(`i18n ok · ${a.size} keys`);
