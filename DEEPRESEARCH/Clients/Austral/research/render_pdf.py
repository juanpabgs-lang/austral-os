#!/usr/bin/env python3
"""Render the strategy memo to HTML + PDF via headless Chrome."""

from pathlib import Path
import html
import subprocess

src = Path(__file__).parent / "2026-10_norfront-fresh_estrategia.md"
md = src.read_text(encoding="utf-8")

# Minimal Markdown-ish to HTML (headings, bold, hr, tables skipped as preformatted blocks).
lines = md.splitlines()
out = ["<!doctype html><html lang='es'><head><meta charset='utf-8'>",
       "<title>Norfront Fresh — estrategia</title>",
       "<style>body{font:15px/1.5 Inter,system-ui,sans-serif;max-width:820px;margin:40px auto;padding:0 24px;color:#111;background:#F1F1F1}",
       "h1{font-size:28px}h2{font-size:20px;margin-top:2em}code,pre{font-size:13px}",
       "hr{border:0;border-top:1px solid #1113}table{border-collapse:collapse;width:100%;font-size:13px}",
       "th,td{border:1px solid #1112;padding:6px 8px;text-align:left}th{background:#111;color:#fff}</style></head><body>"]

def inline(s: str) -> str:
    s = html.escape(s)
    s = s.replace("**", "\x00")
    parts = s.split("\x00")
    buf = []
    for i, p in enumerate(parts):
        buf.append(f"<strong>{p}</strong>" if i % 2 else p)
    s = "".join(buf)
    return s.replace("[Inference]", "<em>[Inference]</em>")

i = 0
in_table = False
in_list = False
while i < len(lines):
    line = lines[i]
    if line.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
        if in_list:
            out.append("</ul>"); in_list = False
        cols = [c.strip() for c in line.strip("|").split("|")]
        out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in cols) + "</tr></thead><tbody>")
        i += 2
        while i < len(lines) and lines[i].startswith("|"):
            cols = [c.strip() for c in lines[i].strip("|").split("|")]
            out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cols) + "</tr>")
            i += 1
        out.append("</tbody></table>")
        continue
    if line.startswith("# "):
        if in_list:
            out.append("</ul>"); in_list = False
        out.append(f"<h1>{inline(line[2:])}</h1>")
    elif line.startswith("## "):
        if in_list:
            out.append("</ul>"); in_list = False
        out.append(f"<h2>{inline(line[3:])}</h2>")
    elif line.startswith("### "):
        if in_list:
            out.append("</ul>"); in_list = False
        out.append(f"<h3>{inline(line[4:])}</h3>")
    elif line.startswith("---"):
        if in_list:
            out.append("</ul>"); in_list = False
        out.append("<hr>")
    elif line.startswith("- "):
        if not in_list:
            out.append("<ul>"); in_list = True
        out.append(f"<li>{inline(line[2:])}</li>")
    elif line.strip() == "":
        if in_list:
            out.append("</ul>"); in_list = False
    else:
        if in_list:
            out.append("</ul>"); in_list = False
        out.append(f"<p>{inline(line)}</p>")
    i += 1
if in_list:
    out.append("</ul>")
out.append("</body></html>")
html_path = src.with_suffix(".html")
html_path.write_text("\n".join(out), encoding="utf-8")
pdf_path = src.with_suffix(".pdf")
subprocess.check_call([
    "google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
    f"--print-to-pdf={pdf_path}", html_path.as_uri(),
])
print("wrote", html_path, pdf_path)
