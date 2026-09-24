# -*- coding: utf-8 -*-
"""
批量提取 data/ 下所有 PDF 报告的文本，每个 PDF 对应生成一个 .md 文件。

用法:
    python pdfs_to_md.py

规则:
- 扫描 data/ 下全部 *.pdf（含子目录）
- 每个 PDF 输出同名 .md 到 data/reports_md/<相对路径>/ 下，保持子目录结构
- 提取方式: PyMuPDF 文字层; 若某页完全无文字层(纯扫描件), 在 md 中标注 [该页为扫描件/图片, 无文字层]
- md 头部写入来源 PDF 路径、页数、提取时间等元信息
"""
import os
import sys
import time
import fitz  # PyMuPDF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 项目根目录(农业)
DATA_DIR = os.path.join(ROOT, "data")
OUT_DIR = os.path.join(DATA_DIR, "reports_md")

PAGES_HEADER = "## 第 {n} 页\n\n"

def extract_pdf_to_md(pdf_path: str, md_path: str) -> dict:
    """提取单个 PDF 全部页文本, 写入 md. 返回统计信息."""
    doc = fitz.open(pdf_path)
    stats = {
        "pdf": pdf_path,
        "pages": doc.page_count,
        "chars": 0,
        "empty_pages": [],
        "ocr_like_pages": [],
    }
    parts = []
    # md 头部元信息
    rel = os.path.relpath(pdf_path, ROOT)
    parts.append("---\n")
    parts.append(f"source: {rel}\n")
    parts.append(f"pages: {doc.page_count}\n")
    parts.append(f"extracted: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    parts.append("extractor: pymupdf 文字层\n")
    parts.append("---\n\n")
    parts.append(f"# {os.path.splitext(os.path.basename(pdf_path))[0]}\n\n")

    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text")
        text = text.replace("\u00a0", " ").strip()
        if not text:
            # 尝试判断是否为扫描页(有图片但无文字层)
            imgs = page.get_images(full=True)
            if imgs:
                stats["ocr_like_pages"].append(i + 1)
                parts.append(PAGES_HEADER.format(n=i + 1))
                parts.append(f"> [该页为图片/扫描件, 无文字层, 共 {len(imgs)} 张图片 — 未做 OCR]\n\n")
            else:
                stats["empty_pages"].append(i + 1)
                parts.append(PAGES_HEADER.format(n=i + 1))
                parts.append("> [该页无文字内容]\n\n")
            continue
        stats["chars"] += len(text)
        parts.append(PAGES_HEADER.format(n=i + 1))
        parts.append(text + "\n\n")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("".join(parts))
    doc.close()
    return stats

def main() -> None:
    pdfs = []
    for dirpath, _dirnames, filenames in os.walk(DATA_DIR):
        if os.path.normpath(OUT_DIR) in [os.path.normpath(os.path.join(dirpath, f)) for f in []]:
            continue
        for fn in filenames:
            if fn.lower().endswith(".pdf"):
                # 跳过输出目录自身的任何文件
                pdfs.append(os.path.join(dirpath, fn))

    # 排除输出目录
    pdfs = [p for p in pdfs if not os.path.abspath(p).startswith(os.path.abspath(OUT_DIR))]
    pdfs.sort()

    print(f"发现 {len(pdfs)} 份 PDF")
    results = []
    for idx, pdf in enumerate(pdfs, 1):
        rel = os.path.relpath(pdf, DATA_DIR)
        stem = os.path.splitext(rel)[0]
        md_path = os.path.join(OUT_DIR, stem + ".md")
        os.makedirs(os.path.dirname(md_path), exist_ok=True)
        t0 = time.time()
        try:
            stats = extract_pdf_to_md(pdf, md_path)
            stats["seconds"] = round(time.time() - t0, 2)
            stats["status"] = "ok"
        except Exception as e:  # noqa: BLE001
            stats = {"pdf": pdf, "status": "error", "error": str(e)}
        results.append(stats)
        if idx % 10 == 0 or idx == len(pdfs):
            print(f"  进度 {idx}/{len(pdfs)}")

    # 汇总
    ok = sum(1 for r in results if r["status"] == "ok")
    err = [r for r in results if r["status"] == "error"]
    print(f"完成: {ok}/{len(pdfs)} 成功, {len(err)} 失败")
    for r in err:
        print(f"  [错误] {r['pdf']}: {r['error']}")

    # 简要质量报告: 提取字符数过少(可能为扫描件)的文件
    low = [r for r in results if r.get("status") == "ok" and r.get("chars", 0) < 200 * r.get("pages", 1)]
    if low:
        print("以下文件提取字符量偏低, 可能是扫描件, 建议 OCR 处理:")
        for r in low:
            print(f"  {os.path.relpath(r['pdf'], ROOT)}  chars={r['chars']}  pages={r['pages']}")

    # 写汇总清单
    manifest = os.path.join(OUT_DIR, "_manifest.md")
    with open(manifest, "w", encoding="utf-8") as f:
        f.write("# reports_md 索引\n\n")
        f.write("每个 PDF 提取的文本版(md), 保持子目录结构.\n\n")
        f.write("| md 文件 | 源 PDF | 页数 | 字符数 | 状态 |\n")
        f.write("|---|---|---:|---:|---|\n")
        for r in results:
            if r["status"] == "ok":
                rel_md = os.path.relpath(
                    os.path.join(OUT_DIR, os.path.splitext(os.path.relpath(r["pdf"], DATA_DIR))[0] + ".md"),
                    OUT_DIR,
                )
                f.write(
                    f"| {rel_md} | {os.path.relpath(r['pdf'], DATA_DIR)} | "
                    f"{r.get('pages', '-')} | {r.get('chars', '-')} | ok |\n"
                )
            else:
                f.write(
                    f"| - | {os.path.relpath(r['pdf'], DATA_DIR)} | - | - | 错误: {r.get('error')} |\n"
                )
    print(f"索引: {manifest}")

if __name__ == "__main__":
    sys.exit(main())
