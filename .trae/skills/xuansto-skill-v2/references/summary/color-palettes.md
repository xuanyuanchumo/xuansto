# 行业配色方案数据库

## Core Points
- 包含161套行业配色方案，每套含主色、辅色、CTA色、背景色、文字色及使用场景
- 按行业分类：SaaS(15套)、金融、医疗、教育、电商等
- 搜索策略：按行业关键词搜索，BM25排序权重：行业匹配(50%)+场景匹配(30%)+色彩协调度(20%)
- 每次搜索返回Top 3配色，选择后必须通过反模式过滤

## Applicable Scenarios
- Design System Generator Agent按行业匹配配色方案
- UI Designer Agent选择项目配色
- 验证配色方案的WCAG AA对比度合规性
