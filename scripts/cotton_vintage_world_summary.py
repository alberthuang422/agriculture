#!/usr/bin/env python3
"""Derive analysis-ready world cotton vintage table + validation prints.

From cotton_wasde_vintage_2010_2022.csv (all cotton rows, WASDE snapshots):
  - World table is in Million 480-lb bales (unit variants normalized)
  - Attributes: Production / Domestic Use / Imports / Exports / Beginning Stocks / Ending Stocks
Output:
  - cotton_world_vintage_summary.csv
      report_date, market_year, role(proj=new-crop projection / est=current-year estimate),
      production, domestic_use, imports, exports, beginning_stocks, ending_stocks, stocks_to_use_pct
Validation:
  - print monthly Ending Stocks path for MY 2011/12 (2010/11 bull), 2016/17, 2021/22 (world, proj row)
"""
import csv, collections, os

BASE = "/Users/alberthuang/agriculture/data/fundamentals/cotton/vintage"
SRC = os.path.join(BASE, "cotton_wasde_vintage_2010_2022.csv")

UNIT_OK = {"Million 480-Pounds Bales", "Million 480 Pound Bales",
           "Million 480-lb. Bales", "Million 480-Pound Bales"}
ATTR_NORM = {
    "Production": "production", "Domestic Use": "domestic_use",
    "Imports": "imports", "Exports": "exports",
    "Beginning Stocks": "beginning_stocks", "Beginning stocks": "beginning_stocks",
    "Ending Stocks": "ending_stocks", "Ending stocks": "ending_stocks",
}
MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

def report_key(rd):
    m, y = rd.split()
    return (int(y), MONTHS[m])

rows = []
with open(SRC, newline="") as f:
    for r in csv.DictReader(f):
        if r["Region"] != "World" or r["Unit"] not in UNIT_OK:
            continue
        attr = ATTR_NORM.get(r["Attribute"])
        if not attr:
            continue
        flag = (r["ProjEstFlag"] or "").strip().lower()
        my = r["MarketYear"] or ""
        my_start = int(my[:4]) if my[:4].isdigit() else None
        rk = report_key(r["ReportDate"])
        if "proj" in flag:
            role = "proj"
        elif "est" in flag:
            role = "est"
        elif my_start:
            # infer: crop developing at report time starts in report year if month>=5 else year-1
            crop_start = rk[0] if rk[1] >= 5 else rk[0] - 1
            role = "proj" if my_start == crop_start else "est"
        else:
            continue  # aggregate/summary rows without market year
        try:
            val = float(r["Value"])
        except (ValueError, TypeError):
            continue
        rows.append({
            "report_date": r["ReportDate"], "rk": rk,
            "market_year": r["MarketYear"], "role": role, "attr": attr, "value": val,
        })

# pivot: (report_date, market_year, role) -> attrs
agg = collections.defaultdict(dict)
for r in rows:
    key = (r["rk"], r["report_date"], r["market_year"], r["role"])
    agg[key][r["attr"]] = r["value"]

out = []
for (rk, rd, my, role), d in sorted(agg.items(), key=lambda kv: kv[0][0]):
    prod, use = d.get("production"), d.get("domestic_use")
    es, bs = d.get("ending_stocks"), d.get("beginning_stocks")
    su = round(es / use * 100, 1) if es is not None and use else None
    out.append({
        "report_date": rd, "market_year": my, "role": role,
        "production": prod, "domestic_use": use, "imports": d.get("imports"),
        "exports": d.get("exports"), "beginning_stocks": bs, "ending_stocks": es,
        "stocks_to_use_pct": su,
    })

out_path = os.path.join(BASE, "cotton_world_vintage_summary.csv")
fields = ["report_date", "market_year", "role", "production", "domestic_use", "imports",
          "exports", "beginning_stocks", "ending_stocks", "stocks_to_use_pct"]
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(out)
print(f"world summary rows: {len(out)} -> {out_path}")

# validation: monthly ending-stocks (proj = new crop) for bull cycles
print("\n=== World new-crop (Proj) ending stocks & S/U path, bull cycles ===")
for my_target in ["2010/11", "2011/12", "2016/17", "2021/22"]:
    print(f"\n-- MY {my_target} --")
    for o in out:
        if o["role"] == "proj" and o["market_year"] == my_target:
            print(f"  {o['report_date']:>16}: stocks={o['ending_stocks']}, S/U={o['stocks_to_use_pct']}%")
