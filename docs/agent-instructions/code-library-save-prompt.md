# Code Library — 代码存档规则

> 每次任务结束时自动将新增代码存进个人代码图书馆。
> 原理：git add → git commit → post-commit hook 自动提取入库。

## 必须遵守的规则

### 任务结束时自动存档

每个任务结束时（最后一条消息发出之前），**必须执行以下操作**：

```bash
# 1. 进入项目根目录（如果不在）
cd <当前项目根目录>

# 2. 初始化 git 仓库（如果还不是）
git rev-parse --git-dir 2>/dev/null || git init

# 3. 添加所有文件
git add -A

# 4. 提交代码，生成有意义的提交信息
git commit -m "auto: <简短的中文说明，写清楚新增了什么功能>"

# 示例提交信息：
#   auto: 添加 PDF 文本提取函数
#   auto: 实现用户认证中间件
#   auto: 添加 CSV 解析器
#   auto: 修复日期格式化编码问题
```

### 什么情况下跳过

- 本次只有文档/注释/README 修改，没有实质性代码
- 用户明确说"不需要保存"、"测试用的"、"不用存档"
- 只有配置文件（.json/.yaml/.toml）变更，没有函数/类定义

### 任务开始时搜索已有代码

开始写代码之前，优先搜索是否有现成的：

**安装 Code Library 后可用：**
```bash
python ~/code-library/scripts/search_code.py "<任务关键词>"
```

如果找到匹配的代码，优先复用而不是重新写。

## 为什么需要做这个

安装 Code Library 时，系统已经配置了：
1. **全局 git post-commit hook** — 每次 `git commit` 后自动提取新增函数入库
2. **定时同步任务** — 每天自动跨设备同步

所以 agent 只需要做 `git add + git commit`，剩下的全自动完成。
