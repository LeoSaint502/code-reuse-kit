#!/usr/bin/env python3
"""
install_agent_config.py — 为所有主流 AI agent 安装代码存档规则。

自动检测已安装的 agent，配置为：
  任务结束时自动执行 git add + git commit → 触发 hook 自动提取入库。

支持的 agent：
  - Reasonix（全局 AGENTS.md，已存在单独流程，这里作为备用）
  - Claude Code（全局 ~/.claude/CLAUDE.md）
  - Cursor（每项目 .cursorrules）
  - GitHub Copilot（每项目 .github/copilot-instructions.md）
  - Windsurf（每项目 .windsurfrules）

用法：
  python install_agent_config.py --global              # 安装所有支持的全局配置
  python install_agent_config.py --project /path       # 在指定项目中安装所有配置
  python install_agent_config.py --detect              # 自动检测并安装
  python install_agent_config.py --list                # 列出检测到的 agent
"""

import argparse
import os
import shutil
import subprocess
import sys

# ── 路径 ────────────────────────────────────────────────────────────────

PROMPT_SRC = os.path.join(
    os.path.dirname(__file__), "..", "docs", "agent-instructions", "code-library-save-prompt.md"
)

# 每个 agent 的配置目标路径
AGENT_CONFIGS = {
    "claude-code-global": {
        "name": "Claude Code（全局）",
        "path": os.path.expanduser("~/.claude/CLAUDE.md"),
        "scope": "global",
        "priority": 1,
    },
    "cursor-project": {
        "name": "Cursor（每项目 .cursorrules）",
        "path": ".cursorrules",
        "scope": "project",
        "priority": 2,
    },
    "copilot-project": {
        "name": "GitHub Copilot（每项目 .github/copilot-instructions.md）",
        "path": ".github/copilot-instructions.md",
        "scope": "project",
        "priority": 2,
    },
    "windsurf-project": {
        "name": "Windsurf（每项目 .windsurfrules）",
        "path": ".windsurfrules",
        "scope": "project",
        "priority": 2,
    },
}


# ── 工具 ────────────────────────────────────────────────────────────────

def ok(msg: str):
    print(f"  ✓ {msg}")


def warn(msg: str):
    print(f"  ⚠ {msg}")


def fail(msg: str):
    print(f"  ✗ {msg}", file=sys.stderr)


def step(msg: str):
    print(f"\n  [{msg}]")


def read_prompt() -> str:
    """读取统一的 prompt 内容"""
    src = os.path.abspath(PROMPT_SRC)
    if not os.path.isfile(src):
        fail(f"prompt 文件未找到: {src}")
        sys.exit(1)
    with open(src, encoding="utf-8") as f:
        return f.read()


# ── Agent 检测 ──────────────────────────────────────────────────────────

def detect_agents() -> list[str]:
    """返回已检测到的 agent 标识列表"""
    detected = []

    # Claude Code: 检查 ~/.claude 目录或 claude CLI
    if shutil.which("claude"):
        detected.append("claude-code-global")
    elif shutil.which("claude.exe"):
        detected.append("claude-code-global")
    elif os.path.isdir(os.path.expanduser("~/.claude")):
        detected.append("claude-code-global")

    # Cursor: 检查 cursor CLI 或 AppData
    if shutil.which("cursor"):
        detected.append("cursor-project")
    elif os.name == "nt":
        cursor_paths = [
            os.path.expanduser("~/AppData/Local/Programs/cursor/Cursor.exe"),
            os.path.expanduser("~/AppData/Local/cursor/Cursor.exe"),
            os.path.expanduser("~\\AppData\\Local\\Programs\\cursor\\Cursor.exe"),
            os.path.expanduser("~\\AppData\\Local\\cursor\\Cursor.exe"),
        ]
        if any(os.path.isfile(p) for p in cursor_paths):
            detected.append("cursor-project")

    # GitHub Copilot: 检查 VS Code 扩展或 copilot CLI
    if shutil.which("github-copilot-cli"):
        detected.append("copilot-project")

    # Windsurf
    if shutil.which("windsurf"):
        detected.append("windsurf-project")

    return detected


def list_agents():
    """列出检测到的 agent"""
    detected = detect_agents()
    print("\n=== 检测到的 AI Agent ===")
    for key in AGENT_CONFIGS:
        cfg = AGENT_CONFIGS[key]
        mark = "✅" if key in detected else "  "
        print(f"  {mark} {cfg['name']}")

    not_detected = [k for k in AGENT_CONFIGS if k not in detected]
    if not_detected:
        print(f"\n  未检测到（可手动安装）:")
        for key in not_detected:
            cfg = AGENT_CONFIGS[key]
            print(f"     • {cfg['name']}")
    print()


# ── 安装 ────────────────────────────────────────────────────────────────

