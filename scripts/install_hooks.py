#!/usr/bin/env python3
"""
install_hooks.py — 一键安装全自动代码提取 & 同步。

做什么：
  1. 安装全局 git post-commit hook → 每次 git commit 后自动提取代码入库
  2. 注册系统定时任务 → 每天自动 git push 同步到远端

对小白来说 = 正常写代码 + git commit，其他全自动。

用法：
  python install_hooks.py              # 安装全部
  python install_hooks.py --git-only   # 只装 git hook
  python install_hooks.py --sync-only  # 只装定时同步
  python install_hooks.py --uninstall  # 卸载
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import stat
import subprocess
import sys

CODE_LIBRARY_DIR = os.path.expanduser("~/code-reuse-kit")
SCRIPTS_DIR = os.path.join(CODE_LIBRARY_DIR, "scripts")
HOOKS_DIR = os.path.expanduser("~/.git-hooks")
POST_COMMIT_PATH = os.path.join(HOOKS_DIR, "post-commit")

SYNC_SCRIPT = os.path.join(SCRIPTS_DIR, "sync.py")
EXTRACT_SCRIPT = os.path.join(SCRIPTS_DIR, "extract_from_diff.py")


# ── 工具函数 ────────────────────────────────────────────────────────────

def is_windows() -> bool:
    return platform.system() == "Windows"


def ok(msg: str):
    print(f"  ✓ {msg}")


def warn(msg: str):
    print(f"  ⚠ {msg}")


def fail(msg: str):
    print(f"  ✗ {msg}", file=sys.stderr)


def run(cmd: list, cwd: str | None = None, check: bool = True):
    # Resolve executable path (critical on Windows for .cmd/.bat like npm)
    exe = shutil.which(cmd[0])
    resolved = [exe] + cmd[1:] if exe else cmd
    try:
        subprocess.run(resolved, cwd=cwd, check=check, text=True, timeout=60)
    except subprocess.CalledProcessError as e:
        if check:
            print(f"  ✗ 命令失败: {' '.join(cmd)} (exit={e.returncode})", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        if check:
            print(f"  ✗ 命令未找到: {' '.join(cmd)}", file=sys.stderr)
            sys.exit(1)
    except subprocess.TimeoutExpired:
        if check:
            print(f"  ✗ 命令超时: {' '.join(cmd)}", file=sys.stderr)
            sys.exit(1)


def has_git() -> bool:
    return shutil.which("git") is not None


# ── 全局 git post-commit hook ──────────────────────────────────────────

def ensure_hooks_dir():
    os.makedirs(HOOKS_DIR, exist_ok=True)


def set_global_hooks_path():
    """设置 git --global core.hooksPath，使所有仓库共用同一套 hooks"""
    cur = subprocess.run(
        ["git", "config", "--global", "--get", "core.hooksPath"],
        capture_output=True, text=True
    ).stdout.strip()

    if cur == HOOKS_DIR:
        ok("全局 core.hooksPath 已指向 ~/.git-hooks")
        return

    run(["git", "config", "--global", "core.hooksPath", HOOKS_DIR])
    ok(f"已设置全局 core.hooksPath → {HOOKS_DIR}")


def install_post_commit_hook():
    """创建 post-commit hook：每次 commit 后自动运行 extract_from_diff.py"""
    ensure_hooks_dir()

    hook_content = f'''#!/usr/bin/env sh
# ── Code Reuse Kit: auto-extract on commit ──────────────────────────
# 每次 git commit 后，自动从本次 diff 中提取新增函数/类入库。
# 由 install_hooks.py 安装，无需手动操作。

EXTRACT_SCRIPT="{EXTRACT_SCRIPT}"

if [ ! -f "$EXTRACT_SCRIPT" ]; then
    exit 0
fi

# 获取当前仓库路径
REPO_DIR=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_DIR" ]; then
    exit 0
fi

# 跳过 code-reuse-kit 仓库自身（避免递归）
if [ "$REPO_DIR" = "{CODE_LIBRARY_DIR}" ]; then
    exit 0
fi

# 静默执行，不阻塞 commit。失败也不影响。
python3 "$EXTRACT_SCRIPT" --repo "$REPO_DIR" --silent 2>/dev/null || \\
python "$EXTRACT_SCRIPT" --repo "$REPO_DIR" --silent 2>/dev/null || true

exit 0
'''

    with open(POST_COMMIT_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(hook_content)

    # 加可执行权限（Unix）
    if not is_windows():
        st = os.stat(POST_COMMIT_PATH)
        os.chmod(POST_COMMIT_PATH, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    ok(f"post-commit hook 已安装 → {POST_COMMIT_PATH}")


def uninstall_hook():
    """卸载 git hook"""
    if os.path.isfile(POST_COMMIT_PATH):
        os.remove(POST_COMMIT_PATH)
        ok("post-commit hook 已删除")
    else:
        warn("post-commit hook 不存在")

    cur = subprocess.run(
        ["git", "config", "--global", "--get", "core.hooksPath"],
        capture_output=True, text=True
    ).stdout.strip()
    if cur == HOOKS_DIR:
        run(["git", "config", "--global", "--unset", "core.hooksPath"], check=False)
        ok("全局 core.hooksPath 已清除")


# ── 定时同步任务 ────────────────────────────────────────────────────────

def install_scheduled_sync():
    """注册系统定时任务（Windows: Task Scheduler / Unix: cron）"""
    if is_windows():
        _install_windows_task()
    else:
        _install_cron_job()


def _install_windows_task():
    """用 schtasks.exe 创建每天一次的同步任务"""
    python = sys.executable
    task_name = "CodeLibrarySync"
    task_cmd = f'"{python}" "{SYNC_SCRIPT}"'

    # 先查是否已存在
    check = subprocess.run(
        ["schtasks", "/Query", "/TN", task_name],
        capture_output=True, text=True
    )
    if check.returncode == 0:
        ok(f"Windows 计划任务 '{task_name}' 已存在")
        return

    cmd = [
        "schtasks", "/Create",
        "/SC", "DAILY",
        "/TN", task_name,
        "/TR", task_cmd,
        "/ST", "10:00",  # 每天上午 10 点
        "/F",  # 强制创建
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        ok(f"Windows 计划任务已创建: 每天 10:00 → {SYNC_SCRIPT}")
    else:
        fail(f"创建计划任务失败: {r.stderr.strip()}")


def _install_cron_job():
    """用 crontab 添加每天一次的同步任务"""
    cron_line = f"0 10 * * * cd {CODE_LIBRARY_DIR} && {sys.executable} {SYNC_SCRIPT} >> ~/code-reuse-kit/sync.log 2>&1"

    # 检查是否已有
    try:
        existing = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True, timeout=10
        )
        if SYNC_SCRIPT in existing.stdout:
            ok("cron 任务已存在")
            return

        new_cron = (existing.stdout or "") + cron_line + "\n"
        p = subprocess.run(
            ["crontab", "-"],
            input=new_cron, capture_output=True, text=True, timeout=10
        )
        if p.returncode == 0:
            ok(f"cron 任务已添加: 每天 10:00 → {SYNC_SCRIPT}")
        else:
            fail(f"添加 cron 任务失败: {p.stderr.strip()}")
    except FileNotFoundError:
        fail("crontab 命令未找到，请手动设置定时任务")


def uninstall_scheduled_sync():
    if is_windows():
        task_name = "CodeLibrarySync"
        r = subprocess.run(
            ["schtasks", "/Delete", "/TN", task_name, "/F"],
            capture_output=True, text=True
        )
        if r.returncode == 0:
            ok("Windows 计划任务已删除")
        else:
            warn("计划任务不存在或删除失败")
    else:
        try:
            existing = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True, timeout=10
            )
            lines = [l for l in existing.stdout.splitlines() if SYNC_SCRIPT not in l]
            new_cron = "\n".join(lines) + "\n"
            subprocess.run(["crontab", "-"], input=new_cron, text=True, timeout=10)
            ok("cron 任务已删除")
        except Exception as e:
            warn(f"删除 cron 任务失败: {e}")


def check_git_installed():
    if not has_git():
        print("  ✗ 需要 Git，请先安装: https://git-scm.com/downloads", file=sys.stderr)
        sys.exit(1)
    ok("Git 已安装")


# ── 主流程 ──────────────────────────────────────────────────────────────

def print_banner():
    print("""
