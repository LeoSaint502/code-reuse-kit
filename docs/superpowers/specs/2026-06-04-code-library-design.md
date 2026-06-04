# Code Reuse Kit — AI Agent 代码复用库设计文档

## 概述

当 Reasonix agent 在运行过程中为实现某个目的而编写了代码（函数、脚本、工具类等），自动为这些代码添加索引并存入可复用的代码库。下次遇到类似任务时，agent 能自动搜索到这个库，找到已有代码直接复用，而不是重新写一遍。

## 核心架构

```
┌─────────────────────────────────────────────────────┐
│                    Git 仓库（跨机器同步）              │
│  ~/code-reuse-kit/                                     │
│  ├── lessons/              ← compound-agent JSONL    │
│  ├── .cache/lessons.sqlite ← FTS5 搜索引擎           │
│  └── scripts/              ← 代码提取层              │
└─────────────────────────────────────────────────────┘
                            ↕ git push/pull
                  机器A ←──────────────→ 机器B

┌─ Reasonix 工作流 ──────────────────────────────────┐
│                                                     │
│  [任务开始] → search_code <关键词> → 注入已有代码   │
│                                                      │
│  [写代码中] → write_file/edit_file                  │
│                                                      │
│  [任务结束] → extract_from_diff.py                   │
│                 ↓                                    │
│              解析 git diff                           │
│                 ↓                                    │
│              提取新增函数/类 + 生成摘要              │
│                 ↓                                    │
│              ca learn --type code_snippet "..."      │
│                 ↓                                    │
│              git push (跨机器同步)                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 组件设计

### 1. compound-agent (存储 + 搜索底座)

**安装**：
```bash
npm install -g compound-agent
mkdir -p ~/code-reuse-kit && cd ~/code-reuse-kit
ca setup
```

**存储**：
- `lessons/index.jsonl` — Git 追踪的源文件（真相来源）
- `.cache/lessons.sqlite` — FTS5 全文搜索索引
- 嵌入向量（用于语义搜索）

**主要命令**：
- `ca learn "<insight>" --type code_snippet --citation file:line` — 注册代码片段
- `ca search "<query>"` — 搜索已有代码
- `ca list` — 列出所有条目

**跨设备同步**：JSONL 存在 Git 中，`git push/pull` 即同步。

### 2. extract_from_diff.py（代码提取层）

**位置**：`~/code-reuse-kit/scripts/extract_from_diff.py`

**功能**：
- 解析 `git diff HEAD~1` 或两个 commit 之间的差异
- 识别新增行（+ 开头）
- 用正则/AST 提取函数定义、类定义
- 提取函数的 docstring 和 import 依赖
- 生成功能摘要
- 自动添加语言/功能标签
- 调用 `ca learn` 注册到知识库

**支持的源语言**：
- Python（用 `ast` 模块解析）
- JavaScript / TypeScript（用正则提取 `function`/`=>`/`class`）
- Shell（用正则提取函数名）

**去重机制**：
- 用函数名 + 文件路径 + 行号做 hash 作为 ID
- 已存在的跳过
- 同一函数被多次修改 → 保留最新版本

**粒度**：
- 每个条目 = 函数签名 + docstring + 文件路径 + import 依赖
- 约 200-400 token 每个条目
- 需要完整实现时才去读源文件（lazy load）

### 3. search_code.py（搜索封装）

**位置**：`~/code-reuse-kit/scripts/search_code.py`

**功能**：封装 `ca search`，输出格式化结果

**输出格式**：
```
## 找到的已有代码

### [语言] 函数名
- **文件**: path/to/file.py:42
- **签名**: `def function_name(param: str) -> bool`
- **摘要**: 函数功能的简短描述
- **依赖**: import x, from y import z
```

### 4. code-reuse skill（Reasonix 技能）

**位置**：`~/.codex/skills/code-reuse/SKILL.md`

**行为**：
- 任务开始时自动调用 `search_code.py` 搜索已有代码
- 将匹配结果格式化后注入 context
- 任务结束时执行 `extract_from_diff.py` 提取新增代码

### 5. AGENTS.md 规则

**位置**：`%APPDATA%/reasonix/AGENTS.md`（Windows）或 `~/.config/reasonix/AGENTS.md`（其他）

添加以下规则：
```
## 代码复用规则

1. **任务开始时**：自动运行 `python ~/code-reuse-kit/scripts/search_code.py "<任务关键词>"`，
   将返回的已有代码片段注入 context
2. **写代码时**：如果写了可复用的函数/类，记录文件路径和用途
3. **任务结束时**：自动运行 `python ~/code-reuse-kit/scripts/extract_from_diff.py --repo <当前路径>`
   扫描 git diff，提取新增代码入库
4. **定期**：运行 `cd ~/code-reuse-kit && git push` 同步到其他机器
```

## 数据格式

### JSONL 条目示例

```jsonl
{"id":"py-parse-pdf-a3f2c","type":"pattern","language":"python","name":"parse_pdf","signature":"def parse_pdf(path: str) -> str","docstring":"Extract text from PDF file using pypdf","file":"utils/pdf_parser.py","imports":"from pypdf import PdfReader","content_lines":5,"timestamp":"2026-06-04T10:30:00Z","project":"doc-tools","tags":["pdf","text-extraction"]}
```

## 实施步骤

1. **安装 compound-agent**：`npm install -g compound-agent`
2. **初始化代码库**：`mkdir -p ~/code-reuse-kit && cd ~/code-reuse-kit && ca setup && git init`
3. **编写 extract_from_diff.py**：实现 git diff 解析 + 函数提取 + ca learn 调用
4. **编写 search_code.py**：封装 ca search，格式化输出
5. **安装 code-reuse skill**：复制 skill 文件到 `~/.codex/skills/code-reuse/`
6. **更新 AGENTS.md**：添加代码复用规则
7. **推送到远端**：`git remote add origin <url> && git push -u origin main`
8. **测试**：写一个简单函数 → 任务结束 → 检查是否入库 → 新任务搜索是否命中
