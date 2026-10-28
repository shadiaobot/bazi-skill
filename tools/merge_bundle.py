"""Build a two-book merged Capability Bundle (structural trial v0.1).

Reads fusion/books/<book>/{claims,boundaries,divergences}.yaml, groups by the
15 domains, and writes a cangjie-compatible bundle under
fusion/merged/. Cards are generated scaffolds: real evidence, template prose.

Usage:
    python merge_bundle.py --out fusion/merged
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

import yaml

DOMAINS = {
    "D01": ("sizhu-qiyun", "排盘与起运", "critical",
            ["按节气定年月柱，按日干定时柱", "排四柱后起大运，三日折一岁", "标注节气判界与夜子时"]),
    "D02": ("shishen-dingwei", "十神与关系", "high",
            ["以日干为我，按五行生克与阴阳同异定十神", "区分透干与藏支的效力", "判合冲刑害本身（合化是否成格转 D15）"]),
    "D03": ("wangshuai-yueling", "旺衰与月令", "high",
            ["查日干在四支的十二长生", "判月令司令之字", "得时为旺、党众为强，两维合判"]),
    "D04": ("yongshen-jifa", "取用与忌法", "critical",
            ["从月令取用（或以病处定药）", "按顺逆两用定喜忌", "逐条核对用之某神不可某"]),
    "D05": ("geju-panding", "格局判定", "critical",
            ["以月令取格", "列成格条件与破格条件", "找救应之神，判成中有败/败中有成"]),
    "D06": ("bingyao-cengci", "病药与层次", "high",
            ["找克害用神之字为病", "找能去病之字为药", "按病药配比定层次"]),
    "D07": ("dayun-liunian", "大运与流年", "critical",
            ["定大运干支与交运关口", "大运重地支、流年看天干", "判岁运生克与合冲"]),
    "D08": ("guansha-hunza", "官杀混杂", "high",
            ["判官杀是否混杂", "选制伏或合去之法", "核制伏是否太过"]),
    "D09": ("shangguan-ge", "伤官格", "high",
            ["判官星是否伤尽", "查财星能否通关", "按柱位与气候分流"]),
    "D10": ("yangren-rige", "阳刃与特殊日格", "high",
            ["查羊刃/日刃", "判官煞制刃是否得力", "核特殊日格成破"]),
    "D11": ("shensha-chabiao", "神煞查法", "medium",
            ["按年干/日干/年支/日支查神煞", "核神煞是否落空亡", "只作断语加成，不推翻格局"]),
    "D12": ("liuqin-tuanduan", "六亲（含小儿）", "medium",
            ["十神映射六亲", "按柱位定是谁", "查受克与岁运应期"]),
    "D13": ("nvming-duanfa", "女命", "medium",
            ["以官为夫、食伤为子女", "数官杀位与合局", "标注时代局限"]),
    "D14": ("xingqing-jibing", "性情与疾病", "medium",
            ["五行配五常论性情", "取受伤最重之脏", "标注不能替代医学判断"]),
    "D15": ("conghua-baxiang", "从格与化气", "high",
            ["验日主无根、旺神成局", "判天干合而化神是否成格（得月令、无争合妒合）", "标注破格条件"]),
}

BOOK_SHORT = {
    "yuanhai-ziping": "渊海",
    "ziping-zhenquan": "真诠",
    "shenfeng-tongkao": "神峰",
    "mingli-yueyan": "约言",
}

HINTS = {
    "D01": ["排盘", "起运", "小运", "四柱"],
    "D02": ["十神", "干支", "合", "冲", "覆载", "动静"],
    "D03": ["旺衰", "月令", "长生", "强弱", "休囚"],
    "D04": ["用神", "喜忌", "忌法", "扶抑"],
    "D05": ["格", "成格", "破格", "格局"],
    "D06": ["病", "药", "层次", "贵贱"],
    "D07": ["大运", "流年", "岁运", "太岁", "行运"],
    "D08": ["官", "杀", "煞"],
    "D09": ["伤官"],
    "D10": ["羊刃", "阳刃", "日贵", "魁罡", "金神"],
    "D11": ["神煞", "贵人", "空亡", "纳音", "驿马"],
    "D12": ["六亲", "妻", "子息", "父母"],
    "D13": ["女命"],
    "D14": ["性情", "疾病", "寿元"],
    "D15": ["从", "化", "象"],
}


def domain_questions(path: Path) -> dict[str, list[str]]:
    """Pull the 必问 questions per domain from fusion/domain-prompts.md."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    parts = re.split(r"(?m)^## (D\d\d)", text)
    for i in range(1, len(parts), 2):
        dom, body = parts[i], parts[i + 1]
        qs = [q.strip() for q in re.findall(r"^\s*\d+\.\s*(.+)$", body, re.M)]
        out[dom] = qs[:3]
    return out


