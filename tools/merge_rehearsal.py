"""Merge rehearsal: per-domain view across all books in fusion/books.

Usage:
    python merge_rehearsal.py --books fusion/books --out fusion/merge-rehearsal.md
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import yaml

DOMAIN_NAMES = {
    "D01": "排盘与起运", "D02": "十神与关系", "D03": "旺衰与月令",
    "D04": "取用与忌法", "D05": "格局判定", "D06": "病药与层次",
    "D07": "大运与流年", "D08": "官杀混杂", "D09": "伤官格",
    "D10": "阳刃与特殊日格", "D11": "神煞查法", "D12": "六亲（含小儿）",
    "D13": "女命", "D14": "性情与疾病", "D15": "从格与化气",
}


def load(path: Path):
    if not path.exists():
        return []
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", default="fusion/books")
    ap.add_argument("--out", default="fusion/merge-rehearsal.md")
    args = ap.parse_args()

    books = [p for p in sorted(Path(args.books).iterdir()) if p.is_dir() and not p.name.startswith("_")]
    claims = defaultdict(list)
    bounds = defaultdict(list)
    corrs = defaultdict(list)
    terms = []
    divs = []
    stats = {}
    for b in books:
        c = load(b / "claims.yaml")
        bd = load(b / "boundaries.yaml")
        r = load(b / "corroborations.yaml")
        t = load(b / "terms.yaml")
        d = load(b / "divergences.yaml")
        stats[b.name] = {"claims": len(c), "boundaries": len(bd), "corroborations": len(r),
                         "terms": len(t), "divergences": len(d)}
        for x in c:
            claims[x["domain"]].append((b.name, x))
        for x in r:
            corrs[x["domain"]].append((b.name, x))
        for x in bd:
            bounds[x["domain"]].append((b.name, x))
        terms += [(b.name, x) for x in t]
        divs += [(b.name, x) for x in d]

    out = ["# 两书合并预演", "",
           "| 书 | claims | boundaries | corroborations | terms | divergences |", "|---|---|---|---|---|---|"]
    for name, s in stats.items():
        out.append(f"| {name} | {s['claims']} | {s['boundaries']} | {s['corroborations']} | {s['terms']} | {s['divergences']} |")

    names = [b.name for b in books]
    short = {"yuanhai-ziping": "渊海", "ziping-zhenquan": "真诠", "shenfeng-tongkao": "神峰"}
    heads = " | ".join(short.get(n, n) for n in names)
    out += ["", "## 域覆盖", "",
            f"| 域 | 名称 | {heads} | 边界 | 合计 | 判定 |",
            "|---|---|" + "---|" * len(names) + "---|---|---|"]
    weak = []
    for d in sorted(DOMAIN_NAMES):
        rows = claims.get(d, [])
        by = defaultdict(int)
        for b, _ in rows:
            by[b] += 1
        bb = defaultdict(int)
        for b, _ in bounds.get(d, []):
            bb[b] += 1
        total = len(rows) + len(bounds.get(d, []))
        verdict = "强" if total >= 8 else ("中" if total >= 3 else "弱")
        if total < 3:
            weak.append((d, total))
        cells = " | ".join(str(by.get(n, 0)) for n in names)
        out.append(f"| {d} | {DOMAIN_NAMES[d]} | {cells} | {sum(bb.values())} | {total} | {verdict} |")

    out += ["", "## 各域证据分布", ""]
    for d in sorted(DOMAIN_NAMES):
        rows = claims.get(d, [])
        out.append(f"### {d} {DOMAIN_NAMES[d]}（{len(rows)} 条）")
        by = defaultdict(list)
        for b, x in rows:
            by[b].append(x)
        for b in sorted(by):
            out.append(f"- **{b}**：" + "；".join(x["title"] for x in by[b][:8]))
        cs = corrs.get(d, [])
        if cs:
            out.append("- 佐证：" + "；".join(f"{x['stance']}" for _, x in cs))
        out.append("")

    out += ["## 跨书分歧", ""]
    for b, x in divs:
        out.append(f"- **{x['id']}**（{x['domain']}）{x['question']} → 采用 `{x['adopted']}`")

    out += ["", "## 术语", ""]
    for b, x in terms:
        out.append(f"- {x['term']}（{b}）")

    out += ["", "## 结构诊断", ""]
    if weak:
        out.append("覆盖偏弱的域：" + "、".join(f"{d}({n})" for d, n in weak))
    out.append(f"- 域总数：{len(DOMAIN_NAMES)}；有证据的域：{sum(1 for d in DOMAIN_NAMES if claims.get(d))}")
    out.append("- 说明：书一为能力级摘要（15 条），书二为规则级证据（86 条），两者颗粒度不同，计数仅供结构判断")

    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[:24]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
