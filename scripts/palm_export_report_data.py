# -*- coding: utf-8 -*-
"""导出 110 号棕榈油报告所需数据 JSON"""
import json, csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
B = os.path.join(ROOT, "data", "fundamentals", "palm")
OUT = os.path.join(ROOT, "reports", "110_棕榈油基本面全景_20261007")

I = json.load(open(os.path.join(B, "palm_indicators.json"), encoding="utf-8"))
E = json.load(open(os.path.join(B, "palm_enso_detrended.json"), encoding="utf-8"))
S = json.load(open(os.path.join(B, "palm_scenario.json"), encoding="utf-8"))
SUP = json.load(open(os.path.join(B, "palm_supplement.json"), encoding="utf-8"))
C = I["countries"]


def g(cc, my, k):
    for r in C.get(cc, []):
        if r["my"] == my:
            return r.get(k) or 0
    return 0


mp = []
with open(os.path.join(B, "mpob_monthly_2026.csv"), encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        d = {}
        for k, v in r.items():
            k = (k or "").strip()
            if k in ("ym", "note"):
                d[k] = v
            else:
                try:
                    d[k] = float(v) if v not in (None, "") else None
                except ValueError:
                    d[k] = v
        mp.append(d)

KS = ["area_kha", "yield", "prod", "dom", "industrial", "food", "imp", "exp", "end", "beg", "stu"]
KS2 = ["imp", "dom", "industrial", "end"]


def blk(cc, ks):
    ys = sorted(r["my"] for r in C.get(cc, []))
    return {y: {k: g(cc, y, k) for k in ks} for y in ys if y >= "1990"}


D = {"world": I["world"], "oils": I["oils"], "price": I["price_monthly"],
     "mpob": mp, "enso": E, "scen": S, "sup": SUP,
     "id": blk("ID", KS), "my": blk("MY", KS),
     "in_": blk("IN", KS2), "ch": blk("CH", KS2),
     "e4": blk("E4", KS2), "pk": blk("PK", KS2)}

os.makedirs(OUT, exist_ok=True)
json.dump(D, open(os.path.join(OUT, "_data.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("exported %.0f KB" % (os.path.getsize(os.path.join(OUT, "_data.json")) / 1024))
print("world", len(I["world"]), "price", len(I["price_monthly"]), "mpob", len(mp), "id", len(D["id"]))
print("mpob sample", mp[0])
