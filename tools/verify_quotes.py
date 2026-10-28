"""Verbatim quote checker for stage-1 candidates (deterministic, no LLM).

Every candidate carries a ``source_quote`` that must be copied word-for-word
from the 「原文（含眉批）」 section of a chapter.  This tool checks that claim
against the corpus and separates three failure classes:

* ``ok``          quote found in 原文 (whitespace-insensitive, ellipsis allowed)
* ``baihua``      quote was taken from the modern translator's 白话译文 (hard error)
* ``missing``     quote not found anywhere (paraphrase, typo, or OCR damage)

Usage:
    python verify_quotes.py <candidate.md | raw_dir> [...] \
        --corpus books/yuanhai-ziping/source/corpus \
        --out .work/verify/quote-check.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is optional at runtime
    yaml = None

SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.M)
YUAN_KEYS = ("原文",)
BAI_KEYS = ("白话",)
ITEM_RE = re.compile(r"^- id:\s*(\S+)", re.M)
ELLIPSIS_RE = re.compile(r"[…\.]{2,}|…")
WRAP_CHARS = '"“”\'‘’ '
MIN_PART = 4
QUOTE_FIELDS = (
    "source_quote",
    "author_definition",
    "quote",
    "example_quote",
    "source_quote_1",
    "原文",
)
TRAILING_PUNCT = "。，、；：！？.,;:!?」』”\"'）)"


def normalize(text: str) -> str:
    """Drop whitespace and normalise quote marks so wrapping stops mattering."""
    text = unicodedata.normalize("NFKC", text)
    out = [ch for ch in text if not ch.isspace()]
    return "".join(out)


def clean_quote(raw: str) -> str:
    text = raw.strip()
    if text.startswith("|") or text.startswith(">"):
        text = text[1:].strip()
    while len(text) >= 2 and text[0] in WRAP_CHARS and text[-1] in WRAP_CHARS:
        text = text[1:-1].strip()
    return text


def pick_quote(entry: dict) -> tuple[str, str]:
    """Return (field_name, quote) using the first populated quote field."""
    for field in QUOTE_FIELDS:
        value = entry.get(field)
        if isinstance(value, str) and value.strip():
            return field, clean_quote(value)
    return "", ""


def split_sections(body: str) -> dict[str, str]:
    """Return {heading: text} for a chapter file."""
    sections: dict[str, str] = {}
    matches = list(SECTION_RE.finditer(body))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections[m.group(1)] = body[start:end]
    return sections


def load_corpus(corpus_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    yuan: dict[str, str] = {}
    bai: dict[str, str] = {}
    for path in sorted(corpus_dir.glob("*.md")):
        body = path.read_text(encoding="utf-8")
        # page markers (`<!-- page 162 -->`) are extraction artifacts, not 原文;
        # drop them so a quote spanning a page break still verifies
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
        sections = split_sections(body)
        label = path.stem
        y = "".join(v for k, v in sections.items() if any(x in k for x in YUAN_KEYS))
        b = "".join(v for k, v in sections.items() if any(x in k for x in BAI_KEYS))
        if not y:  # no headings at all: treat the whole file as 原文
            y = body
        yuan[label] = normalize(y)
        bai[label] = normalize(b)
    return yuan, bai


def parse_items(text: str) -> list[dict[str, str]]:
    """Pull (id, source_quote) pairs out of a candidate file."""
    blocks = [m.group(1) for m in re.finditer(r"```ya?ml\s*\n(.*?)```", text, re.S)]
    if not blocks:
        blocks = [text]
    items: list[dict[str, str]] = []
    for block in blocks:
        if yaml is not None:
            try:
                data = yaml.safe_load(block)
            except Exception:
                data = None
            if isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict) and entry.get("id"):
                        field, quote = pick_quote(entry)
                        items.append(
                            {
                                "id": str(entry["id"]).strip(),
                                "field": field,
                                "source_quote": quote,
                            }
                        )
                continue
        items.extend(regex_items(block))
    return [it for it in items if it["id"]]


def regex_items(block: str) -> list[dict[str, str]]:
    items = []
    marks = list(ITEM_RE.finditer(block))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(block)
        chunk = block[m.start():end]
        field, quote = "", ""
        for name in QUOTE_FIELDS:
            inline = re.search(rf"^\s+{name}:\s*(.+)$", chunk, re.M)
            if inline and inline.group(1).strip() not in ("|", ">", "|-", ">-"):
                field, quote = name, inline.group(1)
                break
            scalar = re.search(rf"^\s+{name}:\s*[|>][-+]?\s*\n((?:\s{{4,}}.*\n?)+)", chunk, re.M)
            if scalar:
                field = name
                quote = re.sub(r"^\s{4}", "", scalar.group(1), flags=re.M)
                break
        items.append({"id": m.group(1), "field": field, "source_quote": clean_quote(quote)})
    return items


def locate(needle: str, haystack: dict[str, str]) -> str | None:
    for label, text in haystack.items():
        if needle and needle in text:
            return label
    return None


def locate_parts(needle: str, haystack: dict[str, str]) -> tuple[str, int]:
    """Handle quotes that elide text with ellipses.

    Every part must be found verbatim, but the parts may sit in different
    chapters (a quote may legitimately join two related passages).  The set of
    chapters is returned so that such joins stay visible in the report.
    """
    parts = [p for p in ELLIPSIS_RE.split(needle) if len(p) >= MIN_PART]
    if len(parts) < 2:
        return "", 0
    found: list[str] = []
    for part in parts:
        for label, text in haystack.items():
            if part in text:
                found.append(label)
                break
        else:
            # tolerate a punctuation mark the transcriber added at a fragment
            # boundary, exactly like the `ok-punct` rule for whole quotes
            trimmed_part = part.rstrip(TRAILING_PUNCT)
            if len(trimmed_part) >= MIN_PART:
                for label, text in haystack.items():
                    if trimmed_part in text:
                        found.append(label)
                        break
                else:
                    return "", 0
            else:
                return "", 0
    return " + ".join(sorted(set(found))), len(parts)


def check_file(path: Path, yuan: dict[str, str], bai: dict[str, str]) -> list[dict[str, object]]:
    items = parse_items(path.read_text(encoding="utf-8"))
    results = []
    for item in items:
        quote = item["source_quote"]
        norm = normalize(quote)
        trimmed = norm.rstrip(TRAILING_PUNCT)
        if not norm:
            status, where, note = "empty", "", "条目没有 source_quote"
        elif len(norm) < 8:
            status, where, note = "short", "", "引用过短，无法核验"
        elif (where := locate(norm, yuan)):
            status, note = "ok", ""
        elif len(trimmed) >= 8 and (where := locate(trimmed, yuan)):
            status, note = "ok-punct", "仅句末标点与原文不同（截断处改写）"
        elif (where := locate(norm, bai)):
            status, note = "baihua", "引文出自白话译文，不是原文"
        elif (found := locate_parts(norm, yuan))[0]:
            where, count = found
            note = f"含省略号，分 {count} 段命中"
            status = "ok-join" if " + " in where else "ok"
        elif (found := locate_parts(norm, bai))[0]:
            where, count = found
            status, note = "baihua", f"省略引文命中白话译文，分 {count} 段"
        else:
            where, status, note = "", "missing", "原文中找不到该引文（改写、讹字或抽取错误）"
        results.append(
            {
                "file": str(path),
                "id": item["id"],
                "field": item.get("field", "source_quote"),
                "status": status,
                "chapter": where,
                "note": note,
                "head": quote[:40],
                "raw_quote": quote,
            }
        )
    return results


def explain(row: dict[str, object], yuan: dict[str, str]) -> str:
    """Show where a missing quote stops matching the corpus."""
    quote = normalize(str(row["raw_quote"]))
    for label, text in yuan.items():
        best = 0
        for size in range(min(len(quote), 200), 7, -1):
            if quote[:size] in text:
                best = size
                break
        if best:
            pos = text.find(quote[:best]) + best
            return (
                f"{row['id']} 前 {best}/{len(quote)} 字吻合（{label}）：\n"
                f"    引文续：{quote[best:best + 30]}\n"
                f"    原文续：{text[pos:pos + 30]}"
            )
    return f"{row['id']} 与任何章节都无 8 字以上吻合（引文开头：{quote[:20]}）"


def repair_context(row: dict[str, object], yuan: dict[str, str], width: int) -> str:
    """Corpus window aligned to the quote, for hand-repairing one entry."""
    quote = normalize(str(row["raw_quote"]))
    head = quote[:8]
    for label, text in yuan.items():
        pos = text.find(head)
        if pos >= 0:
            span = min(len(quote) + width, len(text) - pos)
            return (
                f"{row['id']} [{row['status']}] {label}\n"
                f"  Q: {quote}\n"
                f"  C: {text[pos:pos + span]}"
            )
    for label, text in yuan.items():
        for size in range(7, 3, -1):
            pos = text.find(quote[:size])
            if pos >= 0:
                span = min(len(quote) + width, len(text) - pos)
                return (
                    f"{row['id']} [{row['status']}] {label} (仅前 {size} 字定位)\n"
                    f"  Q: {quote}\n"
                    f"  C: {text[pos:pos + span]}"
                )
    return f"{row['id']} [{row['status']}] 无法定位\n  Q: {quote}"


def collect(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob("*.md") if p.is_file()))
        elif path.is_file():
            files.append(path)
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--corpus", default="books/yuanhai-ziping/source/corpus")
    ap.add_argument("--out", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--show-ok", action="store_true")
    ap.add_argument("--explain", action="store_true", help="打印未命中条目的吻合断点")
    ap.add_argument("--context", type=int, default=0, help="为未通过条目打印原文对齐窗口")
    args = ap.parse_args()

    yuan, bai = load_corpus(Path(args.corpus))
    if not yuan:
        print(f"corpus empty: {args.corpus}", file=sys.stderr)
        return 2

    rows: list[dict[str, object]] = []
    for path in collect(args.targets):
        rows.extend(check_file(path, yuan, bai))

    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row["status"])] = counts.get(str(row["status"]), 0) + 1

    lines = ["# 引文核验（source_quote 逐字比对原文）", ""]
    lines.append(f"- 语料章节：{len(yuan)}")
    lines.append(f"- 条目总数：{len(rows)}")
    for status in sorted(counts):
        lines.append(f"- {status}: {counts[status]}")
    lines.append("")
    problem = [r for r in rows if r["status"] not in ("ok", "ok-join")]
    joins = [r for r in rows if r["status"] == "ok-join"]
    lines.append(f"## 需处理（{len(problem)} 条）")
    lines.append("")
    lines.append("| 文件 | id | 状态 | 命中章节 | 说明 | 引文开头 |")
    lines.append("|---|---|---|---|---|---|")
    for row in problem:
        lines.append(
            f"| {Path(str(row['file'])).name} | {row['id']} | {row['status']} | "
            f"{row['chapter']} | {row['note']} | {str(row['head']).replace('|', '丨')} |"
        )
    lines += ["", f"## 跨段拼接，需人工复核（{len(joins)} 条）", ""]
    lines += ["| 文件 | id | 涉及章节 | 引文开头 |", "|---|---|---|---|"]
    for row in joins:
        lines.append(
            f"| {Path(str(row['file'])).name} | {row['id']} | {row['chapter']} | "
            f"{str(row['head']).replace('|', '丨')} |"
        )
    if args.show_ok:
        lines += ["", "## 通过条目", "", "| 文件 | id | 命中章节 | 引文开头 |", "|---|---|---|---|"]
        for row in rows:
            if row["status"] == "ok":
                lines.append(
                    f"| {Path(str(row['file'])).name} | {row['id']} | {row['chapter']} | "
                    f"{str(row['head']).replace('|', '丨')} |"
                )
    report = "\n".join(lines) + "\n"

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
    if args.explain:
        suspects = [r for r in rows if r["status"] == "missing"]
        print(f"--- explain: {len(suspects)} 条未命中 ---")
        for row in suspects:
            print(explain(row, yuan))
    if args.context:
        flagged = [r for r in rows if r["status"] not in ("ok", "empty")]
        print(f"--- repair context: {len(flagged)} 条 ---")
        for row in flagged:
            print(repair_context(row, yuan, args.context))
    if args.json:
        json_path = Path(args.json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps([{k: v for k, v in r.items() if k != "raw_quote"} for r in rows],
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"items={len(rows)} " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    for row in problem[:40]:
        print(f"  [{row['status']}] {row['id']} :: {str(row['head'])[:36]}")
    if args.out:
        print(f"report: {args.out}")
    return 0 if counts.get("missing", 0) == 0 and counts.get("baihua", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
