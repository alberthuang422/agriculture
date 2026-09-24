# -*- coding: utf-8 -*-
"""102 号报告最终静态校验：payload 完整性、markPoint 坐标、口径注记、结构平衡。"""
import re, io, json, os

BASE = r"C:\Users\Administrator\Desktop\农业"
h = io.open(os.path.join(BASE, "reports", "102_白糖两轮牛市全周期复盘_2015_2023", "index.html"),
            encoding="utf-8").read()

P = json.loads(re.search(r"var P = (\{.*?\});\n", h, re.S).group(1))
js = h.split("var P = ")[1]

out = []
out.append("size: %d bytes" % len(h))

# 1. payload refs
refs = sorted(set(re.findall(r"\bP\.([A-Za-z_]\w*)", js)))
out.append("JS refs: %s" % refs)
out.append("UNDEFINED refs: %s" % ([r for r in refs if r not in P] or "none"))

# 2. C1 peak coords must match true peaks in payload
coords = [(int(a), float(b)) for a, b in re.findall(r"coord:\[(\d+),\s*([\d.]+)\]", h)]
out.append("all markPoint coords: %s" % coords)
for nm in ("N15", "N23"):
    pk = max(P[nm], key=lambda r: r[1])
    hit = [c for c in coords if c[0] == pk[0] and abs(c[1] - pk[1]) < 0.02]
    out.append("  %s n=%d true peak=%s -> matched in JS: %s"
               % (nm, len(P[nm]), pk, "OK" if hit else "MISMATCH"))
    out.append("     x within axis max(480): %s" % (pk[0] <= 480))

# 3. markLine / axis
out.append("markLine xAxis: %s" % re.findall(r"xAxis:(\d+)", h))
out.append("C1 xAxis max: %s" % re.findall(r"min:0,max:(\d+)", h))

# 4. 口径注记
out.append("caption 口径提示: %s" % ("口径提示" in h))
out.append("caption 282 vs 275: %s" % ("第 282 与第 275 个交易日" in h))
out.append("note 275-282 交易日: %s" % ("275-282 个交易日" in h))
out.append("stale '267 个交易日': %s" % ("267 个交易日" in h))
out.append("stale '+129%%' bare: %s" % (len(re.findall(r"\+129%", h))))
out.append("stale '+59%%' bare: %s" % (len(re.findall(r"\+59%", h))))

# 5. structure
out.append("div balance: %d / %d" % (h.count("<div"), h.count("</div>")))
out.append("table balance: %d / %d" % (h.count("<table"), h.count("</table>")))
out.append("h2: %d | h3: %d" % (len(re.findall(r"<h2", h)), len(re.findall(r"<h3", h))))
ids = re.findall(r'id="(s\d+)"', h)
nav = re.findall(r'href="#(s\d+)"', h)
out.append("anchors missing: %s" % ([n for n in nav if n not in ids] or "none"))
out.append("charts: %s" % re.findall(r'id="(c\d)"', h))
out.append("leftovers TODO/allpx/_r102: %s"
           % [t for t in ("TODO", "allpx", "_r102", "undefined", "NaN") if t in h] or "none")

io.open(os.path.join(BASE, "scripts", "_r102_chk.txt"), "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
