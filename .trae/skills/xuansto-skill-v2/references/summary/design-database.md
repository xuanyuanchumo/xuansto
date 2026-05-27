# UI风格设计数据库

## Core Points
- 定义67种UI风格，每种含名称、关键词、最佳场景、性能评级、可访问性评级和框架实现提示
- 按需搜索策略：先按类别定位再按关键词匹配，BM25排序权重：关键词(40%)+场景(30%)+行业(30%)
- 每次搜索返回Top 5风格供推理引擎排序
- 与Design System Generator Agent集成，用于风格推理选择

## Applicable Scenarios
- Design System Generator Agent推理选择UI风格
- UI Designer Agent参考风格设计界面
- 前端项目风格选型和设计系统建立
