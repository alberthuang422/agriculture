# -*- coding: utf-8 -*-
"""补充核查：具体日期收盘、vintage 矩阵覆盖范围、2022/23 终值来源。"""
import csv, io, os, json

BASE = r"C:\Users\Administrator\Desktop\农业"
rows = list(csv.DictReader(io.open(os.path.join(BASE, "data/price/sugar/sb_price_daily.csv"), encoding="utf-8-sig")))
C = {r["time"]: float(r["close"]) for r in rows}
H = {r["time"]: float(r["high"]) for r in rows}
L = {r["time"]: float(r["low"]) for r in rows}

out = []
def p(s=""): out.append(str(s))

p("=" * 78); p("1. 特定日期"); p("=" * 78)
for t in ["2017-05-22", "2017-08-22", "2017-08-31", "2023-12-01", "2023-12-29", "2023-11-30",
          "2024-01-02", "2024-01-24", "2024-01-25", "2024-01-31", "2017-01-04", "2017-01-05",
          "2017-02-06", "2016-11-02", "2016-11-30", "2017-04-05", "2017-10-04",
          "2023-12-04", "2024-02-05", "2024-05-06", "2024-11-04"]:
    if t in C:
        p("  %s  close=%.2f  high=%.2f  low=%.2f" % (t, C[t], H[t], L[t]))
    else:
        p("  %s  (非交易日/缺)" % t)

p(); p("=" * 78); p("2. 2017-08 全月收盘（核对 '关税三个月后 13.51'）"); p("=" * 78)
for r in rows:
    if r["time"].startswith("2017-08") or r["time"].startswith("2017-09"):
        p("  %s close=%.2f" % (r["time"], C[r["time"]]))

p(); p("=" * 78); p("3. vintage 矩阵：2022/23 与 2023/24 的全部列"); p("=" * 78)
mv = os.path.join(BASE, "data/fundamentals/sugar/iso/iso_balance_vintage_matrix.csv")
rd = list(csv.DictReader(io.open(mv, encoding="utf-8-sig")))
cols = list(rd[0].keys())
p("  columns(%d): %s" % (len(cols), cols))
p("  rows=%d  market_years=%s" % (len(rd), sorted(set(r[cols[0]] for r in rd))))
for r in rd:
    if r[cols[0]] in ("2022/23", "2023/24", "2015/16"):
        nz = [(c, r[c]) for c in cols[1:] if r[c] not in ("", None)]
        p("  %s: %s" % (r[cols[0]], " ".join("%s=%s" % (c, v) for c, v in nz)))

p(); p("=" * 78); p("4. iso_world_balance source/notes（终值口径）"); p("=" * 78)
f2 = os.path.join(BASE, "data/fundamentals/sugar/iso/iso_world_balance_2010_2026.csv")
for r in csv.DictReader(io.open(f2, encoding="utf-8-sig")):
    if r["market_year"] in ("2015/16", "2022/23", "2023/24"):
        p("  %s: bal=%s end=%s su=%s" % (r["market_year"], r["balance_mt"], r["end_stocks_mt"], r["stock_to_use_pct"]))
        p("      source=%s" % r.get("source"))
        p("      notes=%s" % r.get("notes"))

p(); p("=" * 78); p("5. vintage_path_key_years.json 结构"); p("=" * 78)
V = json.load(io.open(os.path.join(BASE, "data/fundamentals/sugar/iso/vintage_path_key_years.json"), encoding="utf-8"))
for k in sorted(V.keys()):
    p("  %s -> %d 版: %s ... %s" % (k, len(V[k]), sorted(V[k].items())[0], sorted(V[k].items())[-1]))

io.open(os.path.join(BASE, "scripts", "_r102_verify5.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
