import csv, io, os, json

base = r"C:\Users\Administrator\Desktop\农业"
p = os.path.join(base, "data", "price", "sugar", "sb_price_daily.csv")
c = os.path.join(base, "data", "cftc", "sugar_cftc_futonly_1986_2026.csv")

px = []
with io.open(p, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        px.append({"d": row["time"], "c": float(row["close"]), "h": float(row["high"]), "l": float(row["low"])})
cot = []
with io.open(c, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        cot.append({"d": row["date"], "net": int(row["nc_net"]), "l": int(row["nc_l"]), "s": int(row["nc_s"]), "oi": int(row["oi"])})

# weekly price aligned to COT report dates (nearest trading day on/before)
byd = {r["d"]: r for r in px}
dates = sorted(byd)
import bisect
def price_on_or_before(dt):
    i = bisect.bisect_right(dates, dt) - 1
    return byd[dates[i]] if i >= 0 else None

res = {"cot_price": [], "monthly": {}, "key": {}}
for r in cot:
    if r["d"] < "2014-01-01": continue
    q = price_on_or_before(r["d"])
    res["cot_price"].append({"d": r["d"], "c": q["c"] if q else None, "net": r["net"], "l": r["l"], "s": r["s"], "oi": r["oi"]})

# monthly OHLC over full span
d = {}
for r in px:
    k = r["d"][:7]
    if k not in d: d[k] = {"o": r["c"], "h": r["h"], "l": r["l"], "cl": r["c"]}
    else:
        d[k]["h"] = max(d[k]["h"], r["h"]); d[k]["l"] = min(d[k]["l"], r["l"]); d[k]["cl"] = r["c"]
res["monthly"] = {k: v for k, v in sorted(d.items())}

# specific date lookups
probe = ["2015-08-24","2015-09-01","2015-10-01","2015-12-31","2016-02-01","2016-05-02","2016-08-01",
         "2016-10-06","2016-12-15","2017-02-01","2017-05-22","2017-08-22","2018-10-01",
         "2022-10-03","2022-11-01","2023-01-03","2023-04-25","2023-05-01","2023-06-01","2023-08-01",
         "2023-09-01","2023-11-07","2023-12-01","2024-01-02","2024-03-01","2024-06-04","2025-01-02","2026-09-18"]
for q in probe:
    r = price_on_or_before(q)
    cr = None
    for x in cot:
        if x["d"] <= q: cr = x
    if r and cr:
        res["key"][q] = {"price_date": r["d"], "close": r["c"], "cot_date": cr["d"], "net": cr["net"], "l": cr["l"], "s": cr["s"]}

# net long around 2023-11 peak vs 2023-04
window = [x for x in cot if "2023-09-01" <= x["d"] <= "2023-12-31"]
res["key"]["_2023_autumn_net"] = [[x["d"], x["net"], x["l"], x["s"]] for x in window]

with io.open(os.path.join(base, "scripts", "_bull_data.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False)

lines = []
for k, v in res["key"].items():
    lines.append("%s -> %s" % (k, json.dumps(v, ensure_ascii=False)))
with io.open(os.path.join(base, "scripts", "_bull_key.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("ok")
