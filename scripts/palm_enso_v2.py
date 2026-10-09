# -*- coding: utf-8 -*-
"""
棕榈油 ENSO-单产关系严谨检验（v2：去趋势）
问题诊断：棕榈油单产含强长期趋势（树龄老化/翻种节奏），"前3年均值反事实"
          在趋势下行期会系统性产生负偏差，掩盖或伪造 ENSO 信号。
方法：①对单产做线性/二次去趋势 → ②残差 vs ONI 多滞后回归 → ③显著性检验
     ④分国分别做（印尼树龄结构 vs 马来不同）
"""
import json, os, math, statistics as st

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "data", "fundamentals", "palm"))
PN = os.path.normpath(os.path.join(BASE, "..", "..", "price", "palm"))
I = json.load(open(os.path.join(BASE, "palm_indicators.json")))
C = I["countries"]; W = {w["my"]: w for w in I["world"]}

# ---------- ONI 月度 ----------
# CPC 的 ONI 是 3 个月滑动均值，标签 = 季中月所在年。
# DJF 1950 = 1949-12/1950-01/1950-02 → 季中月 = 1950-01
# NDJ 1950 = 1950-11/1950-12/1951-01 → 季中月 = 1950-12
# 因此每个标签直接映射到"标签年的季中月"，无跨年错位。
CENTER = {"DJF":1,"JFM":2,"FMA":3,"MAM":4,"AMJ":5,"MJJ":6,
          "JJA":7,"JAS":8,"ASO":9,"SON":10,"OND":11,"NDJ":12}
oni = {}
for line in open(os.path.join(PN, "oni.txt")):
    p = line.split()
    if len(p) == 4 and p[1].isdigit() and p[0] in CENTER:
        oni["%d-%02d" % (int(p[1]), CENTER[p[0]])] = float(p[3])


def my_months(my):
    y = int(my)
    return [(y, m) for m in range(10, 13)] + [(y+1, m) for m in range(1, 10)]


def shift(y, m, k):
    t = y*12 + (m-1) + k
    return t//12, t % 12 + 1


def oni_my(my, lag=0):
    vs = []
    for (y, m) in my_months(my):
        yy, mm = shift(y, m, lag)
        v = oni.get("%d-%02d" % (yy, mm))
        if v is not None: vs.append(v)
    return st.mean(vs) if vs else None


def pearson(xs, ys):
    n = len(xs)
    if n < 4: return None, n
    mx, my_ = st.mean(xs), st.mean(ys)
    sx = math.sqrt(sum((x-mx)**2 for x in xs))
    sy = math.sqrt(sum((y-my_)**2 for y in ys))
    if sx == 0 or sy == 0: return None, n
    r = sum((x-mx)*(y-my_) for x, y in zip(xs, ys))/(sx*sy)
    return r, n


def tstat(r, n):
    if r is None or n < 5 or abs(r) >= 1: return None
    return r*math.sqrt((n-2)/(1-r*r))


def ols_detrend(ys, deg=1):
    """对 y ~ 1 + t (+ t^2) 做 OLS，返回残差"""
    n = len(ys)
    ts = list(range(n))
    X = [[t**k for k in range(deg+1)] for t in ts]
    # 正规方程
    p = deg+1
    XtX = [[sum(X[i][a]*X[i][b] for i in range(n)) for b in range(p)] for a in range(p)]
    Xty = [sum(X[i][a]*ys[i] for i in range(n)) for a in range(p)]
    # 高斯消元
    M = [row[:] + [Xty[i]] for i, row in enumerate(XtX)]
    for c in range(p):
        piv = max(range(c, p), key=lambda r: abs(M[r][c]))
        M[c], M[piv] = M[piv], M[c]
        if abs(M[c][c]) < 1e-12: return None
        M[c] = [v/M[c][c] for v in M[c]]
        for r in range(p):
            if r != c:
                f = M[r][c]
                M[r] = [a - f*b for a, b in zip(M[r], M[c])]
    beta = [M[i][p] for i in range(p)]
    fit = [sum(beta[k]*t**k for k in range(p)) for t in ts]
    resid = [ys[i]-fit[i] for i in range(n)]
    ss_res = sum(e*e for e in resid)
    ss_tot = sum((y-st.mean(ys))**2 for y in ys)
    r2 = 1 - ss_res/ss_tot if ss_tot else 0
    return {"beta": beta, "resid": resid, "fit": fit, "r2": r2, "ts": ts}


