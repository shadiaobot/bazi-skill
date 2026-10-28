---
name: bazi
description: |
  以《渊海子平》《子平真诠》等古籍规则分析四柱八字：排盘起运、十神、旺衰、取用、格局、病药、大运、六亲等 15 个域；流派分歧并列并标注采用口径；仅供传统文化研究与娱乐，不构成现实决策依据。
license: MIT (code) / CC BY 4.0 (content)
metadata:
  author: shadiaobot
  cangjie.generated-by: cangjie-tools v2.5.0
  cangjie.variant: single
  cangjie.bundle-id: bundle.bazi-merged
  cangjie.capability-count: 15
  cangjie.entrypoint-count: 1
---
# 八字规则体系（四书合编） — 全书能力入口

> **使用声明**：本技能仅供传统文化研究、娱乐与自我反思，不构成医疗、心理、法律、投资、婚姻或其他专业建议；不承诺预测效度，不应作为现实决策依据。

## 触发与不触发

**适用**：与本书能力域相关的咨询与任务（见下方路由表的意图列）。
**不适用**：
- 要求预测效度的请求
- 非子平体系的术数
- 编者按与白话译文不作为原文依据
- 替代医疗、心理、法律、投资、婚姻等专业意见

## 核心原则（常驻速览，概览类问题读到这里即可回答）

1. 以日干为我，年月时为根苗果。
2. 用神自月令取；《子平真诠》另立相神与成败救应。
3. 吉凶不取决于神名，而取决于是否合于需要。
4. 大运重地支、流年看天干；成格变格比单纯吉凶更重。

## 能力路由（先读本表，按意图加载 1 张能力卡）

| 用户意图 | 先读 | 补读/备注 |
|---|---|---|
| 询问排盘与起运；排盘与起运的判断与依据 | references/capabilities/sizhu-qiyun.md | — |
| 询问十神与关系；十神与关系的判断与依据 | references/capabilities/shishen-dingwei.md | — |
| 询问旺衰与月令；旺衰与月令的判断与依据 | references/capabilities/wangshuai-yueling.md | — |
| 询问取用与忌法；取用与忌法的判断与依据 | references/capabilities/yongshen-jifa.md | — |
| 询问格局判定；格局判定的判断与依据 | references/capabilities/geju-panding.md | — |
| 询问病药与层次；病药与层次的判断与依据 | references/capabilities/bingyao-cengci.md | — |
| 询问大运与流年；大运与流年的判断与依据 | references/capabilities/dayun-liunian.md | — |
| 询问官杀混杂；官杀混杂的判断与依据 | references/capabilities/guansha-hunza.md | — |
| 询问伤官格；伤官格的判断与依据 | references/capabilities/shangguan-ge.md | — |
| 询问阳刃与特殊日格；阳刃与特殊日格的判断与依据 | references/capabilities/yangren-rige.md | — |
| 询问神煞查法；神煞查法的判断与依据 | references/capabilities/shensha-chabiao.md | — |
| 询问六亲（含小儿）；六亲（含小儿）的判断与依据 | references/capabilities/liuqin-tuanduan.md | — |
| 询问女命；女命的判断与依据 | references/capabilities/nvming-duanfa.md | — |
| 询问性情与疾病；性情与疾病的判断与依据 | references/capabilities/xingqing-jibing.md | — |
| 询问从格与化气；从格与化气的判断与依据 | references/capabilities/conghua-baxiang.md | — |

**非能力类查询**：
- 书名/作者/章节/整书概览 → references/overview.md
- 术语解释 → references/glossary.md
- 决策规则速查（不需要原文依据时） → references/cheatsheet.md
- 完整意图与关键词索引（本表未覆盖的意图先查这里） → references/capability-index.md

## 加载规则

- 每次任务先读本文件，再按路由表加载 **1** 张能力卡；任务明确跨域时最多加载 2 张。
- 概览/书名类问题不加载能力卡，用「核心原则」与 overview.md 回答。
- 路由表与 capability-index.md 都无法命中的意图，明确告知超出本书范围，不要硬套。

## 边界与判停

- 缺出生时间时先索要
- 四书冲突未决时并列并标注采用口径
- 将体系内推演用于现实决策时，必须明确说明仅供娱乐与参考
