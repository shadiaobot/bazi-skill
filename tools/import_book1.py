"""Import book 1 (渊海子平) capability cards into the fusion evidence format.

Each of the 16 cards becomes one claim, mapped to a domain. The R-section
blockquote becomes the quote; the card's one_liner becomes the rule.

Usage:
    python import_book1.py --out fusion/books/yuanhai-ziping/claims.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

SLUG_DOMAIN = {
    "sizhu-qiyun": "D01",
    "shishen-dingwei": "D02",
    "wangshuai-yueling": "D03",
    "yongshen-jifa": "D04",
    "geju-panding": "D05",
    "bingyao-cengci": "D06",
    "dayun-liunian": "D07",
    "guansha-hunza": "D08",
    "shangguan-ge": "D09",
    "yangren-rige": "D10",
    "shensha-chabiao": "D11",
    "liuqin-tuanduan": "D12",
    "xiaoer-guansha": "D12",
    "nvming-duanfa": "D13",
    "xingqing-jibing": "D14",
    "conghua-baxiang": "D15",
}


def r_quote(card: Path) -> str:
    text = card.read_text(encoding="utf-8")
    m = re.search(r"## R.*?\n(.*?)\n## ", text, re.S)
    if not m:
        return ""
    block = m.group(1)
    quotes = re.findall(r"^>\s*「(.+?)」", block, re.M)
    if not quotes:
        return ""
    return quotes[0].strip()


def first_bullet(card: Path) -> str:
    text = card.read_text(encoding="utf-8")
    m = re.search(r"## B.*?\n(.*?)(?:\n## |\Z)", text, re.S)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        s = line.strip()
        if s.startswith("- "):
            return s[2:].strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="books/yuanhai-ziping/.cangjie/capabilities")
    ap.add_argument("--out", default="fusion/books/yuanhai-ziping/claims.yaml")
    args = ap.parse_args()

    src = Path(args.src)
    bundle = yaml.safe_load((src / "verified.yaml").read_text(encoding="utf-8"))
    rows = ["# 《渊海子平》能力卡导入（每卡一条 claim，证据取自卡片 R 段）", ""]
    n = 0
    for cap in bundle["capabilities"]:
        slug = cap["slug"]
        domain = SLUG_DOMAIN.get(slug)
        if not domain:
            continue
        card_path = src / cap["card"]
        quote = r_quote(card_path)
        if not quote:
            continue
        n += 1
        ev = (cap.get("source_evidence") or [{}])[0]
        boundary = first_bullet(card_path) or "见能力卡 B 段"
        entry = {
            "id": f"c-yh-{n:04d}",
            "domain": domain,
            "title": cap["title"],
            "source_id": "src-yuanhai-ziping",
            "location": ev.get("location", "见能力卡"),
            "quote": quote,
            "rule": cap.get("one_liner", ""),
            "trigger": cap.get("intents", ["按能力卡适用场景"])[0] if cap.get("intents") else "按能力卡适用场景",
            "logic": cap.get("one_liner", ""),
            "boundary": boundary[:200],
            "limits": "由能力卡 R/I/E/B 六段承载；本条为合并预演用的能力级摘要",
            "novelty": "new",
            "relates": [],
            "tags": [slug],
        }
        rows.append(yaml.safe_dump([entry], allow_unicode=True, sort_keys=False).strip())
        rows.append("")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"imported {n} capabilities -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
