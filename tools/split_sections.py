"""Split each chapter file into its four editorial sections.

The luckclub PDF edition prints every chapter as: 原文 (with 眉批) / 白话译文 /
关键词 / 现代启示.  Only the first two belong to the transmitted text; 关键词 and
现代启示 are added by the modern publisher and must not be treated as the
author's claims.

Usage:
    python split_sections.py <source_dir>

Writes:
    <source_dir>/sections/<chapter>/yuanwen.md|baihua.md|keywords.md|commentary.md
    <source_dir>/corpus/<chapter>.md      (原文 + 白话译文 only, for extractors)
    <source_dir>/section-report.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

FOOTER_RE = re.compile(r"^www\.luckclub\.cn")
PAGE_RE = re.compile(r"^<!-- page (\d+) -->$")

MARKERS = {
    "原 文": "yuanwen",
    "原文": "yuanwen",
    "白话译文": "baihua",
    "关键词": "keywords",
    "现代启示": "commentary",
}
LABELS = {
    "yuanwen": "原文（含眉批）",
    "baihua": "白话译文",
    "keywords": "关键词（编者所加）",
    "commentary": "现代启示（编者所加）",
}


def main() -> int:
    src = Path(sys.argv[1])
    chap_dir = src / "chapters"
    sections_root = src / "sections"
    corpus_root = src / "corpus"
    sections_root.mkdir(parents=True, exist_ok=True)
    corpus_root.mkdir(parents=True, exist_ok=True)

    report = ["# 分段结果", "", "| 章 | 原文段 | 白话段 | 关键词段 | 现代启示段 | 缺段 |", "|---|---|---|---|---|---|"]
    for path in sorted(chap_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        header_lines = []
        body_lines = []
        for line in text.splitlines():
            (header_lines if line.startswith(("#", ">")) and not body_lines else body_lines).append(line)

        current = None
        buckets: dict[str, list[str]] = {k: [] for k in LABELS}
        for line in body_lines:
            s = line.strip()
            key = MARKERS.get(s)
            if key:
                current = key
                continue
            if FOOTER_RE.match(s) or s == "《》":
                continue
            if current:
                buckets[current].append(line)

        ch_dir = sections_root / path.stem
        ch_dir.mkdir(parents=True, exist_ok=True)
        missing = []
        for key, lines in buckets.items():
            body = "\n".join(lines).strip()
            (ch_dir / f"{key}.md").write_text(
                f"# {path.stem} · {LABELS[key]}\n\n{body}\n", encoding="utf-8"
            )
            if len(body) < 30:
                missing.append(key)

        # corpus view: transmitted text only
        corpus_body = []
        for key in ("yuanwen", "baihua"):
            content = "\n".join(buckets[key]).strip()
            if content:
                corpus_body.append(f"## {LABELS[key]}\n\n{content}")
        (corpus_root / f"{path.stem}.md").write_text(
            header_lines[0] + "\n\n" + "\n\n".join(corpus_body) + "\n", encoding="utf-8"
        )

        report.append(
            f"| {path.stem} | {len(buckets['yuanwen'])} | {len(buckets['baihua'])} | "
            f"{len(buckets['keywords'])} | {len(buckets['commentary'])} | {','.join(missing) or '-'} |"
        )

    (src / "section-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"sections written for {len(list(chap_dir.glob('*.md')))} chapters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
