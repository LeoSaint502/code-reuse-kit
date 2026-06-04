#!/usr/bin/env python3
"""
install_code_library.py — One-click setup of the code-reuse-kit ecosystem.

Usage:
    git clone https://github.com/LeoSaint502/code-reuse-kit.git
    cd code-reuse-kit
    python scripts/install_code_library.py
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys

# ── 安装流程中会调用的辅助脚本 ──
HOOKS_INSTALLER = os.path.join(os.path.dirname(__file__), "install_hooks.py")
AGENT_CONFIG_INSTALLER = os.path.join(os.path.dirname(__file__), "install_agent_config.py")

GITHUB_REPO = "https://github.com/LeoSaint502/code-reuse-kit.git"
DEST = os.path.expanduser("~/code-reuse-kit")
AGENTS_SECTION_MARKER = "## 代码复用规则"


def step(msg: str):
    print(f"\n{'=' * 60}")
    print(f"  {msg}")
    print(f"{'=' * 60}")


def ok(msg: str = "[OK] 完成"):
    print(f"  {msg}")


def run(cmd: list, cwd: str | None = None, check: bool = True):
    # Resolve executable path (critical on Windows for .cmd/.bat like npm)
    exe = shutil.which(cmd[0])
    resolved = [exe] + cmd[1:] if exe else cmd
    try:
        subprocess.run(resolved, cwd=cwd, check=check, text=True)
    except FileNotFoundError:
        print(f"  ✗ 命令未找到: {' '.join(cmd)}", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"  ✗ 命令失败 (exit={e.returncode}): {' '.join(cmd)}", file=sys.stderr)
        sys.exit(1)


def is_windows() -> bool:
    return platform.system() == "Windows"


def find_ca() -> str:
    """Locate the ca executable across platforms."""
    ca = shutil.which("ca")
    if ca:
        return ca
    ca = shutil.which("ca.cmd")
    if ca:
        return ca
    fallbacks = [
        os.path.expanduser("~\\AppData\\Roaming\\npm\\ca.cmd"),
        os.path.expanduser("~\\AppData\\Roaming\\npm\\ca"),
        "/usr/local/bin/ca",
        "/opt/homebrew/bin/ca",
    ]
    for p in fallbacks:
        if os.path.isfile(p):
            return p
    return "ca"


def find_reasonix_agents_path() -> str | None:
    candidates = []
    if is_windows():
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            candidates.append(os.path.join(appdata, "reasonix", "AGENTS.md"))
    candidates.extend([
        os.path.expanduser("~/.config/reasonix/AGENTS.md"),
        os.path.expanduser("~/.reasonix/AGENTS.md"),
    ])
    for p in candidates:
        if os.path.isfile(p):
            return p
    return candidates[0] if candidates else None


def check_prerequisites():
    step("[1/9] 检查依赖")
    deps = {"git": "git", "python3": "python3", "node": "node", "npm": "npm"}
    if is_windows():
        deps["python3"] = "python"

    for name, cmd in deps.items():
        if shutil.which(cmd):
            ok(f"{name}: 已安装")
        else:
            print(f"  ✗ {name} 未安装，请先安装", file=sys.stderr)
            print(f"    - Git:   https://git-scm.com/downloads")
            print(f"    - Python: https://www.python.org/downloads/")
            print(f"    - Node:   https://nodejs.org/", file=sys.stderr)
            sys.exit(1)
    ok("所有依赖检查通过")
    return deps["python3"]


def clone_or_pull():
    step("[2/9] 拉取 code-reuse-kit 仓库")
    if os.path.isdir(os.path.join(DEST, ".git")):
        print("  仓库已存在，执行 git pull...")
        run(["git", "pull", "--ff-only"], cwd=DEST)
        ok("已更新到最新")
    else:
        print(f"  克隆到 {DEST} ...")
        parent = os.path.dirname(DEST)
        os.makedirs(parent, exist_ok=True)
        run(["git", "clone", GITHUB_REPO, DEST])
        ok("克隆完成")


def install_compound_agent():
    step("[3/9] 安装 compound-agent")
    if shutil.which("ca") or shutil.which("ca.cmd"):
        ok("compound-agent (ca) 已安装")
        return
    print("  通过 npm 全局安装 compound-agent...")
    run(["npm", "install", "-g", "compound-agent"])
    ok("compound-agent 安装完成")


def init_compound_agent():
    step("[4/9] 初始化 compound-agent")
    ca = find_ca()
    claude_dir = os.path.join(DEST, ".claude")
    if os.path.isdir(claude_dir):
        ok("compound-agent 已初始化，跳过")
    else:
        print("  运行 ca init ...")
        run([ca, "init"], cwd=DEST)

    print("  重建 SQLite 索引...")
    run([ca, "rebuild"], cwd=DEST, check=False)

    docs_dir = os.path.join(DEST, "docs")
    if os.path.isdir(docs_dir):
        print("  索引文档目录 docs/ ...")
        run([ca, "index-docs", "docs/"], cwd=DEST, check=False)
    ok("compound-agent 初始化完成")


def install_reasonix_config():
    step("[5/9] 安装 reasonix AGENTS.md 配置")
    agents_path = find_reasonix_agents_path()
    if not agents_path:
        print("  ⚠ 未找到 reasonix AGENTS.md 路径，跳过")
        return

    agents_dir = os.path.dirname(agents_path)
    os.makedirs(agents_dir, exist_ok=True)

    section = f"""

