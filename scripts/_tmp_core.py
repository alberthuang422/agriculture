import csv, io, os, json, itertools
from collections import defaultdict

base = r"C:\Users\Administrator\Desktop\农业"
psd = os.path.join(base, "data", "fundamentals", "sugar", "raw", "psd_sugar_all.csv")
tr  = os.path.join(base, "data", "fundamentals", "sugar", "sugar_tradeable.csv")

# ending stocks by country-year
end = defaultdict(dict)   # code -> {my: val}
names = {}
with io.open(psd, encoding="utf-8-sig") as f:
    for r in csv.reader(f):
        if len(r) < 12: continue
        names[r[2]] = r[3]
        if r[7] == "176":
            end[r[2]][int(r[4])] = end[r[2]].get(int(r[4]), 0) + float(r[11])

# target series
tgt = {}
with io.open(tr, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        my = int(row["MY"])
        tgt[my] = {"core": float(row["core_stocks"]), "R1": float(row["R1_stocks"]),
                   "R2": float(row["R2_stocks"]), "w": float(row["w_stocks"]),
                   "cn": float(row["cn"]), "ind": float(row["ind"]),
                   "core_share": float(row["core_share"])}

out = []
# verify R1 / R2 hypotheses
for my in [2015, 2019, 2023]:
    t = tgt[my]
    w = sum(end[c].get(my, 0) for c in end)
    r1 = w - t["cn"]
    r2 = w - t["cn"] - t["ind"]
    out.append("MY%d: w=%.0f (csv w=%.0f) | R1 calc=%.0f (csv %.0f) | R2 calc=%.0f (csv %.0f)" % (
        my, w, t["w"], r1, t["R1"], r2, t["R2"]))
    out.append("    cn csv=%.0f psd=%.0f | ind csv=%.0f psd=%.0f" % (
        t["cn"], end["CH"].get(my,0), t["ind"], end["IN"].get(my,0)))

# brute force: find country set reproducing core_stocks for 2015,2019,2023 simultaneously
years = [2015, 2019, 2023]
codes = [c for c in end if any(end[c].get(y, 0) > 0 for y in years)]
targets = [tgt[y]["core"] for y in years]
out.append("")
out.append("target core_stocks: %s" % list(zip(years, targets)))

found = []
# greedy: start from big holders, try combos up to size 8 among top-20 holders
top = sorted(codes, key=lambda c: -max(end[c].get(y, 0) for y in years))[:20]
out.append("top20 holders: %s" % [(c, names[c]) for c in top])

for k in range(2, 9):
    for combo in itertools.combinations(top, k):
        vals = [sum(end[c].get(y, 0) for c in combo) for y in years]
        if all(abs(v - t) <= 60 for v, t in zip(vals, targets)):
            found.append((combo, vals))
    if found: break

out.append("")
out.append("=== MATCHES (tolerance 60kt) ===")
for combo, vals in found[:20]:
    out.append("   %s -> %s" % ([names[c] for c in combo], [round(v) for v in vals]))
if not found:
    out.append("   none found; core may use ISO MY or non-PSD source")

# also: check core_share meaning
out.append("")
for my in [2015, 2019, 2023]:
    t = tgt[my]
    w = sum(end[c].get(my, 0) for c in end)
    out.append("MY%d core/w = %.2f%% (csv core_share=%.2f%%)" % (my, t["core"]/w*100, t["core_share"]))

with io.open(os.path.join(base, "scripts", "_tmp_core.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("ok")
