#!/usr/bin/env python3
"""
做梦机制 v2 —— 结构感知采样器
不再纯随机，而是按三种策略加权采样：
   1. Gap 型：被其他文章引用次数多，但自身内容极短（幽灵概念/stub）
   2. Stale 型：最后修改时间最久远的卡片（年久失修）
   3. Bridge 型：出链数量异常高的枢纽节点（值得审视其连接质量）
"""

import os
import re
import random
import argparse
from collections import Counter
from datetime import datetime

# 改进的维基链接正则表达式
# 支持格式：[[链接]], [[链接|显示文本]], [[链接#锚点]], [[链接#锚点|显示文本]]
# 也支持链接中包含特殊字符，但不包含不匹配的括号
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#([^\]]*?))?(?:\|([^\]]*?))?\]\]")


def extract_tags_from_content(content: str) -> list:
    """
    从Markdown内容中提取建议标签
    综合实现：从多个语义丰富的位置提取关键词作为标签建议
    """
    tags = []

    # 提取标题作为高权重标签（标题通常概括了段落的核心概念）
    headers = re.findall(r"^#{1,6}\s+(.+)$", content, re.MULTILINE)
    for header in headers:
        # 提取标题中的中文词汇和英文单词
        chinese_words = re.findall(r"[\u4e00-\u9fff]{2,}", header)
        english_words = re.findall(r"\b[a-zA-Z]{2,}\b", header)
        # 标题词汇权重更高，添加两次
        tags.extend([word.lower() for word in chinese_words + english_words] * 2)

    # 提取粗体文本作为中等权重标签（粗体通常强调重要概念）
    bold_text = re.findall(r"\*\*(.*?)\*\*|__(.*?)__", content)
    for match in bold_text:
        text = match[0] if match[0] else match[1]
        if text:
            chinese_words = re.findall(r"[\u4e00-\u9fff]{2,}", text)
            english_words = re.findall(r"\b[a-zA-Z]{2,}\b", text)
            tags.extend([word.lower() for word in chinese_words + english_words])

    # 提取斜体文本作为较低权重标签（斜体可能包含术语或特殊表达）
    italic_text = re.findall(r"\*(.*?)\*|_(.*?)_", content)
    for match in italic_text:
        text = match[0] if match[0] else match[1]
        if text and len(text.strip()) > 1:  # 避免单个字符
            # 斜体权重较低，只添加一次
            chinese_words = re.findall(r"[\u4e00-\u9fff]{2,}", text)
            english_words = re.findall(r"\b[a-zA-Z]{2,}\b", text)
            tags.extend([word.lower() for word in chinese_words + english_words])

    # 提取代码块中的技术术语
    code_blocks = re.findall(r"```[\w]*\n(.*?)\n```|`(.+?)`", content, re.DOTALL)
    for match in code_blocks:
        code_text = match[0] if match[0] else match[1]
        if code_text:
            # 从代码中提取可能的技术术语（变量名、函数名等）
            # 简单方法：提取下划线连接的单词和驼峰命名
            snake_case = re.findall(r"\b[a-z]+(?:_[a-z]+)+\b", code_text)
            camel_case = re.findall(r"\b[a-z]+[A-Z][a-zA-Z]*\b", code_text)
            # 将snake_case转换为空格分隔的词汇
            for word in snake_case:
                parts = word.split("_")
                tags.extend([part.lower() for part in parts if len(part) > 1])
            # 驼峰命名简单处理：添加整个词汇
            tags.extend([word.lower() for word in camel_case if len(word) > 2])

    # 提取列表项中的关键词（无序和有序列表）
    list_items = re.findall(
        r"^[\s]*[-*+]\s+(.+)$|^[\s]*\d+\.\s+(.+)$", content, re.MULTILINE
    )
    for match in list_items:
        item_text = match[0] if match[0] else match[1]
        if item_text:
            # 列表项通常包含重要信息，提取关键词
            chinese_words = re.findall(r"[\u4e00-\u9fff]{2,}", item_text)
            english_words = re.findall(
                r"\b[a-zA-Z]{3,}\b", item_text
            )  # 英文单词至少3个字符避免太常见的词
            tags.extend([word.lower() for word in chinese_words + english_words])

    # 提取第一段内容的关键词（通常是概述）
    # 获取第一个非空段落（跳过frontmatter）
    paragraphs = re.split(r"\n\s*\n", content.strip())
    for para in paragraphs:
        if para.strip() and not para.strip().startswith("---"):
            # 取前200个字符作为概述
            summary = para.strip()[:200]
            chinese_words = re.findall(r"[\u4e00-\u9fff]{2,}", summary)
            english_words = re.findall(r"\b[a-zA-Z]{3,}\b", summary)
            tags.extend([word.lower() for word in chinese_words + english_words])
            break  # 只处理第一段

    # 去重并返回前15个标签（增加数量以容纳更多来源）
    # 同时保留出现频率高的标签（简单计数）
    from collections import Counter

    tag_counts = Counter(tags)
    # 返回出现频率前15的标签
    return [tag for tag, _ in tag_counts.most_common(15)]


