# -*- coding: utf-8 -*-
"""棕榈油补充分析：面积-单产分解 / 老龄树 / 价格分位 / 贸易集中度 / 需求弹性"""
import json, os, statistics as st

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "data", "fundamentals", "palm"))
PN = os.path.normpath(os.path.join(BASE, "..", "..", "price", "palm"))
I = json.load(open(os.path.join(BASE, "palm_indicators.json")))
C = I["countries"]; W = {w["my"]: w for w in I["world"]}
OUT = {}


def g(cc, my, k):
    for r in C.get(cc, []):
        if r["my"] == my:
            return r.get(k) or 0
    return 0


def pr(s, v):
    return round(100.0*(sum(1 for x in s if x < v)+.5)/len(s), 1)


# ---------- 1) 面积 vs 单产分解 ----------
print("=" * 88)
print("一、产量增长分解：面积扩张 vs 单产提升（棕榈油供给的两个引擎）")
print("=" * 88)
print("  %-6s | %-24s | %-24s | %s" % ("MY", "全球 面积kha/单产/产量", "印尼", "马来"))
for my in ["1990", "2000", "2005", "2010", "2015", "2020", "2024", "2025", "2026"]:
    if my not in W: continue
    w = W[my]
    print("  %-6s | %7.0f / %5.2f / %6.0f | %7.0f / %5.2f / %6.0f | %6.0f / %5.2f / %6.0f" % (
        my, w["area_kha"], w["yield"], w["prod"]/1000,
        g("ID", my, "area_kha"), g("ID", my, "yield"), g("ID", my, "prod")/1000,
        g("MY", my, "area_kha"), g("MY", my, "yield"), g("MY", my, "prod")/1000))

# 复合增长率
def cagr(cc, k, y0, y1, src=None):
    if src is None:
        a, b = W[y0][k], W[y1][k]
    else:
        a, b = g(cc, y0, k), g(cc, y1, k)
    n = int(y1) - int(y0)
    if a <= 0 or b <= 0 or n <= 0: return None
    return 100*((b/a)**(1.0/n) - 1)

print()
print("  复合年增长率（CAGR, %%/年）：")
print("  %-14s %10s %10s %10s %10s" % ("期间", "全球面积", "全球单产", "全球产量", "备注"))
for y0, y1 in [("1990", "2000"), ("2000", "2010"), ("2010", "2020"), ("2020", "2026"), ("2015", "2026")]:
    print("  %-14s %+9.2f %+9.2f %+9.2f" % ("%s-%s" % (y0, y1),
          cagr(None, "area_kha", y0, y1) or 0, cagr(None, "yield", y0, y1) or 0,
          cagr(None, "prod", y0, y1) or 0))
print()
print("  分国 2015→2026：")
for cc, nm in [("ID", "印尼"), ("MY", "马来")]:
    print("    %s 面积 %+.2f%%/年 | 单产 %+.2f%%/年 | 产量 %+.2f%%/年" % (
        nm, cagr(cc, "area_kha", "2015", "2026", 1), cagr(cc, "yield", "2015", "2026", 1),
        cagr(cc, "prod", "2015", "2026", 1)))
    print("       → 面积 %.0f→%.0f kha (%+.0f) | 单产 %.2f→%.2f (%+.2f)" % (
        g(cc, "2015", "area_kha"), g(cc, "2026", "area_kha"),
        g(cc, "2026", "area_kha")-g(cc, "2015", "area_kha"),
        g(cc, "2015", "yield"), g(cc, "2026", "yield"),
        g(cc, "2026", "yield")-g(cc, "2015", "yield")))

