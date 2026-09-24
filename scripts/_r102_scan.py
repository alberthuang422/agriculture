# -*- coding: utf-8 -*-
"""102 号报告：正文残留旧值扫描 + 关键数字全文一致性交叉核对。"""
import io, os, re, json, csv, bisect
from datetime import date, timedelta

BASE = r"C:\Users\Administrator\Desktop\农业"
b = io.open(os.path.join(BASE, "scripts", "_r102_body.txt"), encoding="utf-8").read()
out = []
def p(s=""): out.append(str(s))

# ============ A. 残留旧值扫描 ============
p("=" * 76); p("A. 残留旧值扫描（应全部为 0）"); p("=" * 76)
stale = {
    "95.4%": "旧背离比(2015/16)", "79.5%": "旧背离比(2023)", "210 天": "旧领先天数",
    "+1,918": "旧2023/24修订", "连续上修 5 次": "旧上修链条", "连续五个版本": "旧版本数",
    "单月 -16.4%": "旧单月跌幅", "-27.7%": "不可复现崩塌值", "20.84</b>": "旧反弹价(未标注)",
    "70-77%": "旧锁定层区间", "提前 7 个月": "旧月数", "窗内最低": "误改残留",
    "净持仓归零点": "旧标签", "4 周内从 +16.5": "旧净多崩塌", "4 周暴减": "旧周数",
    "23.02 → 23.29": "旧价格差", "顶后 46 周": "旧周数",
}
bad = 0
for k, v in stale.items():
    n = b.count(k)
    p("  %-22s %-24s count=%d" % (k, v, n))
    if n: bad += 1
p("  >>> 残留项: %d" % bad)

# ============ B. 新值一致性（全文出现处应统一） ============
p(); p("=" * 76); p("B. 新值一致性检查"); p("=" * 76)
for k in ["99.9%", "83.0%", "196 天", "9 天", "+1,865", "-18.7%", "67-77%",
          "8 周内", "-24.3%", "-9.4%", "36 周", "45 周", "30 周", "21.18", "24.46",
          "六个版本", "23.02 → 23.26"]:
    n = b.count(k)
    p("  %-18s count=%d" % (k, n))
    if n == 0: p("     !! 未出现")

# ============ C. 顶后路径逐条可复现性 ============
p(); p("=" * 76); p("C. 顶后路径可复现性（基准=价峰对齐报表收盘）"); p("=" * 76)
rows = list(csv.DictReader(io.open(os.path.join(BASE, "data/price/sugar/sb_price_daily.csv"), encoding="utf-8-sig")))
d = [r["time"] for r in rows]; C = {r["time"]: float(r["close"]) for r in rows}
for lbl, align, base in [("2015/16", "2016-10-04", 23.26), ("2023", "2023-11-07", 27.55)]:
    p("  %s 基准 %s = %.2f" % (lbl, align, base))
    for wk in (4, 8, 13, 26, 52):
        tgt = date.fromisoformat(align) + timedelta(days=wk * 7)
        c = [t for t in d if date.fromisoformat(t) <= tgt]
        t2 = c[-1]
        ch = (C[t2] / base - 1) * 100
        p("     %+3d 周 -> %s %6.2f = %+6.1f%%" % (wk, t2, C[t2], ch))

# ============ D. 结构完整性 ============
p(); p("=" * 76); p("D. 结构完整性"); p("=" * 76)
p("  div %d/%d | table %d/%d | ul %d/%d | ol %d/%d | tr %d/%d"
  % (b.count("<div"), b.count("</div>"), b.count("<table"), b.count("</table>"),
     b.count("<ul"), b.count("</ul>"), b.count("<ol"), b.count("</ol>"),
     b.count("<tr"), b.count("</tr>")))
p("  h2 %d | h3 %d | td %d/%d | th %d/%d"
  % (len(re.findall(r"<h2", b)), len(re.findall(r"<h3", b)),
     b.count("<td"), b.count("</td>"), b.count("<th"), b.count("</th>")))
ids = re.findall(r'id="(s\d+)"', b); nav = re.findall(r'href="#(s\d+)"', b)
p("  anchors missing: %s" % ([n for n in nav if n not in ids] or "none"))
p("  charts: %s" % re.findall(r'id="(c\d)"', b))
used = set()
for m in re.finditer(r'class="([^"]+)"', b):
    used |= set(m.group(1).split())
css = io.open(os.path.join(BASE, "scripts", "_r102_css.txt"), encoding="utf-8").read()
defined = set(re.findall(r"\.([A-Za-z][\w-]*)", css))
p("  classes missing in CSS: %s" % (sorted(used - defined) or "none"))

io.open(os.path.join(BASE, "scripts", "_r102_scan.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
