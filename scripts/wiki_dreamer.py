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

WIKILINK_RE = re.compile(r'\[\[(.*?)(?:\|.*?)?\]\]')


def scan_wiki(wiki_dir):
    """扫描 wiki 目录，返回 {basename: {path, mtime, content_len, out_links}}"""
    nodes = {}
    target_dirs = [
        os.path.join(wiki_dir, 'projects'),
        os.path.join(wiki_dir, 'concepts'),
    ]
    # 也扫描 wiki 根目录下的 md（但排除 README / index）
    for d in [wiki_dir] + target_dirs:
        if not os.path.exists(d):
            continue
        for root, dirs, files in os.walk(d):
            dirs[:] = [x for x in dirs if not x.startswith('.')]
            for f in files:
                if not f.endswith('.md') or f.endswith('.marp.md'):
                    continue
                if f.lower() in ('readme.md', 'index.md'):
                    continue
                fp = os.path.join(root, f)
                basename = f[:-3]
                try:
                    content = open(fp, 'r', encoding='utf-8').read()
                    mtime = os.path.getmtime(fp)
                    out_links = WIKILINK_RE.findall(content)
                    out_link_targets = [l.split('#')[0].strip() for l in out_links]
                    nodes[basename] = {
                        'path': fp,
                        'mtime': mtime,
                        'content_len': len(content),
                        'out_links': out_link_targets,
                    }
                except Exception:
                    pass
    return nodes


def score_nodes(nodes):
    """为每个节点计算综合"值得做梦"分数，分数越高越优先被选中。"""
    # 统计每个 basename 被引用的次数（入链度）
    in_degree = Counter()
    for info in nodes.values():
        for target in info['out_links']:
            in_degree[target] += 1

    now = datetime.now().timestamp()
    scored = []

    for basename, info in nodes.items():
        score = 0.0

        # --- Gap 评分 ---
        # 被引用次数多但自身内容短 → 很可能是 stub 或幽灵概念
        refs = in_degree.get(basename, 0)
        if info['content_len'] < 500 and refs >= 2:
            score += 30 + refs * 5  # 强烈加分
        elif info['content_len'] < 1000 and refs >= 1:
            score += 10

        # --- Stale 评分 ---
        # 距上次修改越久，分数越高（按天计算）
        days_since_mod = (now - info['mtime']) / 86400
        if days_since_mod > 90:
            score += 25
        elif days_since_mod > 30:
            score += 15
        elif days_since_mod > 7:
            score += 5

        # --- Bridge 评分 ---
        # 出链数量异常多的枢纽 → 审视连接质量
        out_count = len(info['out_links'])
        if out_count > 10:
            score += 20
        elif out_count > 5:
            score += 10

        # 加一点随机扰动防止每次结果完全一样
        score += random.uniform(0, 8)

        scored.append((basename, score, info))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def find_ghost_concepts(nodes):
    """找出被引用但完全没有对应文章的"幽灵概念"。"""
    all_targets = set()
    for info in nodes.values():
        for t in info['out_links']:
            all_targets.add(t)
    ghosts = all_targets - set(nodes.keys())
    # 统计每个幽灵被引用的次数
    ghost_counts = Counter()
    for info in nodes.values():
        for t in info['out_links']:
            if t in ghosts:
                ghost_counts[t] += 1
    return ghost_counts


def main():
    parser = argparse.ArgumentParser(description="做梦机制 v2 —— 结构感知采样")
    parser.add_argument("--wiki", required=True, help="Wiki 目录的绝对路径")
    parser.add_argument("--limit", type=int, default=3, help="采样的知识节点数量")
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

    print(f"🌌 【梦境采样节点】({limit} 篇) — 按 Gap/Stale/Bridge 综合评分选出：")
    for basename, score, info in selected:
        days_old = (datetime.now().timestamp() - info['mtime']) / 86400
        tag_parts = []
        if info['content_len'] < 500:
            tag_parts.append("Gap/Stub")
        if days_old > 30:
            tag_parts.append(f"Stale({int(days_old)}天)")
        if len(info['out_links']) > 5:
            tag_parts.append(f"Bridge(出链{len(info['out_links'])})")
        tags = ", ".join(tag_parts) if tag_parts else "一般"
        print(f"   [{tags}] -> {info['path']}")

    print("\n请仔细研读以上卡片，寻找隐蔽的跨领域连接并生成新 Insight 卡片。")


if __name__ == "__main__":
    main()
