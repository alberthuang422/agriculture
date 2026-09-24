# -*- coding: utf-8 -*-
"""CT 棉花期货日线取数：stooq (ct.f) 备选多个符号"""
import urllib.request, csv, io, json, sys

out = []
for sym in ("ct.f", "cotton.f", "ctc.f"):
    url = f"https://stooq.com/q/d/l/?s={sym}&i=d"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        txt = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        print(sym, "->", txt[:120].replace("\n", " | "))
        if txt and "Date" in txt.split("\n")[0] and "\x1e" not in txt:
            rows = list(csv.DictReader(io.StringIO(txt)))
            print(sym, "rows:", len(rows), "first:", rows[0], "last:", rows[-1])
            if len(rows) > 100:
                out.append({"sym": sym, "n": len(rows), "first": rows[0], "last": rows[-1],
                            "csv": txt})
                break
    except Exception as e:
        print(sym, "ERR", repr(e))

if out and out[0].get("csv"):
    open(r"C:\Users\Administrator\Desktop\stock\data\cotton\ct_stooq_1d.csv", "w").write(out[0]["csv"])
    print("SAVED ct_stooq_1d.csv")
else:
    print("NO reliable source; need fallback")
