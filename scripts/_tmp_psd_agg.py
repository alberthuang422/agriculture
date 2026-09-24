import csv, io, os
from collections import defaultdict

base = r"C:\Users\Administrator\Desktop\农业"
p = os.path.join(base, "data", "fundamentals", "sugar", "raw", "psd_sugar_all.csv")

attr = defaultdict(int)          # (code, name) -> count
ncol = defaultdict(int)
samples = []
with io.open(p, encoding="utf-8-sig") as f:
    for i, row in enumerate(csv.reader(f)):
        ncol[len(row)] += 1
        if len(row) < 12: continue
        attr[(row[7], row[8])] += 1
        if i < 3: samples.append(row)

out = []
out.append("ncol distribution: %s" % dict(ncol))
out.append("sample row: %s" % samples[0])
out.append("--- ATTRS (%d distinct) ---" % len(attr))
for (code, name), n in sorted(attr.items()):
    out.append("%s | %-40s | %d" % (code, name, n))

with io.open(os.path.join(base, "scripts", "_tmp_attrs.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("ok")
