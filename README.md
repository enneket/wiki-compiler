<div align="center">
  <h1>🧠 Wiki Compiler: AI-Native Agentic Knowledge Base</h1>
  <p><strong>复刻 Andrej Karpathy 的 LLM 知识库理念，融合 Claude Code 的深层做梦机制</strong></p>
  <p>完全由 AI 自主驾驶、运维、除草与沉思的 Obsidian 第二大脑引擎。</p>
</div>

---

## 🌟 为什么创造它？

Andrej Karpathy 曾在推特中分享了一个极其高效的现代研究流：**不要再自己痛苦地写笔记！**把所有的论文、文章、截图粗暴地扔进一个 `raw/` 文件夹中，然后让 LLM 作为“知识库编译器 (Wiki Compiler)”，自动把它们提炼、打双链、分类到结构化的 Obsidian 知识库中。

我们不仅 1:1在本地实现了 Karpathy 的构想，甚至走得更远——我们为其引入了源自最前沿 Agent 架构的 **"Dreaming (做梦/沉思) 机制"** 以及硬核的 **Idempotent (幂等去重扫描)**。

这不再只是一堆 Python 脚本，而是一个 **活着的、会自我反思的知识管家**。

## 🔥 核心革命性特性

### 1. 🛡️ 幂等增量编译 (Idempotent Sync)
告别 AI 重复造词和内容滚雪球的噩梦！内置强大的哈希防重叠引擎。
无论你触发多少次编译指令，系统只会揪出 `raw/` 文件夹下**新增或修改过**的文件。丢入资料，忘掉它，执行 `/wiki-compiler`——剩下的交给 AI。

### 2. 🌌 Claude 式"做梦"机制 (Night Watcher & Latent Walk)
当你的大模型闲置时，不如让它做个梦（通过 `/wiki-dream` 唤醒）：
- **夜间巡逻 (Night Watch)**：它会首先帮你扫描并捞起那些被你随手扔弃但“遗忘处理”的生数据，主动问你：“主人，需要顺手帮你把这 3 份文件入库吗？”
- **灵感跨界 (Latent Connection)**：系统独创的 **Gap/Stale/Bridge 三维加权算法**不再是掷骰子，它会挑出被遗忘的“幽灵卡片”或“高频交通枢纽”，强制 AI 在风马牛不相及的知识碎片中寻找关联，结晶产生出全新的洞见 (Insight)！

### 3. 🤔 Q&A 回填的自生长闭环
每一次你用 Agent 询问“深度整合问题”的心血，都不会再消失在滚动的历史对话栏里。模型将会触发主动询问：_“本次回答非常有价值，是否需要我将其回填为永久知识节点？”_

### 4. 🚀 Obsidian 原生“降维”可视化
不需要外挂复杂的图表工具，AI 会直接生成带 Obsidian 专属特性的 Markdown：
- **自带 Dataview Metadata**：所有笔记强绑定 `Maturity` (成熟度：stub -> reviewed) 等生命周期 YAML 标签。
- **自动伴生 Marp 幻灯片**：针对宏大的知识主题，AI 顺手丢一份 `.marp.md`，点开网页一键 PPT 演讲，逼格拉满！
- **Auto-Stub 自愈引擎**：一键断链体检，自动补全缺失的空白占位卡。

---

## 🛠 工作流机理

```mermaid
graph TD
    A[🗂️ 粗暴扔进 raw/ 目录] --> B{/wiki-compiler};
    B -->|防重检查: sync| C[🤖 研读、抽取实体、写成 MD];
    C --> D[💾 存入 Obsidian wiki/];
    D --> E[📊 生成 YAML / Mermaid / Marp];
    
    Z[💤 Agent 休息时间] -.-> F{/wiki-dream};
    F -.-> G[1. 捕捉遗忘的 raw 数据];
    F -.-> H[2. 三维提取知识死角];
    H -.-> I[⭐ 结晶出前沿洞察 Insight.md];
```

## 🚀 极简起手式 (Quick Start)

1. 下载或 Clone 本仓库作为你的 Agent Skills 之一。
2. 告诉你的 Agent 你的 `raw/` 资料库绝对路径以及 `wiki/` 知识库绝对路径。
3. 对话框内输入：`/wiki-compiler`。
4. 躺平，看看 AI 是如何像真正的学者一样为你整理书架的。
5. 偶尔输入 `/wiki-dream`，迎接思维碰撞的彩蛋！

> _"I rarely touch the wiki directly. It's the domain of the LLM." – Andrej Karpathy_
> **现在，你也能拥有这句话背后的底气。**

---

### *📜 附文：作为 Agent Skill 的执行规范*
> 下方内容为系统 `SKILL.md` 的原文架构，指导任意大语言模型进行本系统的运维工作（LLM Prompting Directive）：

*(详见当前库内的 `SKILL.md`)*
