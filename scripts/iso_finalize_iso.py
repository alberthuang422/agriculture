# -*- coding: utf-8 -*-
"""以 ISO 官方 PDF 精确值收口 iso 库, 修正 HEADLINES 舍入/媒体误导值."""
import json, csv, os

BASE = r'C:\Users\Administrator\Desktop\农业\data\fundamentals\sugar\iso'
JP = os.path.join(BASE, 'iso_qmo_vintage.json')
with open(JP, encoding='utf-8') as f:
    d = json.load(f)

# ---------- 1) vintages 逐条修正为官方 PDF 精确值 ----------
by_id = {v['id']: v for v in d['vintages']}

v = by_id['QMO-2025-08']
v['production_mt'] = 180.593
v['consumption_mt'] = 180.824
v['ending_stocks_mt'] = None   # Aug-2025 官方 PDF 未发布该期库存; 92.489 实为 2024/25 现值
v['stock_to_use_pct'] = None
v['notes'] = v['notes'] + ' [官方PDF校正: Aug-2025 期未发布库存列; 此前媒体转述的 92.489 为 2024/25 期末库存, 已移除]'

v = by_id['QMO-2025-11']
v['production_mt'] = 181.767  # 官方(媒体 181.77)
v['consumption_mt'] = 180.142 # 官方 ✓
v['ending_stocks_mt'] = 95.015
v['stock_to_use_pct'] = 52.74
v['notes'] = v['notes'] + ' [官方PDF校正: 期末库存 95.015, 库消比 52.74]'

v = by_id['QMO-2026-02']
v['production_mt'] = 181.287  # 官方 ✓
v['consumption_mt'] = 180.069 # 官方 ✓
v['ending_stocks_mt'] = 93.300
v['stock_to_use_pct'] = 51.81
v['notes'] = v['notes'] + ' [官方PDF校正: 期末库存 93.300 库消比 51.81 一致]'

v = by_id['QMO-2026-05']
v['production_mt'] = 182.004  # 官方(此前缺失)
v['consumption_mt'] = 179.760
v['ending_stocks_mt'] = 95.240
v['stock_to_use_pct'] = 44.15  # updated口径(旧口径52.98)
v['updated_end_stocks_mt'] = 79.360
v['stock_to_use_old_pct'] = 52.98
v['notes'] = v['notes'] + ' [官方PDF校正: 产量 182.004 官方值; 旧口径库消比 52.98 / updated 44.15, 期末库存 95.240 / updated 79.360]'

v = by_id['QMO-2026-08']
v['balance_mt'] = 1.144  # 官方(HEADLINES 舍入 1.1)
v['production_mt'] = 180.695
v['consumption_mt'] = 179.551
v['ending_stocks_mt'] = None  # Aug-2026 库存重审不发布
v['stock_to_use_pct'] = None
v['notes'] = v['notes'] + ' [官方PDF校正: surplus 官方 1.144 Mt(HEADLINES 舍入 1.1); 产量 180.695 消费 179.551; 库存自本期暂停发布(数据重审中)]'

v = by_id['QMO-2026-08-first-2026-27']
v['balance_mt'] = -0.234  # 官方(HEADLINES 舍入 -0.2)
v['production_mt'] = 180.141
v['consumption_mt'] = 180.375
v['trade_surplus_mt'] = 1.3
v['notes'] = v['notes'] + ' [官方PDF校正: 首版 official: 生产 180.141, 消费 180.375, 产销差 -0.234 Mt(HEADLINES 舍入 -0.2)]'

# ---------- 2) revision_timeline 更新为官方值 ----------
for row in d['revision_timeline_2025_26_mt']:
    if row['vintage'] == '2025-08 (1st)':
        row.update(balance=-0.231, production=180.593, consumption=180.824)
    elif row['vintage'] == '2025-11 (2nd)':
        row.update(balance=1.625, production=181.767, consumption=180.142)
    elif row['vintage'] == '2026-02 (3rd)':
        row.update(balance=1.218, production=181.287, consumption=180.069)
    elif row['vintage'] == '2026-05 (4th)':
        row.update(balance=2.244, production=182.004, consumption=179.760)
    elif row['vintage'] == '2026-08 (5th)':
        row.update(balance=1.144, production=180.695, consumption=179.551)

# ---------- 3) 同步 2024/25 修订链到 JSON (新增块) ----------
d['revision_timeline_2024_25_mt'] = [
    {"vintage": "2024-11", "balance": -2.513},
    {"vintage": "2025-02", "balance": -4.881},
    {"vintage": "2025-05", "balance": -5.466},
    {"vintage": "2025-08", "balance": -4.879},
    {"vintage": "2025-11", "balance": -2.916},
    {"vintage": "2026-02", "balance": -3.464},
    {"vintage": "2026-05", "balance": -3.196},
    {"vintage": "2026-08", "balance": -3.643},
]
d['revision_timeline_2024_25_mt_note'] = '2024/25 缺口修订链(千吨, 官方 PDF): 2024-11 首版 -2,513 → 2025-08 扩大至 -4,879 → 2025-11 收窄 -2,916 → 2026-02 -3,464 → 2026-05 -3,196 → 2026-08 -3,643'

