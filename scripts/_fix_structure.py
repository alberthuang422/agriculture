# -*- coding: utf-8 -*-
"""
收敛 data/ 目录乱象：
- fundamentals/sugar/iso/iso/ 嵌套重复（iso 内又套一个 iso，实为同一份数据的重复）
- 顶层 sugar/、cotton/ 移除（品种目录归入 fundamentals/）
目标结构：
  data/fundamentals/sugar/{iso,raw}
  data/fundamentals/cotton/{raw,wasde_2026}
  data/fundamentals/{sugar,cotton,wheat,corn,soybean}/ 品种散件
"""
import os, shutil, csv, hashlib

data = r'C:\Users\Administrator\Desktop\农业\data'
log = []

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

def copytree_contents(src_dir, dst_dir):
    """把 src_dir 下的内容复制进 dst_dir（不嵌套 src 目录名）"""
    if not os.path.exists(src_dir):
        return
    os.makedirs(dst_dir, exist_ok=True)
    # 复制文件
    for f in os.listdir(src_dir):
        s = os.path.join(src_dir, f)
        d = os.path.join(dst_dir, f)
        if os.path.isdir(s):
            continue  # 目录递归处理
        if os.path.exists(d):
            if os.path.getsize(d) == os.path.getsize(s) and md5(d) == md5(s):
                pass  # 已是相同
            else:
                raise SystemExit(f'CONFLICT {d}')
        else:
            shutil.copy2(s, d)
    # 递归复制子目录
    for d in os.listdir(src_dir):
        s = os.path.join(src_dir, d)
        if os.path.isdir(s):
            copytree_contents(s, os.path.join(dst_dir, d))

def erase(src):
    """递归删除目录/文件（绕过 shutil.move 的跨路径问题）"""
    if os.path.isfile(src):
        os.remove(src)
    elif os.path.isdir(src):
        for f in os.listdir(src):
            erase(os.path.join(src, f))
        os.rmdir(src)

# ============================================================
# 1) 修复 fundamentals/sugar/ 下的嵌套：保留 iso/{balance_pdfs,headlines,market_reports}
#    清除 iso/iso/ 重复嵌套
nest = os.path.join(data, 'fundamentals', 'sugar', 'iso', 'iso')
if os.path.exists(nest):
    # 校验与上级 iso 是否重复
    parent = os.path.join(data, 'fundamentals', 'sugar', 'iso')
    dup = True
    for item in os.listdir(nest):
        s = os.path.join(nest, item)
        d = os.path.join(parent, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                dup = False
                break
        elif os.path.isfile(s):
            if not os.path.exists(d) or md5(s) != md5(d):
                dup = False
                break
    log.append(f'nest iso/iso dup={dup}')
    if dup:
        erase(nest)
        log.append('  removed iso/iso (dup of parent)')
    else:
        # 非纯重复，把嵌套内容并入上级
        copytree_contents(nest, parent)
        erase(nest)
        log.append('  merged iso/iso -> iso/')

# ============================================================
# 2) 把顶层 sugar/、cotton/ 的内容按品种收进 fundamentals/
#    sugar/iso + sugar/raw -> fundamentals/sugar/
if os.path.exists(os.path.join(data, 'sugar')):
    copytree_contents(os.path.join(data, 'sugar', 'iso'), os.path.join(data, 'fundamentals', 'sugar', 'iso'))
    copytree_contents(os.path.join(data, 'sugar', 'raw'), os.path.join(data, 'fundamentals', 'sugar', 'raw'))
    erase(os.path.join(data, 'sugar'))
    log.append('sugar/ -> fundamentals/sugar/')

#    cotton/raw + cotton/wasde_2026 -> fundamentals/cotton/
if os.path.exists(os.path.join(data, 'cotton')):
    copytree_contents(os.path.join(data, 'cotton', 'raw'), os.path.join(data, 'fundamentals', 'cotton', 'raw'))
    copytree_contents(os.path.join(data, 'cotton', 'wasde_2026'), os.path.join(data, 'fundamentals', 'cotton', 'wasde_2026'))
    erase(os.path.join(data, 'cotton'))
    log.append('cotton/ -> fundamentals/cotton/')

print('\n'.join(log))
print('DONE')