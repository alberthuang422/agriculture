import csv, io, os, json
from collections import defaultdict

base = r"C:\Users\Administrator\Desktop\农业"
p = os.path.join(base, "data", "fundamentals", "sugar", "raw", "psd_sugar_all.csv")

A = {"020":"beg","028":"prod","057":"imp","088":"exp","126":"disp","176":"end"}
rows = []
with io.open(p, encoding="utf-8-sig") as f:
    for r in csv.reader(f):
        if len(r) < 12: continue
        if r[7] not in A: continue
        rows.append((r[2], int(r[4]), A[r[7]], float(r[11])))

Y0, Y1 = 2010, 2027
def agg(codes, y0=Y0, y1=Y1):
    d = defaultdict(lambda: defaultdict(float))
    for cc, y, k, v in rows:
        if (codes is None or cc in codes) and y0 <= y <= y1:
            d[y][k] += v
    return d

W   = agg(None)
# 可贸易/净出口核心国（正确 PSD 国码）
CORE = {"BR","TH","IN","AS"}          # 巴西 泰国 印度 澳大利亚
COREX= {"BR","TH","IN","AS","CH","E4"}# +中国(CH) +欧盟(E4)
THI  = {"TH","IN"}                     # 泰国+印度（政策性库存）
BRx  = {"BR"}

sets = {"W":W, "CORE":agg(CORE), "COREX":agg(COREX), "THI":agg(THI), "BR":agg(BRx)}
sets["BR_TH_AU_IN"] = sets["CORE"]

res = {}
for name, d in sets.items():
    rec = {}
    for y in range(Y0, Y1+1):
        if y not in d: continue
        v = d[y]
        prod, cons, imp, exp_, end, beg = v["prod"], v["disp"], v["imp"], v["exp"], v["end"], v["beg"]
        rec[str(y)] = {
            "prod": round(prod), "cons": round(cons), "imp": round(imp), "exp": round(exp_),
            "end": round(end), "beg": round(beg),
            "bal": round(prod + imp - exp_ - cons),
            "su": round(end/cons*100, 2) if cons else None,
        }
    res[name] = rec

# 可贸易库存 = 核心净出口国库存 (CORE) ；世界库存占比
share = {}
for y in range(Y0, Y1+1):
    k = str(y)
    if k in res["CORE"] and k in res["W"] and res["W"][k]["end"]:
        share[k] = round(res["CORE"][k]["end"]/res["W"][k]["end"]*100, 1)
        share[k+"_thi"] = round(res["THI"][k]["end"]/res["W"][k]["end"]*100, 1)
        share[k+"_br"] = round(res["BR"][k]["end"]/res["W"][k]["end"]*100, 1)
res["share"] = share

out = os.path.join(base, "data", "fundamentals", "sugar_psd_aggregates_2010_2027.json")
with io.open(out, "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)

# human readable summary
lines = []
lines.append("=== WORLD vs CORE(BR+TH+IN+AU) vs TH+IN  ending stocks / stock-to-use ===")
lines.append("%-6s %10s %7s %10s %7s %10s %7s %8s %8s" % ("MY","W_end","W_s/u","CORE_end","C_s/u","THI_end","T_s/u","CORE/W%","BR/W%"))
for y in range(2013, 2027):
    k = str(y)
    if k not in res["W"]: continue
    w, c, t = res["W"][k], res["CORE"][k], res["THI"][k]
    lines.append("%-6s %10d %7.1f %10d %7.1f %10d %7.1f %8.1f %8.1f" % (
        k, w["end"], w["su"] or 0, c["end"], c["su"] or 0, t["end"], t["su"] or 0,
        share.get(k,0), share.get(k+"_br",0)))

lines.append("")
lines.append("=== WORLD balance & stocks 2013-2026 (USDA PSD, raw value, 1000MT) ===")
for y in range(2013, 2027):
    k = str(y)
    if k not in res["W"]: continue
    w = res["W"][k]
    lines.append("%s prod=%7d cons=%7d bal=%+6d end=%7d s/u=%5.1f%%" % (
        k, w["prod"], w["cons"], w["bal"], w["end"], w["su"] or 0))

lines.append("")
lines.append("=== KEY COUNTRIES production/exports/stocks 2014-2024 ===")
for cc, nm in [("BR","Brazil"),("TH","Thailand"),("IN","India"),("AS","Australia"),("CH","China"),("E4","EU")]:
    d = agg({cc})
    lines.append("--- %s (%s) ---" % (nm, cc))
    for y in range(2014, 2025):
        if y not in d: continue
        v = d[y]
        lines.append("   %d prod=%7.0f exp=%7.0f end=%7.0f imp=%6.0f cons=%7.0f" % (
            y, v["prod"], v["exp"], v["end"], v["imp"], v["disp"]))

with io.open(os.path.join(base, "scripts", "_tmp_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ok")
