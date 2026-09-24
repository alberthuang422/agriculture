import csv, io, os
from collections import defaultdict

base = r"C:\Users\Administrator\Desktop\农业"
p = os.path.join(base, "data", "fundamentals", "sugar", "raw", "psd_sugar_all.csv")

end = defaultdict(float)     # (code,name) -> ending stocks 2023
prod = defaultdict(float)
names = {}
with io.open(p, encoding="utf-8-sig") as f:
    for r in csv.reader(f):
        if len(r) < 12: continue
        if r[4] != "2023": continue
        names[r[2]] = r[3]
        if r[7] == "176": end[(r[2], r[3])] += float(r[11])
        if r[7] == "028": prod[(r[2], r[3])] += float(r[11])

out = ["=== TOP 25 by ENDING STOCKS 2023 ==="]
for k, v in sorted(end.items(), key=lambda x: -x[1])[:25]:
    out.append("%-4s %-28s end=%9.0f  prod=%9.0f" % (k[0], k[1], v, prod.get(k, 0)))

out.append("")
out.append("=== codes containing C / I / B / T / A (check CN vs CH) ===")
for c in sorted(names):
    if c[0] in "CIBTA":
        out.append("%-4s %s   end=%.0f prod=%.0f" % (c, names[c], end.get((c, names[c]), 0), prod.get((c, names[c]), 0)))

with io.open(os.path.join(base, "scripts", "_tmp_codes.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("ok")
