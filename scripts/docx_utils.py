#!/usr/bin/env python3
"""
docx_utils.py — docx 文档处理通用工具函数

可复用函数：
  - split_bracket_spans(text)  → 拆分括号嵌套，支持任意深度
  - get_valid_citations(text)  → 提取干净引用标记 [1-3], [6,15,16]
"""

import re


def split_bracket_spans(text: str) -> list[dict]:
    """将文本按括号嵌套拆分为段落。

    返回 [{"text": ..., "is_bracket": bool, "inner": str|None}, ...]，
    其中 is_bracket=True 的段为括号包围的内容（含嵌套），
    inner 为最内层合法引用标记（含括号）。

    示例：
      >>> split_bracket_spans("前[中[7]后]末")
      → [{"text":"前","is_bracket":False},
         {"text":"[中[7]后]","is_bracket":True,"inner":"[7]"},
         {"text":"末","is_bracket":False}]
    """
    segments = []
    i = 0
    while i < len(text):
        if text[i] == '[':
            depth = 1
            j = i + 1
            while j < len(text) and depth > 0:
                if text[j] == '[':
                    depth += 1
                elif text[j] == ']':
                    depth -= 1
                j += 1
            span = text[i:j]
            inner = re.search(r'\[([0-9,\-]+)\]', span)
            segments.append({
                'text': span,
                'is_bracket': True,
                'inner': inner.group(1) if inner else None,
            })
            i = j
        else:
            j = i
            while j < len(text) and text[j] != '[':
                j += 1
            segments.append({'text': text[i:j], 'is_bracket': False, 'inner': None})
            i = j
    return segments


def get_valid_citations(text: str) -> list[str]:
    """从文本中提取干净引用标记（排除年份、浮点数等误匹配）。

    返回形如 ['[1-3]', '[6,15,16]', '[11,17,18]'] 的列表。

    排除规则：
      - 年份（如 [2004]）：跳过
      - 浮点数引用（如 [1.5]）：跳过
      - 长度超过 20 字符的非标准引用（如 [genome_ID]）：跳过
    """
    results = []
    for m in re.finditer(r'\[([0-9,\-]+)\]', text):
        full = m.group(0)
        content = m.group(1)
        # 排除年份
        if re.match(r'^(19|20)\d{2}$', content):
            continue
        # 排除浮点数
        if '.' in content:
            continue
        # 排除超长内容
        if len(full) > 20:
            continue
        results.append(full)
    return results
