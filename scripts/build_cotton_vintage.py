#!/usr/bin/env python3
"""Build cotton vintage dataset from WASDE historical snapshot CSVs.

Sources:
  - wasde_zips/extracted/oce-wasde-report-data-2010-04-to-2015-12.csv
  - wasde_zips/extracted/oce-wasde-report-data-2016-01-to-2020-12.csv
  - monthly_2021_2022/oce-wasde-report-data-YYYY-MM.csv

Output:
  - data/fundamentals/cotton/vintage/cotton_wasde_vintage_2010_2022.csv  (all cotton rows)
  - summary stats printed
"""
import csv, glob, os, sys

BASE = "/Users/alberthuang/agriculture/data/fundamentals/cotton/vintage"
SOURCES = [
    os.path.join(BASE, "wasde_zips/extracted/oce-wasde-report-data-2010-04-to-2015-12.csv"),
    os.path.join(BASE, "wasde_zips/extracted/oce-wasde-report-data-2016-01-to-2020-12.csv"),
] + sorted(glob.glob(os.path.join(BASE, "raw/monthly_2021_2022/oce-wasde-report-data-*.csv")))

out_rows = []
report_dates = set()
for src in SOURCES:
    with open(src, newline="", encoding="utf-8-sig", errors="replace") as f:
        r = csv.DictReader(f)
        for row in r:
            if (row.get("Commodity") or "").strip().lower() == "cotton":
                out_rows.append(row)
                report_dates.add(row["ReportDate"])

out_path = os.path.join(BASE, "cotton_wasde_vintage_2010_2022.csv")
fields = ["WasdeNumber","ReportDate","ReportTitle","Attribute","ReliabilityProjection",
          "Commodity","Region","MarketYear","ProjEstFlag","AnnualQuarterFlag",
          "Value","Unit","ReleaseDate","ReleaseTime","ForecastYear","ForecastMonth"]
with open(out_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    w.writerows(out_rows)

print(f"cotton rows: {len(out_rows)}  -> {out_path}")
print(f"report dates: {len(report_dates)}")
rd = sorted(report_dates, key=lambda s: (s.split()[-1], ["January","February","March","April","May","June","July","August","September","October","November","December"].index(s.split()[0])))
print("range:", rd[0], "->", rd[-1])

# quick stats: units, attributes, top regions
import collections
units = collections.Counter(r["Unit"] for r in out_rows)
attrs = collections.Counter(r["Attribute"] for r in out_rows)
regions = collections.Counter(r["Region"] for r in out_rows)
print("\nunits:", dict(units))
print("\nattributes:", dict(attrs))
print("\ntop regions:", regions.most_common(15))
