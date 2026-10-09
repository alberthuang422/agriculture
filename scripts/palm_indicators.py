# -*- coding: utf-8 -*-
"""棕榈油 PSD 核心指标计算
产出: data/fundamentals/palm/palm_indicators.json + palm_world_balance.csv
指标: 全球平衡表 / STU及分位 / 面积-单产分解 / 工业vs食用消费 / 油脂板块份额 / P-D价差
"""
import json, os, csv, statistics as st

P = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "..", "data", "fundamentals", "palm"))
W = json.load(open(os.path.join(P, "psd_vegoil_world.json")))
C = json.load(open(os.path.join(P, "psd_palm_countries.json")))
PN = os.path.normpath(os.path.join(P, "..", "..", "price", "palm"))
YEARS = [str(y) for y in range(1989, 2027)]


def flat(cell):
    return {r["attributeId"]: r["value"] for r in cell}


def g(cc, y, aid, default=0.0):
    d = W.get(cc, {}).get(y)
    return flat(d).get(aid, default) if d else default


PALM, SOY, COCO, PKO, RAPE, SUN = "4243000", "4232000", "4242000", "4244000", "4239100", "4236000"
OILS = {"palm": PALM, "soyoil": SOY, "rapeseed": RAPE, "sunflower": SUN, "coconut": COCO, "pko": PKO}

# ---------- 1) 全球棕榈油平衡表 ----------
world = []
for y in YEARS:
    d = W.get(PALM, {}).get(y)
    if not d:
        continue
    f = flat(d)
    prod, dc, es, exp = f.get(28, 0), f.get(125, 0), f.get(176, 0), f.get(88, 0)
    world.append({
        "my": y, "area_kha": f.get(4, 0), "yield": round(f.get(184, 0), 4),
        "beg": f.get(20, 0), "prod": prod, "imp": f.get(57, 0),
        "dom_cons": dc, "industrial": f.get(140, 0), "food": f.get(149, 0),
        "feed_waste": f.get(161, 0), "exp": exp, "end": es,
        "surplus": round(prod - dc, 1),
        "stu": round(100.0 * es / dc, 2) if dc else None,
        "biodiesel_share": round(100.0 * f.get(140, 0) / dc, 1) if dc else None,
        "vintage": "%s-%s" % (d[0]["calendarYear"], d[0]["month"]),
    })

# STU 历史分位（多窗口披露）
def pct_rank(series, val):
    below = sum(1 for v in series if v < val)
    return round(100.0 * (below + 0.5) / len(series), 1)

stu_all = [w["stu"] for w in world if w["my"] < "2026"]
for win, lo in [("1989-2025", "1989"), ("2010-2025", "2010"), ("2000-2025", "2000")]:
    s = [w["stu"] for w in world if lo <= w["my"] < "2026"]
    cur = world[-1]["stu"]
    world[-1]["stu_pctile_" + win] = pct_rank(s, cur)
    print("STU %s: 当前 %.1f%% → 分位 %.1f%% (n=%d, 区间 %.1f-%.1f)" % (
        win, cur, pct_rank(s, cur), len(s), min(s), max(s)))

# ---------- 2) 油脂板块：产量份额 + STU ----------
oils = {}
for name, cc in OILS.items():
    rows = []
    for y in YEARS:
        d = W.get(cc, {}).get(y)
        if not d: continue
        f = flat(d)
        rows.append({"my": y, "prod": f.get(28, 0), "cons": f.get(125, 0),
                     "end": f.get(176, 0), "exp": f.get(88, 0),
                     "stu": round(100.0 * f.get(176, 0) / f.get(125, 0), 2) if f.get(125) else None})
    oils[name] = rows

# ---------- 3) 主产国：印尼 vs 马来西亚 ----------
ctry = {}
CN = {"MY": "Malaysia", "ID": "Indonesia", "IN": "India", "CH": "China", "E4": "EU",
      "PK": "Pakistan", "BG": "Bangladesh", "TH": "Thailand", "US": "USA", "BR": "Brazil"}
