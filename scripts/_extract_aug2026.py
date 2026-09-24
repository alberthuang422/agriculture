# -*- coding: utf-8 -*-
"""Extract 2026/27 country rows from ISO Aug-2026 memo PDF to verify regional composition."""
from pypdf import PdfReader
import io

P = r"C:/Users/Administrator/Desktop/农业/data/fundamentals/sugar/iso/balance_pdfs/world_sugar_balance_august_2026.pdf"
OUT = r"C:/Users/Administrator/Desktop/农业/scripts/_iso_aug2026_countries.txt"

r = PdfReader(P)
lines = []
for i, page in enumerate(r.pages):
    t = page.extract_text() or ""
    lines.append(f"===== PAGE {i+1} =====")
    lines.append(t)

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("pages:", len(r.pages))