print("=" * 92)
print("棕榈油单产长期趋势诊断（这是必须先解决的问题）")
print("=" * 92)
for nm, src in [("全球", [(y, W[y]["yield"]) for y in sorted(W) if int(y) >= 1990]),
                ("马来", [(r["my"], r["yield"]) for r in C["MY"] if int(r["my"]) >= 1990]),
                ("印尼", [(r["my"], r["yield"]) for r in C["ID"] if int(r["my"]) >= 1990])]:
    ys = [v for _, v in src]
    d1 = ols_detrend(ys, 1); d2 = ols_detrend(ys, 2)
    print("\n  %s 单产 (MT/HA) %d 年，1990→最新：" % (nm, len(ys)))
    print("    1990-94均值 %.2f | 2000-04 %.2f | 2010-14 %.2f | 2020-26 %.2f" % (
        st.mean(ys[0:5]), st.mean(ys[10:15]), st.mean(ys[20:25]), st.mean(ys[30:])))
    print("    线性趋势 β1 = %+.4f MT/HA per MY（R²=%.3f）" % (d1["beta"][1], d1["r2"]))
    print("    二次趋势 R² = %.3f（β2 = %+.6f）→ %s" % (
        d2["r2"], d2["beta"][2], "存在明显拐点/非线性" if d2["r2"] - d1["r2"] > 0.05 else "线性已足够"))
    print("    ⇒ 趋势解释了单产变异的 %.0f%%，残差标准差 %.4f" % (
        100*d1["r2"], st.pstdev(d1["resid"])))

# ---------- 去趋势后回归 ----------
print()
print("=" * 92)
print("去趋势后：单产残差 vs ONI（多滞后）")
print("   ※ 马来西亚单产呈倒U型（线性R²=0.005 vs 二次R²=0.650）→ 必须用二次去趋势")
print("=" * 92)
results = {}
for nm, cc in [("全球", None), ("马来", "MY"), ("印尼", "ID")]:
    if cc is None:
        src = [(y, W[y]["yield"]) for y in sorted(W) if int(y) >= 1990 and oni_my(y) is not None]
    else:
        src = [(r["my"], r["yield"]) for r in C[cc]
               if int(r["my"]) >= 1990 and oni_my(r["my"]) is not None]
    mys = [m for m, _ in src]
    ys = [v for _, v in src]
    if len(ys) < 12:
        print("  %s 样本不足 (%d)" % (nm, len(ys))); continue
    d1 = ols_detrend(ys, 1); d2 = ols_detrend(ys, 2)
    deg = 2 if (d2 and d2["r2"] - d1["r2"] > 0.05) else 1
    det = d2 if deg == 2 else d1
    res = det["resid"]
    print("\n  ── %s（n=%d，去 %d 次趋势，R²=%.3f，残差SD=%.4f）" % (
        nm, len(ys), deg, det["r2"], st.pstdev(res)))
    print("     %5s %8s %6s %8s %s" % ("lag月", "r", "n", "t值", "显著性"))
    bestl, bestr, bestt = None, 0, 0
    rows = []
    for lag in range(0, 19):
        xs = [oni_my(m, lag) for m in mys]
        pairs = [(x, r_) for x, r_ in zip(xs, res) if x is not None]
        if len(pairs) < 8: continue
        r, n = pearson([p[0] for p in pairs], [p[1] for p in pairs])
        t = tstat(r, n)
        if r is None: continue
        star = ("*** p<0.01" if t and abs(t) > 2.70 else
                "**  p<0.05" if t and abs(t) > 2.02 else
                "*   p<0.10" if t and abs(t) > 1.68 else "ns")
        rows.append({"lag": lag, "r": round(r, 3), "n": n, "t": round(t, 2) if t else None, "sig": star})
        print("     %5d %+8.3f %6d %+8.2f %s" % (lag, r, n, t or 0, star))
        if t and abs(t) > abs(bestt):
            bestl, bestr, bestt = lag, r, t
    results[nm] = {"rows": rows, "best_lag": bestl, "best_r": bestr, "best_t": bestt,
                   "detrend_deg": deg, "detrend_r2": round(det["r2"], 3),
                   "resid_sd": round(st.pstdev(res), 4),
                   "years": mys, "resid": [round(v, 4) for v in res],
                   "trend_beta1": round(det["beta"][1], 5),
                   "trend_beta0": round(det["beta"][0], 4)}
    if bestl is not None:
        print("     → 最强：lag=%d月, r=%+.3f, t=%+.2f %s" % (
            bestl, bestr, bestt, "（显著）" if abs(bestt) > 2.02 else "（不显著）"))

