"""Tabulate candidate coverage per stage-0 task id.

Stage 1.5 needs the coverage audit to be built from the task list in
BOOK_OVERVIEW.md, not from the candidate pool itself.  This tool reads the
merged candidate files, extracts each item's ``task_ids``, and prints a
per-task tally plus the ids that back it.

Usage:
    python task_coverage.py books/yuanhai-ziping/candidates --out .work/task-coverage.md
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

ITEM_RE = re.compile(r"^- id:\s*(\S+)\s*$", re.M)
TASK_RE = re.compile(r"^\s+task_ids:\s*\[(.*?)\]", re.M | re.S)
TYPE_RE = re.compile(r"^\s+type:\s*(\S+)\s*$", re.M)

TASK_LABELS = {
    "task-01": "排四柱（节气分界、子时判界）",
    "task-02": "起大运小运",
    "task-03": "十神定位与六亲映射",
    "task-04": "旺衰判断",
    "task-05": "取格（内外十八格等）",
    "task-06": "取用神与忌法",
    "task-07": "病药诊断",
    "task-08": "官杀混杂与制伏",
    "task-09": "伤官格处理",
    "task-10": "特殊日格（羊刃魁罡等）",
    "task-11": "墓库、杂气、刑合、时墓",
    "task-12": "神煞查法",
    "task-13": "大运、太岁、流年",
    "task-14": "六亲推断",
    "task-15": "女命断法",
    "task-16": "性情、疾病、寿元、小儿",
    "task-17": "综合断富贵贫贱",
    "task-18": "化气与神趣八法",
    "task-19": "命例排演",
    "task-20": "赋文与歌诀检索",
}


def read_items(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    marks = list(ITEM_RE.finditer(text))
    items = []
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        chunk = text[mark.start() : end]
        tasks = TASK_RE.search(chunk)
        ids = re.findall(r"task-\d\d", tasks.group(1)) if tasks else []
        type_m = TYPE_RE.search(chunk)
        items.append(
            {
                "id": mark.group(1),
                "tasks": sorted(set(ids)),
                "type": type_m.group(1) if type_m else "",
                "file": path.name,
            }
        )
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates_dir")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    cdir = Path(args.candidates_dir)
    by_task: dict[str, list[dict]] = defaultdict(list)
    total = 0
    untagged = []
    for path in sorted(p for p in cdir.glob("*.md")):
        for item in read_items(path):
            total += 1
            if not item["tasks"]:
                untagged.append(item)
                continue
            for t in item["tasks"]:
                by_task[t].append(item)

    rows = [
        "# 阶段 1.5 覆盖审计底表（按原书任务清单）",
        "",
        f"- 候选总数：{total}",
        f"- 未标 task_ids 的条目：{len(untagged)}",
        "",
        "| task | 任务 | 候选数 | 其中 principles | counter-examples | cases | frameworks | glossary |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for t in sorted(TASK_LABELS):
        items = by_task.get(t, [])
        kinds = defaultdict(int)
        for it in items:
            kinds[it["type"] or it["file"].replace(".md", "")] += 1
        rows.append(
            f"| {t} | {TASK_LABELS[t]} | {len(items)} | "
            f"{kinds.get('principle', 0) + kinds.get('calculation', 0)} | "
            f"{kinds.get('counter-example', 0)} | {kinds.get('case', 0)} | "
            f"{kinds.get('framework', 0) + kinds.get('procedure', 0) + kinds.get('troubleshooting', 0)} | "
            f"{kinds.get('term', 0)} |"
        )

    rows += ["", "## 各任务候选明细（id）", ""]
    for t in sorted(TASK_LABELS):
        items = by_task.get(t, [])
        ids = "、".join(sorted({it["id"] for it in items}))
        rows.append(f"- **{t}**（{len(items)} 条）：{ids or '（无）'}")

    if untagged:
        rows += ["", "## 未标 task_ids 的条目", ""]
        rows.append("、".join(f"{it['id']}（{it['file']}）" for it in untagged))

    text = "\n".join(rows) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"written {args.out}")
    print(text[:1200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