# 面积增长贡献 vs 单产贡献分解（对数分解）
import math
print()
print("  产量增长归因（对数分解，2015→2026）：")
for cc, nm in [(None, "全球"), ("ID", "印尼"), ("MY", "马来")]:
    if cc is None:
        a0, a1 = W["2015"]["area_kha"], W["2026"]["area_kha"]
        y0_, y1_ = W["2015"]["yield"], W["2026"]["yield"]
    else:
        a0, a1 = g(cc, "2015", "area_kha"), g(cc, "2026", "area_kha")
        y0_, y1_ = g(cc, "2015", "yield"), g(cc, "2026", "yield")
    if a0 > 0 and a1 > 0 and y0_ > 0 and y1_ > 0:
        la, ly = math.log(a1/a0), math.log(y1_/y0_)
        tot = la + ly
        print("    %-6s 面积贡献 %.0f%% | 单产贡献 %.0f%%  (ΔlnArea=%.4f, ΔlnYield=%.4f)" % (
            nm, 100*la/tot if tot else 0, 100*ly/tot if tot else 0, la, ly))
        OUT["attribution_" + (cc or "world")] = {"area_pct": round(100*la/tot, 1) if tot else None,
                                                "yield_pct": round(100*ly/tot, 1) if tot else None}

# ---------- 2) 贸易集中度 ----------
print()
print("=" * 88)
print("二、供给集中度与贸易结构")
print("=" * 88)
my = "2026"
idp, myp = g("ID", my, "prod"), g("MY", my, "prod")
tot_p = W[my]["prod"]
ide, mye = g("ID", my, "exp"), g("MY", my, "exp")
tot_e = W[my]["exp"]
print("  MY2026 产量集中度：印尼 %.1f Mt (%.1f%%) + 马来 %.1f Mt (%.1f%%) = %.1f%%" % (
    idp/1000, 100*idp/tot_p, myp/1000, 100*myp/tot_p, 100*(idp+myp)/tot_p))
print("  MY2026 出口集中度：印尼 %.1f Mt (%.1f%%) + 马来 %.1f Mt (%.1f%%) = %.1f%%" % (
    ide/1000, 100*ide/tot_e, mye/1000, 100*mye/tot_e, 100*(ide+mye)/tot_e))
print("  → 两国出口占全球出口 %.1f%%，而占全球产量 %.1f%%" % (
    100*(ide+mye)/tot_e, 100*(idp+myp)/tot_p))
print()
print("  主要进口方（MY2026，千吨）：")
imps = [(cc, g(cc, my, "imp")) for cc in C]
imps.sort(key=lambda x: -x[1])
tot_i = sum(v for _, v in imps)
cum = 0
for cc, v in imps[:8]:
    cum += v
    print("    %-12s %7.0f  份额 %5.1f%%  累计 %5.1f%%  (国内工业占 %.0f%%)" % (
        I["countryNames"].get(cc, cc), v, 100*v/tot_i, 100*cum/tot_i,
        100*g(cc, my, "industrial")/g(cc, my, "dom") if g(cc, my, "dom") else 0))
OUT["concentration"] = {"prod_top2_pct": round(100*(idp+myp)/tot_p, 1),
                        "exp_top2_pct": round(100*(ide+mye)/tot_e, 1),
                        "imports": [{"cc": c, "imp": v} for c, v in imps[:8]]}

# 出口/产量比 → 可贸易量弹性放大倍数
print()
print("  可贸易量弹性（1 ÷ 出口/产量）：产量跌1%%时出口需跌的%%（假设消费刚性）")
for cc, nm in [("ID", "印尼"), ("MY", "马来"), ("TH", "泰国")]:
    e_, p_ = g(cc, my, "exp"), g(cc, my, "prod")
    if p_: print("    %-6s 出口/产量 %5.1f%% → 放大 %.2fx" % (nm, 100*e_/p_, p_/e_ if e_ else 0))

# ---------- 3) 价格分位 ----------
print()
print("=" * 88)
print("三、价格定位（IMF/FRED 月度，美元/吨）")
print("=" * 88)
pm = {r["ym"]: r for r in I["price_monthly"]}
palm = {ym: r["palm"] for ym, r in pm.items() if r.get("palm")}
soy = {ym: r["soy"] for ym, r in pm.items() if r.get("soy")}
lat_ym = max(palm)
lat = palm[lat_ym]
pool_all = list(palm.values())
pool_10 = [v for ym, v in palm.items() if ym >= "2016-01"]
pool_5 = [v for ym, v in palm.items() if ym >= "2021-01"]
print("  棕榈油最新 %s = %.0f $/mt" % (lat_ym, lat))
print("    → 1980以来分位 %.1f%% (n=%d, 区间 %.0f-%.0f, 均值 %.0f)" % (
    pr(pool_all, lat), len(pool_all), min(pool_all), max(pool_all), st.mean(pool_all)))
