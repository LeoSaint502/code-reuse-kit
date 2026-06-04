# Code Reuse Kit

跨设备、跨项目代码复用仓库。自动从你的 **git diff** 中提取可复用函数/类，用 compound-agent 做语义搜索。

---

## 📖 小白从零开始 — 手把手教程

> **你完全不需要会任何东西。** 没写过代码、没用过 Git、不知道什么是"命令行"都没关系。
> 跟着下面的步骤走就行。

### 这个工具是干嘛的？

你以后写代码的时候，很多函数其实是**重复的**（比如读取文件、解析日期、发送网络请求）。
这个工具**自动帮你记住**你写过哪些有用的代码，下次 AI agent 再遇到类似任务时，就可以直接拿来用，不用重新写。

**简单说：你只管写代码，它帮你建一个"个人代码图书馆"，越用越强大。**

---

### 第一步：安装三个必须软件

> 按顺序一个一个装，装完一个再装下一个。

#### ① 安装 Git

1. 打开浏览器，进入 https://git-scm.com/download/win
2. 点击下载，下载完成后双击安装
3. **一路点"Next（下一步）"就行**，所有选项保持默认
4. 安装完成

**怎么检查装好了？** 按住键盘 `Win + R`，输入 `cmd` 回车，在黑框里输入：
```
git --version
```
如果显示 `git version 2.xx.x` 之类的文字，说明装好了。

#### ② 安装 Python

1. 打开 https://www.python.org/downloads/
2. 点击黄色的 **Download Python** 按钮
3. 下载完成后双击安装
4. **⚠️ 重要：安装时一定勾选 "Add Python to PATH"**（页面最下面）
5. 点 "Install Now"

**检查：** 在黑框里输入 `python --version`，显示 `Python 3.xx.x` 就对了。

#### ③ 安装 Node.js

1. 打开 https://nodejs.org/
2. 点击绿色的 **LTS** 版本下载
3. 双击安装，一路 Next

**检查：** 在黑框里输入 `node --version`，显示 `vxx.x.x` 就对了。

---

### 第二步：安装这个工具（Code Reuse Kit）

> 下面的命令，**直接复制粘贴**到黑框里，敲回车执行。
> 一行一行来，先复制第一行 → 回车 → 等它跑完 → 再复制第二行 → 回车。

**① 打开黑框（终端）**
- 按键盘 `Win + R`，输入 `cmd`，回车

**② 依次输入以下命令（一次一行，每次等它跑完再说）**

```bash
git clone https://github.com/LeoSaint502/code-reuse-kit.git
```
```bash
cd code-reuse-kit
```
```bash
python scripts\install_code_library.py
```

> 安装脚本会自动下载所有需要的东西，大概需要 1-3 分钟。
> 期间如果弹出安全提示，点"允许"或"是"。

---

### 第三步：开始用 AI agent 写代码

> 安装完这个工具后，你的日常流程就是这样了。

你找了一个 AI agent（比如 Claude、Cursor、GitHub Copilot），让它帮你写代码。

#### 正常的工作流程（用 Reasonix）

> ✅ 如果你用的是 **Reasonix** agent，`/code-reuse-kit-save` skill 已安装。

