import argparse
import datetime as dt
import os
from pathlib import Path

from openai import OpenAI


AI_PROMPT = """你是我的 AI 资讯研究员。请检索并整理过去 24 小时内最重要的 AI 相关资讯，重点关注：

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


TASKS = {
    "ai": {
        "filename": "{date}-AI-晨间简报.md",
        "prompt": AI_PROMPT,
    },
    "french": {
        "filename": "{date}-DALF-C1-法语学习.md",
        "prompt": FRENCH_PROMPT,
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
    parser.add_argument("--model", default=os.environ.get("OPENAI_DAILY_MODEL", "gpt-5.1"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    task = TASKS[args.task]
    target = Path(task["filename"].format(date=args.date))
    if target.exists() and target.stat().st_size > 1024 and not args.force:
        print(f"exists, skip: {target}")
        return

    client = OpenAI()
    content = generate(client, task["prompt"], args.date, args.model)
    target.write_text(content, encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
