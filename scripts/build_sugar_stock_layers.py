import csv, io, os, json
from collections import defaultdict

base = r"C:\Users\Administrator\Desktop\农业"
psd = os.path.join(base, "data", "fundamentals", "sugar", "raw", "psd_sugar_all.csv")

A = {"020":"beg","028":"prod","057":"imp","088":"exp","126":"disp","176":"end"}
rows = []
with io.open(psd, encoding="utf-8-sig") as f:
    for r in csv.reader(f):
        if len(r) < 12 or r[7] not in A: continue
        rows.append((r[2], r[3], int(r[4]), A[r[7]], float(r[11])))

d = defaultdict(lambda: defaultdict(float))
nm = {}
for cc, cn, y, k, v in rows:
    d[(cc, y)][k] += v
    nm[cc] = cn

def G(cc, y, k): return d[(cc, y)].get(k, 0.0)
def W(y, k): return sum(d[(c, y)].get(k, 0.0) for c in nm if (c, y) in d)

KEY = ["BR","TH","IN","CH","PK","E4","US","ID","MX","AS","EG","RS","UP","RP","IR"]
YEARS = list(range(2014, 2026))

out = []
out.append("=== ENDING STOCKS COMPOSITION (1000 MT, raw value; share of world) ===")
hdr = "MY    " + "".join("%9s" % c for c in KEY) + "%9s" % "WORLD"
out.append(hdr)
for y in YEARS:
    w = W(y, "end")
    line = "%-6d" % y
    for c in KEY:
        line += "%9.0f" % G(c, y, "end")
    line += "%9.0f" % w
    out.append(line)

out.append("")
out.append("=== SHARE OF WORLD ENDING STOCKS (%) ===")
out.append(hdr)
for y in YEARS:
    w = W(y, "end") or 1
    line = "%-6d" % y
    for c in KEY:
        line += "%9.1f" % (G(c, y, "end")/w*100)
    line += "%9.1f" % 100.0
    out.append(line)

# freely-tradeable residual: world minus the "locked" layer (CN state, IN policy, TH residual, PK, ID, US, MX, EG, RU, UA, PH, IR)
LOCKED = ["CH","IN","TH","PK","ID","US","MX","EG","RS","UP","RP","IR"]
out.append("")
out.append("=== STOCK LAYERING: locked (policy/domestic-buffer) vs residual ===")
out.append("MY     world   locked   locked%%  residual(BR+AU+EU+GT+AR+CO+others)")
for y in YEARS:
    w = W(y, "end")
    lk = sum(G(c, y, "end") for c in LOCKED)
    out.append("%-6d %7.0f %8.0f %7.1f%% %10.0f" % (y, w, lk, lk/w*100, w-lk))

# Brazil: production / exports / stocks / stock-to-export ratio
out.append("")
out.append("=== BRAZIL: the marginal supplier (zero-carryover machine) ===")
out.append("MY    prod     exp   end  end/exp%%  cons")
for y in YEARS:
    pr, ex, en, co = G("BR",y,"prod"), G("BR",y,"exp"), G("BR",y,"end"), G("BR",y,"disp")
    out.append("%-6d %6.0f %7.0f %5.0f %8.1f%% %6.0f" % (y, pr, ex, en, (en/ex*100 if ex else 0), co))

# India & Thailand exports (policy swing)
out.append("")
out.append("=== INDIA / THAILAND exports (policy swing supplier) ===")
out.append("MY     IN_exp  IN_prod  IN_end   TH_exp  TH_prod  TH_end")
for y in YEARS:
    out.append("%-6d %7.0f %8.0f %7.0f %8.0f %8.0f %7.0f" % (
        y, G("IN",y,"exp"), G("IN",y,"prod"), G("IN",y,"end"),
        G("TH",y,"exp"), G("TH",y,"prod"), G("TH",y,"end")))

# China drawdown
out.append("")
out.append("=== CHINA: state reserve drawdown ===")
out.append("MY     prod   imp   cons    end  end%%world")
for y in YEARS:
    w = W(y, "end") or 1
    out.append("%-6d %6.0f %6.0f %6.0f %6.0f %8.1f%%" % (
        y, G("CH",y,"prod"), G("CH",y,"imp"), G("CH",y,"disp"), G("CH",y,"end"), G("CH",y,"end")/w*100))

# world balance + stocks + s/u
out.append("")
out.append("=== WORLD BALANCE (USDA PSD raw value) ===")
out.append("MY      prod    cons     bal     beg     end   s/u%%  exp")
for y in YEARS:
    pr, co, im, ex = W(y,"prod"), W(y,"disp"), W(y,"imp"), W(y,"exp")
    bg, en = W(y,"beg"), W(y,"end")
    out.append("%-6d %7.0f %7.0f %+7.0f %7.0f %7.0f %5.1f%% %6.0f" % (
        y, pr, co, pr+im-ex-co, bg, en, en/co*100, ex))

# save structured json for the report
res = {"years": YEARS, "key": KEY,
       "end": {c: {str(y): round(G(c,y,"end")) for y in YEARS} for c in KEY},
       "world_end": {str(y): round(W(y,"end")) for y in YEARS},
       "world": {str(y): {k: round(W(y,k)) for k in ["beg","prod","imp","exp","disp","end"]} for y in YEARS},
       "locked": {str(y): round(sum(G(c,y,"end") for c in LOCKED)) for y in YEARS},
       "countries": {c: {str(y): {k: round(G(c,y,k)) for k in ["prod","imp","exp","disp","end"]} for y in YEARS} for c in ["BR","TH","IN","CH","E4","AS","PK"]},
       "locked_list": LOCKED}
with io.open(os.path.join(base, "data", "fundamentals", "sugar", "sugar_stock_layers_2014_2025.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)

with io.open(os.path.join(base, "scripts", "_tmp_stocks.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("ok")
