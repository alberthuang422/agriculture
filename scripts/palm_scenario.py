# -*- coding: utf-8 -*-
"""
棕榈油库存分层 + 厄尔尼诺情景分析 + 需求弹性
沿用糖项目 skill 方法论：
- 库存按"释放决策权"分层，不按地理分层
- 情景推演只改分子（期末库存 = 基线 + 产量偏差），不重复计基线盈余
- 分位给多窗口
产出: data/fundamentals/palm/palm_scenario.json
"""
import json, os, statistics as st

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "data", "fundamentals", "palm"))
I = json.load(open(os.path.join(BASE, "palm_indicators.json")))
E = json.load(open(os.path.join(BASE, "palm_enso_lag.json")))
W = {w["my"]: w for w in I["world"]}
C = I["countries"]
CN = I["countryNames"]


def get(cc, my, k):
    for r in C[cc]:
        if r["my"] == my:
            return r.get(k) or 0
    return 0


def pr(series, v):
    return round(100.0 * (sum(1 for x in series if x < v) + .5) / len(series), 1)


OUT = {}
MY = "2026"          # 2026/27，进行中
PREV = "2025"        # 2025/26，刚收官
w26, w25 = W[MY], W[PREV]

print("=" * 84)
print("一、全球棕榈油供需松紧定位（MY2026 = 2026/27，vintage 2026-09）")
print("=" * 84)
print("  产量 %.1f Mt | 消费 %.1f Mt | 盈余 %.2f Mt | 期末库存 %.2f Mt | STU %.1f%%" % (
    w26["prod"]/1000, w26["dom_cons"]/1000, w26["surplus"]/1000, w26["end"]/1000, w26["stu"]))
print("  上年 MY2025: 产量 %.1f | 消费 %.1f | 盈余 %.2f | 期末 %.2f | STU %.1f%%" % (
    w25["prod"]/1000, w25["dom_cons"]/1000, w25["surplus"]/1000, w25["end"]/1000, w25["stu"]))
print("  Δ产量 %+.1f Mt | Δ消费 %+.1f Mt | Δ盈余 %+.2f Mt | Δ库存 %+.2f Mt | ΔSTU %+.1fpct" % (
    (w26["prod"]-w25["prod"])/1000, (w26["dom_cons"]-w25["dom_cons"])/1000,
    (w26["surplus"]-w25["surplus"])/1000, (w26["end"]-w25["end"])/1000, w26["stu"]-w25["stu"]))

# ---------- 库存分层 ----------
print()
print("=" * 84)
print("二、库存分层（按释放决策权，非地理）")
print("=" * 84)
layers = []
tot = w26["end"]
for cc in [c for c in ["ID", "MY", "IN", "CH", "E4", "PK", "BG", "TH", "US", "BR",
                       "MX", "EG", "NI", "KE", "VM", "RP"] if c in C]:
    e = get(cc, MY, "end")
    nt = get(cc, MY, "exp") - get(cc, MY, "imp")
    ind = get(cc, MY, "industrial")
    dom = get(cc, MY, "dom")
    if e <= 0: continue
    layers.append({"cc": cc, "name": CN.get(cc, cc), "end": e, "net_trade": nt,
                   "industrial": ind, "dom": dom,
                   "bio_lock_pct": round(100.0*ind/dom, 1) if dom else 0,
                   "share": round(100.0*e/tot, 1)})
layers.sort(key=lambda x: -x["end"])
covered = sum(l["end"] for l in layers)
print("  %-10s %8s %7s %10s %9s %s" % ("国家", "期末库存", "份额%", "净贸易", "工业/国内", "分层"))
for l in layers:
    nt = l["net_trade"]
    if nt > 500:
        tier = "① 净出口国持有（可立即动用）"
    elif abs(nt) <= 500:
        tier = "② 平衡型（自用，部分可动）"
    else:
        tier = "③ 净进口国持有（只能'少进口'间接影响）"
    print("  %-10s %8.0f %6.1f%% %+10.0f %8.1f%%  %s" % (
        l["name"], l["end"], l["share"], nt, l["bio_lock_pct"], tier))