def load(path: Path):
    if not path.exists():
        return []
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", default="fusion/books")
    ap.add_argument("--out", default="fusion/merged")
    args = ap.parse_args()

    books = [p for p in sorted(Path(args.books).iterdir()) if p.is_dir() and not p.name.startswith("_")]
    claims = defaultdict(list)
    bounds = defaultdict(list)
    examples = defaultdict(list)
    divs = []
    for b in books:
        for x in load(b / "claims.yaml"):
            claims[x["domain"]].append((b.name, x))
        for x in load(b / "boundaries.yaml"):
            bounds[x["domain"]].append((b.name, x))
        for x in load(b / "examples.yaml"):
            examples[x["domain"]].append((b.name, x))
        divs += load(b / "divergences.yaml")

    out = Path(args.out)
    cards_dir = out / "capabilities" / "cards"
    book_dir = out / "capabilities" / "book"
    cards_dir.mkdir(parents=True, exist_ok=True)
    book_dir.mkdir(parents=True, exist_ok=True)
    questions = domain_questions(Path("fusion/domain-prompts.md"))

    caps = []
    for d, (slug, title, importance, steps) in DOMAINS.items():
        rows = claims.get(d, [])
        bds = bounds.get(d, [])
        dvs = [x for x in divs if x["domain"] == d]
        if not rows:
            continue
        # one representative quote per book keeps R 段 cross-book honest
        hints = HINTS.get(d, [])
        by_book = {}
        for b, x in rows:
            if not x.get("quote") or b in by_book:
                continue
            if any(h in x.get("title", "") for h in hints):
                by_book[b] = x["quote"]
        for b, x in rows:
            if x.get("quote") and b not in by_book:
                by_book[b] = x["quote"]
        quotes = list(by_book.values())[:3]
        # group rules by book for the interpretation section
        grouped = defaultdict(list)
        for b, x in rows:
            grouped[b].append(x)
        # pick a worked example if any claim looks like one
        example = None
        if examples.get(d):
            example = examples[d][0]
        for b, x in rows:
            if any(k in x["title"] for k in ("例", "命造", "造", "验")):
                example = (b, x)
                break
        btext = [x["failure_mode"] for _, x in bds[:5]]

        card = [f"# {title}", "", "## R — 原文", ""]
        for q in quotes:
            card += [f"> 「{q.strip().strip(chr(34) + '“”')}」", ""]
        card += ["## I — 解读", "",
                 f"本域汇总四书 {len(rows)} 条规则、{len(bds)} 条失败模式。各书要点：", ""]
        for b in sorted(grouped):
            ts = [x["title"] for x in grouped[b][:6]]
            card.append(f"- **{BOOK_SHORT.get(b, b)}**：" + "；".join(ts))
        if dvs:
            card += ["", f"**流派分歧（{len(dvs)} 条）**："]
            for dv in dvs:
                card.append(f"- {dv['question']} → 采用 `{BOOK_SHORT.get(dv['adopted'], dv['adopted'])}`；"
                            f"备用：{dv.get('fallback_when', '')}")
        card += ["", "## A1 — 示例", ""]
        if example:
            b, ex = example
            card += [f"原书命例（{BOOK_SHORT.get(b, b)}·{ex.get('location', '')}）：{ex['title']}", "",
                     f"> 「{ex['quote'].strip().strip(chr(34) + '“”')}」", ""]
            if ex.get("outcome"):
                card.append(f"原书结论：{ex['outcome']}")
            card.append("按 E 段步骤复算该例，可逐条对照原文。")
        else:
            card += ["原书未提供本域独立命例；以下为合成演练（非原书命例，不构成事实判断）。",
                     "取一个给定的四柱，按 E 段逐步核验，每步注明依据来源；缺输入时先停下索要。"]
        qs = questions.get(d, [])
        card += ["", "## A2 — 何时触发", ""]
        card.append(f"用户询问「{title}」相关问题、且给出或讨论八字命局时使用。典型问法：")
        card += [f"- {q}" for q in qs] or [f"- {title}怎么判断"]
        card += ["- 单一其他主题时转对应域；要求预测具体人事结果时不承诺效度。", ""]
        card += ["## E — 执行步骤", ""]
        card += [f"{i}. {s}" for i, s in enumerate(steps, 1)]
        card += ["", "## B — 边界", ""]
        if btext:
            card += [f"- 失败模式：{t}" for t in btext]
        for dv in dvs:
            card += [f"- 流派分歧：{dv['question']}（采用 `{BOOK_SHORT.get(dv['adopted'], dv['adopted'])}`；{dv['fallback_when']}）"]
        card += ["- 命理体系未经统计检验，输出为体系内推演，不是事实预测。"]
        (cards_dir / f"{slug}.md").write_text("\n".join(card) + "\n", encoding="utf-8")

        caps.append({
            "capability_id": f"cap.bazi.{slug}",
            "revision": 1,
            "status": "active",
            "slug": slug,
            "title": title,
            "importance": importance,
            "importance_rationale": f"三书合并后本域证据 {len(rows)} 条规则 + {len(bds)} 条边界。",
            "one_liner": steps[0],
            "intents": [f"询问{title}", f"{title}的判断与依据"],
            "keywords": [title, slug],
            "also_read": [],
            "card": f"cards/{slug}.md",
            "frontmatter": {
                "description": f"用户询问{title}相关问题时使用；单一其他主题请转对应域；不承诺预测效度。",
                "tags": ["bazi", d],
            },
            "source_evidence": [
                {"source_id": "src-yuanhai-ziping", "location": "见各条 claim 的 location"},
                {"source_id": "src-ziping-zhenquan", "location": "见各条 claim 的 location"},
            ],
            "promotion": {"destination": "router"},
            "resources": [],
        })

    bundle = {
        "schema_version": 1,
        "bundle_id": "bundle.bazi-merged",
        "book": {
            "title": "八字规则体系（渊海子平 · 子平真诠 合编）",
            "author": "四书合编（当前两本）",
            "source_pack": "src-bazi-merged",
            "baseline_tag": "trial-2026-10-27",
        },
        "entry": {
            "name": "bazi",
            "description": "以《渊海子平》《子平真诠》等古籍规则分析四柱八字：排盘起运、十神、旺衰、取用、格局、病药、大运、六亲等 15 个域；流派分歧并列并标注采用口径；不承诺预测效度。",
            "core_principles": [
                "以日干为我，年月时为根苗果。",
                "用神自月令取；《子平真诠》另立相神与成败救应。",
                "吉凶不取决于神名，而取决于是否合于需要。",
                "大运重地支、流年看天干；成格变格比单纯吉凶更重。",
            ],
            "out_of_scope": ["要求预测效度的请求", "非子平体系的术数", "编者按与白话译文不作为原文依据"],
            "stop_conditions": ["缺出生时间时先索要", "两书冲突未决时并列并标注采用口径"],
        },
        "router_entry": {
            "name": "bazi",
            "description": "八字规则体系总入口：15 个能力域，覆盖排盘、十神、旺衰、取用、格局、病药、大运、官杀、伤官、阳刃、神煞、六亲、女命、性情疾病、从化；两书冲突处并列并标注默认口径。",
        },
        "promotion_budget": 8,
        "capabilities": caps,
    }
    (out / "capabilities" / "verified.yaml").write_text(
        yaml.safe_dump(bundle, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8"
    )
    ov = ["# 八字规则体系（四书合编）", "",
          "## 构成", "",
          "| 书 | 规则 | 定位 |", "|---|---|---|",
          "| 渊海子平 | 474 | 规则库底座 |",
          "| 子平真诠 | 86 | 用神—相神与成败救应 |",
          "| 神峰通考 | 38 | 病药源头与辟谬 |",
          "| 命理约言 | 27 | 教科书式标准化 |", "",
          f"合计 {sum(len(v) for v in claims.values())} 条规则、"
          f"{sum(len(v) for v in bounds.values())} 条边界、{len(divs)} 条跨书分歧。", "",
          "## 使用原则", "",
          "1. 书是证据，技能是能力域；本 skill 按 15 个域组织，不按书分章。",
          "2. 分歧处并列，并标注默认口径与切换条件。",
          "3. 体系效度未经统计检验，输出为体系内推演。"]
    (book_dir / "overview.md").write_text("\n".join(ov) + "\n", encoding="utf-8")
    # glossary: book 1's curated list + every book's term-difference records
    base = Path("books/yuanhai-ziping/GLOSSARY.md")
    parts = []
    if base.exists():
        parts.append(base.read_text(encoding="utf-8").strip())
    term_rows = []
    for b in books:
        for t in load(b / "terms.yaml"):
            term_rows.append(
                f"### {t['term']}（{BOOK_SHORT.get(b.name, b.name)}）\n\n"
                f"- 本书定义：{t.get('author_definition', '').strip()}\n"
                f"- 与通行用法：{t.get('usage_note', '')}\n"
                f"- 差异书目：{', '.join(t.get('differs_from', [])) or '—'}\n"
            )
    if term_rows:
        parts.append("## 四书术语差异\n\n" + "\n".join(term_rows))
    (book_dir / "glossary.md").write_text("\n\n---\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"capabilities={len(caps)} claims={sum(len(v) for v in claims.values())} "
          f"boundaries={sum(len(v) for v in bounds.values())} divergences={len(divs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
