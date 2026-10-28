"""Output evaluation: does the merged skill answer representative tasks correctly?

Feeds SKILL.md + the relevant capability card as context, asks three fixed
tasks, and saves raw answers for checking.

Usage:
    python output_eval.py [--out .work/stage4/output-eval]
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path

CONFIG = Path.home() / ".codex" / "config.toml"
BUILD = Path("build/bazi")

TASKS = [
    ("A-排盘", "sizhu-qiyun",
     "阳历1992年8月15日下午3点出生，男性。请排出四柱并说明起运，指出哪些信息你无法确定。"),
    ("B-病药", "bingyao-cengci",
     "四柱纯土，日主为水。按病药法判断：病在哪里、药是什么、层次如何？"),
    ("C-岁运", "dayun-liunian",
     "岁冲运和运冲岁，哪个凶？依据是什么？"),
]


def read_config():
    text = CONFIG.read_text(encoding="utf-8")
    return (re.search(r'base_url\s*=\s*"([^"]+)"', text).group(1).rstrip("/"),
            re.search(r'experimental_bearer_token\s*=\s*"([^"]+)"', text).group(1),
            re.search(r'^model\s*=\s*"([^"]+)"', text, re.M).group(1))


def ask(base, token, model, system, prompt):
    payload = {"model": model,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": prompt}],
               "temperature": 0, "max_tokens": 4000}
    for attempt in range(3):
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
            msg = data["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            return content or (msg.get("reasoning_content") or "").strip()
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".work/stage4/output-eval")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    base, token, model = read_config()
    skill = (BUILD / "SKILL.md").read_text(encoding="utf-8")

    results = []
    for name, card, prompt in TASKS:
        card_text = (BUILD / "references" / "capabilities" / f"{card}.md").read_text(encoding="utf-8")
        system = ("你是「八字规则体系」技能。严格按下列 SKILL.md 与能力卡作答；"
                  "引用原文时注明书与章节；体系效度须声明。\n\n" + skill + "\n\n" + card_text)
        answer = ask(base, token, model, system, prompt)
        (out / f"{name}.md").write_text(f"# {name}\n\n**任务**：{prompt}\n\n---\n\n{answer}\n", encoding="utf-8")
        results.append((name, answer))
        print(f"{name}: {len(answer)} chars")
    print("saved to", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
