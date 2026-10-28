"""Split extracted per-page text into per-chapter files and an index.

Usage:
    python build_chapters.py <source_dir>

Reads <source_dir>/pages/p*.txt, groups pages by the "第 N 章" markers that this
edition prints at the top of each chapter, and writes:
    <source_dir>/chapters/NNNN-<title>.md
    <source_dir>/chapter-index.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CHAPTER_RE = re.compile(r"^第\s*(\d+)\s*章\s*$")
FOOTER_RE = re.compile(r"^www\.luckclub\.cn")


def clean_page(text: str) -> str:
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if FOOTER_RE.match(s):
            continue
        if s in {"《》", "》- 古籍典藏 www.luckclub.cn"}:
            continue
        lines.append(s)
    return "\n".join(lines)


def slugify(title: str) -> str:
    t = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title).strip("-")
    return t[:40] or "chapter"


def safe_name(idx: int, title: str) -> str:
    return f"{idx:04d}-{slugify(title)}.md"


def main() -> int:
    src = Path(sys.argv[1])
    pages_dir = src / "pages"
    out_dir = src / "chapters"
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = sorted(pages_dir.glob("p*.txt"), key=lambda p: int(p.stem[1:]))
    chapters: list[dict] = []
    for path in pages:
        num = int(path.stem[1:])
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        found = None
        for pos, line in enumerate(lines[:4]):
            m = CHAPTER_RE.match(line.strip())
            if m:
                found = (pos, int(m.group(1)))
                break
        if found:
            pos, number = found
            title = ""
            for line in lines[pos + 1 :]:
                s = line.strip()
                if s and s not in {"《》", "原 文", "原文"}:
                    title = s
                    break
            chapters.append(
                {"chapter": number, "title": title, "start": num, "pages": [num], "texts": [text]}
            )
        elif chapters:
            chapters[-1]["pages"].append(num)
            chapters[-1]["texts"].append(text)

    index_rows = [
        "# 渊海子平 · 章节索引",
        "",
        "| 章 | 标题 | 起始页 | 结束页 | 页数 | 字数 | 文件 |",
        "|---|---|---|---|---|---|---|",
    ]
    for ch in chapters:
        body = "\n\n".join(f"<!-- page {p} -->\n\n{clean_page(t)}" for p, t in zip(ch["pages"], ch["texts"]))
        fname = safe_name(ch["chapter"], ch["title"])
        header = f"# 第 {ch['chapter']} 章 · {ch['title']}\n\n> 源文件页码: p{ch['start']:04d}-p{ch['pages'][-1]:04d}（本 PDF 版《渊海子平》，含原文/白话译文/关键词/现代启示）\n"
        (out_dir / fname).write_text(header + "\n" + body + "\n", encoding="utf-8")
        chars = len(re.sub(r"\s", "", body))
        index_rows.append(
            f"| {ch['chapter']} | {ch['title']} | {ch['start']} | {ch['pages'][-1]} | "
            f"{len(ch['pages'])} | {chars} | {fname} |"
        )

    (src / "chapter-index.md").write_text("\n".join(index_rows) + "\n", encoding="utf-8")
    total = sum(len(re.sub(r"\s", "", "\n".join(c["texts"]))) for c in chapters)
    print(f"chapters: {len(chapters)}  total_chars: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
