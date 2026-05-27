# Design Token 系统架构参考文档

## Core Points
- Design Token是连接设计与开发的桥梁，实现设计决策集中管理、跨平台转换和自动化交付
- 三层分类模型：Global Tokens(全局原始值)→Alias Tokens(语义化别名)→Component Tokens(组件级令牌)
- Style Dictionary工具链：定义JSON/YAML→编译转换→输出多平台格式(CSS/JS/Swift/Kotlin)
- 跨平台转换策略：Web(CSS Variables)、React(Native模块)、桌面(平台原生API)

## Applicable Scenarios
- Design System Generator Agent输出Design Token
- Frontend Stylist Agent实现主题系统和Token消费
- 跨平台项目统一设计令牌管理
