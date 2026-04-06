#!/usr/bin/env python3
"""
标签提取器 - 从Markdown内容中自动提取建议标签
"""

import re
import json
from collections import Counter
from typing import List, Set, Dict, Tuple
import math


def extract_tags_from_content(content: str, max_tags: int = 10) -> List[str]:
    """
    从Markdown内容中提取建议标签

    算法：
    1. 移除代码块、链接、图片等特殊Markdown语法
    2. 提取标题和粗体文本作为高权重词汇
    3. 计算词频，过滤停用词
    4. 基于TF-IDF-like评分选择顶级标签

    Args:
        content: Markdown文档内容
        max_tags: 返回的最大标签数量

    Returns:
        建议标签列表，按相关性排序
    """
    # 基础停用词列表（可扩展）
    STOP_WORDS = {
        "的",
        "了",
        "在",
        "是",
        "我",
        "有",
        "和",
        "就",
        "不",
        "人",
        "都",
        "一",
        "一个",
        "上",
        "也",
        "很",
        "到",
        "说",
        "要",
        "去",
        "你",
        "会",
        "着",
        "没有",
        "看",
        "好",
        "自己",
        "这",
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "can",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "me",
        "him",
        "her",
        "us",
        "them",
    }

    # 移除代码块（```...``` 和 `...`）
    content_no_code = re.sub(r"`{3}.*?`{3}", "", content, flags=re.DOTALL)
    content_no_code = re.sub(r"`.*?`", "", content_no_code)

    # 移除图片！[alt](url)
    content_no_images = re.sub(r"!\[.*?\]\(.*?\)", "", content_no_code)

    # 移除链接[text](url)但保留text（因为text可能是有价值的）
    # 但我们要特别处理wiki链接[[text]]和[[text|display]]
    content_no_links = re.sub(r"\[([^\]]*?)\]\([^)]*?\)", r"\1", content_no_images)

    # 提取标题（# 标题，## 标题等）作为高权重内容
    headers = re.findall(r"^(#{1,6})\s*(.+)$", content_no_links, flags=re.MULTILINE)
    header_text = " ".join([header[1] for header in headers])

    # 提取粗体文本（**文本** 或 __文本__）作为中等权重
    bold_text = re.findall(r"\*\*(.*?)\*\*|__(.*?)__", content_no_links)
    bold_text_flat = " ".join([item for pair in bold_text for item in pair if item])

    # 提取斜体文本（*文本* 或 _文本_）作为低权重
    italic_text = re.findall(r"\*(.*?)\*|_(.*?)_", content_no_links)
    italic_text_flat = " ".join([item for pair in italic_text for item in pair if item])

    # 组合所有文本，标题权重最高
    weighted_content = (
        header_text * 3
        + " "
        + bold_text_flat * 2
        + " "
        + italic_text_flat
        + " "
        + content_no_links
    )

    # 提取中文词汇（连续的汉字）
    chinese_words = re.findall(r"[\u4e00-\u9fff]{2,}", weighted_content)

    # 提取英文单词
    english_words = re.findall(r"\b[a-zA-Z]{2,}\b", weighted_content)

    # 合并所有词汇
    all_words = chinese_words + [word.lower() for word in english_words]

    # 过滤停用词和太常见的词
    filtered_words = [
        word for word in all_words if word.lower() not in STOP_WORDS and len(word) > 1
    ]

    # 计算词频
    word_freq = Counter(filtered_words)

    # 计算TF-IDF-like分数（简化版：考虑词长和位置）
    scored_words = []
    total_words = len(filtered_words)

    for word, freq in word_freq.items():
        # 基础TF分数
        tf = freq / total_words if total_words > 0 else 0

        # 词长奖励（中等长度的词通常更有信息量）
        length_score = min(len(word) / 10, 1.0)  # 归一化到0-1

        # 位置奖励：出现在标题中的词加分
        position_bonus = (
            1.5 if word in header_text or any(word in h[1] for h in headers) else 1.0
        )

        # 综合分数
        score = tf * (1 + length_score) * position_bonus

        scored_words.append((word, score))

    # 按分数排序并返回顶级标签
    scored_words.sort(key=lambda x: x[1], reverse=True)
    top_tags = [word for word, score in scored_words[:max_tags]]

    return top_tags


