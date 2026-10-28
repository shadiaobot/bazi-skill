"""Verify cross-book divergence quotes against each book's own corpus.

Usage:
    python verify_divergences.py fusion/books/<slug>/divergences.yaml

Map source_id -> corpus dir below when new books are added.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from verify_quotes import load_corpus, locate, normalize  # noqa: E402

BOOKS = {
    "src-yuanhai-ziping": "books/yuanhai-ziping/source/corpus",
    "src-ziping-zhenquan": "books/ziping-zhenquan/source/corpus",
    "src-shenfeng-tongkao": "books/shenfeng-tongkao/source/corpus",
    "src-mingli-yueyan": "books/mingli-yueyan/source/corpus",
}


def main() -> int:
    path = Path(sys.argv[1])
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    corpora = {k: load_corpus(Path(v))[0] for k, v in BOOKS.items()}
    bad = 0
    total = 0
    for rec in data:
        for pos in rec.get("positions", []):
            total += 1
            book = pos.get("book")
            quote = normalize(pos.get("quote", ""))
            where = locate(quote, corpora.get(book, {}))
            if not where:
                bad += 1
                print(f"[missing] {rec['id']} @ {book}: {pos.get('quote','')[:40]}")
    print(f"positions={total} missing={bad}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
