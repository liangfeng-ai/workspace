import argparse
import datetime as dt
import os
from pathlib import Path

from openai import OpenAI


AI_PROMPT = """你是我的 AI 资讯研究员。请检索并整理过去 24 小时内最重要的 AI 相关新闻，重点关注：

1. 大模型与 AI 产品更新
2. OpenAI、Anthropic、Google DeepMind、Meta、Microsoft、xAI、Mistral、阿里、腾讯、百度、字节等公司的重要动态
3. 新模型发布、能力升级、价格变化、API 更新
4. AI 编程工具、Agent、自动化工具的新进展
5. AI 投资、并购、监管、版权、安全相关事件
6. 重要论文、开源项目、技术突破
7. 对普通用户、开发者、创业者有实际影响的变化

只保留高价值信息，避免营销稿、重复新闻和低质量传闻。

输出格式：

# 今日 AI 简报：YYYY-MM-DD

## 一句话总结
用 1-3 句话概括今天最重要的 AI 趋势。

## 重点新闻
按重要性排序，列出 5-10 条。每条包含标题、简短摘要、为什么重要、来源链接。

## 值得关注的产品 / 工具
列出今天出现或更新的 AI 工具、模型、API、开源项目。说明它适合谁、能做什么、是否值得尝试。

## 技术与论文
如果有重要论文或技术突破，请用非专业人士也能理解的方式解释核心价值。

## 对我的启发
请从开发者、个人效率、创业机会三个角度，提炼 3-5 条可行动启发。

## 今日最值得深入阅读的 3 个链接
给出标题、链接和推荐理由。

要求：
- 优先使用一手来源，例如官方博客、GitHub、论文、公司公告、监管机构公告。
- 新闻要注明发布时间。
- 如果信息尚未确认，请明确标注“未确认”。
- 不要编造链接、数据或发布日期。
- 中文输出，表达简洁，信息密度高。
- 控制在 5 分钟内可以读完，优先告诉我今天最值得关注、最可能影响我使用 AI 和开发 AI 产品的事情。
"""


FRENCH_PROMPT = """你是我的法语 DALF C1 学习教练。我的当前水平是 DELF B2，目标是在阅读理解、词汇深度、表达准确性、论证能力和高级书面/口语表达上逐步达到 DALF C1。

请根据当天日期，为我生成一份法语学习任务。内容必须实时更新，优先使用最近的法语世界新闻、文化、社会、经济、科技或思想类材料。材料难度应高于 B2、接近 C1，但不能过难到无法学习。

每天输出以下结构：

1. 今日阅读材料
- 选择一篇真实、近期、法语原文材料。
- 给出标题、来源、日期和链接。
- 用中文说明为什么这篇材料适合 B2 到 C1 过渡。
- 提供一段 250-400 词左右的法语阅读节选或概述，不要过度简化。

2. 阅读理解
- 用法语提出 5 个理解问题。
- 其中 3 个是信息理解，2 个是观点、隐含逻辑或作者立场分析。
- 问题难度对标 DALF C1。

3. 高阶词汇
- 从材料中提取 12 个 C1 倾向词汇、搭配或固定表达。
- 每个词条包括：法语原词/表达、中文解释、法语释义、原文或近似语境例句、一个我可以主动仿写的句子模板。

4. 表达升级
- 给出 6 个可以替换 B2 普通表达的 C1 表达。
- 格式：B2 表达、C1 表达、使用场景、示例句。

5. 论证训练
- 根据今日材料提出一个 DALF C1 风格作文/口语论证题。
- 给出立场 A、立场 B、可用论点 3 个、可用反驳 2 个、一段 C1 水平示范开头，约 100-130 词，使用自然高级法语。

6. 主动输出任务
- 给我一个 12-15 分钟可完成的小任务。
- 要求我用法语写 120-180 词，或准备 2 分钟口头回答。
- 给出明确要求，例如必须使用今天的 5 个词汇和 2 个高级表达。

7. 复习
- 回顾最近一次学习中的词汇和表达。
- 如果没有历史记录，则创建一个“待复习清单”。
- 每天循环复现旧词，但不要机械重复，要换新语境。

输出语言要求：
- 讲解用中文。
- 法语材料、问题、示范句和表达训练用法语。
- 不要给泛泛建议，要给我当天可以直接学习的内容。
- 难度保持在 B2+ 到 C1 之间。
- 如果引用实时材料，必须注明来源和日期。
"""


