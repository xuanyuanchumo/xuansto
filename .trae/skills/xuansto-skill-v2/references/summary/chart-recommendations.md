# 图表类型推荐数据库

## Core Points
- 包含25种图表类型，按用途分5类：比较(5种)、趋势、分布、关系、流程
- 每种图表包含使用场景、数据要求和D3/Chart.js/ECharts框架实现提示
- 搜索策略：按数据用途关键词搜索，BM25排序权重：用途匹配(40%)+数据结构匹配(35%)+场景匹配(25%)
- 每次搜索返回Top 3图表类型供选择，Agent应按需搜索不预加载

## Applicable Scenarios
- Frontend Developer Agent选择合适的图表类型实现数据可视化
- Design System Generator Agent推荐图表组件
- 数据可视化需求分析和图表选型
