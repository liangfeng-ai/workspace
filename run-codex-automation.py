import datetime as dt
import os
import pathlib
import re
import subprocess
import sys
import tomllib


AUTOMATION_SUFFIX = {
    "ai": "AI-晨间简报.md",
    "automation": "DALF-C1-法语学习.md",
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in AUTOMATION_SUFFIX:
        print("Usage: run-codex-automation.py <ai|automation>", file=sys.stderr)
        return 2

    automation_id = sys.argv[1]
    home = pathlib.Path.home()
    toml_path = home / ".codex" / "automations" / automation_id / "automation.toml"
    if not toml_path.exists():
        print(f"Automation config not found: {toml_path}", file=sys.stderr)
        return 1

    with toml_path.open("rb") as f:
        config = tomllib.load(f)

    status = config.get("status")
    if status != "ACTIVE":
        print(f"Automation {automation_id} is {status}; skipping.")
        return 0

    cwd_values = config.get("cwds") or [r"D:\每日必看"]
    workdir = pathlib.Path(cwd_values[0])
    workdir.mkdir(parents=True, exist_ok=True)

    today = dt.datetime.now().strftime("%Y-%m-%d")
    suffix = suffix_from_prompt(config.get("prompt", "")) or AUTOMATION_SUFFIX[automation_id]
    target = workdir / f"{today}-{suffix}"

    if target.exists() and target.stat().st_size > 1024:
        print(f"Target already exists; skipping: {target}")
        return 0

    prompt = build_prompt(config.get("prompt", ""), today, target)
    output_file = workdir / "logs" / f"{today}-{automation_id}-codex-last-message.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "codex",
        "exec",
        "--search",
        "--skip-git-repo-check",
        "--sandbox",
        "danger-full-access",
        "--ask-for-approval",
        "never",
        "-C",
        str(workdir),
        "-m",
        str(config.get("model") or "gpt-5.5"),
        "-o",
        str(output_file),
        prompt,
    ]

    print(f"Running Codex automation: {automation_id}")
    print(f"Workdir: {workdir}")
    print(f"Target: {target}")
    result = subprocess.run(cmd, cwd=workdir, text=True)

    if result.returncode != 0:
        print(f"Codex exited with code {result.returncode}", file=sys.stderr)
        return result.returncode

    if not target.exists() or target.stat().st_size <= 1024:
        print(f"Codex completed but target file is missing or too small: {target}", file=sys.stderr)
        return 1

    print(f"Created: {target}")
    return 0


def suffix_from_prompt(prompt: str) -> str | None:
    match = re.search(r"文件名格式为\s+YYYY-MM-DD-([^。\\n]+?\.md)", prompt)
    if not match:
        return None
    return match.group(1).strip()


def build_prompt(base_prompt: str, today: str, target: pathlib.Path) -> str:
    return f"""{base_prompt}

今天日期是 {today}。

这是由 Windows 计划任务触发的非交互自动化。请严格执行：
- 必须生成今天 {today} 的内容。
- 必须把最终 Markdown 保存到这个精确路径：{target}
- 如果需要检索实时材料，请使用可核验来源；不要编造链接、发布时间或数据。
- 保存文件后，最终回复只需要说明文件路径和完成状态。
- 不要询问用户确认；直接完成任务。
"""


if __name__ == "__main__":
    raise SystemExit(main())
