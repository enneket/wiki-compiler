#!/usr/bin/env python3
"""
轻量级 Wiki 全文搜索 CLI (BM25 风格)
供 LLM Agent 在回答复杂问题前"先查再答"，避免盲读所有文件。

用法:
  python3 query_wiki.py --wiki /path/to/wiki --query "强化学习 奖励函数" --top 5
"""
import os
import re
import math
import argparse
from collections import Counter

STOPWORDS_ZH = set("的了在是我有和人这中大为上个国不以会也".split() + list("到说时要就出产可对"))


def tokenize(text):
    """极简分词：英文按空格/标点切，中文按单字切（粗糙但够用）。"""
    # 先把英文单词抽出来
    en_tokens = re.findall(r'[a-zA-Z0-9_\-]+', text.lower())
    # 中文按单字（bigram 效果更好但这里保持简单）
    zh_chars = re.findall(r'[\u4e00-\u9fff]', text)
    # 中文 bigram
    zh_bigrams = [zh_chars[i] + zh_chars[i + 1] for i in range(len(zh_chars) - 1)]
    all_tokens = en_tokens + zh_chars + zh_bigrams
    return [t for t in all_tokens if t not in STOPWORDS_ZH and len(t.strip()) > 0]


def load_corpus(wiki_dir):
    """加载 wiki 目录下所有 md 文件。"""
    docs = {}
    for root, dirs, files in os.walk(wiki_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if not f.endswith('.md') or f.endswith('.marp.md'):
                continue
            fp = os.path.join(root, f)
            try:
                content = open(fp, 'r', encoding='utf-8').read()
                docs[fp] = content
            except Exception:
                pass
    return docs


def bm25_search(query_tokens, docs_tokens, k1=1.5, b=0.75):
    """BM25 排序。返回 [(doc_path, score)]。"""
    N = len(docs_tokens)
    if N == 0:
        return []

    # 平均文档长度
    avg_dl = sum(len(toks) for toks in docs_tokens.values()) / N

    # 每个 query token 的 IDF
    idf = {}
    for qt in set(query_tokens):
        df = sum(1 for toks in docs_tokens.values() if qt in toks)
        if df > 0:
            idf[qt] = math.log((N - df + 0.5) / (df + 0.5) + 1)
        else:
            idf[qt] = 0

    scores = []
    for path, toks in docs_tokens.items():
        tf_counter = Counter(toks)
        dl = len(toks)
        score = 0.0
        for qt in set(query_tokens):
            if qt not in idf or idf[qt] == 0:
                continue
            tf = tf_counter.get(qt, 0)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * dl / avg_dl)
            score += idf[qt] * numerator / denominator
        scores.append((path, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def snippet(content, query_tokens, window=80):
    """从文档中提取包含查询词的上下文片段。"""
    content_lower = content.lower()
    best_pos = -1
    for qt in query_tokens:
        pos = content_lower.find(qt)
        if pos != -1:
            best_pos = pos
            break
    if best_pos == -1:
        return content[:150].replace('\n', ' ').strip() + "..."

    start = max(0, best_pos - window)
    end = min(len(content), best_pos + len(qt) + window)
    s = content[start:end].replace('\n', ' ').strip()
    if start > 0:
        s = "..." + s
    if end < len(content):
        s = s + "..."
    return s


def main():
    parser = argparse.ArgumentParser(description="Wiki 全文搜索 (BM25)")
    parser.add_argument("--wiki", required=True, help="Wiki 目录")
    parser.add_argument("--query", required=True, help="搜索查询")
    parser.add_argument("--top", type=int, default=5, help="返回结果数")
    args = parser.parse_args()

    docs = load_corpus(args.wiki)
    if not docs:
        print("⚠️ 知识库为空或路径错误。")
        return

    query_tokens = tokenize(args.query)
    if not query_tokens:
        print("⚠️ 查询词为空。")
        return

    docs_tokens = {path: tokenize(content) for path, content in docs.items()}
    results = bm25_search(query_tokens, docs_tokens)

    # 过滤掉零分结果
    results = [(p, s) for p, s in results if s > 0]

    if not results:
        print(f"🔍 没有找到与 \"{args.query}\" 相关的知识库条目。")
        return

    top = results[:args.top]
    print(f"🔍 搜索 \"{args.query}\" — 共找到 {len(results)} 条结果，展示前 {len(top)} 条：\n")
    for i, (path, score) in enumerate(top, 1):
        rel = os.path.relpath(path, args.wiki)
        snip = snippet(docs[path], query_tokens)
        print(f"  {i}. [{rel}] (相关度: {score:.2f})")
        print(f"     {snip}")
        print()


if __name__ == "__main__":
    main()
