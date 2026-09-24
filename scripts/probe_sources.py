# -*- coding: utf-8 -*-
"""探测甘蔗面积/单产数据源可达性"""
import urllib.request, json, sys, ssl

ctx = ssl.create_default_context()
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def probe(name, url, parser):
    try:
        req = urllib.request.Request(url, headers=HDRS)
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            print(f"[OK] {name} HTTP {resp.status} len={len(raw)}")
            parser(raw)
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {e}")

def parse_faostat(raw):
    try:
        d = json.loads(raw)
        if "data" in d:
            rows = d["data"]
            print(f"  FAOSTAT rows={len(rows)}")
            for r in rows[:5]:
                print("  ", {k: r.get(k) for k in ("area", "item", "element", "year", "value", "unit")})
        else:
            print("  FAOSTAT unexpected:", str(d)[:300])
    except Exception as e:
        print("  parse err:", e, raw[:200])

def parse_generic(raw):
    print("  ", raw[:300].replace(chr(10), " "))

# FAOSTAT: 糖料作物 item_code=156 (Sugar cane), element 5312=Area harvested (ha), 351=中国
probe("FAOSTAT 甘蔗收获面积(中国2022)",
      "https://fenixservices.fao.org/faostat/api/v1/en/data?item_code=156&element_code=5312&area_code=351&year=2022",
      parse_faostat)

# FAOSTAT 产量 element 5510 / 单产 element 5419
probe("FAOSTAT 甘蔗单产(中国2022)",
      "https://fenixservices.fao.org/faostat/api/v1/en/data?item_code=156&element_code=5419&area_code=351&year=2022",
      parse_faostat)

# FAO 老版 Bulk Downloads 是否可达（CSV 全量）
probe("FAOSTAT bulk CSV 根目录",
      "https://bulk.uni-fao.org/production/crops/",
      parse_generic)

# USDA PSD: 面积属性码 33 (Area Harvested)? 官方属性: 01 production / 31 supply 等. 试试 33/34
probe("USDA PSD 糖面积属性(码33)",
      "https://apps.fas.usda.gov/psdonline/api/downloadData?commodityCode=0612000&marketYear=2022&AttributeId=33&agLevelId=0&format=csv",
      parse_generic)
probe("USDA PSD 糖面积属性(码34?)",
      "https://apps.fas.usda.gov/psdonline/api/downloadData?commodityCode=0612000&marketYear=2022&AttributeId=34&agLevelId=0&format=csv",
      parse_generic)