+------------------------------------------------------+
|  Code Reuse Kit — 全自动安装                           |
|  安装后只要正常 git commit，代码自动入库 + 定时同步  |
+------------------------------------------------------+
""")


def main():
    parser = argparse.ArgumentParser(description="安装自动代码提取 & 同步")
    parser.add_argument("--git-only", action="store_true", help="只安装 git hook")
    parser.add_argument("--sync-only", action="store_true", help="只安装定时同步")
    parser.add_argument("--uninstall", action="store_true", help="卸载所有自动配置")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.uninstall:
        print_banner()
        print("--- 卸载自动配置 ---")
        uninstall_hook()
        uninstall_scheduled_sync()
        print("\n卸载完成。")
        return

    print_banner()
    check_git_installed()

    do_git = not args.sync_only
    do_sync = not args.git_only

    if do_git:
        print("\n--- [1/2] 安装全局 git post-commit hook ---")
        print("  原理: git commit 后自动触发 extract_from_diff.py，无需手动操作。")
        print(f"  对所有仓库生效（跳过 code-reuse-kit 自身）。\n")
        set_global_hooks_path()
        install_post_commit_hook()

    if do_sync:
        print("\n--- [2/2] 注册定时同步任务 ---")
        print("  原理: 每天 10:00 自动 git pull + 重建索引，保持跨设备同步。")
        print(f"  脚本: {SYNC_SCRIPT}\n")
        install_scheduled_sync()

    print(f"""
{'='*50}
  安装完成！
{'='*50}

  你现在只需要：
    1. 正常写代码
    2. 正常 git commit
    3. 其他全自动 ✓

  post-commit hook: {POST_COMMIT_PATH}
  定时同步:        每天 10:00
  提取脚本:        {EXTRACT_SCRIPT}
  同步脚本:        {SYNC_SCRIPT}

  卸载:
    python {os.path.join(SCRIPTS_DIR, "install_hooks.py")} --uninstall
""")

    # 验证 hook 文件存在
    if os.path.isfile(POST_COMMIT_PATH):
        ok("验证: post-commit hook 文件存在")
    else:
        fail("验证: post-commit hook 文件缺失！")


if __name__ == "__main__":
    main()
