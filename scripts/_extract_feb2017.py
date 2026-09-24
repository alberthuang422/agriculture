# -*- coding: utf-8 -*-
"""Extract country-level rows (India/Thailand/Brazil) from ISO Feb-2017 memo PDF
to verify 2015/16 deficit composition. Output to txt for reading."""
from pypdf import PdfReader
import io, re

P = r"C:/Users/Administrator/Desktop/农业/data/fundamentals/sugar/iso/balance_pdfs/historical/world_sugar_balance_february_2017.pdf"
OUT = r"C:/Users/Administrator/Desktop/农业/scripts/_iso_feb2017_countries.txt"

r = PdfReader(P)
lines = []
for i, page in enumerate(r.pages):
    t = page.extract_text() or ""
    lines.append(f"===== PAGE {i+1} =====")
    lines.append(t)

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("pages:", len(r.pages))