```
┌─ 你的日常 ─────────────────────────────────────────┐
│                                                      │
│  ① 打开 Reasonix                                     │
│                                                      │
│  ② 告诉它你要做什么（比如"写一个读取 PDF 的函数"）     │
│                                                      │
│  ③ Reasonix 写好代码，任务结束时 **自动存档**         │
│     （你什么都不用做）                                 │
│                                                      │
│  ④ 完事！代码自动入库 ✓                              │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**你不用打开黑框，不用输入任何命令。Agent 全自动搞定。**

#### 正常的工作流程（用 Claude Code）

> ✅ 安装时已配置 **全局 CLAUDE.md**，Claude Code 任务结束时会自动存档。
> 你也**什么都不用做**。

```
┌─ 你的日常 ─────────────────────────────────────────┐
│                                                      │
│  ① 打开 Claude Code                                  │
│                                                      │
│  ② 告诉它你要做什么                                    │
│                                                      │
│  ③ Claude Code 写好代码，任务结束时 **自动存档**       │
│     （你什么都不用做）                                 │
│                                                      │
│  ④ 完事！代码自动入库 ✓                              │
│                                                      │
└──────────────────────────────────────────────────────┘
```

#### 正常的工作流程（用 Cursor / Copilot / Windsurf）

> 首次使用时，在你的项目目录下运行一次配置命令，之后也全自动。
> **只需要做一次，以后就不用管了。**

```bash
# 在你的项目目录里运行一次（只需要做一次）
python ~/code-reuse-kit/scripts/install_agent_config.py --project .
```

运行后，agent **每次任务结束都会自动 git commit**，无需你手动操作。

```
┌─ 你的日常 ─────────────────────────────────────────┐
│                                                      │
│  ① 打开 Cursor / Copilot / Windsurf                  │
│                                                      │
│  ② 告诉它你要做什么                                    │
│                                                      │
│  ③ AI 写好代码，任务结束时 **自动存档**（一次配置后）  │
│                                                      │
│  ④ 完事！代码自动入库 ✓                              │
│                                                      │
└──────────────────────────────────────────────────────┘
```

> 💡 **为什么 Cursor/Copilot 需要多一步？**
> Reasonix 和 Claude Code 支持全局指令，所有项目都自动生效。
> Cursor/Copilot/Windsurf 的指令是每个项目单独生效的，所以在每个项目里需要运行一次配置命令。

---

### 常见问题

**Q: 什么是"黑框"？怎么打开？**
A: 就是"命令提示符"。按键盘左下角的 `Windows 键 + R`，输入 `cmd`，回车。

**Q: "路径"是什么？**
A: 就是你放代码的文件夹的地址。比如你桌面上有个文件夹叫 `my-code`，路径通常是：
```
C:\Users\你的用户名\Desktop\my-code
```
在黑框里输入 `cd 路径` 就可以去到那个文件夹。

**Q: 什么是 git commit？为什么每次都要做？**
A: 你可以把它理解为"拍照存档"——把你现在的代码拍个快照存下来。
这个工具就是在你"拍照"的时候，自动把你写的新函数提取出来入库。
**如果你用 Reasonix 或 Claude Code，agent 会自动帮你拍照，你不需要知道 git 是什么。**

**Q: 我什么都不懂，搞砸了怎么办？**
A: 目前这个阶段你几乎不可能搞砸。就算命令报错了，也只是没有存进去而已，不会影响你的代码。放心试。

**Q: 我用的不是 Reasonix，是 Cursor/其他 agent，也能自动存档吗？**
A: 可以！
- **Claude Code** → 安装时已自动配好，和 Reasonix 一样全自动。
- **Cursor / Copilot / Windsurf** → 在项目目录里运行一次 `python ~/code-reuse-kit/scripts/install_agent_config.py --project .`，之后每次任务结束也会自动存档。

---

## 🚀 一键安装

```bash
# 克隆并运行安装脚本（会自动配置所有依赖 + 全自动模式）
git clone https://github.com/LeoSaint502/code-reuse-kit.git
cd code-reuse-kit
python scripts/install_code_library.py
```

## ✅ 使用验证 — 如何确保"没有再造轮子"

> 系统自动积累可复用的代码索引。你可以通过以下 4 种方式验证它是否在工作。

### 验证方法 ①：搜索已有代码

```bash
cd ~/code-reuse-kit
python scripts/search_code.py "关键词"
```

例如搜索 "extract"，返回 8 条匹配结果。

### 验证方法 ②：看索引文件

索引存储位置：
```
~/code-reuse-kit/.claude/lessons/index.jsonl
```
每一行是一条函数/类的记录（只存"名片"：函数名 + 说明 + 位置，不存代码本体）。

### 验证方法 ③：看 AI agent 的回复

在遵循规则的项目中，agent 每次任务结束时会在回复中标明：
- **"复用了 xxx 代码（来源: 代码图书馆）"** — 说明本次没有重写轮子
- **"无可复用代码，全部新写"** — 说明本次是新功能

### 验证方法 ④：查看 GitHub 同步记录

索引文件 `.claude/lessons/index.jsonl` 被 git 跟踪，push 到 GitHub 后，任何人都可以 clone 后直接用。

### 当前索引统计（截至 2026-06-04）

| 来源 | 索引条目 | 说明 |
|------|:--------:|------|
| 项目1 scripts/ | 49 | analyze_bid / extract_tables / generate_docs 等 7 个脚本 |
| 项目2 | 3 | _apply_polish.py 的 3 个函数 |
| **总计** | **52 条** | 持续增长中 |

---

## 🔄 全自动工作流（更新版）

安装后你只需做一件事：**正常写代码 + git commit**。

```

你写代码 -> git commit
                  |
                  v
          +----------------------+
          | post-commit hook     |  <- 自动提取新增函数入库
          +----------+-----------+
                     |
                     v
          +----------------------+
          | ca learn 注册        |
          | 索引写入 index.jsonl |
          +----------+-----------+
                     |
                     v
          +----------------------+
          | git push（手动/定时）|
          | 同步到 GitHub        |
          +----------+-----------+
                     |
                     v
          +----------------------+
          | AI agent 下次写代码前|
          | search_code.py 自动搜|
          | 找到->复用 / 找不到->新写|
          +----------------------+
