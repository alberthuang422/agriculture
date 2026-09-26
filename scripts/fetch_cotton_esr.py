#!/usr/bin/env python3
"""Fetch US cotton (All Upland) ESR weekly comparison data from USDA FAS ESRQS API.

- Comparison5YearReport: current MY (2026/27) weekly accumulated exports / accumulated net sales
  vs yearAgo1..5 (2025/26 .. 2021/22 same marketing-year week) + 5-yr average, per destination.
- GetExportsByMarketingYear: annual ESR exports by marketing year (running bales).

Output: data/fundamentals/cotton/us_cotton_esr_20260925/ (raw json) + esr_summary.json
"""
import json, time, urllib.request, urllib.parse, os, sys

BASE = "https://apps.fas.usda.gov/esrqs/api"
FIXED_SECRET = "00000000-0000-0000-0000-00000000000000000000-0000-0000-0000-000000000000"
OUT = "/Users/alberthuang/agriculture/data/fundamentals/cotton/us_cotton_esr_20260925"
os.makedirs(OUT, exist_ok=True)

def http(url, data=None, headers=None, method="GET"):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def get_json(url, tok):
    return json.loads(http(url, headers={"Authorization": f"Bearer {tok}", "User-Agent": "Mozilla/5.0"}))

def main():
    body = urllib.parse.urlencode({
        "client_id": "eAuth_Client", "client_secret": FIXED_SECRET,
        "grant_type": "client_credentials"}).encode()
    tok = json.loads(http(f"{BASE}/token".replace("/api/token", "/token"), data=body,
                          headers={"Content-Type": "application/x-www-form-urlencoded",
                                   "User-Agent": "Mozilla/5.0"}))["access_token"]
    print("token ok")

    COMMODITY = 27  # ALL UPLAND COTTON, running bales
    countries = {
        "5700": "China", "5520": "Vietnam", "5350": "Pakistan", "5380": "Bangladesh",
        "4890": "Turkey", "2010": "Mexico", "5330": "India", "5800": "Korea, Rep.",
        "5880": "Japan", "5600": "Indonesia", "5490": "Thailand", "2150": "Honduras",
    }
    reports = {20: "accumulated_exports", 40: "accumulated_net_sales", 50: "outstanding_sales"}

    result = {"fetched_at": "2026-09-25", "commodity": "All Upland Cotton",
              "unit": "Running Bales", "marketing_year": "2026/27 (Aug 2026-Jul 2027)",
              "countries": {}}
    for cc, name in countries.items():
        result["countries"][name] = {}
        for rc, rname in reports.items():
            url = (f"{BASE}/reports/Comparison5YearReport?CommodityId={COMMODITY}"
                   f"&DestinationCountryCode={cc}&ReportCode={rc}")
            for attempt in range(3):
                try:
                    rows = get_json(url, tok)
                    break
                except Exception as e:
                    print("retry", name, rc, e, file=sys.stderr)
                    time.sleep(3)
            else:
                rows = []
            result["countries"][name][rname] = rows
            time.sleep(0.4)
        print(f"{name}: {[len(v) for v in result['countries'][name].values()]}")
        with open(f"{OUT}/esr_5y_by_country.json", "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=1)

    # annual exports by marketing year (ESR annual, running bales)
    ann = get_json(f"{BASE}/lookups/GetExportsByMarketingYear?CommodityId={COMMODITY}&MarketingYearFrom=2016&MarketingYearTo=2027", tok)
    with open(f"{OUT}/esr_annual_exports_2016_2027.json", "w") as f:
        json.dump(ann, f, ensure_ascii=False, indent=1)
    print("annual rows:", len(ann))
    print("DONE")

if __name__ == "__main__":
    main()
