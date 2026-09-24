# -*- coding: utf-8 -*-
"""拉取 FAOSTAT 甘蔗(Crops - Sugar cane, item 156) 面积/单产/产量
element: 5312=Area harvested(ha), 5419=Yield(hg/ha), 5510=Production(t)
国家: 全球=5000, 中国=351, 巴西=21, 印度=100, 泰国=216, 美国=231,
      墨西哥=140, 巴基斯坦=165, 印尼=101, 澳大利亚=5, 危地马拉=89, 哥伦比亚=44
年份: 2005-2025
"""
import urllib.request, urllib.error, json, time, ssl, os, sys

ctx = ssl.create_default_context()
HDRS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

ELEMENTS = {"area": 5312, "yield": 5419, "prod": 5510}
AREAS = {
    "WLD": 5000, "CN": 351, "BR": 21, "IN": 100, "TH": 216, "US": 231,
    "MX": 140, "PK": 165, "ID": 101, "AU": 5, "GT": 89, "CO": 44,
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "data", "fundamentals", "sugar", "raw")
os.makedirs(DATA_DIR, exist_ok=True)
OUT = os.path.join(DATA_DIR, "faostat_sugarcane_raw.json")

def fetch(url, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=45, context=ctx) as resp:
                return resp.status, resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 521:
                time.sleep(6 + i * 5)  # 服务器侧故障，退避重试
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(4 + i * 3)
    return None, last

results = {"meta": {"source": "FAOSTAT Crops API", "item": "Sugar cane (156)",
                    "elements": ELEMENTS, "areas": AREAS, "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())},
           "data": {}}

failures = []
for aname, acode in AREAS.items():
    for ename, ecode in ELEMENTS.items():
        url = (f"https://fenixservices.fao.org/faostat/api/v1/en/data"
               f"?item_code=156&element_code={ecode}&area_code={acode}&year=2005,2006,2007,2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025")
        status, raw = fetch(url)
        if status != 200:
            failures.append((aname, ename, str(raw)))
            print(f"[FAIL] {aname}/{ename}: {raw}", flush=True)
            continue
        try:
            d = json.loads(raw)
            rows = d.get("data", [])
            recs = []
            for r in rows:
                recs.append({
                    "year": r.get("year"), "value": r.get("value"),
                    "unit": r.get("unit"), "flag": r.get("flag"),
                })
            results["data"][f"{aname}_{ename}"] = recs
            print(f"[OK] {aname}/{ename}: {len(recs)} rows", flush=True)
        except Exception as e:
            failures.append((aname, ename, f"parse {e}"))
            print(f"[PARSE FAIL] {aname}/{ename}: {e}", flush=True)

results["failures"] = failures
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print("SAVED:", OUT)
print("FAILURES:", failures)