# -*- coding: utf-8 -*-
import csv, json, io

src = r"C:\Users\Administrator\Desktop\农业\data\cftc\results_cot\agri_cot_history_1995_2026.csv"
rows = []
with open(src, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["market"].startswith("棉花"):
            rows.append(r)

out = {"n": len(rows), "first": rows[0]["date"], "last": rows[-1]["date"]}

def val(r, k):
    try: return float(r[k])
    except (ValueError, TypeError): return None

net = [val(r, "nc_net") for r in rows]
pair = [(r["date"], n) for r, n in zip(rows, net) if n is not None]
dates = [p[0] for p in pair]; nets = [p[1] for p in pair]
last = nets[-1]

def pct(series, v):
    return 100.0 * sum(1 for x in series if x < v) / len(series)

def series_since(d0):
    return [n for d, n in pair if d >= d0]

out["nc_net_last"] = last
out["pct_full"] = pct(nets, last)
out["pct_10y"] = pct(series_since("2016-09-01"), last)
out["pct_5y"] = pct(series_since("2021-09-01"), last)
out["pct_3y"] = pct(series_since("2023-09-01"), last)
out["hist_max"] = [max(nets), dates[nets.index(max(nets))]]
out["hist_min"] = [min(nets), dates[nets.index(min(nets))]]
out["oi_last"] = val(rows[-1], "oi")
# OI 分位（同序列自算）
oi = [(r["date"], val(r, "oi")) for r in rows if val(r, "oi") is not None]
ois = [o[1] for o in oi]
out["oi_pct_full"] = pct(ois, ois[-1])
out["oi_hist_max"] = [max(ois), oi[ois.index(max(ois))][0]]
# 近 12 周动态
tail = pair[-13:]
out["weekly"] = [{"date": d, "nc_net": n, "oi": val(r, "oi"),
                  "nc_l": val(r, "nc_l"), "nc_s": val(r, "nc_s")} for r, (d, n) in zip(rows[-13:], tail)]
out["chg_12w"] = last - tail[0][1]

# 历史同名极值事件（净多 TOP10）
top10 = sorted(pair, key=lambda p: -p[1])[:10]
out["top10"] = top10
json.dump(out, open(r"C:\Users\Administrator\Desktop\农业\data\cftc\results_cot\cotton_cot_stats_20260920.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
