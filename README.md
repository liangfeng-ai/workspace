# 每日必看

这个目录现在统一保存三类每日自动化产物：

- `AI信息\YYYY-MM-DD-AI-晨间简报.md`
- `法语学习\YYYY-MM-DD-DALF-C1-法语学习.md`
- `英语学习\YYYY-MM-DD-IELTS-7.0-英语学习.md`

## AI 工具费曼学习雷达

`.github/workflows/ai-tool-radar.yml` 在工作日北京时间 `07:20` 运行
`scripts/collect_ai_tool_candidates.py`，从 GitHub Search、Hugging Face Hub
和官方组织仓库收集公开的 AI 工具候选。

- 每日候选：`data/ai-tool-radar/YYYY-MM-DD.json`
- 30 天去重状态：`data/ai-tool-radar/seen.json`
- 通用学习指令：`prompts/ai-tool-learning.md`
- 本地 Codex 学习卡：工作日 `08:20` 写入 Obsidian `峰峰/AI工具学习`

这个 workflow 不调用 OpenAI，也不需要新的 secret。公开仓库只保存公开候选和
通用提示词；费曼解释、完成情况、学习评分和私人文件只保存在本地 Obsidian。

## GitHub Actions 调度

仓库里的 `.github/workflows/daily.yml` 会在 GitHub 云端运行，不依赖本机开机。

- `08:05` 北京时间：生成 AI 晨间简报
- `09:05` 北京时间：生成法语学习
- `21:05` 北京时间：生成英语学习

需要在 GitHub 仓库的 `Settings -> Secrets and variables -> Actions` 配置：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`

## 本机备用调度

本机也保留了 Windows 任务计划程序作为备用链路。

稳定链路：

`Windows Task Scheduler -> py D:\CodexAutomations\run-codex-automation.py <automation_id> -> codex exec -> 写入 D:\每日必看\<分类目录>`

## 任务时间

- `Codex 每日 AI 晨间简报`：每天 `08:05`
- `Codex 每日法语学习`：每天 `09:05`
- `Codex 每日英语学习`：每天 `21:05`

## 目录说明

- [`D:\每日必看\AI信息`](/D:/每日必看/AI信息)
- [`D:\每日必看\法语学习`](/D:/每日必看/法语学习)
- [`D:\每日必看\英语学习`](/D:/每日必看/英语学习)
- [`D:\每日必看\logs`](/D:/每日必看/logs)
