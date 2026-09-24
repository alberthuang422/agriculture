import csv, io, os, json, datetime

base = r"C:\Users\Administrator\Desktop\农业"

# ---- load daily price (front month continuous) ----
p = os.path.join(base, "data", "price", "sugar", "sb_price_daily.csv")
px = []
with io.open(p, encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    for row in r:
        px.append((row["time"], float(row["close"]), float(row["high"]), float(row["low"])))

def seg(a, b):
    return [x for x in px if a <= x[0] <= b]

out = []

def describe(label, a, b):
    s = seg(a, b)
    if not s:
        out.append("%s: no data" % label); return
    closes = [x[1] for x in s]
    lo = min(s, key=lambda x: x[3])
    hi = max(s, key=lambda x: x[2])
    out.append("== %s (%s ~ %s) n=%d" % (label, a, b, len(s)))
    out.append("   start close %.2f on %s | end close %.2f on %s" % (closes[0], s[0][0], closes[-1], s[-1][0]))
    out.append("   LOW  intraday %.2f on %s" % (lo[3], lo[0]))
    out.append("   HIGH intraday %.2f on %s" % (hi[2], hi[0]))
    out.append("   close-low %.2f on %s | close-high %.2f on %s" % (min(closes), s[closes.index(min(closes))][0], max(closes), s[closes.index(max(closes))][0]))
    out.append("   lo->hi: +%.2f c/lb (+%.1f%%), days=%d" % (hi[2]-lo[3], (hi[2]/lo[3]-1)*100,
        (datetime.date.fromisoformat(hi[0])-datetime.date.fromisoformat(lo[0])).days))

# 2015 bull: bottom Aug-2015, top Oct-2016
describe("2015 bull full", "2014-09-01", "2016-12-31")
describe("2015 leg1 (Aug15-Oct16 top)", "2015-08-01", "2016-10-31")
describe("2016 pullback+leg2", "2016-10-01", "2017-02-28")
# 2023 bull: bottom Nov-2022, top Nov-2023
describe("2023 bull full", "2022-09-01", "2024-03-31")
describe("2023 leg (Nov22-Nov23)", "2022-11-01", "2023-12-15")

# monthly closes for both windows -> for charts
def monthly(a, b):
    d = {}
    for t, c, h, l in seg(a, b):
        k = t[:7]
        if k not in d: d[k] = [c, h, l, c]
        else:
            d[k][1] = max(d[k][1], h); d[k][2] = min(d[k][2], l); d[k][3] = c
    return [{"m": k, "o": round(v[0],2), "hi": round(v[1],2), "lo": round(v[2],2), "cl": round(v[3],2)} for k, v in sorted(d.items())]

m15 = monthly("2014-06-01", "2017-12-31")
m23 = monthly("2022-06-01", "2024-06-30")
out.append("MONTHLY_2015=" + json.dumps(m15))
out.append("MONTHLY_2023=" + json.dumps(m23))

# ---- CFTC ----
c = os.path.join(base, "data", "cftc", "sugar_cftc_futonly_1986_2026.csv")
cot = []
with io.open(c, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        cot.append(row)

def cot_ext(a, b, label):
    s = [r for r in cot if a <= r["date"] <= b]
    if not s: out.append(label+": none"); return
    nets = [(r["date"], int(r["nc_net"])) for r in s]
    longs = [(r["date"], int(r["nc_l"])) for r in s]
    shorts = [(r["date"], int(r["nc_s"])) for r in s]
    mx = max(nets, key=lambda x: x[1]); mn = min(nets, key=lambda x: x[1])
    mxl = max(longs, key=lambda x: x[1]); mxs = max(shorts, key=lambda x: x[1])
    out.append("== CFTC %s (%s~%s) n=%d" % (label, a, b, len(s)))
    out.append("   nc_net MIN %+d on %s | MAX %+d on %s" % (mn[1], mn[0], mx[1], mx[0]))
    out.append("   nc_long MAX %d on %s | nc_short MAX %d on %s" % (mxl[1], mxl[0], mxs[1], mxs[0]))
    out.append("   SERIES=" + json.dumps([[r["date"], int(r["nc_net"]), int(r["nc_l"]), int(r["nc_s"]), int(r["oi"])] for r in s]))

cot_ext("2014-06-01", "2017-12-31", "2015 cycle")
cot_ext("2022-06-01", "2024-06-30", "2023 cycle")

with io.open(os.path.join(base, "scripts", "_tmp_bull.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")
