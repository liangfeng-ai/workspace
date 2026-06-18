# 每日必看

这个目录现在统一保存三类每日自动化产物：

- `AI信息\YYYY-MM-DD-AI-晨间简报.md`
- `法语学习\YYYY-MM-DD-DALF-C1-法语学习.md`
- `英语学习\YYYY-MM-DD-IELTS-7.0-英语学习.md`

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
