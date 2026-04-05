#!/usr/bin/env python3
"""
Wiki 健康检查引擎 v2
功能：
  1. 检测断裂的双向链接（死链）
  2. 自动为高频死链生成 Stub 占位卡片
  3. 检测孤立页面（无入链的文章）
"""
import os
import re
import argparse
from collections import Counter
from datetime import date

WIKILINK_RE = re.compile(r'\[\[(.*?)(?:\|.*?)?\]\]')


def scan_all_md(wiki_dir):
    """返回 {basename: filepath} 和 {basename: content}"""
    paths = {}
    contents = {}
    for root, dirs, files in os.walk(wiki_dir):
        if '/.' in root or '\\.' in root:
            continue
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if f.endswith('.md') and not f.endswith('.marp.md'):
                basename = f[:-3]
                fp = os.path.join(root, f)
                paths[basename] = fp
                try:
                    contents[basename] = open(fp, 'r', encoding='utf-8').read()
                except Exception:
                    contents[basename] = ""
    return paths, contents


def main():
    parser = argparse.ArgumentParser(description="Wiki 健康检查与 Stub 自动生成")
    parser.add_argument("--wiki", required=True, help="Wiki 目录")
    parser.add_argument("--auto-stub", action="store_true",
                        help="自动为被引用>=2次的死链生成 stub 卡片")
    parser.add_argument("--stub-dir", default=None,
                        help="Stub 卡片存放目录（默认 wiki/concepts/）")
    args = parser.parse_args()

    wiki_dir = args.wiki
    stub_dir = args.stub_dir or os.path.join(wiki_dir, 'concepts')

    paths, contents = scan_all_md(wiki_dir)

    # --- 1. 死链检测 ---
    broken_counter = Counter()
    broken_sources = {}  # target -> [source basenames]
    in_degree = Counter()

    for basename, content in contents.items():
        matches = WIKILINK_RE.findall(content)
        for m in matches:
            target = m.split('|')[0].split('#')[0].strip()
            if not target:
                continue
            in_degree[target] += 1
            if target not in paths:
                broken_counter[target] += 1
                broken_sources.setdefault(target, []).append(basename)

    print("═══════════════════════════════════════")
    print("  📋 Obsidian Wiki 健康检查报告")
    print("═══════════════════════════════════════\n")

    if not broken_counter:
        print("✅ 没有死链，所有双向链接指向均存在。\n")
    else:
        print(f"⚠️ 发现 {len(broken_counter)} 个死链（被引用但不存在的概念）：")
        for target, count in broken_counter.most_common(20):
            sources_str = ", ".join(broken_sources[target][:3])
            if len(broken_sources[target]) > 3:
                sources_str += " 等"
            print(f"   [[{target}]] — 引用 {count} 次 (来自: {sources_str})")
        print()

    # --- 2. 孤立页面检测 ---
    orphans = []
    for basename in paths:
        if basename.lower() in ('readme', 'index', 'dashboard'):
            continue
        if in_degree.get(basename, 0) == 0:
            orphans.append(basename)

    if orphans:
        print(f"🏝️ 发现 {len(orphans)} 个孤立页面（无任何入链）：")
        for o in orphans[:15]:
            print(f"   - {o} ({paths[o]})")
        if len(orphans) > 15:
            print(f"   ... 还有 {len(orphans) - 15} 个")
        print()
    else:
        print("✅ 没有孤立页面，所有卡片至少被引用一次。\n")

    # --- 3. 自动生成 Stub ---
    if args.auto_stub:
        high_priority = [(t, c) for t, c in broken_counter.most_common()
                         if c >= 2]
        if not high_priority:
            print("💡 没有需要自动生成 stub 的高频死链。")
            return

        if not os.path.exists(stub_dir):
            os.makedirs(stub_dir, exist_ok=True)

        created = 0
        for target, count in high_priority:
            stub_path = os.path.join(stub_dir, f"{target}.md")
            if os.path.exists(stub_path):
                continue
            sources = broken_sources.get(target, [])
            backlinks = "\n".join(f"- [[{s}]]" for s in sources)
            stub_content = f"""---
type: concept
maturity: stub
date: {date.today().isoformat()}
tags: [auto-generated, needs-review]
aliases: []
---

# {target}

> [!WARNING]
> 本页面由知识库健康检查引擎自动生成（Stub），内容待补充。
> 被以下 {count} 篇文章引用。

## 反向链接
{backlinks}

## 待补充内容
<!-- 请在此处填入或请求 AI 补充该概念的详细描述 -->
"""
            try:
                with open(stub_path, 'w', encoding='utf-8') as f:
                    f.write(stub_content)
                created += 1
                print(f"   📝 已创建 stub: {stub_path}")
            except Exception as e:
                print(f"   ❌ 创建失败 {stub_path}: {e}")

        print(f"\n✅ 共自动创建 {created} 个 stub 占位卡片。")


if __name__ == "__main__":
    main()
