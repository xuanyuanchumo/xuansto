# 数据库指南参考文档

## Core Points
- 命名规范：表名snake_case复数、列名snake_case、索引idx_表_列、外键fk_表_引用表
- 索引策略：B-tree默认、GIN用于JSONB/全文搜索、部分索引过滤常用查询条件
- 查询优化：避免SELECT *、使用EXPLAIN分析、N+1问题用JOIN或批量查询、分页用游标
- 迁移管理：版本化SQL文件、向前兼容、可回滚、生产环境迁移前备份

## Applicable Scenarios
- Database Engineer Agent设计数据库Schema和索引
- DBA Agent优化查询性能和执行迁移
- Code Reviewer Agent检查SQL代码规范
