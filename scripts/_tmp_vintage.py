import csv, io, os, json, glob

base = r"C:\Users\Administrator\Desktop\农业"
isodir = os.path.join(base, "data", "fundamentals", "sugar", "iso")

out = []
out.append("=== dir listing: %s ===" % isodir)
out.append("exists=%s" % os.path.isdir(isodir))
if os.path.isdir(isodir):
    for n in sorted(os.listdir(isodir)):
        out.append("   %s" % n)

cands = glob.glob(os.path.join(base, "data", "**", "early_vintage_matrix*.csv"), recursive=True)
out.append("=== glob candidates ===")
for c in cands: out.append("   %s" % c)

target = None
for c in cands:
    if "2015" in c: target = c; break
if not target and cands: target = cands[0]

data = {}
if target:
    with io.open(target, encoding="utf-8-sig") as f:
        rd = csv.reader(f)
        hdr = next(rd)
        vint = hdr[1:]
        out.append("=== header (%d cols) ===" % len(hdr))
        out.append("   %s" % vint)
        for r in rd:
            if not r or not r[0].strip(): continue
            my = r[0].strip()
            vals = {}
            for i, v in enumerate(r[1:]):
                v = v.strip()
                if not v: continue
                if i < len(vint) and vint[i] != "unit":
                    try: vals[vint[i]] = float(v)
                    except ValueError: pass
            data[my] = vals
            out.append("   %s -> %d vintages, nfields=%d" % (my, len(vals), len(r)))

    out.append("")
    for my in ["2015/16","2016/17","2017/18","2021/22","2022/23","2023/24"]:
        if my not in data: continue
        out.append("=== %s vintage path (kt tel quel) ===" % my)
        items = sorted(data[my].items())
        for v, x in items: out.append("   %s %+8.0f" % (v, x))
        if len(items) >= 2:
            out.append("   >> first %s %+.0f -> last %s %+.0f (delta %+.0f)" % (
                items[0][0], items[0][1], items[-1][0], items[-1][1], items[-1][1]-items[0][1]))
        out.append("")

    with io.open(os.path.join(isodir, "vintage_path_key_years.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

with io.open(os.path.join(base, "scripts", "_tmp_vintage.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("ok")
