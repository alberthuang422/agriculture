import io, re

s = io.open("reports/110_棕榈油基本面全景_20261007/index.html", encoding="utf-8").read()

# 1) every .up/.dn cell must carry an explicit sign or direction word (non-color cue)
cells = re.findall(r"<td[^>]*class='num[^']*(?:up|dn)[^']*'[^>]*>(.*?)</td>", s)
cells += re.findall(r'<td[^>]*class="num[^"]*(?:up|dn)[^"]*"[^>]*>(.*?)</td>', s)
nosign = [c for c in cells if not re.search(r'[+\-−↑↓▲▼]|\bup\b|\bdn\b', re.sub(r'<[^>]+>', '', c))]
print("up/dn cells total:", len(cells), "| without explicit sign:", len(nosign))
for c in nosign[:10]:
    print("   ", c[:90])

# 2) tag chips carry text labels (not color-only)
tags = re.findall(r'<span class="tag (\w+)">([^<]*)</span>', s)
from collections import Counter
print("\ntag chips:", Counter(t[0] for t in tags))
print("distinct labels:", sorted({t[1] for t in tags}))

# 3) chart series use lineType/symbol differentiation
print("\n=== 图表系列区分手段 ===")
for t in ("lineStyle:{", "type:'dashed'", "type:'solid'", "symbol:'", "label:{show:true"):
    print("   %-20s x%d" % (t, s.count(t)))

# 4) theme consistency with prior project reports
for f in ("reports/97_棉花基本面全景_20260920/index.html",
          "reports/94_白糖可贸易国家全景_2000_2026/index.html"):
    try:
        o = io.open(f, encoding="utf-8").read()
        m = re.search(r'--bg:\s*(#[0-9a-fA-F]{3,6})', o)
        print("\n%s -> --bg %s" % (f.split('/')[1], m.group(1) if m else "?"))
    except Exception as e:
        print("\n%s -> %s" % (f, e))
m = re.search(r'--bg:\s*(#[0-9a-fA-F]{3,6})', s)
print("report 110 --bg:", m.group(1))