def extract_existing_tags(frontmatter: str) -> List[str]:
    """
    从YAML frontmatter中提取现有标签

    Args:
        frontmatter: YAML frontmatter字符串

    Returns:
        现有标签列表
    """
    tags = []
    # 匹配tags: [item1, item2] 或 tags:\n  - item1\n  - item2
    tag_match = re.search(
        r"tags\s*:\s*(?:\[(.*?)\]|\n(?:.*?\-.*?\n)*?)", frontmatter, re.DOTALL
    )
    if tag_match:
        tag_content = tag_match.group(1) if tag_match.group(1) else tag_match.group(0)
        # 提取括号内的内容或列表项
        if "[" in tag_content:
            # [item1, item2] 格式
            tags_raw = re.findall(r"\[(.*?)\]", tag_content)
            if tags_raw:
                tags = [
                    tag.strip().strip("'\"")
                    for tag in tags_raw[0].split(",")
                    if tag.strip()
                ]
        else:
            # - item1 格式
            tags = re.findall(r'\-\s*[\'"](.*?)[\'"]', tag_content)
            if not tags:
                tags = re.findall(r"\-\s*(\S+)", tag_content)

    return [tag.strip() for tag in tags if tag.strip()]


def suggest_missing_tags(
    content: str, existing_tags: List[str] = None, max_suggestions: int = 5
) -> List[str]:
    """
    建议缺失的标签

    Args:
        content: 完整的Markdown内容（包括frontmatter）
        existing_tags: 已存在的标签列表
        max_suggestions: 最大建议数量

    Returns:
        建议但尚未存在的标签列表
    """
    if existing_tags is None:
        existing_tags = []

    # 提取frontmatter和正文内容
    frontmatter_match = re.match(
        r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL | re.MULTILINE
    )
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        body_content = frontmatter_match.group(2)
        current_tags = extract_existing_tags(frontmatter)
    else:
        # 没有frontmatter，整个内容作为正文
        body_content = content
        current_tags = []

    # 合并已有标签
    all_existing_tags = set(existing_tags + current_tags)

    # 从内容中提取建议标签
    suggested_tags = extract_tags_from_content(
        body_content, max_tags=max_suggestions * 2
    )

    # 过滤掉已经存在的标签
    missing_tags = [
        tag
        for tag in suggested_tags
        if tag.lower() not in {t.lower() for t in all_existing_tags}
    ]

    return missing_tags[:max_suggestions]


if __name__ == "__main__":
    # 测试用例
    test_content = """---
tags: [machine-learning, neural-networks]
status: draft
---

# 测试深度学习在计算机视觉中的应用

## 项目概述

本文探讨了[[深度学习]]技术在[[计算机视觉]]领域的最新进展，特别是在[[目标检测]]和[[图像分类]]方面的应用。

### 核心贡献

我们提出了一种新型的[[卷积神经网络|CNN]]架构，该架构在标准基准测试中表现出色。

#### 实验结果

在ImageNet数据集上，我们的方法将top-1准确率提高了2.3%，在COCO目标检测基准上实现了15.7%的mAP提升。

### 相关工作

以前的工作包括[[循环神经网络|RNN]]在序列建模中的应用以及[[变换器|Transformer]]在自然语言处理中的突破。

## 结论

深度学习继续推动人工智能的发展，未来研究方向包括[[强化学习]]和[[无监督学习]]的结合。
"""

    print("=== 标签提取器测试 ===")
    print("提取的标签:", extract_tags_from_content(test_content, max_tags=10))
    print("建议的缺失标签:", suggest_missing_tags(test_content, max_suggestions=5))
