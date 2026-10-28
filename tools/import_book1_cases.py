"""Import book 1 case candidates into fusion examples."""

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
    "task-17": "D06", "task-18": "D15", "task-19": "D05", "task-20": "D05",
}
PRIORITY = ["D13", "D14", "D15", "D12", "D11", "D10", "D09", "D08",
            "D07", "D06", "D05", "D04", "D03", "D02", "D01"]


def load_items(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"(?m)^(?=- id:)", text)
    out = []
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
            out += [x for x in data if isinstance(x, dict) and x.get("id")]
    return out


def pick(item: dict) -> str | None:
    ds = [TASK_DOMAIN[t] for t in item.get("task_ids") or [] if t in TASK_DOMAIN]
    for d in PRIORITY:
        if d in ds:
            return d
    return None


def main() -> int:
    src = Path("books/yuanhai-ziping/candidates/cases.md")
    if not src.exists():
        print("no cases.md")
        return 1
    rows = []
    for c in load_items(src):
        d = pick(c)
        if not d:
            continue
        q = (c.get("source_quote") or "").strip()
        q = re.sub(r"\s+", "", q)
        if len(q) > 150:
            q = q[:148] + "……"
        rows.append({
            "id": f"e-yh-{len(rows)+1:03d}",
            "domain": d,
            "source_id": "src-yuanhai-ziping",
            "location": c.get("source_chapter", ""),
            "title": c.get("title", ""),
            "quote": q,
            "outcome": c.get("outcome", ""),
            "kind": c.get("example_kind", "worked_example"),
        })
    out = Path("fusion/books/yuanhai-ziping/examples.yaml")
    out.write_text(yaml.safe_dump(rows, allow_unicode=True, sort_keys=False, width=120), encoding="utf-8")
    print(f"examples={len(rows)} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