print("    → 近10年分位   %.1f%% (n=%d, 区间 %.0f-%.0f, 均值 %.0f)" % (
    pr(pool_10, lat), len(pool_10), min(pool_10), max(pool_10), st.mean(pool_10)))
print("    → 近5年分位    %.1f%% (n=%d, 区间 %.0f-%.0f, 均值 %.0f)" % (
    pr(pool_5, lat), len(pool_5), min(pool_5), max(pool_5), st.mean(pool_5)))
print("  历史极值：最高 %.0f (%s) | 最低 %.0f (%s)" % (
    max(pool_all), max(palm, key=palm.get), min(pool_all), min(palm, key=palm.get)))
s_lat = soy[lat_ym]
print()
print("  豆油最新 %.0f $/mt → 1980以来分位 %.1f%%" % (s_lat, pr(list(soy.values()), s_lat)))
print("  P-D 价差 %.0f $/mt（豆油升水）" % (s_lat - lat))
print("    拆解 2024-12 → %s：棕榈油 %+.0f（%+.0f%%）| 豆油 %+.0f（%+.0f%%）" % (
    lat_ym, lat - palm["2024-12"], 100*(lat-palm["2024-12"])/palm["2024-12"],
    s_lat - soy["2024-12"], 100*(s_lat-soy["2024-12"])/soy["2024-12"]))
OUT["price"] = {"latest_ym": lat_ym, "palm": round(lat, 1), "soy": round(s_lat, 1),
                "spread": round(s_lat-lat, 1),
                "palm_pctile_all": pr(pool_all, lat), "palm_pctile_10y": pr(pool_10, lat),
                "palm_pctile_5y": pr(pool_5, lat),
                "palm_max": max(pool_all), "palm_max_ym": max(palm, key=palm.get),
                "palm_min": min(pool_all), "palm_min_ym": min(palm, key=palm.get),
                "palm_mean_all": round(st.mean(pool_all), 0)}

# 林吉特口径
myr = {ym: r.get("usdmyr") for ym, r in pm.items() if r.get("usdmyr")}
if lat_ym in myr:
    print("  USD/MYR %.3f → 林吉特口径约 %.0f MYR/mt（对比 BMD FCPO 2026-10-07 收盘：Oct RM4,310 / Dec RM4,524 / Mar27 RM4,834）" % (
        myr[lat_ym], lat*myr[lat_ym]))
    print("    → 期货曲线：Dec26 RM4,524 vs Mar27 RM4,834 = 远月升水 %.0f MYR (+%.1f%%) → Contango，反映近端累库、远端EN减产预期" % (
        4834-4524, 100*(4834-4524)/4524))

# ---------- 4) 需求弹性：工业 vs 食用 ----------
print()
print("=" * 88)
print("四、需求结构：工业（生柴+油化）已成为增量主引擎")
print("=" * 88)
rows = []
for my in sorted(W):
    w = W[my]
    rows.append({"my": my, "ind": w["industrial"], "food": w["food"], "tot": w["dom_cons"],
                 "share": w["biodiesel_share"]})
print("  期间           Δ工业(千吨)  Δ食用(千吨)  工业增量占总增量")
for y0, y1 in [("2000", "2010"), ("2010", "2020"), ("2020", "2026"), ("2015", "2026"), ("2025", "2026")]:
    a = next(r for r in rows if r["my"] == y0); b = next(r for r in rows if r["my"] == y1)
    di, df = b["ind"]-a["ind"], b["food"]-a["food"]
    print("  %-14s %+11.0f %+11.0f %14.0f%%" % (
        "%s→%s" % (y0, y1), di, df, 100*di/(di+df) if (di+df) else 0))
    OUT.setdefault("demand_growth", []).append({"period": "%s-%s" % (y0, y1), "d_ind": di, "d_food": df,
                                               "ind_share_pct": round(100*di/(di+df), 1) if (di+df) else None})

json.dump(OUT, open(os.path.join(BASE, "palm_supplement.json"), "w"), ensure_ascii=False, indent=1)
print("\nsaved ->", os.path.join(BASE, "palm_supplement.json"))
