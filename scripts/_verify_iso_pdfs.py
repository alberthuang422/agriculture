from pypdf import PdfReader
import os, io

BASE = r"C:/Users/Administrator/Desktop/农业/data/fundamentals/sugar/iso/balance_pdfs"
OUT = r"C:/Users/Administrator/Desktop/农业/scripts/_iso_pdf_verify.txt"

targets = [
    os.path.join(BASE, "world_sugar_balance_august_2026.pdf"),
    os.path.join(BASE, "world_sugar_balance_may_2026.pdf"),
    os.path.join(BASE, "world_sugar_balance_november_2024.pdf"),
    os.path.join(BASE, "historical", "world_sugar_balance_february_2017.pdf"),
    os.path.join(BASE, "historical", "world_sugar_balance_august_2024.pdf"),
]

lines = []
for p in targets:
    name = os.path.basename(p)
    try:
        r = PdfReader(p)
        meta = r.metadata
        t0 = (r.pages[0].extract_text() or "").replace("\n", " | ")
        lines.append("== %s | pages=%d" % (name, len(r.pages)))
        lines.append("   meta: %s" % (dict(meta) if meta else None))
        lines.append("   p1: %s" % t0[:500])
    except Exception as e:
        lines.append("== %s | ERROR %s" % (name, e))
    lines.append("")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done")
