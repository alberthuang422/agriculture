import csv, io, json, os

base = r"C:\Users\Administrator\Desktop\农业"
out = []

# 1. price file range
p = os.path.join(base, "data", "price", "sugar", "sb_price_daily.csv")
with io.open(p, encoding="utf-8-sig") as f:
    rows = list(csv.reader(f))
out.append("price rows: %d  header=%s" % (len(rows), rows[0]))
out.append("first=%s  last=%s" % (rows[1][:5], rows[-1][:5]))

# 2. cftc range
c = os.path.join(base, "data", "cftc", "sugar_cftc_futonly_1986_2026.csv")
with io.open(c, encoding="utf-8-sig") as f:
    crows = list(csv.reader(f))
out.append("cftc rows: %d header=%s" % (len(crows), crows[0]))
out.append("cftc first=%s last=%s" % (crows[1][0], crows[-1][0]))

with io.open(os.path.join(base, "scripts", "_tmp_probe.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("ok")
