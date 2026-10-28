# 八字规则体系（Bazi Rule System）

把《渊海子平》《子平真诠》《神峰通考》《命理约言》四部古籍的方法论，蒸馏成一个可调用、可追溯、可对照流派的 Agent Skill。

作者：**shadiaobot**

- **1 个入口**：`bazi`
- **15 个能力域**：排盘起运、十神、旺衰、取用、格局、病药、大运、官杀、伤官、阳刃、神煞、六亲、女命、性情疾病、从化
- **625 条规则 + 394 条失败模式 + 19 条跨书分歧**
- 每条判断都能回查到「哪本书、第几章」的原文

> **仅供娱乐与传统文化研究。** 本技能不承诺预测效度，不构成医疗、心理、法律、投资、婚姻或其他专业建议，也不应作为高风险或现实决策的依据。完整声明见 [`DISCLAIMER.md`](DISCLAIMER.md)。

## 目录

```
bazi-skill/
├── SKILL.md                     # 技能入口（frontmatter + 使用流程）
├── DISCLAIMER.md                # 使用边界与免责声明
├── references/
│   ├── capabilities/*.md        # 15 张能力卡（R/I/A1/A2/E/B 六段）
│   ├── capability-index.md      # 意图 → 能力卡索引
│   ├── cheatsheet.md            # 一句话规则速查
│   ├── glossary.md              # 术语表（含四书用法差异）
│   └── overview.md              # 四书构成与使用原则
├── evidence/                    # 可追溯证据（四本书各自一份）
│   ├── yuanhai-ziping/          # claims / boundaries / examples / brief / coverage
│   ├── ziping-zhenquan/         # claims / corroborations / terms / divergences
│   ├── shenfeng-tongkao/
│   └── mingli-yueyan/
├── tools/                       # 复现管线（抽取→切章→核验→合并→编译→盲测）
└── docs/                        # 评测记录与试编报告
```

## 安装

Codex：

```powershell
Copy-Item -Recurse . "$env:USERPROFILE\.codex\skills\bazi"
```

Claude Code：

```bash
cp -r . ~/.claude/skills/bazi
```

之后直接问：

- 「1992年8月15日下午三点，男，排个八字」
- 「我这八字用神取什么」
- 「这命层次高不高，有没有病药」
- 「今年流年怎么样」

## 它和普通命理回答的区别

1. **先定位能力域**，再按该域的执行步骤走，不自由发挥
2. **每条规则附原文出处**（书 + 章节）
3. **遇流派分歧并列**：例如「阴干有没有羊刃」四书说法不同，卡内写明采用哪一说、什么条件下换用另一说
4. **边界前置**：缺出生时间、节气不明、要求预测具体事件时，先停下说明

## 证据与可复现

- 每本书的 `claims.yaml` 记录规则原文（逐字、≤150 字）、位置、触发条件、判断逻辑与局限
- `boundaries.yaml` 记录失败模式，直接构成能力卡的 B 段
- `divergences.yaml` 记录跨书分歧：立场、引文、采用口径、切换条件
- 引文全部经 `tools/verify_quotes.py` 逐字回核（0 缺引）
- 域级盲测：36 题（30 正题 + 6 诱饵）→ **36/36**，见 `docs/domain-report.md`
- 输出实测：病药、岁运两题通过；排盘题结论正确。含出生输入的评测回放不纳入公开仓库，避免发布个人时间信息

复现大致流程：

```bash
python tools/extract_pdf.py <pdf> books/<slug>/source
python tools/build_chapters.py books/<slug>/source
python tools/split_sections.py books/<slug>/source
python tools/verify_quotes.py fusion/books/<slug>/claims.yaml --corpus books/<slug>/source/corpus
python tools/merge_bundle.py --out fusion/merged
python tools/cj-scripts/cangjie.py compile --bundle fusion/merged/capabilities --out build/bazi --output single --yes
```

## 版本与来源

| 书 | 作者 | 本版来源 |
|---|---|---|
| 渊海子平 | 宋·徐升编述，明·唐锦池合编 | luckclub.cn 古籍典藏 PDF |
| 子平真诠 | 清·沈孝瞻（徐乐吾注） | 同上 |
| 神峰通考 | 明·张楠 | 同上 |
| 命理约言 | 清·陈素庵 | 同上 |

**只收录了各书「原文（含眉批）」层**。该 PDF 版本的「白话译文」「关键词」「现代启示」为现代编者所加，属第三方内容，本仓库未收录、未引用。

## 授权

- **代码与工具**（`tools/`）：MIT，见 `LICENSE-CODE`
- **规则整理、能力卡、证据编排**（其余内容）：CC BY 4.0，见 `LICENSE-CONTENT`
- 四部古籍原文属公有领域

版权与整理成果署名为 **shadiaobot**。

## 已知局限

- 四书均未做统计效度检验，本技能只做「体系内推演」
- 女命、疾病、身份类断语带有明清社会语境，卡内已标 `epoch-limit`
- 命理约言的赋文与部分格章为抽样采集，未逐章通读（见各书 `coverage.md`）
- 排盘依赖精确节气时刻，需外部天文数据补齐
