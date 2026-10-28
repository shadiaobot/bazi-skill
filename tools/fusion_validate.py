"""Validate fusion evidence records (claims / corroborations / terms / divergences).

Usage:
    python fusion_validate.py fusion/books/<book-slug>

Checks: domain ids, quote length, required fields, stance enum, id prefixes,
duplicate ids. Exits non-zero when anything fails.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except Exception:  # noqa: BLE001
    print("need pyyaml: python -m pip install pyyaml")
    raise SystemExit(2)

DOMAINS = {f"D{i:02d}" for i in range(1, 16)}
PREFIX = {
    "claims.yaml": "c-",
    "corroborations.yaml": "r-",
    "boundaries.yaml": "b-",
    "examples.yaml": "e-",
    "terms.yaml": "t-",
    "divergences.yaml": "d-",
}
REQUIRED = {
    "claims.yaml": ["id", "domain", "title", "source_id", "location", "quote",
                    "rule", "trigger", "logic", "boundary", "limits", "novelty"],
    "corroborations.yaml": ["id", "domain", "corroborates", "source_id", "location",
                            "quote", "stance", "note"],
    "boundaries.yaml": ["id", "domain", "source_id", "location", "quote",
                        "failure_mode", "mechanism", "bound_to"],
    "examples.yaml": ["id", "domain", "source_id", "location", "quote", "title"],
    "terms.yaml": ["id", "term", "source_id", "location", "author_definition"],
    "divergences.yaml": ["id", "domain", "question", "positions", "adopted"],
}


def quote_len(text: str) -> int:
    return len(re.sub(r"\s", "", text or ""))


def main() -> int:
    book = Path(sys.argv[1])
    problems: list[str] = []
    seen: Counter = Counter()
    total = 0
    for fname, prefix in PREFIX.items():
        path = book / fname
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if not isinstance(data, list):
            problems.append(f"{fname}: 顶层必须是列表")
            continue
        for i, rec in enumerate(data, 1):
            total += 1
            rid = str(rec.get("id", ""))
            seen[rid] += 1
            for field in REQUIRED[fname]:
                if not rec.get(field):
                    problems.append(f"{fname}#{i} ({rid}): 缺少 {field}")
            if rid and not rid.startswith(prefix):
                problems.append(f"{fname}#{i}: id 前缀应为 {prefix}")
            if rec.get("domain") and rec["domain"] not in DOMAINS:
                problems.append(f"{fname}#{i} ({rid}): 未知域 {rec['domain']}")
            if quote_len(rec.get("quote", "")) > 150:
                problems.append(f"{fname}#{i} ({rid}): 引文 {quote_len(rec.get('quote',''))} 字 >150")
            if fname == "claims.yaml" and rec.get("novelty") not in {"new", "extends", "contradicts"}:
                problems.append(f"{fname}#{i} ({rid}): novelty 非法")
            if fname == "corroborations.yaml" and rec.get("stance") not in {"same", "extends", "contradicts"}:
                problems.append(f"{fname}#{i} ({rid}): stance 非法")
    dups = [k for k, v in seen.items() if v > 1 and k]
    if dups:
        problems.append("重复 id: " + ", ".join(sorted(dups)[:10]))

    print(f"records={total} problems={len(problems)}")
    for p in problems[:40]:
        print(" -", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
