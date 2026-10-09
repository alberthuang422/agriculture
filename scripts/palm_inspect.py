# -*- coding: utf-8 -*-
"""棕榈油 PSD 口径探查：属性可用性 + 恒等式校验 + 市场年窗口"""
import json, os, collections
P = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "data", "fundamentals", "palm"))
W = json.load(open(os.path.join(P, "psd_vegoil_world.json")))
C = json.load(open(os.path.join(P, "psd_palm_countries.json")))
ATTR = {x["attributeId"]: x["attributeName"]
        for x in json.load(open("/tmp/attrs.json"))}

def flat(cell):
    """list of attribute rows -> {aid: value}"""
    d = {}
    for r in cell:
        d[r["attributeId"]] = r["value"]
    return d

# 1) 全球棕榈油：哪些属性有值、哪些年份有值
print("=" * 70)
print("全球 Oil,Palm 属性可用性（有值年份数 / 38）")
print("=" * 70)
cnt = collections.Counter()
for y, cell in W["4243000"].items():
    for r in cell:
        if r["value"] not in (None, 0):
            cnt[r["attributeId"]] += 1
for aid, n in sorted(cnt.items()):
    print("  %-4d %-32s %d" % (aid, ATTR.get(aid, "?"), n))

# 2) 恒等式校验：棕榈油用 125 还是 126
print()
print("=" * 70)
print("恒等式校验（全球 Oil,Palm）")
print("=" * 70)
bad_supply = bad_dist = 0
for y in sorted(W["4243000"]):
    d = flat(W["4243000"][y])
    beg, prod, imp = d.get(20, 0), d.get(28, 0), d.get(57, 0)
    ts, exp, es, td = d.get(86, 0), d.get(88, 0), d.get(176, 0), d.get(178, 0)
    dc = d.get(125, 0)
    s1 = beg + prod + imp
    s2 = dc + exp + es
    if abs(s1 - ts) > 1:
        bad_supply += 1
        print("  %s 供给不平: beg+prod+imp=%s vs TotalSupply=%s" % (y, s1, ts))
    if abs(s2 - td) > 1 or abs(s2 - s1) > 1:
        bad_dist += 1
        print("  %s 分配不平: DomCons+exp+ES=%s vs TD=%s (supply=%s)" % (y, s2, td, s1))
print("  供给不平 %d 年 / 分配不平 %d 年" % (bad_supply, bad_dist))

# 125 分解校验
print()
print("  DomCons(125) 分解 = Industrial(140)+Food(149)+FeedWaste(161):")
for y in ["2020", "2024", "2025", "2026"]:
    d = flat(W["4243000"][y])
    parts = d.get(140, 0) + d.get(149, 0) + d.get(161, 0)
    print("    %s: 125=%s | 140+149+161=%s | diff=%s" % (
        y, d.get(125), parts, d.get(125, 0) - parts))

# 3) 各国属性可用性（工业消费=生柴代理是否可得）
print()
print("=" * 70)
print("分国属性可用性（Oil,Palm MY2026）")
print("=" * 70)
for cc in ["MY", "ID", "IN", "CH", "E4"]:
    d = flat(C[cc]["2026"])
    print("  %s: " % cc + ", ".join("%s(%d)=%.0f" % (ATTR.get(a, a)[:16], a, v)
                                    for a, v in sorted(d.items()) if v))

# 4) vintage 分布（国家级，棕榈油）
print()
print("=" * 70)
print("vintage（calendarYear-month）分布 · 棕榈油国家级")
print("=" * 70)
v = collections.Counter()
for cc, yrs in C.items():
    for y, cell in yrs.items():
        v["%s-%s" % (cell[0]["calendarYear"], cell[0]["month"])] += 1
for k, n in sorted(v.items()):
    print("  %s : %d 条" % (k, n))

# 5) 市场年窗口 —— 从 FAS Oilseeds 报告确认
print()
print("=" * 70)
print("全球平衡表关键年份（千吨）")
print("=" * 70)
hdr = "%-6s %8s %8s %8s %8s %8s %8s %7s %7s"
print(hdr % ("MY", "面积kha", "单产", "产量", "工业", "食用", "期末库存", "出口", "STU%"))
for y in sorted(W["4243000"])[-14:]:
    d = flat(W["4243000"][y])
    stu = 100.0 * d.get(176, 0) / d.get(125, 1) if d.get(125) else 0
    print(hdr % (y, "%.0f" % d.get(4, 0), "%.3f" % d.get(184, 0), "%.0f" % d.get(28, 0),
                 "%.0f" % d.get(140, 0), "%.0f" % d.get(149, 0), "%.0f" % d.get(176, 0),
                 "%.0f" % d.get(88, 0), "%.1f" % stu))