print("  %-10s %8.0f %6.1f%%   （16 主产消国小计；其余国家合计 %.0f 千吨）" % (
    "小计", covered, 100.0*covered/tot, tot - covered))

# 硬缓冲 = 净出口国持有，但要扣掉生柴强制锁定部分
t1 = [l for l in layers if l["net_trade"] > 500]
t1_tot = sum(l["end"] for l in t1)
# 印尼 B50 锁定：工业消费中约 2/3 为生柴（GAPKI 2026-05：生柴1035/总消费2078=49.8%，工业口径）
# 用保守口径：印尼工业消费 15850 中 B50 生柴约占 (1035/2141*12)/23725 ≈ 国内消费的52%
id_bio = get("ID", MY, "industrial")
id_bio_frac = 0.85   # 工业消费中生柴占比（其余为油脂化学）GAPKI: 生柴1035 vs 油化187 → 85%
id_locked = id_bio * id_bio_frac
print()
print("  ① 净出口国持有合计 = %.0f 千吨（全球库存 %.1f%%）" % (t1_tot, 100.0*t1_tot/tot))
print("     其中印尼工业消费（生柴为主）约 %.0f 千吨 × %.0f%% = %.0f 千吨受 B50 强制掺混锁定" % (
    id_bio, 100*id_bio_frac, id_locked))
hard = t1_tot
print("     ⇒ 名义硬缓冲 %.0f 千吨 = 世界消费 %.1f 天 / 世界出口 %.1f%%" % (
    hard, hard/w26["dom_cons"]*365, 100.0*hard/w26["exp"]))

# ---------- 历史对比：净出口国持有层的厚度 ----------
print()
print("  净出口国持有层（印尼+马来）历史序列：")
hist = []
for my in sorted(W):
    a = get("ID", my, "end") + get("MY", my, "end")
    if a > 0:
        wt = W[my]["end"]
        hist.append((my, a, 100.0*a/wt if wt else 0))
for my, a, s in hist[-12:]:
    print("    MY%s  ID+MY 期末 %.0f 千吨 = 全球库存 %.1f%%" % (my, a, s))
OUT["stock_layers"] = layers
OUT["layer_hist"] = [{"my": m, "id_my_end": a, "share_pct": round(s, 1)} for m, a, s in hist]

# ---------- 三、厄尔尼诺情景 ----------
print()
print("=" * 84)
print("三、厄尔尼诺情景推演（只改分子：期末库存 = 基线 + 产量偏差）")
print("=" * 84)
ev = E["events"]
# 历史强EN马来单产偏差
my_devs = [e["my_yield_dev"] for e in ev if e["my_yield_dev"] is not None and e["my"] != "2026"]
id_devs = [e["id_yield_dev"] for e in ev if e["id_yield_dev"] is not None and e["my"] != "2026"]
w_devs = [e["world_yield_dev"] for e in ev if e["world_yield_dev"] is not None and e["my"] != "2026"]
print("  历史强EN事件（n=%d，剔本轮）单产偏差%%：" % len(my_devs))
print("    马来西亚  均值 %+.1f  中位 %+.1f  区间 [%+.1f, %+.1f]" % (
    st.mean(my_devs), st.median(my_devs), min(my_devs), max(my_devs)))
print("    印尼      均值 %+.1f  中位 %+.1f  区间 [%+.1f, %+.1f]" % (
    st.mean(id_devs), st.median(id_devs), min(id_devs), max(id_devs)))
print("    全球      均值 %+.1f  中位 %+.1f  区间 [%+.1f, %+.1f]" % (
    st.mean(w_devs), st.median(w_devs), min(w_devs), max(w_devs)))
print("    最严重参照：MY2015 强EN(峰值ONI+2.59) → 马来单产 %.1f%% / 印尼 %.1f%% / 全球 %.1f%%" % (
    next(e["my_yield_dev"] for e in ev if e["my"] == "2015"),
    next(e["id_yield_dev"] for e in ev if e["my"] == "2015"),
    next(e["world_yield_dev"] for e in ev if e["my"] == "2015")))

