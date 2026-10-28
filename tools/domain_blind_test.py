"""Domain-level blind test for the merged bazi skill.

Asks a fresh API context to route 36 prompts to one of 15 capability domains
(or none), then scores exact matches.

Usage:
    python domain_blind_test.py [--out .work/stage4/domain-report.md]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

CONFIG = Path.home() / ".codex" / "config.toml"

DOMAINS = {
    "D01": ("排盘与起运", "排四柱、节气分界、起大运与小运"),
    "D02": ("十神与关系", "十神定位、干支作用、合冲刑害本身（不含合化成格）"),
    "D03": ("旺衰与月令", "日主旺衰、月令司令、得令得势"),
    "D04": ("取用与忌法", "取用神、喜忌配对、忌法"),
    "D05": ("格局判定", "取格、成格破格、兼格"),
    "D06": ("病药与层次", "病药诊断、贵贱贫富层次"),
    "D07": ("大运与流年", "大运、交运、太岁流年"),
    "D08": ("官杀混杂", "正官七杀、混杂、制伏与化杀"),
    "D09": ("伤官格", "伤官见官、伤尽、伤官生财"),
    "D10": ("阳刃与特殊日格", "羊刃、日刃、日贵、魁罡、金神"),
    "D11": ("神煞查法", "贵人、驿马、空亡、纳音等"),
    "D12": ("六亲（含小儿）", "父母兄弟妻子女、小儿"),
    "D13": ("女命", "女命夫星子星、贵贱"),
    "D14": ("性情与疾病", "性情、疾病、寿元"),
    "D15": ("从格与化气", "从格、天干合而化神成格（甲己化土等）、神趣八法"),
}

CASES = [
    ("D01", "1992年8月15日下午三点出生，帮我排个八字"),
    ("D01", "我几岁起运？第一步大运是什么"),
    ("D02", "庚金对我这个甲木日主来说算七杀还是正官？"),
    ("D02", "帮我把这个八字的十神标一下"),
    ("D03", "甲木生在亥月算身旺吗？"),
    ("D03", "我这个八字到底是身强还是身弱？"),
    ("D04", "我这八字用神该取什么？"),
    ("D04", "如果财星是我的用神，最怕什么？"),
    ("D05", "丙日午月、地支巳午未全，这是什么格？"),
    ("D05", "这个八字到底成格了没有？"),
    ("D06", "这命层次高不高？有没有病、有没有药？"),
    ("D06", "为什么有的人八字看起来平平，却能发大财？"),
    ("D07", "今年流年对我怎么样？"),
    ("D07", "换大运那几年要注意什么？"),
    ("D08", "官杀混杂怎么办？"),
    ("D08", "七杀太旺是不是一定要制？"),
    ("D09", "伤官见官真的必凶吗？"),
    ("D09", "我这个伤官格能不能用财？"),
    ("D10", "月令阳刃要用什么来制？"),
    ("D10", "魁罡日出生有什么讲究？"),
    ("D11", "我的天乙贵人在哪个字上？"),
    ("D11", "命里空亡影响大吗？"),
    ("D12", "从八字能看父母兄弟的情况吗？"),
    ("D12", "子女缘怎么样？"),
    ("D13", "女命官杀多代表什么？"),
    ("D13", "女命伤官旺该怎么断？"),
    ("D14", "能从这个八字看出我的性格吗？"),
    ("D14", "八字能看出我容易得什么病吗？"),
    ("D15", "日主无根、满局是财，算从财格吗？"),
    ("D15", "甲己合化土需要什么条件？"),
    ("none", "帮我写一段 Python 爬虫"),
    ("none", "今天北京天气怎么样？"),
    ("none", "推荐几本八字入门的书"),
    ("none", "帮我把这段英文翻译成中文"),
    ("none", "帮我订一张明天去上海的机票"),
    ("none", "紫微斗数怎么排盘？"),
]


def read_config():
    text = CONFIG.read_text(encoding="utf-8")
    base = re.search(r'base_url\s*=\s*"([^"]+)"', text).group(1).rstrip("/")
    token = re.search(r'experimental_bearer_token\s*=\s*"([^"]+)"', text).group(1)
    model = re.search(r'^model\s*=\s*"([^"]+)"', text, re.M).group(1)
    return base, token, model


def ask(base, token, model, system, prompt):
    payload = {"model": model,
               "messages": [{"role": "system", "content": system},
                            {"role": "user", "content": prompt}],
               "temperature": 0, "max_tokens": 400}
    for attempt in range(3):
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data = json.loads(r.read().decode("utf-8"))
            msg = data["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            # prefer the final answer; reasoning often enumerates every domain
            return content or (msg.get("reasoning_content") or "")
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)
    return ""


def parse(text: str) -> str:
    hits = [(text.rfind(d), d) for d in DOMAINS if d in text]
    if hits:
        return max(hits)[1]
    return "none" if re.search(r"\bnone\b|不适用", text.lower()) else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=".work/stage4/domain-report.md")
    args = ap.parse_args()

    base, token, model = read_config()
    system = ("你是八字能力域路由器。给定用户问题，判断它属于下列哪个能力域，"
              "只输出域名（D01–D15）或 none，不要解释。\n\n"
              + "\n".join(f"{k} {v[0]}：{v[1]}" for k, v in DOMAINS.items()))

    rows, ok = [], 0
    for i, (exp, prompt) in enumerate(CASES, 1):
        got = parse(ask(base, token, model, system, prompt)) or "unparsed"
        good = got == exp
        ok += good
        rows.append((exp, got, prompt, good))
        print(f"{i}/{len(CASES)} exp={exp} got={got} {'OK' if good else 'X'} {prompt[:20]}")

    by_dom = defaultdict(lambda: [0, 0])
    for exp, got, _, good in rows:
        by_dom[exp][0] += good
        by_dom[exp][1] += 1

    lines = ["# 域级盲测（四书合并版 bazi）", "",
             f"- 题目：{len(rows)}（30 正题 + 6 诱饵）",
             f"- 命中：{ok}/{len(rows)} = {ok/len(rows):.1%}", "",
             "| 期望域 | 命中 |", "|---|---|"]
    for d in sorted(by_dom):
        a, n = by_dom[d]
        lines.append(f"| {d} | {a}/{n} |")
    lines += ["", "| # | 期望 | 实际 | 题目 |", "|---|---|---|---|"]
    for i, (exp, got, prompt, good) in enumerate(rows, 1):
        lines.append(f"| {i} | {exp} | {got} | {prompt} |")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"accuracy={ok}/{len(rows)} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
