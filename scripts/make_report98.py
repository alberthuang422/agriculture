# -*- coding: utf-8 -*-
"""生成 98 号报告：全球甘蔗面积与单产 20 年全景（2005–2024）
数据源: OWID(FAOSTAT Production 2025 release) 甘蔗产量/单产；面积 = 产量 / 单产
"""
import json, os, csv

BASE = "C:/Users/Administrator/Desktop/农业/data/fundamentals/sugar"
OUT_DIR = "C:/Users/Administrator/Desktop/农业/reports/98_甘蔗面积单产全景_2005_2024"
os.makedirs(OUT_DIR, exist_ok=True)

S = json.load(open(os.path.join(BASE, "sugarcane_stats_report.json"), encoding="utf-8"))
CSV_PATH = os.path.join(BASE, "sugarcane_area_yield_2005_2024.csv")

# ---- 读分国序列 ----
rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))
per = {}
for r in rows:
    per.setdefault(r["country_cn"], {})[int(r["year"])] = {
        "area": float(r["area_1000ha"]), "yield": float(r["yield_t_per_ha"])}

countries_order = ["巴西", "印度", "泰国", "中国", "巴基斯坦", "墨西哥",
                   "印尼", "美国", "澳大利亚", "哥伦比亚", "危地马拉"]

DATA = {
    "Y": list(range(2005, 2025)),
    "world_area": [round(r["area"], 1) for r in S["world_series"]],
    "world_yield": [round(r["yield"], 2) for r in S["world_series"]],
    "world_prod": [round(r["prod"] / 1e6, 1) for r in S["world_series"]],
    "series": {cn: {
        "area": [per[cn][y]["area"] for y in range(2005, 2025)],
        "yield": [per[cn][y]["yield"] for y in range(2005, 2025)],
    } for cn in countries_order},
}

WORLD = S["world_overview"]
CN = S["countries"]["中国"]
BR = S["countries"]["巴西"]
IN = S["countries"]["印度"]
TH = S["countries"]["泰国"]

brk = S["area_change_breakdown"]
top2 = brk[0]["chg_1000ha"] + brk[1]["chg_1000ha"]
top2_share = round(100 * top2 / S["world_area_chg"], 1)

kpi = {
    "world_area_2005": f'{WORLD["area_2005_1000ha"]:,.0f}',
    "world_area_2024": f'{WORLD["area_2024_1000ha"]:,.0f}',
    "world_area_chg": f'{WORLD["area_chg_1000ha"]:+,.0f}',
    "world_area_pct": f'{WORLD["area_pct"]:+.1f}',
    "world_yield_2005": f'{WORLD["yield_2005"]:.1f}',
    "world_yield_2024": f'{WORLD["yield_2024"]:.1f}',
    "world_yield_pct": f'{WORLD["yield_chg_pct"]:+.1f}',
    "top2_share": f'{top2_share:.0f}',
    "cn_area_pct": f'{CN["area_pct"]:+.1f}',
    "cn_yield_pct": f'{CN["yield_chg_pct"]:+.1f}',
    "cn_yield_max": f'{CN["yield_max"]:.1f}',
    "cn_yield_year": CN["yield_max_year"],
    "cn_area_max": f'{CN["area_max"]:,.0f}',
    "cn_area_peak_year": CN["area_max_year"],
    "cn_area_2024": f'{CN["area_2024"]:,.0f}',
    "br_area_pct": f'{BR["area_pct"]:+.1f}',
    "in_area_pct": f'{IN["area_pct"]:+.1f}',
    "th_yield_min": f'{TH["yield_min"]:.1f}',
    "th_yield_min_year": TH["yield_min_year"],
}

tbl_rows = []
for cn in countries_order:
    st = S["countries"][cn]
    tbl_rows.append({
        "cn": cn,
        "a05": f'{st["area_2005"]:,.0f}', "a24": f'{st["area_2024"]:,.0f}',
        "ad": f'{st["area_chg_1000ha"]:+,.0f}',
        "ap": f'{st["area_pct"]:+.1f}',
        "y05": f'{st["yield_2005"]:.1f}', "y24": f'{st["yield_2024"]:.1f}',
        "yp": f'{st["yield_chg_pct"]:+.1f}',
    })

JS = json.dumps(DATA, ensure_ascii=False)
ROWS_JS = json.dumps(tbl_rows, ensure_ascii=False)

# 全球三要素逐年表（HTML 静态行）
yr_tbl = []
for i, r in enumerate(S["world_series"]):
    y = r["year"]
    ap = ((r["area"] / S["world_series"][i-1]["area"] - 1) * 100) if i > 0 else None
    yp = ((r["yield"] / S["world_series"][i-1]["yield"] - 1) * 100) if i > 0 else None
    yr_tbl.append(
        "<tr><td>{y}</td><td class='num'>{a:,.0f}</td><td class='num'>{yd:.1f}</td>"
        "<td class='num'>{p:.0f}</td>"
        "<td class='num'>{ap}</td><td class='num'>{yp}</td></tr>".format(
            y=y, a=r["area"], yd=r["yield"], p=r["prod"] / 1e6,
            ap=(("+" if ap >= 0 else "") + f"{ap:.1f}%") if ap is not None else "-",
            yp=(("+" if yp >= 0 else "") + f"{yp:.1f}%") if yp is not None else "-"))
YR_ROWS = "\n".join(yr_tbl)

# 国别表（HTML 静态行）
tr_rows = []
for r in tbl_rows:
    cls = "green" if float(r["ad"].replace(",", "")) < 0 else "red"
    tr_rows.append(
        "<tr><td><b>{cn}</b></td><td class='num'>{a05}</td><td class='num'>{a24}</td>"
        "<td class='num {c1}'>{ad}</td><td class='num {c2}'>{ap}%</td>"
        "<td class='num'>{y05}</td><td class='num'>{y24}</td>"
        "<td class='num {c1}'>{yp}%</td></tr>".format(
            cn=r["cn"], a05=r["a05"], a24=r["a24"],
            c1="green" if float(r["ad"].replace(",", "")) < 0 else "red",
            c2="green" if float(r["ad"].replace(",", "")) < 0 else "red",
            ad=r["ad"], ap=r["ap"], y05=r["y05"], y24=r["y24"], yp=r["yp"]))
TR_ROWS = "\n".join(tr_rows)

# 用普通模板（非 f-string），占位符替换，避免花括号转义问题
with open(os.path.join(BASE, "report98_template.html"), "r", encoding="utf-8") as f:
    html = f.read()

html = (html
        .replace("__KPI__", json.dumps(kpi, ensure_ascii=False))
        .replace("__JS__", JS)
        .replace("__ROWS_JS__", ROWS_JS)
        .replace("__YR_ROWS__", YR_ROWS)
        .replace("__TR_ROWS__", TR_ROWS))

out_path = os.path.join(OUT_DIR, "index.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
print("WROTE:", out_path, len(html), "chars")
assert "echarts" in html and JS in html
print("OK")