# 外部共识
consensus = [
    {"src": "彭博 7 位分析师调查 (2026-09)", "my2027_id": 49000, "my2027_my": 19500,
     "note": "两国合计同比 −3%"},
    {"src": "GAPKI 2027 产量降幅指引", "chg": "−5% → −3%（已下修收窄）",
     "note": "承认减产但烈度低于最悲观"},
    {"src": "USDA PSD MY2026 (vintage 2026-09)", "my": 19600, "id": 47200,
     "note": "马来 −3.0% / 印尼 +1.1%"},
    {"src": "USDA FAS GAIN 马来报告 (2026-07-01)", "my2026_my": 19700,
     "note": "已下调 30 万吨，理由=EN干旱，但影响落在 MY2026/27 第3-4季"},
]
print()
print("  外部机构 2027 年产量指引：")
for c in consensus:
    print("    %-38s %s" % (c["src"], c.get("note", "")))

# 情景阶梯：以 MY2026 为基线，推 MY2027
base_p = w26["prod"]
base_c = w26["dom_cons"]
base_e = w26["end"]
print()
print("  情景阶梯（作用于 MY2027 = 2027/28；基线 = MY2026 水平外推）")
print("  %-28s %10s %10s %8s %10s" % ("情景", "产量Δ%", "产量Mt", "STU%", "全球分位"))
scen = []
stu_pool = [W[y]["stu"] for y in sorted(W) if y <= "2025"]
for nm, dev in [("USDA MY2026 基线（无新增减产）", 0.0),
                ("彭博调查共识（两国 −3%）", -3.0),
                ("GAPKI 悲观情形（−5%）", -5.0),
                ("历史强EN中位（马来−2.0/印尼−6.9）", -5.5),
                ("MY2015 类比（全球单产 −9.8%）", -9.8),
                ("极端：马来 −15.8%（2015实际）全球折算", -15.8)]:
    p = base_p * (1 + dev/100)
    # 消费按 MY2025→MY2026 的趋势增速外推
    cg = (w26["dom_cons"] - w25["dom_cons"]) / w25["dom_cons"]
    c = base_c * (1 + cg)
    e = base_e + (p - base_p) - (c - base_c)
    stu = 100.0*e/c if c else 0
    scen.append({"name": nm, "dev_pct": dev, "prod": p, "cons": c, "end": e,
                 "stu": round(stu, 2), "pctile": pr(stu_pool, stu)})
    print("  %-28s %+9.1f%% %10.1f %7.1f%% %9.1f%%" % (nm, dev, p/1000, stu, pr(stu_pool, stu)))
OUT["scenarios"] = scen

# 库存覆盖月数
print()
print("  缓冲覆盖能力（MY2026 基线）：")
print("    全球期末库存 %.0f 千吨 = 全球消费 %.2f 个月 = %.0f 天" % (
    base_e, base_e/(base_c/12), base_e/base_c*365))
print("    净出口国持有 %.0f 千吨 = 全球消费 %.2f 个月" % (t1_tot, t1_tot/(base_c/12)))
OUT["buffer"] = {"world_end": base_e, "world_cons": base_c, "world_exp": w26["exp"],
                 "months_cover": round(base_e/(base_c/12), 2),
                 "netexp_layer": t1_tot, "netexp_months": round(t1_tot/(base_c/12), 2)}

# ---------- 四、需求侧：生柴政策弹性 ----------
print()
print("=" * 84)
print("四、需求侧结构：生物柴油的锁定效应")
print("=" * 84)
print("  %-6s %9s %9s %9s %9s" % ("MY", "工业消费", "食用消费", "工业占比", "印尼工业"))
for my in ["2000", "2005", "2010", "2015", "2020", "2024", "2025", "2026"]:
    if my in W:
        ww = W[my]
        print("  %-6s %9.0f %9.0f %8.1f%% %9.0f" % (
            my, ww["industrial"], ww["food"], ww["biodiesel_share"], get("ID", my, "industrial")))
id_ind_15 = get("ID", "2015", "industrial"); id_ind_26 = get("ID", MY, "industrial")
print()
print("  印尼工业消费 MY2015 %.0f → MY2026 %.0f 千吨，增 %.0f 千吨（+%.0f%%）" % (
    id_ind_15, id_ind_26, id_ind_26-id_ind_15, 100*(id_ind_26-id_ind_15)/id_ind_15))