ENGLISH_PROMPT = """你是我的每日雅思英语训练教练。我的当前水平是：大学英语六级擦边通过；目标是：雅思总分 7.0，重点提升听力、口语、阅读能力，写作只做辅助。请每天为我生成一份可执行的英语学习任务，难度从 IELTS 6.0-6.5 逐步推进到 7.0。

请严格按以下结构输出，中文解释为主，英文材料和练习保留英文：

# 今日 IELTS 7.0 训练

## 1. 今日输入材料
请优先选择真实、较新的英文材料，适合 IELTS 6.5-7.0 水平：
- 1 篇阅读材料：来自 BBC / The Guardian / NPR / The Economist / Scientific American / National Geographic / Reuters 等可靠来源，主题优先选择教育、科技、社会、健康、环境、经济、文化。
- 1 个听力材料：来自 BBC Learning English / TED / NPR / YouTube 英语访谈 / IELTS Listening 风格材料。
请给出标题、来源、发布日期或访问日期、链接，并说明为什么适合我今天练习。

## 2. 阅读训练：从“看懂”到“雅思阅读速度”
基于今日阅读材料，生成：
- 文章 150-250 词中文摘要
- 8 个核心词汇或短语：英文、中文、原文语境、可替换表达
- 5 道雅思阅读题型练习，至少覆盖 True/False/Not Given、Matching、Multiple Choice、Summary Completion 中的 2 种
- 答案与解析
- 1 个“长难句拆解”：解释句子结构、逻辑关系、可模仿表达

## 3. 听力训练：精听 + 抓主旨
基于今日听力材料，生成：
- 听前预测：根据标题预测 5 个可能出现的关键词
- 第一遍泛听任务：让我回答 3 个主旨问题
- 第二遍精听任务：选取 6-10 句关键表达做听写练习
- 易听错点提醒：连读、弱读、同音近音、数字、人名地名、转折信号
- 听后复述模板：用 80-120 词英文复述材料内容

## 4. 口语训练：从中式表达到 IELTS 7.0
围绕今日主题，生成：
- 3 个 IELTS Speaking Part 1 问题
- 1 个 Part 2 cue card
- 4 个 Part 3 深度追问
- 每题给出：普通答案思路、7 分答案结构、可直接套用的高分表达
- 给我一个 90 秒口语任务，并要求我录音或大声回答
- 最后给出自评标准：fluency、vocabulary、grammar、pronunciation、idea development

## 5. 今日输出任务
请安排一个 20-30 分钟内能完成的输出任务：
- 口语：围绕今日主题说 90 秒
- 阅读：整理 5 个生词并各造 1 句
- 听力：听写 6 句关键句
请给出明确的完成格式，方便我把答案发回来让你批改。

## 6. 复习机制
请每天复现前 3 天学过的内容：
- 随机抽查 5 个旧词汇
- 复用 2 个旧表达造新句
- 提醒我昨天最容易遗忘或最该重复的训练点

## 7. 难度调节
如果我连续 3 天完成度较高，请提升材料难度和口语追问深度。
如果我完成困难，请降低材料长度，但保留雅思 7.0 的表达目标。

不要给我泛泛建议，必须每天给出具体材料、具体题目、具体答案、具体输出任务。
"""


TASKS = {
    "ai": {
        "filename": "{date}-AI-晨间简报.md",
        "prompt": AI_PROMPT,
    },
    "french": {
        "filename": "{date}-DALF-C1-法语学习.md",
        "prompt": FRENCH_PROMPT,
    },
    "english": {
        "filename": "英语学习/{date}-IELTS-7.0-英语学习.md",
        "prompt": ENGLISH_PROMPT,
    },
}


def shanghai_today() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d")


def generate(client: OpenAI, prompt: str, date: str, model: str) -> str:
    response = client.responses.create(
        model=model,
        input=(
            f"今天日期是 {date}。\n"
            "请生成当天内容。必须只输出最终 Markdown 正文，不要包裹代码块，不要解释执行过程。\n\n"
            f"{prompt}"
        ),
        tools=[{"type": "web_search"}],
    )
    return response.output_text.strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=TASKS.keys(), required=True)
    parser.add_argument("--date", default=shanghai_today())
    parser.add_argument("--model", default=os.environ.get("OPENAI_DAILY_MODEL", "gpt-5.5"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    task = TASKS[args.task]
    target = Path(task["filename"].format(date=args.date))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 1024 and not args.force:
        print(f"exists, skip: {target}")
        return

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    content = generate(client, task["prompt"], args.date, args.model)
    target.write_text(content, encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
