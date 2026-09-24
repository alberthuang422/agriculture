import csv, io, os, json
from collections import defaultdict

base = r"C:\Users\Administrator\Desktop\农业"
p = os.path.join(base, "data", "fundamentals", "sugar", "raw", "psd_sugar_all.csv")

A = {"020":"beg","028":"prod","057":"imp","088":"exp","126":"disp","176":"end"}
rows = []
with io.open(p, encoding="utf-8-sig") as f:
    for r in csv.reader(f):
        if len(r) < 12: continue
        code, name = r[7], r[8]
        if code not in A: continue
        rows.append((r[2], r[3], int(r[4]), int(r[5]), A[code], float(r[11])))

countries = sorted(set((c[0], c[1]) for c in rows))
years = sorted(set(c[2] for c in rows))

def agg(codes, y0, y1):
    out = defaultdict(lambda: defaultdict(float))
    for cc, cn, y0_, y1_, k, v in rows:
        if cc in codes and y0 <= y0_ <= y1:
            out[y0_][k] += v
    return out

# world = all countries (check if a World aggregate exists)
world_codes = [c for c, n in countries if n.lower().startswith("world")]
print("world-like:", [(c,n) for c,n in countries if 'orld' in n][:5])

allc = set(c for c, n in countries)
W = agg(allc, 2010, 2027)

# candidate core sets
sets = {
 "BR+TH+IN+AU": {"BR","TH","IN","AU"},
 "BR+TH+IN+AU+CN": {"BR","TH","IN","AU","CN"},
 "BR+TH+IN+AU+EU+CN": {"BR","TH","IN","AU","EU","CN"},
}
res = {}
for label, cs in sets.items():
    res[label] = agg(cs, 2010, 2027)

lines = []
lines.append("== WORLD (sum all countries) ==")
for y in range(2010, 2028):
    d = W.get(y, {})
    if not d: continue
    bal = d["prod"] + d["imp"] - d["exp"] - d["disp"]
    stu = d["end"]/d["disp"]*100 if d["disp"] else 0
    lines.append("%d prod=%.0f cons=%.0f imp=%.0f exp=%.0f end=%.0f bal=%.0f s/u=%.1f%%" % (
        y, d["prod"], d["disp"], d["imp"], d["exp"], d["end"], bal, stu))
for label in sets:
    lines.append("== %s ending stocks ==" % label)
    for y in range(2013, 2027):
        d = res[label].get(y, {})
        if not d: continue
        lines.append("   %d end=%.0f prod=%.0f" % (y, d["end"], d["prod"]))

with io.open(os.path.join(base, "scripts", "_tmp_world.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("done")