{AGENTS_SECTION_MARKER}

> 目标：避免重复造轮子。已经写过的代码自动入库，下次直接复用。
>
> **注意**：提取代码入库已由 git post-commit hook 全自动完成（安装时配置），
> agent 无需手动执行 extract_from_diff.py，只需关注"搜索已有代码"。

### 规则 1：任务开始时搜索已有代码

在开始写任何代码之前，先运行：
```
python ~/code-reuse-kit/scripts/search_code.py "<任务核心关键词>"
```
如果找到了匹配的代码，优先复用而不是重新写。

### 规则 2：写代码时记录

如果写了一个可复用的函数/类/工具，记录：
- 文件路径
- 函数/类名和签名
- 功能描述（在 AGENTS.md 中临时记录供任务结束使用）

### 规则 3：任务结束时自动存档（核心规则）

**每个任务结束时，必须调用 `/code-reuse-kit-save` skill。**

该 skill 会自动执行：
1. `git init`（如果还不是 git 仓库）
2. `git add -A`
3. `git commit -m "auto: 本次做了什么"`
4. post-commit hook 自动完成代码提取入库

用户不需要知道 git 是什么，agent 全包了。
如果提示 `/code-reuse-kit-save` 找不到，手动执行：
```
git add -A && git commit -m "auto: 添加了[功能]"
```

### 规则 4：跨设备同步

由系统定时任务（每天 10:00）自动完成，agent 无需干预。
在其他设备上只需 `cd ~/code-reuse-kit && git pull` 即可获取最新代码索引。

### 规则 5：相关 memory 检查

- 已存 memory 中标记为 "code-reuse" 的内容优先引用
- 使用 remember 工具保存常见任务的代码引用
"""

    if os.path.isfile(agents_path):
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
        if AGENTS_SECTION_MARKER in content:
            ok("reasonix AGENTS.md 已包含代码复用规则，跳过")
            return

    with open(agents_path, "a", encoding="utf-8") as f:
        f.write(section)

    print(f"  → 已追加到: {agents_path}")
    ok("reasonix 配置安装完成")


def print_summary():
    step("✓ 安装完成！")
    ca_path = find_ca()
    print(f"""
  仓库位置: {DEST}
  ca 命令:   {ca_path}

  🔄 自动流程（无需手动操作）:
    AI agent 任务结束时 → 自动 git commit → hook 自动提取入库
    每天 10:00          → 自动跨设备同步

  🤖 AI agent 自动存档已配置:
    ✅ Reasonix → /code-reuse-kit-save skill（任务结束自动存档）
    ✅ Claude Code → ~/.claude/CLAUDE.md（全局规则）
    ✅ Cursor / Copilot / Windsurf → 每项目规则（由 install_agent_config 安装）

  🔍 手动搜索已有代码:
    python ~/code-reuse-kit/scripts/search_code.py "关键词"

  🛠 其他:
    [卸载自动配置]   python ~/code-reuse-kit/scripts/install_hooks.py --uninstall
    [重装/更新]      python ~/code-reuse-kit/scripts/install_code_library.py
    [安装 agent 规则] python ~/code-reuse-kit/scripts/install_agent_config.py --project 项目路径

  下一步:
    - 正常写代码，agent 任务结束自动存档
    - 运行 ca list 查看已积累的 lessons
    - 运行 ca search "关键词" 搜索 knowledge base
""")


def install_code_library_skill():
    """[6/9] 安装 code-reuse-kit-save skill（任务结束自动存档）"""
    step("[6/9] 安装 code-reuse-kit-save skill")
    skill_src = os.path.join(DEST, "skills", "code-reuse-kit-save.md")
    skill_dst_dir = os.path.expanduser("~/.reasonix/skills")
    os.makedirs(skill_dst_dir, exist_ok=True)
    skill_dst = os.path.join(skill_dst_dir, "code-reuse-kit-save.md")
    if os.path.isfile(skill_src):
        import shutil
        shutil.copy2(skill_src, skill_dst)
        ok(f"已安装到 {skill_dst}")
    else:
        print(f"  ⚠ 未找到 {skill_src}，跳过")


def install_auto_hooks():
    """[7/9] 安装全自动 git hook + 定时任务"""
    step("[7/9] 安装全自动代码提取 & 同步")
    print("  运行 install_hooks.py ...")
    run([sys.executable, HOOKS_INSTALLER], cwd=DEST, check=False)
    ok("全自动配置安装完成")


def install_agent_configs():
    """[8/9] 安装其他 AI agent 自动存档规则"""
    step("[8/9] 安装其他 AI agent 自动存档规则")
    print(f"  运行 install_agent_config.py ...")
    run([sys.executable, AGENT_CONFIG_INSTALLER], cwd=DEST, check=False)
    ok("agent 配置安装完成")


def main():
    # Ensure stdout can handle Unicode (especially on Windows/GBK)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    elif hasattr(sys.stdout, "buffer"):
        sys.stdout = sys.stdout.buffer  # raw bytes fallback
    print("""
+------------------------------------------------------+
|  Code Reuse Kit -- One-Click Install                   |
|  https://github.com/LeoSaint502/code-reuse-kit         |
+------------------------------------------------------+
""")
    check_prerequisites()
    clone_or_pull()
    install_compound_agent()
    init_compound_agent()
    install_reasonix_config()
    install_code_library_skill()
    install_agent_configs()
    install_auto_hooks()
    print_summary()


if __name__ == "__main__":
    main()