with open(JP, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print('json updated:', os.path.getsize(JP), 'bytes')

# ---------- 4) 重建 iso_world_balance_2010_2026.csv (官方最新值) ----------
# 官方 Aug-2026 为最新(2013/14-2026/27); 2011/12-2012/13 用 Feb-2026
official = {
 "2011/12": dict(p=163.597, c=157.961, b=5.636, i=54.327, e=54.327, s=73.583, r=46.58, src="ISO WSB Feb-2026"),
 "2012/13": dict(p=171.804, c=163.645, b=8.159, i=60.781, e=60.781, s=81.742, r=49.95, src="ISO WSB Feb-2026"),
 "2013/14": dict(p=174.132, c=164.215, b=9.917, i=57.822, e=57.822, s=91.659, r=55.82, src="ISO WSB Aug-2026"),
 "2014/15": dict(p=169.373, c=167.079, b=2.294, i=58.419, e=58.419, s=93.953, r=56.23, src="ISO WSB Aug-2026"),
 "2015/16": dict(p=163.825, c=170.287, b=-6.462, i=67.814, e=66.943, s=88.362, r=51.89, src="ISO WSB Aug-2026"),
 "2016/17": dict(p=169.073, c=172.683, b=-3.610, i=66.512, e=65.442, s=86.492, r=50.09, src="ISO WSB Aug-2026"),
 "2017/18": dict(p=179.828, c=170.420, b=9.408, i=64.103, e=63.460, s=96.543, r=56.65, src="ISO WSB Aug-2026"),
 "2018/19": dict(p=174.435, c=169.315, b=5.120, i=57.639, e=57.639, s=103.525, r=61.14, src="ISO WSB Aug-2026"),
 "2019/20": dict(p=167.866, c=168.492, b=-0.626, i=65.768, e=65.717, s=102.950, r=61.10, src="ISO WSB Aug-2026"),
 "2020/21": dict(p=168.702, c=169.266, b=-0.564, i=64.901, e=64.858, s=102.544, r=60.58, src="ISO WSB Aug-2026"),
 "2021/22": dict(p=172.189, c=176.066, b=-3.877, i=67.790, e=67.663, s=98.801, r=56.12, src="ISO WSB Aug-2026"),
 "2022/23": dict(p=175.473, c=177.344, b=-1.871, i=68.435, e=68.446, s=96.919, r=54.65, src="ISO WSB Aug-2026"),
 "2023/24": dict(p=180.954, c=181.207, b=-0.253, i=71.616, e=71.521, s=96.761, r=53.40, src="ISO WSB Aug-2026"),
 "2024/25": dict(p=174.994, c=178.637, b=-3.643, i=67.876, e=67.876, s=None, r=None, src="ISO WSB Aug-2026"),
 "2025/26": dict(p=180.695, c=179.551, b=1.144, i=67.328, e=67.299, s=None, r=None, src="ISO WSB Aug-2026"),
 "2026/27": dict(p=180.141, c=180.375, b=-0.234, i=66.908, e=68.184, s=None, r=None, src="ISO WSB Aug-2026 首版"),
}
cols = ["market_year","production_mt","consumption_mt","balance_mt","import_demand_mt",
        "export_availability_mt","end_stocks_mt","stock_to_use_pct","source","notes"]
notes = {
 "2021/22": "ISO 2024年起回溯修订: -2.655(Nov-2023旧) → -3.877(Aug-2026最新)",
 "2022/23": "ISO 2024年起回溯修订: +0.310(Nov-2023旧) → -1.871(Aug-2026最新, 库存重审后)",
 "2023/24": "消费上修至 181.207 创纪录(Aug-2025 曾报 181.639, Nov-2025起修正)",
 "2024/25": "缺口终值 -3.643(Aug-2026); 区间修订轨迹见 revision_timeline_2024_25_mt",
 "2025/26": "官方终值 surplus +1.144(Aug-2026); 修订链 -0.231→1.625→1.218→2.244→1.144",
 "2026/27": "首版(Aug-2026): 产销差 -0.234; 库存/库消比因数据重审未发布",
}
rows = []
for y, dd in official.items():
    r = {"market_year": y}
    for k, ck in [("p","production_mt"),("c","consumption_mt"),("b","balance_mt"),
                  ("i","import_demand_mt"),("e","export_availability_mt"),("s","end_stocks_mt"),
                  ("r","stock_to_use_pct")]:
        r[ck] = dd[k]
    r["source"] = dd["src"]
    r["notes"] = notes.get(y, "")
    rows.append(r)

csv_path = os.path.join(BASE, "iso_world_balance_2010_2026.csv")
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print("csv rebuilt:", csv_path)

# ---------- 5) 同步 historical_final_series (Aug-2026 官方) ----------
series = []
for y in ["2011/12","2012/13","2013/14","2014/15","2015/16","2016/17","2017/18","2018/19",
          "2019/20","2020/21","2021/22","2022/23","2023/24","2024/25","2025/26","2026/27"]:
    dd = official[y]
    series.append({
        "market_year": y,
        "production": dd["p"], "consumption": dd["c"], "balance": dd["b"],
        "end_stocks": dd["s"], "stock_to_use_pct": dd["r"],
        "caliber": "latest official (Aug-2026)" if dd["src"].endswith("Aug-2026") else "latest official",
    })
d["historical_final_series_2010_2026_mt"] = series
with open(JP, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
print("final series synced")

# 校验
with open(JP, encoding='utf-8') as f:
    d2 = json.load(f)
print("JSON valid, vintages:", len(d2['vintages']),
      "| 2025/26 chain:", [x['balance'] for x in d2['revision_timeline_2025_26_mt']])