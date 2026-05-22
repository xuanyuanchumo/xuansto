---
name: database-design-si
parent: universal-devops
department: gongbu
province: shangshusheng
description: |
  数据库设计司 - 工部·水部司

  【职责】数据模型设计、ER图、索引优化、迁移脚本生成

  【触发条件】
  - 数据库表结构设计
  - ER模型建立和优化
  - 数据迁移脚本编写

  【能力】
  - ER图自动生成
  - 正范式化设计
  - 索引策略建议
  - 迁移脚本版本管理
---

# 数据库设计司 (Database Design Si)

> 尚书省 · 工部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| ER图绘制 | HYBRID_ASSISTED | 86% | AI辅助生成初稿 + 人工优化关系 |
| DDL语句生成 | SCRIPTED_BATCH | 95% | 基于ER模型自动生成CREATE TABLE |
| 迁移脚本编写 | SCRIPTED_BATCH | 92% | Alembic/Flyway/Liquibase标准化 |
| 索引优化建议 | AUTONOMOUS_MANUAL | 76% | 需要理解查询模式和数据分布 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取现有Schema、查询语句、性能指标）
- **写操作**: Write, SearchReplace（编写DDL/DML、迁移脚本、索引定义）
- **批量操作**: Schema迁移工具(Alembic/Flyway)、ER图生成器(dbdiagram.io)、SQL格式化工具
- **验证操作**: SQL Linter(sqlfluff)、Schema校验器、EXPLAIN ANALYZE分析

### 注意事项
- ⚠️ 数据库变更必须通过迁移脚本：禁止直接在生产环境执行DDL，所有变更可追溯可回滚
- ⚠️ 大表操作要谨慎：ALTER TABLE在大表上可能长时间锁表，需要在线DDL工具(pt-osc/gh-ost)
- ✅ 采用"数据库即代码"(Database as Code)：Schema定义纳入版本控制，与环境代码同等对待
- ✅ 遵循范式化原则但不教条：适度反范式化以提升查询性能是合理的工程权衡

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| MIGRATION | /migrations/ (迁移脚本目录) | SEQUENTIAL (有序执行) |
| SCHEMA | 数据库Schema元数据 | READ_ONLY (只读查询) |
| BACKUP | 数据库备份文件 | IMMUTABLE (不可修改) |
| CONNECTION | 数据库连接串 | ENCRYPTED + ACCESS_CONTROLLED |
| DOCUMENT | ER图和数据字典 | VERSION_CONTROLLED |

### 竞争规避策略
1. **迁移顺序锁**: 迁移脚本按时间戳排序顺序执行，确保依赖关系正确
2. **环境隔离策略**: 开发/测试/生产使用独立数据库实例，避免互相干扰
3. **蓝绿部署配合**: Schema变更配合应用蓝绿部署，确保零停机迁移

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- Schema变更完全可追溯：每条迁移脚本记录who/when/why，支持任意时间点回滚
- 数据字典公开：所有表的字段含义、类型、约束关系有完整的文档说明
- 性能基线透明：关键查询的执行计划、耗时基线、索引使用情况可视化展示

### OpenClaude 编排
- 智能Schema设计：根据业务实体关系自动推荐合理的表结构和外键设计
- 迁移影响分析：评估Schema变更对现有应用代码的影响范围，提前预警
- SQL性能优化建议：基于慢查询日志和执行计划分析，自动给出索引优化建议

### Claw-Code 契约驱动
- Schema版本化管理：每个迁移脚本对应唯一的版本号，支持前进和回滚
- 变更前备份强制：生产环境Schema变更前必须完成全量备份并通过恢复验证
- 数据完整性约束：NOT NULL/UNIQUE/FOREIGN KEY等约束必须在迁移中明确定义
