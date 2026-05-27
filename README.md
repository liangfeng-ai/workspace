# 每日必看

这个仓库保存两个每日自动化产物：

- `YYYY-MM-DD-AI-晨间简报.md`
- `YYYY-MM-DD-DALF-C1-法语学习.md`

## GitHub Actions 设置

1. 把本目录推到 GitHub 仓库。
2. 在仓库的 `Settings -> Secrets and variables -> Actions -> New repository secret` 添加：
   - `OPENAI_API_KEY`
3. 可选：在 `Variables` 添加 `OPENAI_DAILY_MODEL`，默认是 `gpt-5.1`。
4. workflow 会按 UTC 运行：
   - `00:05 UTC`，对应北京时间 `08:05`，生成 AI 晨间简报。
   - `01:05 UTC`，对应北京时间 `09:05`，生成法语学习任务。

也可以在 GitHub Actions 页面手动运行 `Daily Automations`。