for cc, nm in CN.items():
    rows = []
    for y in YEARS:
        d = C.get(cc, {}).get(y)
        if not d: continue
        f = flat(d)
        rows.append({"my": y, "area_kha": f.get(4, 0), "yield": f.get(184, 0),
                     "prod": f.get(28, 0), "dom": f.get(125, 0),
                     "industrial": f.get(140, 0), "food": f.get(149, 0),
                     "imp": f.get(57, 0), "exp": f.get(88, 0), "end": f.get(176, 0),
                     "beg": f.get(20, 0),
                     "stu": round(100.0 * f.get(176, 0) / f.get(125, 0), 2) if f.get(125) else None,
                     "net_trade": round(f.get(88, 0) - f.get(57, 0), 1)})
    ctry[cc] = rows

# ---------- 4) 价格（IMF/FRED 月度）----------
def fred_csv(path, colname):
    out = {}
    if not os.path.exists(path): return out
    for line in open(path, encoding="utf-8", errors="ignore"):
        p = line.strip().split(",")
        if len(p) < 2 or not p[0][:4].isdigit(): continue
        try: out[p[0][:7]] = float(p[1])
        except ValueError: pass
    return out

price = {
    "palm": fred_csv(os.path.join(PN, "fred_PPOILUSDM.csv"), "palm"),
    "soy": fred_csv(os.path.join(PN, "fred_PSOILUSDM.csv"), "soy"),
    "sun": fred_csv(os.path.join(PN, "fred_PSUNOUSDM.csv"), "sun"),
    "rape": fred_csv(os.path.join(PN, "fred_PROILUSDM.csv"), "rape"),
    "brent": fred_csv(os.path.join(PN, "fred_BRENT.csv"), "brent"),
    "usdmyr": fred_csv(os.path.join(PN, "fred_USDMYR.csv"), "myr"),
}
# 世行长序列（1960-2024）补前段
wb = {}
wbpath = os.path.join(PN, "wb_cmo_vegoil_monthly_1960_2024.csv")
if os.path.exists(wbpath):
    for r in csv.DictReader(open(wbpath, encoding="utf-8")):
        ym = r["ym"].replace("M", "-")
        wb[ym] = {k: (float(v) if v else None) for k, v in r.items() if k != "ym"}

# 合并：IMF 优先（更新），世行补 1960-1999
allpm = {}
for ym, v in wb.items():
    allpm[ym] = {"palm": v.get("palm"), "soy": v.get("soyoil"), "brent": v.get("brent")}
for ym in sorted(price["palm"]):
    allpm[ym] = {"palm": price["palm"][ym], "soy": price["soy"].get(ym),
                 "brent": price["brent"].get(ym), "rape": price["rape"].get(ym),
                 "sun": price["sun"].get(ym), "usdmyr": price["usdmyr"].get(ym)}

pd_spread = {ym: round(v["soy"] - v["palm"], 1)
             for ym, v in allpm.items() if v.get("soy") and v.get("palm")}
