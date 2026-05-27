# 字体配对数据库

## Core Points
- 包含57组字体配对，按情绪分类组织，每组含标题字体、正文字体、情绪标签、最佳场景
- 搜索策略：按情绪关键词搜索，BM25排序权重：情绪匹配(40%)+场景匹配(35%)+行业适配(25%)
- 每次搜索返回Top 3组配对，选择后需验证字体加载性能(标题≤2字重，正文≤3字重)
- 所有字体提供Google Fonts链接，确保可免费商用

## Applicable Scenarios
- Design System Generator Agent推理选择字体配对
- UI Designer Agent为项目选择合适的字体方案
- 验证字体加载性能和可访问性
