# -*- coding: utf-8 -*-
"""
棕榈油（及关联油脂）USDA FAS PSD 平衡表批量采集
- 商品码 4243000 Oil,Palm / 4232000 Oil,Soybean / 4242000 Oil,Coconut
         4244000 Oil,Palm Kernel / 4239100 Oil,Rapeseed / 4236000 Oil,Sunflowerseed
- 全球端点 + 主要生产/消费国
- 输出: data/fundamentals/palm/psd_palm_world.json / psd_palm_countries.json / psd_vegoil_world.json
用法: python scripts/palm_pull_psd.py [--quick]
"""
import json, os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

KEY = os.environ["USDA_FAS_API_KEY"]
BASE = "https://api.fas.usda.gov/api/psd"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "fundamentals", "palm")
OUT = os.path.normpath(OUT)
os.makedirs(OUT, exist_ok=True)

YEARS = list(range(1989, 2027))

# 主产国 + 主消费国（PSD 码，已按 /countries 的 countryName 断言核对）
COUNTRIES = {
    "MY": "Malaysia",      "ID": "Indonesia",     "TH": "Thailand",
    "VM": "Vietnam",       "RP": "Philippines",
    "IN": "India",         "CH": "China",         "PK": "Pakistan",
    "BG": "Bangladesh",    "E4": "European Union","US": "United States",
    "MX": "Mexico",        "BR": "Brazil",        "EG": "Egypt",
    "NI": "Nigeria",       "KE": "Kenya",
}
COMMOD = {"4243000": "Oil, Palm", "4232000": "Oil, Soybean", "4242000": "Oil, Coconut",
          "4244000": "Oil, Palm Kernel", "4239100": "Oil, Rapeseed", "4236000": "Oil, Sunflowerseed"}


def fetch(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"X-Api-Key": KEY, "User-Agent": "psd-pull"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if i == tries - 1:
                sys.stderr.write("FAIL %s : %s\n" % (url, e))
                return None
            time.sleep(1.5 * (i + 1))


def one_world(cc, yy):
    return cc, yy, fetch("%s/commodity/%s/world/year/%s" % (BASE, cc, yy))


def one_country(cc, cty, yy):
    return cc, cty, yy, fetch("%s/commodity/%s/country/%s/year/%s" % (BASE, cc, cty, yy))


def main():
    quick = "--quick" in sys.argv
    yrs = [2010, 2015, 2020] + list(range(2021, 2027)) if quick else YEARS

    # 1) 全球：全部 6 个油脂品种（用于油脂板块对比与替代分析）
    jobs = [(c, y) for c in COMMOD for y in yrs]
    world = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for cc, yy, d in ex.map(lambda j: one_world(*j), jobs):
            if d:
                world.setdefault(cc, {})[str(yy)] = d
    print("world cells:", {k: len(v) for k, v in world.items()})

    # 2) 分国：棕榈油全国家 × 全年份
    jobs2 = [("4243000", c, y) for c in COUNTRIES for y in yrs]
    ctry = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for cc, c_, yy, d in ex.map(lambda j: one_country(*j), jobs2):
            if d:
                ctry.setdefault(c_, {})[str(yy)] = d
    print("country cells:", {k: len(v) for k, v in ctry.items()})

    meta = {"asOf": time.strftime("%Y-%m-%d %H:%M:%S"), "source": "USDA FAS PSD API",
            "commodities": COMMOD, "countries": COUNTRIES,
            "yearsRequested": [min(yrs), max(yrs)], "unitNote": {
                "unitId8": "1000 MT", "unitId4": "1000 HA", "unitId26": "MT/HA"}}
    json.dump(meta, open(os.path.join(OUT, "psd_meta.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(world, open(os.path.join(OUT, "psd_vegoil_world.json"), "w"), ensure_ascii=False)
    json.dump(ctry, open(os.path.join(OUT, "psd_palm_countries.json"), "w"), ensure_ascii=False)
    print("saved ->", OUT)


if __name__ == "__main__":
    main()
