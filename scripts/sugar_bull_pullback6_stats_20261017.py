# -*- coding: utf-8 -*-
"""
白糖牛市内 >6% 回调统计 v2（口径: 收盘价, "创新高"才确认回调结束）
定义:
  - 牛市窗口: sugar_bull_events.json 核实分段
  - 一次回调episode: 从某个窗口内新高(收盘)开始, 价格回落;
    若期间最大回撤 >= 6%, 记为一次合格回调;
    回调结束 = 收盘价首次重新突破该前高 -> 此为新波段的最高点(截至突破时点为首个新高日)
    回调低点 = 期间最低收盘
  - 统计: 回撤深度 / 前高->低点耗时 / 低点->新高涨幅与耗时 / 前高->新高涨幅与耗时
  - 窗口末仍未创新高的回调, 单列标注
"""
import csv, datetime as dt

SRC = r"C:\Users\Administrator\Desktop\农业\data\price\sugar\sb_daily_spliced_20261014.csv"
TH = 0.06

rows = []
with open(SRC, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        rows.append((dt.date.fromisoformat(r['date']), float(r['sb_close'])))
rows.sort()

BULLS = [
    ("2015-16 厄尔尼诺牛市", dt.date(2015, 8, 24), dt.date(2016, 10, 6)),
    ("2020-21 疫情后牛市",   dt.date(2020, 4, 28), dt.date(2021, 11, 18)),
    ("2022-23 牛市",         dt.date(2022, 10, 3), dt.date(2023, 11, 7)),
    ("2026 当前牛市(进行中)", dt.date(2026, 4, 17), dt.date(2026, 10, 13)),
]

def nats(d1, d2):
    return (d2 - d1).days

def analyze(seg, th=TH):
    """seg: [(date, close)]。返回 episodes 列表。"""
    eps = []
    peak_i = 0
    peak_p = seg[0][1]
    trough_i, trough_p = None, None
    n = len(seg)
    i = 1
    in_dd = False
    while i < n:
        d, p = seg[i]
        if not in_dd:
            if p > peak_p:
                peak_i, peak_p = i, p
            else:
                dd = (p / peak_p - 1)
                if dd <= -th:
                    in_dd = True
                    trough_i, trough_p = i, p
        else:
            if p < trough_p:
                trough_i, trough_p = i, p
            elif p > peak_p:
                # 新高 -> episode 结束
                eps.append(dict(hi_d=seg[peak_i][0], hi_p=peak_p,
                                lo_d=seg[trough_i][0], lo_p=trough_p,
                                nh_d=d, nh_p=p))
                in_dd = False
                peak_i, peak_p = i, p
        i += 1
    if in_dd:
        eps.append(dict(hi_d=seg[peak_i][0], hi_p=peak_p,
                        lo_d=seg[trough_i][0], lo_p=trough_p,
                        nh_d=None, nh_p=None,
                        last_d=seg[-1][0], last_p=seg[-1][1]))
    return eps

out = ["白糖牛市 >6% 回调统计（ICE SB#11 日线收盘价，数据截至 2026-10-13）",
       "口径：前高=窗口内收盘新高；回调低点=回落期间最低收盘；回调结束=收盘重新突破前高；阈值 -6%",
       "     低点→波段峰值：回调低点 → 下一个 >6% 回调启动前的最高收盘（下一波段完整峰值）",
       ""]

for name, s, e in BULLS:
    seg = [(d, p) for d, p in rows if s <= d <= e]
    eps = analyze(seg)
    # 下一波段完整峰值: episode k 的低点之后, 到下一个 episode 的前高(即下一轮回调启动前的最高收盘)
    for k, ep in enumerate(eps):
        if ep['nh_p'] is None:
            continue
        if k + 1 < len(eps):
            ep['h2_d'], ep['h2_p'] = eps[k+1]['hi_d'], eps[k+1]['hi_p']
            ep['h2_done'] = True
        else:
            # 最后一个 episode: 下一波段尚未走完, 取 新高日~窗口末 的最高收盘
            cand = [(d, p) for d, p in seg if d >= ep['nh_d']]
            h2d, h2p = max(cand, key=lambda x: x[1])
            ep['h2_d'], ep['h2_p'] = h2d, h2p
            ep['h2_done'] = h2p > ep['hi_p'] and h2d > ep['nh_d']

    out.append(f"【{name}】窗口 {s} ~ {e}")
    out.append("=" * 96)
    for k, ep in enumerate(eps, 1):
        dd = (ep['lo_p'] / ep['hi_p'] - 1) * 100
        line = (f"  #{k}  前高 {ep['hi_d']} @ {ep['hi_p']:.2f} → 低点 {ep['lo_d']} @ {ep['lo_p']:.2f}"
                f"   回撤 {dd:.1f}% / 下跌{nats(ep['hi_d'], ep['lo_d'])}天")
        if ep['nh_p'] is not None:
            g_lo = (ep['nh_p'] / ep['lo_p'] - 1) * 100
            g_hi = (ep['nh_p'] / ep['hi_p'] - 1) * 100
            line += (f"\n        首次创新高 {ep['nh_d']}: 低点→ +{g_lo:.1f}%/{nats(ep['lo_d'], ep['nh_d'])}天, "
                     f"前高→新高用时 {nats(ep['hi_d'], ep['nh_d'])}天")
            if ep.get('h2_done'):
                g2_lo = (ep['h2_p'] / ep['lo_p'] - 1) * 100
                g2_hi = (ep['h2_p'] / ep['hi_p'] - 1) * 100
                line += (f"\n        波段峰值 {ep['h2_d']} @ {ep['h2_p']:.2f}: 低点→峰值 +{g2_lo:.1f}%/{nats(ep['lo_d'], ep['h2_d'])}天, "
                         f"前高→峰值 +{g2_hi:.1f}%/{nats(ep['hi_d'], ep['h2_d'])}天")
            else:
                line += f"\n        [下一波段未走完, 暂以窗口末前最高 {ep['h2_d']} @ {ep['h2_p']:.2f} 计]"
        else:
            rb = (ep['last_p'] / ep['lo_p'] - 1) * 100
            line += f"   [至窗口末未创新高] 低点→窗口末({ep['last_d']}): +{rb:.1f}% / {nats(ep['lo_d'], ep['last_d'])}天"
        out.append(line)
    # 统计摘要（已完成创新高且下一波段走完的 episode）
    done = [ep for ep in eps if ep['nh_p'] is not None and ep.get('h2_done')]
    if done:
        import statistics as st
        g2_lo = [(ep['h2_p']/ep['lo_p']-1)*100 for ep in done]
        g2_hi = [(ep['h2_p']/ep['hi_p']-1)*100 for ep in done]
        t2_lo = [nats(ep['lo_d'], ep['h2_d']) for ep in done]
        t2_hi = [nats(ep['hi_d'], ep['h2_d']) for ep in done]
        t_nh  = [nats(ep['hi_d'], ep['nh_d']) for ep in done]
        dds   = [(ep['lo_p']/ep['hi_p']-1)*100 for ep in done]
        out.append(f"  ▶ 摘要({len(done)}次完成回调): 回撤中位 {st.median(dds):.1f}% | "
                   f"创新高用时中位 {st.median(t_nh):.0f}天 | "
                   f"低点→波段峰值 中位 +{st.median(g2_lo):.1f}% (范围 +{min(g2_lo):.1f}%~+{max(g2_lo):.1f}%), 耗时中位 {st.median(t2_lo):.0f}天 | "
                   f"前高→波段峰值 中位 +{st.median(g2_hi):.1f}%, 耗时中位 {st.median(t2_hi):.0f}天")
    pend = [ep for ep in eps if ep['nh_p'] is None]
    for ep in pend:
        out.append(f"  ▶ 未完成: {ep['hi_d']} @ {ep['hi_p']:.2f} 起的回调(最深 {ep['lo_d']} @ {ep['lo_p']:.2f}, "
                   f"{(ep['lo_p']/ep['hi_p']-1)*100:.1f}%) 至窗口末未创新高")
    out.append("")

txt = "\n".join(out)
print(txt)
with open(r"C:\Users\Administrator\Desktop\农业\data\price\sugar\sugar_bull_pullback6_stats_20261017.txt", "w", encoding="utf-8") as f:
    f.write(txt)