my_ind_15 = get("MY", "2015", "industrial"); my_ind_26 = get("MY", MY, "industrial")
print("  马来工业消费 MY2015 %.0f → MY2026 %.0f 千吨，增 %.0f 千吨（+%.0f%%）" % (
    my_ind_15, my_ind_26, my_ind_26-my_ind_15, 100*(my_ind_26-my_ind_15)/my_ind_15))
# B50 增量
print()
print("  B40→B50 增量（GAPKI / 印尼能矿部口径）：")
print("    GAPKI: B50 年需 CPO 1,600 万吨 vs B40 1,300 万吨 → 增 300 万吨")
print("    GAPKI (2026-05): 完全运行后增量 300-350 万吨/年；2026 年初阶段 150-170 万吨")
print("    印尼能矿部: B50 将棕榈油吸收量从 1,520 万吨提升至 1,630-1,700 万吨")
print("    GAPKI 测算 B50 使 2026 下半年出口减少约 200 万吨（≈27 亿美元）")
b50 = 3000.0
print("    ⇒ 取中值 +%.0f 千吨 CPO 内需 = 全球消费 %.1f%%，相当于全球库存 %.1f 个月" % (
    b50, 100*b50/base_c, b50/(base_c/12)))
OUT["biodiesel"] = {"id_industrial_2015": id_ind_15, "id_industrial_2026": id_ind_26,
                    "my_industrial_2015": my_ind_15, "my_industrial_2026": my_ind_26,
                    "b50_increment_kt": b50}

# ---------- 五、vintage 偏离核查 ----------
print()
print("=" * 84)
print("五、vintage 偏离核查（USDA vs 本土机构最新数据）")
print("=" * 84)
mpob_2026 = {"2026-01": 282, "2026-02": 270, "2026-03": 227, "2026-04": 230,
             "2026-05": 242, "2026-06": 254, "2026-07": 263, "2026-08": 282,
             "2026-09": 337}
print("  MPOB 马来西亚月度总库存（万吨，已核实各月官方发布）：")
print("   ", " / ".join("%s=%.0f" % (k[5:], v) for k, v in sorted(mpob_2026.items())))
psd_my_end = get("MY", "2025", "end")   # MY2025 = 2025/26，期末 2026-09
print("  USDA PSD MY2025（期末 = 2026年9月）马来期末库存 = %.0f 千吨 = %.0f 万吨" % (psd_my_end, psd_my_end/10))
sep = mpob_2026["2026-09"]
print("  MPOB/路透调查 2026年9月实际预期 = %.0f 万吨" % sep)
print("  ⇒ 偏离 = %.0f 万吨，USDA 低估 %.1f%%（vintage 2026-09 未反映9月累库）" % (
    sep - psd_my_end/10, 100*(sep - psd_my_end/10)/sep))
aug = mpob_2026["2026-08"]
print("  即使按 8月已公布实绩 %.0f 万吨，USDA 仍低估 %.0f 万吨（%.1f%%）" % (
    aug, aug - psd_my_end/10, 100*(aug-psd_my_end/10)/aug))
print()
print("  印尼口径偏离：")
print("    GAPKI 2026-05 月末库存 = 304.2 万吨（1-5月累计口径）")
print("    USDA PSD MY2026 印尼期末（= 2027年9月，预测）= %.0f 万吨" % (get("ID", MY, "end")/10))
print("    USDA PSD MY2025 印尼期末（= 2026年9月）= %.0f 万吨" % (get("ID", "2025", "end")/10))
print("    GAPKI 2025-12 月末库存 = 206.8 万吨 → USDA MY2025 期末（2026-09）%.0f 万吨" % (get("ID", "2025", "end")/10))
OUT["vintage"] = {"mpob_2026_stocks_wt": mpob_2026, "psd_my_end_kt": psd_my_end,
                  "gap_wt": round(sep - psd_my_end/10, 1),
                  "gap_pct": round(100*(sep-psd_my_end/10)/sep, 1)}

json.dump(OUT, open(os.path.join(BASE, "palm_scenario.json"), "w"), ensure_ascii=False, indent=1)
print("\nsaved ->", os.path.join(BASE, "palm_scenario.json"))
