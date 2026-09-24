import csv, io, os, json, datetime

base = r"C:\Users\Administrator\Desktop\农业"
c = os.path.join(base, "data", "cftc", "sugar", "sugar_cftc_futonly_1986_2026.csv")
p = os.path.join(base, "data", "price", "sugar", "sb_price_daily.csv")

cot = []
with io.open(c, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        cot.append({"d": row["date"], "net": int(row["nc_net"]), "l": int(row["nc_l"]),
                    "s": int(row["nc_s"]), "oi": int(row["oi"])})
px = []
with io.open(p, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        px.append({"d": row["time"], "c": float(row["close"]), "h": float(row["high"]), "l": float(row["low"])})

import bisect
pdates = sorted({r["d"] for r in px})
pmap = {r["d"]: r for r in px}
def pon(dt):
    i = bisect.bisect_right(pdates, dt) - 1
    return pmap[pdates[i]] if i >= 0 else None

# attach price to each COT week
for r in cot:
    q = pon(r["d"])
    r["c"] = q["c"] if q else None

out = []
def dump(a, b, tag):
    s = [r for r in cot if a <= r["d"] <= b and r["c"] is not None]
    out.append("### %s  (%s ~ %s, n=%d)" % (tag, a, b, len(s)))
    out.append("date,close,net,L,S,OI")
    for r in s:
        out.append("%s,%.2f,%d,%d,%d,%d" % (r["d"], r["c"], r["net"], r["l"], r["s"], r["oi"]))
    out.append("")
    return s

s15 = dump("2015-06-01", "2017-12-31", "CYCLE-2015")
s23 = dump("2022-09-01", "2024-06-30", "CYCLE-2023")

# ---- divergence diagnostics ----
def find(s, key, mode):
    return (max if mode == "max" else min)(s, key=lambda r: r[key])

lines = ["=== DIVERGENCE & UNWIND DIAGNOSTICS ==="]

# 2015/16 cycle
netmax15 = find(s15, "net", "max"); netmin15 = find(s15, "net", "min")
pmax15 = find(s15, "c", "max"); pmin15 = find(s15, "c", "min")
lines.append("[2015-17] net-long MAX %+d on %s (px %.2f) | MIN %+d on %s (px %.2f)" % (
    netmax15["net"], netmax15["d"], netmax15["c"], netmin15["net"], netmin15["d"], netmin15["c"]))
lines.append("[2015-17] close MAX %.2f on %s (net %+d) | MIN %.2f on %s (net %+d)" % (
    pmax15["c"], pmax15["d"], pmax15["net"], pmin15["c"], pmin15["d"], pmin15["net"]))

# 2023 cycle
netmax23 = find(s23, "net", "max"); pmax23 = find(s23, "c", "max")
lines.append("[2022-24] net-long MAX %+d on %s (px %.2f)" % (netmax23["net"], netmax23["d"], netmax23["c"]))
lines.append("[2022-24] close MAX %.2f on %s (net %+d)" % (pmax23["c"], pmax23["d"], pmax23["net"]))

# gap between net-long peak and price peak
for tag, nm, pm in [("2015/16", netmax15, pmax15), ("2023", netmax23, pmax23)]:
    dn = (datetime.date.fromisoformat(pm["d"]) - datetime.date.fromisoformat(nm["d"])).days
    lines.append("[%s] net-long peak -> price peak: %+d days; net at price peak %+d (%.1f%% of peak); px +%.1f%%" % (
        tag, dn, pm["net"], pm["net"]/nm["net"]*100, (pm["c"]/nm["c"]-1)*100))

# short liquidation in 2015/16
smax = find(s15, "s", "max")
smin_after = min([r for r in s15 if r["d"] >= "2015-08-01"], key=lambda r: r["s"])
lines.append("[2015/16] noncomm SHORT peak %d on %s -> trough %d on %s  = %+d (%.1f%%)" % (
    smax["s"], smax["d"], smin_after["s"], smin_after["d"],
    smin_after["s"]-smax["s"], (smin_after["s"]/smax["s"]-1)*100))

# unwind speed after each price peak
def unwind(s, peakdate, nweeks, tag):
    sub = [r for r in s if r["d"] >= peakdate]
    if len(sub) < 2: return
    pk = sub[0]
    lines.append("[%s] unwind from %s (px %.2f, net %+d):" % (tag, pk["d"], pk["c"], pk["net"]))
    for w in [4, 8, 13, 26, 52]:
        if len(sub) > w:
            r = sub[w]
            lines.append("    +%-2dw  %s  px %6.2f (%+6.1f%%)  net %+8d (%+8d, %+6.1f%%)" % (
                w, r["d"], r["c"], (r["c"]/pk["c"]-1)*100, r["net"], r["net"]-pk["net"],
                (r["net"]/pk["net"]-1)*100 if pk["net"] else 0))
unwind(s15, "2016-10-04", 60, "2016 top")
unwind(s23, "2023-11-07", 60, "2023 top")
unwind(s23, "2023-04-25", 60, "2023 Apr net-peak")

# 2023 divergence: Apr peak vs Nov peak
apr = [r for r in s23 if r["d"] == "2023-04-25"][0]
nov = [r for r in s23 if r["d"] == "2023-11-07"][0]
lines.append("")
lines.append("[2023 APR-vs-NOV double top divergence]")
lines.append("    Apr-25: px %.2f  net %+d  L %d  S %d  OI %d" % (apr["c"], apr["net"], apr["l"], apr["s"], apr["oi"]))
lines.append("    Nov-07: px %.2f  net %+d  L %d  S %d  OI %d" % (nov["c"], nov["net"], nov["l"], nov["s"], nov["oi"]))
lines.append("    >> px %+.1f%%  net %+.1f%%  (%+d lots)  L %+.1f%%  S %+.1f%%" % (
    (nov["c"]/apr["c"]-1)*100, (nov["net"]/apr["net"]-1)*100, nov["net"]-apr["net"],
    (nov["l"]/apr["l"]-1)*100, (nov["s"]/apr["s"]-1)*100))

# monthly avg net long vs avg price for both cycles (for charts)
def monthly_avg(s):
    d = {}
    for r in s:
        k = r["d"][:7]
        d.setdefault(k, []).append(r)
    return [{"m": k, "net": round(sum(x["net"] for x in v)/len(v)),
             "px": round(sum(x["c"] for x in v)/len(v), 2),
             "L": round(sum(x["l"] for x in v)/len(v)),
             "S": round(sum(x["s"] for x in v)/len(v)),
             "oi": round(sum(x["oi"] for x in v)/len(v))} for k, v in sorted(d.items())]

res = {"m2015": monthly_avg(s15), "m2023": monthly_avg(s23)}
with io.open(os.path.join(base, "data", "fundamentals", "sugar_bull_positioning.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)

lines.append("")
lines.append("MONTHLY_2015=" + json.dumps(res["m2015"]))
lines.append("MONTHLY_2023=" + json.dumps(res["m2023"]))

with io.open(os.path.join(base, "scripts", "_tmp_div.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ok")
