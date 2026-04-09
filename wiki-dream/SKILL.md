---
name: wiki-dream
description: Wiki Compiler 沉思/做梦机制。当用户要求"做梦"或"沉思"时触发。静默巡逻、深层上下文理解与关系映射，在看似不相关的知识点之间捕捉跨界灵感。
version: 2.1.0
emoji: 🌙
os: ["macos", "linux", "windows"]
author: zhangpelf
repository: https://github.com/zhangpelf/wiki-compiler
---

# Wiki Dreamer (夜间的潜意识漫游者) 🌙

> "当您休息时，Agent 在巡逻。它会在看似不相关的知识点之间进行潜意识漫游，捕捉跨界灵感。"

## 触发条件

当用户发出 `/wiki-dream` 或要求"做梦"、"沉思"时启动此流程。

## 前置变量

仅需 **`WIKI_DIR`**（知识库根目录）。如果上下文未提供，必须询问用户。

---

## 工作流

### 第一阶段：巡逻与拾遗 (Night Watcher)

1. 运行扫描脚本：
   ```
   python3 ../scripts/sync_manifest.py --raw "$RAW_DIR" --wiki "$WIKI_DIR"
   ```
   （如果上下文中存在 `RAW_DIR`）

2. 如果扫描显示有**待处理的增量名单**（漏网遗忘的数据），必须主动向用户发出提醒并请求授权：
   > "提示：发现有一些你丢进去但遗忘处理的原始资料（包含 XXX），是否需要我借助现在的做梦时间顺手帮你把它们编译入库？"

   若用户同意，走 `/wiki-compiler` 工作流。

### 第二阶段：沉思与灵感连接 (Dreaming & Latent Walk)

3. 运行脚本：
   ```
   python3 ../scripts/wiki_dreamer.py --wiki "$WIKI_DIR" --limit 3
   ```

4. 脚本将返回 3 篇系统随机采样的不相关老文章的绝对路径。

5. **沉思与研读**：完整调阅这些卡片并寻找隐蔽的链接。作为极具创意的研究型智能体，在这几个风马牛不相及的碎片之间，洞察它们的"共有结构"和"创新性结合点"。

6. **结晶凝练**：新建一篇命名如 `WIKI_DIR/concepts/Insight-新理念-<日期>.md` 的文章。记录本次"梦境"带来的灵感碰撞，并通过使用 `[[文章A]]`、`[[文章B]]` 等将新 Insight 打造为跨领域的集散节点。

### 第三阶段：健康检查 (Health Check)

7. 运行：
   ```
   python3 ../scripts/health_vis_engine.py --wiki "$WIKI_DIR" --auto-stub
   ```

8. 该脚本会检测死链、孤立页面，并为被高频引用的死链自动生成 Stub 占位卡片（带 `maturity: stub` 标记）。

9. 将检查报告中有价值的发现汇总告知用户。

---

## 元数据约定

生成的 Insight 卡片必须包含 YAML Frontmatter：

```yaml
---
type: insight
maturity: draft
date: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [梦境, 灵感, 跨领域]
aliases: [别名]
---
```

## 严格约束

- **输出语言**：必须以中文交互输出。
- **不篡改原始数据**：永远不要修改 `wiki/` 目录下的现有卡片内容。
- **溯源关联**：新建的 Insight 必须用 `[[双向链接]]` 关联到参与碰撞的原卡片。
