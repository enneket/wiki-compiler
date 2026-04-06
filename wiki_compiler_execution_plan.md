# Wiki Compiler 系统执行计划

## 目标
完成wiki-compiler系统的改进和验证

## 任务列表

1. 创建测试环境
   - 设置测试wiki目录
   - 设置测试原始资料目录
   - 创建测试内容文件

2. 运行增量编译清单同步
   - 执行sync_manifest.py检测新资料
   - 验证Ledger更新功能

3. 测试知识节点采样功能
   - 运行wiki_dreamer.py进行知识节点采样
   - 验证Gap/Stale/Bridge/Tag评分算法
   - 检查输出格式和内容

4. 测试自动标签应用功能
   - 运行wiki_dreamer.py --apply-tags
   - 验证标签正确应用到文章frontmatter
   - 检查有无frontmatter文章的处理

5. 运行健康检查功能
   - 执行health_vis_engine.py
   - 验证死链检测和孤立页面识别

6. 验证系统集成
   - 确保所有组件协同工作
   - 检查中文输出
   - 验证缩进问题修复

## 验证标准
- 所有Python脚本能够正常执行
- wiki_dreamer.py的--apply-tags标志工作正确
- 所有输出使用中文
- 无缩进错误
- 知识节点采样逻辑正确
- 健康检查功能正常