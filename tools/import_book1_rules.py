"""Re-import book 1 (渊海子平) at rule level into the fusion format.

Maps every principle -> claim and every counter-example -> boundary, using the
task_ids each candidate already carries.

Usage:
    python import_book1_rules.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

TASK_DOMAIN = {
    "task-01": "D01", "task-02": "D01", "task-03": "D02", "task-04": "D03",
    "task-05": "D05", "task-06": "D04", "task-07": "D06", "task-08": "D08",
    "task-09": "D09", "task-10": "D10", "task-11": "D05", "task-12": "D11",
    "task-13": "D07", "task-14": "D12", "task-15": "D13", "task-16": "D14",
    "task-17": "D06", "task-18": "D15", "task-20": "D05",
}
# most specific first
PRIORITY = ["D13", "D14", "D15", "D12", "D11", "D10", "D09", "D08",
            "D07", "D06", "D05", "D04", "D03", "D02", "D01"]


def load_items(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    # merged files start with a markdown header and may end with markdown too;
    # parse item by item on "^- id:" and stop each chunk at trailing prose
    parts = re.split(r"(?m)^(?=- id:)", text)
    items = []
    for part in parts:
        if not part.startswith("- id:"):
            continue
        lines = []
        for i, line in enumerate(part.splitlines()):
            if i > 0 and (line.startswith("**") or line.startswith("# ") or line.strip() == "---"):
                break
            lines.append(line)
        try:
            data = yaml.safe_load("\n".join(lines))
        except yaml.YAMLError:
            continue
        if isinstance(data, list):
            items += [x for x in data if isinstance(x, dict) and x.get("id")]
    if items:
        return items
    out = []
    for block in re.findall(r"```ya?ml\s*\n(.*?)```", text, re.S):
        data = yaml.safe_load(block)
        if isinstance(data, list):
            out += [x for x in data if isinstance(x, dict) and x.get("id")]
    return out


def pick_domain(item: dict) -> str | None:
    domains = [TASK_DOMAIN[t] for t in item.get("task_ids") or [] if t in TASK_DOMAIN]
    if not domains:
        return None
    for d in PRIORITY:
        if d in domains:
            return d
    return None


def main() -> int:
    cand = Path("books/yuanhai-ziping/candidates")
    out_dir = Path("fusion/books/yuanhai-ziping")
    out_dir.mkdir(parents=True, exist_ok=True)

    principles = load_items(cand / "principles.md")
    counter = load_items(cand / "counter-examples.md")

    claims, boundaries = [], []
    skipped = 0
    for p in principles:
        if p.get("type") in {"case", "term"}:
            skipped += 1
            continue
        d = pick_domain(p)
        if not d:
            skipped += 1
            continue
        claims.append({
            "id": f"c-yhr-{len(claims)+1:04d}",
            "domain": d,
            "title": p.get("title", ""),
            "source_id": "src-yuanhai-ziping",
            "location": p.get("source_chapter", ""),
            "quote": p.get("source_quote", "").strip(),
            "rule": p.get("summary", "").strip().replace("\n", " "),
            "trigger": p.get("trigger", "见原文条件"),
            "logic": p.get("logic", p.get("summary", "")[:120]),
            "boundary": p.get("limits") or p.get("missing_conditions") or "见原文条件与能力卡 B 段",
            "limits": p.get("limits") or p.get("missing_conditions") or "原候选未单列局限，见原文条件",
            "novelty": "new",
            "relates": [],
            "tags": [t for t in (p.get("tags") or []) if isinstance(t, str)][:5],
            "source_ref": p["id"],
        })

    for c in counter:
        d = pick_domain(c)
        if not d:
            skipped += 1
            continue
        boundaries.append({
            "id": f"b-yhr-{len(boundaries)+1:04d}",
            "domain": d,
            "source_id": "src-yuanhai-ziping",
            "location": c.get("source_chapter", ""),
            "quote": c.get("source_quote", "").strip(),
            "failure_mode": c.get("failure_mode", ""),
            "mechanism": c.get("mechanism", ""),
            "bound_to": c.get("bound_to") or [],
            "tags": [t for t in (c.get("tags") or []) if isinstance(t, str)][:5],
            "source_ref": c["id"],
        })

    # keep the capability-level import as an index
    old = out_dir / "claims.yaml"
    if old.exists() and "能力卡导入" in old.read_text(encoding="utf-8")[:200]:
        (out_dir / "capability-index.yaml").write_text(old.read_text(encoding="utf-8"), encoding="utf-8")

    old.write_text(yaml.safe_dump(claims, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    (out_dir / "boundaries.yaml").write_text(
        yaml.safe_dump(boundaries, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8"
    )
    print(f"claims={len(claims)} boundaries={len(boundaries)} skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
