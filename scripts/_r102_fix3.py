# -*- coding: utf-8 -*-
"""102 号报告正文校正（批次 3）：
   ① 回滚批次1中"底部净持仓"的误改（原值 -9,651@2015-08-18 / +48,601@2022-09-27 本就符合
      "底部日或之前最近报表"口径，且与时间线叙述、空头 25.2 万手自洽）；
   ② 2023/24 累计修订 +1,918 -> +1,865（-253 - (-2118)）；
   ③ "连续上修 5 次"链条混用 ISO 与 F.O.Licht 且时序错乱 -> 改为 ISO 单一机构路径（3 次上修），
      F.O.Licht 单独标注；
   ④ 2022/23 "连续五个版本" -> 六个版本（2022-08/11、2023-02/05/08/11）；
   ⑤ 时间线"反弹至 20.84"补上反弹真实峰值 21.18（2017-02-06）。"""
import io, os, re

BASE = r"C:\Users\Administrator\Desktop\农业"
p = os.path.join(BASE, "scripts", "_r102_body.txt")
b = io.open(p, encoding="utf-8").read()
n0 = len(b)
log = []

def rep(old, new, expect, tag):
    global b
    c = b.count(old)
    assert c == expect, "[%s] count=%d expect=%d :: %s" % (tag, c, expect, old[:90])
    b = b.replace(old, new)
    log.append("%-24s x%-2d %s" % (tag, c, re.sub(r"\s+", " ", re.sub("<[^>]+>", "", old))[:66]))

# ---------- ① 回滚底部净持仓误改 ----------
rep('<tr><td>底部净持仓</td><td class="num">-11,275 手<span class="dim sm">（2015-08-25，窗内最低）</span></td>'
    '<td class="num">+26,065 手<span class="dim sm">（2022-08-09，窗内最低）</span></td>',
    '<tr><td>底部净持仓<span class="dim sm">（底部日对齐报表）</span></td>'
    '<td class="num">-9,651 手<span class="dim sm">（2015-08-18，对应价底 2015-08-24）</span></td>'
    '<td class="num">+48,601 手<span class="dim sm">（2022-09-27，对应价底 2022-10-03）</span></td>',
    1, "回滚底部持仓")

# ---------- ② 2023/24 累计修订 ----------
rep('<td class="num down">-253</td><td class="num up"><b>+1,918</b></td>',
    '<td class="num down">-253</td><td class="num up"><b>+1,865</b></td>', 1, "2023/24 修订")

# ---------- ③ 2015/16 实时上修链条（单一机构口径） ----------
rep('<b>2015/16</b>：市场手里的数字<b>方向正确、幅度保守</b>，且在整个行情期间被<b>连续上修 5 次</b>'
    '（-2,490 → -3,500 → -5,000 → -5,600 → -6,462 kt）。每一次上修都是一次基本面确认，'
    '多头得到持续弹药，因此行情能走 13 个月、涨 136%。',
    '<b>2015/16</b>：市场手里的数字<b>方向正确、幅度保守</b>。<b>ISO 口径</b>在行情期间连续 3 次上修缺口'
    '（2015-08 -2,490 → 2015-11 -3,500 → 2016-02 -5,000 kt），终值 -6,462 kt 落在实时预测区间内；'
    '<b>商业机构更激进</b>（F.O. Licht 2015-11-12 即给 -5,600 kt，Datagro 2016-10 给 2016/17 -8,260 kt）。'
    '每一次上修都是一次基本面确认，多头得到持续弹药，因此行情能走 13 个月、涨 136%。',
    1, "2015/16 上修链条")

# ---------- ④ 2022/23 版本数 ----------
rep('ISO 从 2022-08 到 2023-11 连续五个版本都说 2022/23 是<b>过剩</b>',
    'ISO 从 2022-08 到 2023-11 连续<b>六个版本</b>都说 2022/23 是<b>过剩</b>', 1, "2022/23 版本数")

# ---------- ⑤ 时间线反弹峰值 ----------
rep('价格在 2017 年 2 月反弹至 <b>20.84</b>。',
    '价格在 2017 年 2 月反弹至 <b>21.18</b>（收盘峰 2017-02-06；盘中 21.49）。', 1, "时间线反弹2017")

# ---------- 附：7.2 表末行同步标注 ISO 口径 ----------
rep('<tr style="background:#20242e"><td><b>终值</b></td><td><b>ISO Aug-2026</b></td>'
    '<td class="num down"><b>-6,462 kt</b></td><td>落在实时预测区间内，<b>略偏保守端</b></td></tr>',
    '<tr style="background:#20242e"><td><b>终值</b></td><td><b>ISO Aug-2026</b></td>'
    '<td class="num down"><b>-6,462 kt</b></td>'
    '<td>落在实时预测区间内，介于 ISO 自身最后一版实时预测（2016-02 -5,000）'
    '与 F.O. Licht 激进值（-5,600）之间，<b>偏保守端</b>。'
    '<span class="dim sm">注：本表 ISO 与 F.O. Licht 为两套独立机构口径，不可串成单一修订链。</span></td></tr>',
    1, "7.2 终值行")

io.open(p, "w", encoding="utf-8").write(b)
msg = ["batch3: %d substitutions" % len(log), "size %d -> %d" % (n0, len(b)), ""] + log
io.open(os.path.join(BASE, "scripts", "_r102_fix_log3.txt"), "w", encoding="utf-8").write("\n".join(msg))
print("\n".join(msg))
