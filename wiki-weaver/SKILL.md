---
name: wiki-weaver
description: Wiki Compiler Map-Reduce 学术综述。当用户需要对某个复杂主题进行跨多篇文献的综合论证时触发。深度跨文献综述，拒绝幻觉，句级溯源。
version: 2.1.0
emoji: 🕸️
os: ["macos", "linux", "windows"]
author: zhangpelf
repository: https://github.com/zhangpelf/wiki-compiler
---

# Wiki Weaver (跨文献编织者) 🕸️

> "百篇文献一键并行处理。每一句陈述都必须带上 `[[原始文献]]` 引用。杜绝幻觉，严谨到变态。"

## 触发条件

当用户发出 `/wiki-weaver` 或要求"综述"、"编织"、"Map-Reduce"时启动此流程。

## 前置变量

需要 **`WIKI_DIR`**（知识库根目录）和**搜索词/主题**。如果未提供，必须询问。

---

## 工作流

### 第一阶段：Map (全库检索与精读)

1. 运行脚本：
   ```
   python3 ../scripts/wiki_weaver.py --wiki "$WIKI_DIR" --query "搜索词"
   ```

2. 该脚本将利用 BM25 算法筛选出库内相关度最高的研究片段路径。

3. 获得一组文件绝对路径列表。如果文章超长，请独立分段读取。记录每一条关键结论，并标注原始文件来源。

### 第二阶段：Reduce (分而治之)

4. 对每篇文献进行深度阅读，提炼核心论点、证据和结论。

5. 按照主题维度对所有文献进行分类整理。

### 第三阶段：Synthesis (句级溯源撰写)

6. 生成一篇全新的综述卡片存入 `WIKI_DIR/concepts/`。

7. **强制要求**：综述中的每一句针对事实的客观陈述，末尾必须带有 `[[原始文献名]]` 形式的引用。严禁出现任何无出处的结论。

8. 严禁出现任何幻觉陈述。所有观点必须可验证。

### 第四阶段：验证

9. 自检所有引用是否真实存在于知识库内。

10. 检查链接完整性，确保无死链。

---

## 元数据约定

生成的综述卡片必须包含 YAML Frontmatter：

```yaml
---
type: concept
maturity: authoritative
date: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [综述, 跨领域]
project: 所属项目名
sources: [原始文献路径列表]
---
```

## 严格约束

- **输出语言**：必须以中文交互输出。
- **句级溯源**：每一句事实陈述必须有 `[[引用]]`，无引用则视为幻觉。
- **防幻觉裁判**：遇到知识盲区自动生成 `⚠️ Definition_Needed` 标记，强制进行二元判别。
- **不篡改原始数据**：永远不要修改 `wiki/` 目录下的现有卡片内容。