def extract_existing_tags(frontmatter: str) -> list:
    """
    从YAML frontmatter中提取现有标签
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


def scan_wiki(wiki_dir):
    """扫描 wiki 目录，返回 {basename: {path, mtime, content_len, out_links, tags, suggested_tags}}"""
    nodes = {}
    target_dirs = [
        os.path.join(wiki_dir, "projects"),
        os.path.join(wiki_dir, "concepts"),
    ]
    # 也扫描 wiki 根目录下的 md（但排除 README / index）
    for d in [wiki_dir] + target_dirs:
        if not os.path.exists(d):
            continue
        for root, dirs, files in os.walk(d):
            dirs[:] = [x for x in dirs if not x.startswith(".")]
            for f in files:
                if not f.endswith(".md") or f.endswith(".marp.md"):
                    continue
                if f.lower() in ("readme.md", "index.md"):
                    continue
                fp = os.path.join(root, f)
                basename = f[:-3]
                try:
                    content = open(fp, "r", encoding="utf-8").read()
                    mtime = os.path.getmtime(fp)

                    # 提取维基链接
                    out_links = WIKILINK_RE.findall(content)
                    out_link_targets = [l.split("#")[0].strip() for l in out_links]

                    # 提取frontmatter中的现有标签和内容中的建议标签
                    frontmatter_match = re.match(
                        r"^---\s*\n(.*?)\n---\s*\n(.*)",
                        content,
                        re.DOTALL | re.MULTILINE,
                    )
                    if frontmatter_match:
                        frontmatter = frontmatter_match.group(1)
                        body_content = frontmatter_match.group(2)
                        existing_tags = extract_existing_tags(frontmatter)
                        suggested_tags = extract_tags_from_content(body_content)
                    else:
                        # 没有frontmatter，整个内容作为正文
                        existing_tags = []
                        suggested_tags = extract_tags_from_content(content)

                    nodes[basename] = {
                        "path": fp,
                        "mtime": mtime,
                        "content_len": len(content),
                        "out_links": out_link_targets,
                        "existing_tags": existing_tags,
                        "suggested_tags": suggested_tags,
                    }
                except Exception:
                    pass
    return nodes


def score_nodes(nodes):
    """为每个节点计算综合"值得做梦"分数，分数越高越优先被选中。"""
    # 统计每个 basename 被引用的次数（入链度）
    in_degree = Counter()
    for info in nodes.values():
        for target in info["out_links"]:
            in_degree[target] += 1

    now = datetime.now().timestamp()
    scored = []

    for basename, info in nodes.items():
        score = 0.0

        # --- Gap 评分 ---
        # 被引用次数多但自身内容短 → 很可能是 stub 或幽灵概念
        refs = in_degree.get(basename, 0)
        if info["content_len"] < 500 and refs >= 2:
            score += 30 + refs * 5  # 强烈加分
        elif info["content_len"] < 1000 and refs >= 1:
            score += 10

        # --- Stale 评分 ---
        # 距上次修改越久，分数越高（按天计算）
        days_since_mod = (now - info["mtime"]) / 86400
        if days_since_mod > 90:
            score += 25
        elif days_since_mod > 30:
            score += 15
        elif days_since_mod > 7:
            score += 5

        # --- Bridge 评分 ---
        # 出链数量异常多的枢纽 → 审视连接质量
        out_count = len(info["out_links"])
        if out_count > 10:
            score += 20
        elif out_count > 5:
            score += 10

        # --- Tag Completeness 评分 ---
        # 标签完整性：鼓励既有标签和内容建议标签的结合
        existing_tag_count = len(info["existing_tags"])
        suggested_tag_count = len(info["suggested_tags"])
        total_tag_count = existing_tag_count + suggested_tag_count

        # 有标签总比没有好
        if total_tag_count > 0:
            score += 5
            # 如果既有现有标签又有建议标签，额外加分（表示标签系统工作良好）
            if existing_tag_count > 0 and suggested_tag_count > 0:
                score += 3
            # 标签数量适中时给予适度加分（避免标签过少或过多）
            if 3 <= total_tag_count <= 8:
                score += 2
            # 标签过少时略有扣分
            elif total_tag_count < 3:
                score -= 2

        # 加一点随机扰动防止每次结果完全一样
        score += random.uniform(0, 8)

        scored.append((basename, score, info))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def find_ghost_concepts(nodes):
    """找出被引用但完全没有对应文章的"幽灵概念"。"""
    all_targets = set()
    for info in nodes.values():
        for t in info["out_links"]:
            all_targets.add(t)
    ghosts = all_targets - set(nodes.keys())
    # 统计每个幽灵被引用的次数
    ghost_counts = Counter()
    for info in nodes.values():
        for t in info["out_links"]:
            if t in ghosts:
                ghost_counts[t] += 1
    return ghost_counts


def main():
    parser = argparse.ArgumentParser(description="做梦机制 v2 —— 结构感知采样")
    parser.add_argument("--wiki", required=True, help="Wiki 目录的绝对路径")
    parser.add_argument("--limit", type=int, default=3, help="采样的知识节点数量")
    parser.add_argument(
        "--apply-tags", action="store_true", help="自动应用建议的标签到文章中"
    )
    args = parser.parse_args()

    nodes = scan_wiki(args.wiki)

    if len(nodes) < 2:
        print(f"⚠️ 知识库文章不足 ({len(nodes)} 篇)，无法启动做梦。请先积累更多素材。")
        return

    # 1. 报告幽灵概念（被引用但不存在的知识空白）
    ghosts = find_ghost_concepts(nodes)
    if ghosts:
        top_ghosts = ghosts.most_common(5)
        print("🕳️ 【知识空白警报】以下概念被多次引用但从未创建：")
        for name, count in top_ghosts:
            print(f"   [[{name}]] — 被引用 {count} 次")
        print()

    # 2. 结构感知采样
    scored = score_nodes(nodes)
    limit = min(args.limit, len(scored))
    selected = scored[:limit]

    print(f"🌌 【梦境采样节点】({limit} 篇) — 按 Gap/Stale/Bridge/Tag 综合评分选出：")
    for basename, score, info in selected:
        days_old = (datetime.now().timestamp() - info["mtime"]) / 86400
        tag_parts = []
        if info["content_len"] < 500:
            tag_parts.append("Gap/Stub")
        if days_old > 30:
            tag_parts.append(f"Stale({int(days_old)}天)")
        if len(info["out_links"]) > 5:
            tag_parts.append(f"Bridge(出链{len(info['out_links'])})")

        # 添加标签信息
        if info["existing_tags"] or info["suggested_tags"]:
            tag_info = []
            if info["existing_tags"]:
                tag_info.append(f"现有:{','.join(info['existing_tags'][:3])}")
            if info["suggested_tags"]:
                tag_info.append(f"建议:{','.join(info['suggested_tags'][:3])}")
            tag_parts.append(" | ".join(tag_info))

        tags = ", ".join(tag_parts) if tag_parts else "一般"
        print(f"   [{tags}] -> {info['path']}")

    # 3. 自动应用建议标签（如果指定了 --apply-tags 选项）
    if args.apply_tags:
        print("\n🏷️ 【自动标签应用】正在将建议标签应用到选中的文章中：")
        for basename, score, info in selected:
            if info["suggested_tags"]:  # 只有当有建议标签时才应用
                # 读取文件内容
                with open(info["path"], "r", encoding="utf-8") as f:
                    content = f.read()

                # 检查是否有frontmatter
                frontmatter_match = re.match(
                    r"^---\s*\n(.*?)\n---\s*\n(.*)",
                    content,
                    re.DOTALL | re.MULTILINE,
                )

                if frontmatter_match:
                    # 有frontmatter的情况
                    frontmatter = frontmatter_match.group(1)
                    body_content = frontmatter_match.group(2)

                    # 提取现有标签
                    existing_tags = extract_existing_tags(frontmatter)

                    # 合并现有标签和建议标签，去重
                    all_tags = list(set(existing_tags + info["suggested_tags"]))

                    # 重构frontmatter中的tags部分
                    # 简单方法：替换或添加tags行
                    if "tags:" in frontmatter:
                        # 替换现有的tags行
                        lines = frontmatter.split("\n")
                        new_lines = []
                        for line in lines:
                            if line.strip().startswith("tags:"):
                                # 替换为新的tags行
                                tags_str = ", ".join([f'"{tag}"' for tag in all_tags])
                                new_lines.append(f"tags: [{tags_str}]")
                            else:
                                new_lines.append(line)
                        new_frontmatter = "\n".join(new_lines)
                    else:
                        # 添加新的tags行
                        tags_str = ", ".join([f'"{tag}"' for tag in all_tags])
                        new_frontmatter = frontmatter + f"\ntags: [{tags_str}]"

                    # 写回文件
                    new_content = f"---\n{new_frontmatter}\n---\n{body_content}"
                    with open(info["path"], "w", encoding="utf-8") as f:
                        f.write(new_content)

                    print(f"   已更新标签: {info['path']}")
                    print(f"     原标签: {existing_tags}")
                    print(f"     新标签: {all_tags}")
                else:
                    # 没有frontmatter的情况，在文件开头添加frontmatter
                    tags_str = ", ".join([f'"{tag}"' for tag in info["suggested_tags"]])
                    new_content = f"---\ntags: [{tags_str}]\n---\n{content}"
                    with open(info["path"], "w", encoding="utf-8") as f:
                        f.write(new_content)

                    print(f"   已添加frontmatter和标签: {info['path']}")
                    print(f"     添加的标签: {info['suggested_tags']}")
            else:
                print(f"   无建议标签可应用: {info['path']}")

    print("\n请仔细研读以上卡片，寻找隐蔽的跨领域连接并生成新 Insight 卡片。")


if __name__ == "__main__":
    main()