```

### 新工具：补录已有项目代码

如果有一个已经写了很多代码的旧项目，想一次性入库：

```bash
python ~/code-reuse-kit/scripts/backfill_code_library.py --dir /path/to/project/scripts
```

会自动扫描所有 .py 文件，提取函数/类定义注册到索引。已在项目1（49 条）和项目2（3 条）验证通过。



## 📚 参考与致谢

本项目参考/借鉴了以下 GitHub 开源项目：

### 核心底座

| 项目 | 用途 | 参考了什么 |
|------|------|-----------|
| **[compound-agent](https://github.com/Nathandela/compound-agent)** ⭐18 | 存储引擎 + 搜索引擎 | JSONL+SQLite FTS5 存储模式，`ca learn/list/search` 命令设计，lessons 生命周期管理，hook 系统 |
| **[claudecode-kb](https://github.com/tangero/claudecode-kb)** ⭐9 | 文件组织思路 | 按 `patterns/snippets/troubleshooting/memory` 分类的知识库结构，JSONL 会话日志 append-only 设计 |

### 调研但未直接采用

这些项目提供了重要的设计参考和不做什么的决策依据：

| 项目 | 为什么不直接用 | 学到了什么 |
|------|---------------|-----------|
| **[reza](https://github.com/swebreza/reza)** (Python) | 目标是项目文件索引，不是代码片段复用 | SQLite + FTS5 的存储架构思路 |
| **[Lumen](https://github.com/Sardor-M/lumen)** ⭐7 (TypeScript) | 核心依赖 23 个 MCP 工具，Reasonix 不支持 MCP | 知识图谱 + 跨设备加密同步的理念 |
| **[Alembic](https://github.com/GxFn/Alembic)** (TypeScript) | 重度依赖 MCP 协议 | Tree-sitter AST 提取代码模式的思路 |
| **[claudio-codex](https://github.com/Abraxas-365/claudio-codex)** ⭐4 (Go) | 是代码结构索引器，不是代码复用库 | 函数级代码索引的粒度 |

### 代码提取层的技术来源

`extract_from_diff.py` 中的 AST 解析逻辑参考了：
- Python 标准库 `ast` 模块（官方文档）
- compound-agent 的 `lesson` 存储格式（JSONL schema）

---

## 兼容的 AI Agent

这套方案基于 **git 全局 hook**，不依赖任何特定 AI agent：

| Agent | 存档方式 | 用户操作 |
|-------|:--------:|:--------:|
| Reasonix | `/code-reuse-kit-save` skill | 零操作 |
| Claude Code | `~/.claude/CLAUDE.md` 全局规则 | 零操作 |
| Cursor | `.cursorrules` 每项目 | 一次配置 |
| GitHub Copilot | `.github/copilot-instructions.md` 每项目 | 一次配置 |
| Windsurf | `.windsurfrules` 每项目 | 一次配置 |
| 任何使用 git 的工具 | post-commit hook | 手动 `git add + commit` |

## 🛠 手动命令

```bash
# 搜索已有代码
python ~/code-reuse-kit/scripts/search_code.py "关键词"

# 手动提取（一般不需要，hook 已自动执行）
python ~/code-reuse-kit/scripts/extract_from_diff.py --repo .

# 手动同步
cd ~/code-reuse-kit && python scripts/sync.py

# 卸载自动配置
python ~/code-reuse-kit/scripts/install_hooks.py --uninstall

# 重装/更新
python ~/code-reuse-kit/scripts/install_code_library.py

# 安装 AI agent 自动存档规则
python ~/code-reuse-kit/scripts/install_agent_config.py --project .
```

## 依赖

| 依赖 | 用途 |
|------|------|
| Git | 拉取/同步仓库 + post-commit hook |
| Python 3 | 运行提取/搜索/同步脚本 |
| Node.js / npm | 安装 compound-agent |
| compound-agent (`ca`) | 语义搜索 + 知识管理 |

## 项目结构

```
~/code-reuse-kit/
  scripts/
    extract_from_diff.py       ← 从 git diff 提取代码入库
    search_code.py             ← 搜索已有代码
    backfill_code_library.py   ← ★ 补录已有项目的历史代码到索引
    install_code_library.py    ← 💡 一键安装（从这里开始）
    install_hooks.py           ← 安装全局 git hook + 定时任务
    install_agent_config.py    ← 安装 AI agent 自动存档规则
    sync.py                    ← 每日同步（git pull + 重建索引）
  skills/
    code-reuse-kit-save.md       ← Reasonix 自动存档 skill
  docs/
    agent-instructions/        ← 各 agent 共用的 prompt 模板
  .claude/lessons/             ← 积累的 lessons（git 跟踪）
```