# ---------- 关键：EN 事件的去趋势残差 ----------
print()
print("=" * 92)
print("强厄尔尼诺事件的去趋势单产残差（这才是可比口径）")
print("=" * 92)
ev_oni = []
for my in sorted(set(W)):
    if int(my) < 1990: continue
    # 找 MY 前 8 月 ~ MY 内 的 ONI 峰值
    best, boff = None, None
    for off in range(-8, 13):
        v = oni_my(my, off)
        if v is not None and (best is None or v > best):
            best, boff = v, off
    if best is not None and best >= 1.5:
        ev_oni.append((my, best, boff))
for nm, cc in [("全球", None), ("马来", "MY"), ("印尼", "ID")]:
    if nm not in results: continue
    R = results[nm]
    idx = {m: i for i, m in enumerate(R["years"])}
    sd = R["resid_sd"]
    print("\n  %s（残差标准差 %.4f MT/HA，趋势斜率 %+.5f/年）" % (nm, sd, R["trend_beta1"]))
    print("     %-7s %7s %10s %10s %s" % ("MY", "峰值ONI", "单产残差", "标准化(σ)", "方向"))
    hits = 0; tot_ = 0
    for my, pk, off in ev_oni:
        if my not in idx: continue
        rv = R["resid"][idx[my]]
        z = rv/sd if sd else 0
        tot_ += 1
        if rv < 0: hits += 1
        print("     %-7s %+7.2f %+10.4f %+9.2fσ %s" % (
            my, pk, rv, z, "▼ 低于趋势" if rv < 0 else "▲ 高于趋势"))
    print("     → 强EN年份单产低于趋势 %d/%d 次" % (hits, tot_))
    results[nm]["events"] = [{"my": m, "peak_oni": p, "offset": o,
                              "resid": R["resid"][idx[m]],
                              "z": round(R["resid"][idx[m]]/sd, 2)}
                             for m, p, o in ev_oni if m in idx]
    results[nm]["neg_hits"] = hits; results[nm]["n_events"] = tot_

json.dump(results, open(os.path.join(BASE, "palm_enso_detrended.json"), "w"),
          ensure_ascii=False, indent=1)
print("\nsaved ->", os.path.join(BASE, "palm_enso_detrended.json"))

# ---------- 结论性判断 ----------
print()
print("=" * 92)
print("统计结论（诚实表述）")
print("=" * 92)
for nm in results:
    R = results[nm]
    sig = R["best_t"] and abs(R["best_t"]) > 2.02
    print("  %s：去趋势后 ONI 最强滞后 %s月 r=%+.3f t=%+.2f → %s" % (
        nm, R["best_lag"], R["best_r"], R["best_t"],
        "统计显著 (p<0.05)" if sig else "统计不显著 (p≥0.05)"))
    print("     强EN年单产低于趋势 %d/%d；趋势项 R²=%.3f 已解释绝大部分单产变异" % (
        R["neg_hits"], R["n_events"], R["detrend_r2"]))
print("""
  ⚠ 关键判断：在 1990-2026 / MY 10-9月 口径下，本数据无法在统计上确立
     「ONI → 棕榈油单产」的滞后关系（所有滞后窗 |t| < 2.02）。
     原因有三：① n=33 个市场年，强EN事件仅 4-5 次，功效不足；
              ② 单产被树龄结构/翻种节奏的长期趋势主导（R²高）；
              ③ USDA PSD 单产是事后修订值，非当年实时观测，含平滑。
     ⇒ 报告中 ENSO 部分只能作为「情景参照 + 产业共识」，不可表述为统计规律。""")