vals = list(pd_spread.values())
print("\n=== 豆油-棕榈油价差 P-D spread ($/mt) ===")
print("全样本 %d 个月 (%s → %s)" % (len(vals), min(pd_spread), max(pd_spread)))
print("mean %.0f | median %.0f | p10 %.0f | p90 %.0f | max %.0f (%s) | min %.0f (%s)" % (
    st.mean(vals), st.median(vals), sorted(vals)[len(vals)//10], sorted(vals)[len(vals)*9//10],
    max(vals), max(pd_spread, key=pd_spread.get), min(vals), min(pd_spread, key=pd_spread.get)))
latest = sorted(pd_spread)[-1]
print("最新 %s = %.0f → 分位 %.1f%%" % (latest, pd_spread[latest], pct_rank(vals, pd_spread[latest])))

# ---------- 5) ONI ----------
_SEAS = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
         "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}
oni = {}
for line in open(os.path.join(PN, "oni.txt")):
    p = line.split()
    if len(p) == 4 and p[1].isdigit() and p[0] in _SEAS:
        oni["%s-%02d-%s" % (p[1], _SEAS[p[0]], p[0])] = float(p[3])
print("\n=== ONI 最近 14 期（时间序）===")
for k in sorted(oni)[-14:]:
    v = oni[k]
    tag = "[强EN≥1.5]" if v >= 1.5 else "[EN]" if v >= 0.5 else "[LN]" if v <= -0.5 else "[中性]"
    print("  %s : %+.2f %s" % (k, v, tag))
# 历史强 EN 事件（峰值 ≥1.5）识别：用于单产滞后回归
peak_ev = []
ks = sorted(oni)
for i, k in enumerate(ks):
    if oni[k] >= 1.5 and (i == 0 or oni[ks[i-1]] < oni[k]) and \
       (i == len(ks)-1 or oni[ks[i+1]] <= oni[k]):
        peak_ev.append((k, oni[k]))
print("\n=== 历史强/超强厄尔尼诺峰值事件（ONI≥1.5）===")
for k, v in peak_ev:
    print("  %s : %+.2f" % (k, v))

# ---------- 输出 ----------
out = {"asOf": "2026-10-07", "source": "USDA FAS PSD API (vintage 2026-09) + IMF/FRED + CPC ONI",
       "marketYearNote": "棕榈油市场年 = 10月-次年9月。MY2026 = 2026/27 = 2026-10~2027-09（进行中，预测值）；MY2025 = 2025/26（刚收官）",
       "consumptionNote": "棕榈油消费码 = 125 Domestic Consumption（= 140工业 + 149食用 + 161饲料损耗），与糖的 126 不同",
       "world": world, "oils": oils, "countries": ctry, "countryNames": CN,
       "price_monthly": [{"ym": k, **v, "pd_spread": pd_spread.get(k)} for k, v in sorted(allpm.items()) if k >= "1980-01"],
       "oni": oni}
json.dump(out, open(os.path.join(P, "palm_indicators.json"), "w"), ensure_ascii=False)

_flds = ["my", "area_kha", "yield", "beg", "prod", "imp", "dom_cons", "industrial",
         "food", "feed_waste", "exp", "end", "surplus", "stu", "biodiesel_share", "vintage"]
with open(os.path.join(P, "palm_world_balance.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=_flds, extrasaction="ignore")
    w.writeheader(); w.writerows(world)

# ---------- 摘要打印 ----------
print("\n=== 全球棕榈油平衡表（千吨，MY 10-9月）===")
print("%-6s %8s %7s %9s %9s %9s %8s %8s %6s" % ("MY", "面积kha", "单产", "产量", "工业", "食用", "期末库存", "出口", "STU%"))
for w_ in world[-12:]:
    print("%-6s %8.0f %7.3f %9.0f %9.0f %9.0f %8.0f %8.0f %6.1f" % (
        w_["my"], w_["area_kha"], w_["yield"], w_["prod"], w_["industrial"],
        w_["food"], w_["end"], w_["exp"], w_["stu"]))

print("\n=== 印尼 vs 马来西亚（MY2026）===")
for cc in ["ID", "MY"]:
    r = [x for x in ctry[cc] if x["my"] == "2026"][0]
    print("  %-10s 面积%.0fkha 单产%.2f 产量%.0f 国内%.0f(工业%.0f) 出口%.0f 期末%.0f STU%.1f%%" % (
        CN[cc], r["area_kha"], r["yield"], r["prod"], r["dom"], r["industrial"], r["exp"], r["end"], r["stu"] or 0))

print("\n=== 油脂板块产量份额 ===")
for y in ["2000", "2010", "2020", "2026"]:
    tot = sum(next((r["prod"] for r in rows if r["my"] == y), 0) for rows in oils.values())
    line = "  %s (总%.0f): " % (y, tot)
    for nm, rows in oils.items():
        p = next((r["prod"] for r in rows if r["my"] == y), 0)
        line += "%s %.1f%% | " % (nm, 100.0*p/tot if tot else 0)
    print(line)
print("\nsaved ->", os.path.join(P, "palm_indicators.json"))
