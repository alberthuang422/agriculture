import os, io, sys

base = r"C:\Users\Administrator\Desktop\农业"
out = []
out.append("base exists: %s" % os.path.isdir(base))
out.append("sys.getdefaultencoding: %s" % sys.getdefaultencoding())
out.append("filesystem encoding: %s" % sys.getfilesystemencoding())

d = os.path.join(base, "data")
out.append("data exists: %s" % os.path.isdir(d))
if os.path.isdir(d):
    for n in sorted(os.listdir(d)):
        out.append("  data/%s" % n)
    s = os.path.join(d, "sugar")
    out.append("data/sugar exists: %s" % os.path.isdir(s))
    if os.path.isdir(s):
        for n in sorted(os.listdir(s)):
            out.append("    data/sugar/%s" % n)
            sub = os.path.join(s, n)
            if os.path.isdir(sub):
                for m in sorted(os.listdir(sub)):
                    out.append("      data/sugar/%s/%s" % (n, m))

# try creating dir
iso = os.path.join(base, "data", "sugar", "iso")
out.append("iso path exists: %s  (%r)" % (os.path.isdir(iso), iso))

with io.open(os.path.join(base, "scripts", "_tmp_dbg.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("ok")
