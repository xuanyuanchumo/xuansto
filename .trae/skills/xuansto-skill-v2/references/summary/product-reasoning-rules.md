# 产品类型推理规则数据库

## Core Points
- 包含161种产品类型的UI推理规则，供Design System Generator Agent使用
- 每种产品类型包含UI分类规则、推荐风格、推荐配色行业和反模式
- 推理引擎流程：输入产品关键词→匹配UI分类规则→确定设计方向→选择风格和配色
- Agent应基于产品描述按需搜索，不预加载全部数据

## Applicable Scenarios
- Design System Generator Agent推理产品UI设计方向
- 根据产品类型自动推荐风格和配色
- 验证UI设计是否符合行业反模式检查