def install_config(key: str, prompt: str, project_root: str | None = None):
    """安装某个 agent 的配置文件"""
    cfg = AGENT_CONFIGS.get(key)
    if not cfg:
        fail(f"未知的 agent: {key}")
        return False

    if cfg["scope"] == "project":
        if not project_root:
            warn(f"{cfg['name']} 需要指定项目路径，跳过（使用 --project 指定）")
            return False
        dest = os.path.join(project_root, cfg["path"])
    else:
        dest = cfg["path"]

    dest_dir = os.path.dirname(dest)
    os.makedirs(dest_dir, exist_ok=True)

    # 检查是否已存在（避免重复追加）
    if os.path.isfile(dest):
        with open(dest, encoding="utf-8") as f:
            if "code-library-save-prompt" in f.read() or "Code Library" in f.read():
                ok(f"{cfg['name']} 已配置，跳过")
                return True
        # 追加到已有文件
        with open(dest, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n\n{prompt}")
    else:
        with open(dest, "w", encoding="utf-8") as f:
            f.write(prompt)

    ok(f"{cfg['name']} → {dest}")
    return True


def install_global(prompt: str):
    """安装所有支持的全局配置"""
    step("安装全局配置")
    count = 0

    # Claude Code 全局
    if install_config("claude-code-global", prompt):
        count += 1

    if count == 0:
        warn("无可安装的全局配置")


def install_project(project_root: str, prompt: str):
    """在指定项目中安装所有支持的配置"""
    step(f"安装项目配置 → {os.path.abspath(project_root)}")

    if not os.path.isdir(project_root):
        fail(f"路径不存在: {project_root}")
        return

    count = 0
    for key in [k for k, v in AGENT_CONFIGS.items() if v["scope"] == "project"]:
        if install_config(key, prompt, project_root):
            count += 1

    if count > 0:
        ok(f"已在项目中安装 {count} 个 agent 配置")


# ── 主流程 ──────────────────────────────────────────────────────────────

def print_banner():
    print("""
+------------------------------------------------------+
|  Code Library — 安装 AI Agent 自动存档规则           |
|  让任何 agent 在任务结束时自动保存代码               |
+------------------------------------------------------+
""")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="安装 agent 自动存档规则")
    parser.add_argument("--global", dest="do_global", action="store_true", help="安装全局配置")
    parser.add_argument("--project", type=str, help="在指定项目中安装配置")
    parser.add_argument("--detect", action="store_true", help="自动检测并安装")
    parser.add_argument("--list", action="store_true", help="列出检测到的 agent")
    args = parser.parse_args()

    if args.list:
        list_agents()
        return

    print_banner()
    prompt = read_prompt()

    # 检测到的 agent
    detected = detect_agents()

    if args.do_global:
        install_global(prompt)

    if args.project:
        install_project(args.project, prompt)

    if args.detect:
        if not detected:
            warn("未检测到已安装的 AI agent。你可以手动安装:")
            warn("  python install_agent_config.py --global  (安装 Claude Code 全局配置)")
            warn("  python install_agent_config.py --project /项目路径  (安装 Cursor/Copilot/Windsurf 配置)")
        else:
            # 自动分类安装
            global_keys = [k for k in detected if AGENT_CONFIGS[k]["scope"] == "global"]
            project_keys = [k for k in detected if AGENT_CONFIGS[k]["scope"] == "project"]

            if global_keys:
                install_global(prompt)

            if project_keys:
                print("\n  ⚠ 检测到以下 agent 需要每项目配置：")
                for key in project_keys:
                    print(f"     • {AGENT_CONFIGS[key]['name']}")
                print(f"\n  请在项目目录中运行：")
                print(f"    python install_agent_config.py --project <项目路径>")

                # 如果当前目录看起来像项目，直接安装
                cwd = os.getcwd()
                if os.path.isfile(os.path.join(cwd, "pyproject.toml")) or \
                   os.path.isfile(os.path.join(cwd, "package.json")) or \
                   os.path.isfile(os.path.join(cwd, "Cargo.toml")) or \
                   os.path.isdir(os.path.join(cwd, ".git")):
                    print(f"  → 当前目录看起来是项目根目录，正在安装...")
                    install_project(cwd, prompt)

    # 如果没有指定任何模式，默认检测并安装全局配置
    if not (args.do_global or args.project or args.detect or args.list):
        install_global(prompt)
        warn("已安装全局配置。如需安装每项目配置，运行：")
        warn(f"  python {sys.argv[0]} --project <项目路径>")

    # 验证 prompt 文件存在
    src = os.path.abspath(PROMPT_SRC)
    if os.path.isfile(src):
        ok(f"prompt 源文件: {src}")

    print(f"\n  {'='*50}")
    print(f"  完成！agent 下次启动后自动生效。")
    print(f"  {'='*50}")


if __name__ == "__main__":
    main()
