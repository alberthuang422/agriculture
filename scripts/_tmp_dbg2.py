import os, io, glob

base = r"C:\Users\Administrator\Desktop\农业"
out = []

for sub in ["data", "data/cftc", "data/fundamentals", "data/price", "scripts"]:
    d = os.path.join(base, sub)
    out.append("=== %s  exists=%s ===" % (sub, os.path.isdir(d)))
    if os.path.isdir(d):
        try:
            for n in sorted(os.listdir(d)):
                fp = os.path.join(d, n)
                sz = os.path.getsize(fp) if os.path.isfile(fp) else -1
                out.append("   %-46s %s" % (n, sz if sz >= 0 else "DIR"))
        except Exception as e:
            out.append("   ERR %s" % e)

out.append("=== glob sugar/cftc anywhere ===")
for pat in ["data/**/*.csv"]:
    for f in sorted(glob.glob(os.path.join(base, pat), recursive=True)):
        out.append("   %s" % f)

with io.open(os.path.join(base, "scripts", "_tmp_dbg2.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("ok")
