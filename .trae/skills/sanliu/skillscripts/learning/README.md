# 三省六部技能 - 自动学习系统

## 概述

本模块实现了完整的自动学习能力，包括模式识别、最佳实践提取、知识库管理和知识应用四大核心功能。

## 创建的文件

### 核心模块

1. **[pattern_recognizer.py](file:///d:/Projects/TraeProjects/skiller/.trae/skills/sanliu/skillscripts/learning/pattern_recognizer.py)** - 模式识别器
   - 成功模式识别算法
   - 失败模式识别算法
   - 优化模式识别算法
   - 模式置信度评估

2. **[best_practice_extractor.py](file:///d:/Projects/TraeProjects/skiller/.trae/skills/sanliu/skillscripts/learning/best_practice_extractor.py)** - 最佳实践提取器
   - 代码最佳实践提取
   - 架构最佳实践提取
   - 流程最佳实践提取
   - 实践质量评估

3. **[knowledge_updater.py](file:///d:/Projects/TraeProjects/skiller/.trae/skills/sanliu/skillscripts/learning/knowledge_updater.py)** - 知识库更新器
   - 知识自动分类
   - 知识质量评估
   - 知识去重和合并
   - 知识版本管理

4. **[knowledge_application_engine.py](file:///d:/Projects/TraeProjects/skiller/.trae/skills/sanliu/skillscripts/learning/knowledge_application_engine.py)** - 知识应用引擎
   - 知识检索和匹配
   - 知识应用建议生成
   - 知识应用效果跟踪
   - 知识反馈收集

5. **[auto_learner.py](file:///d:/Projects/TraeProjects/skiller/.trae/skills/sanliu/skillscripts/learning/auto_learner.py)** - 自动学习主控制器
   - 整合所有组件
   - 学习流程管理
   - 学习报告生成

### 辅助文件

6. **[__init__.py](file:///d:/Projects/TraeProjects/skiller/.trae/skills/sanliu/skillscripts/learning/__init__.py)** - 包初始化文件
7. **[example_usage.py](file:///d:/Projects/TraeProjects/skiller/.trae/skills/sanliu/skillscripts/learning/example_usage.py)** - 使用示例

## 实现的功能

### 1. 增强模式识别器

#### 成功模式识别
- 自动识别高成功率的执行模式
- 提取成功指标（成功率、质量分数、性能分数）
- 计算模式置信度（very_high, high, medium, low, very_low）
- 模式特征提取（代码结构、执行上下文、性能指标、时间特征）

#### 失败模式识别
- 识别失败执行模式
- 提取失败指标（失败率、错误数量、错误类型、严重程度）
- 错误特征分析（错误类型、错误消息、堆栈跟踪）
- 失败模式聚类

#### 优化模式识别
- 对比优化前后的数据
- 计算改进率、性能提升、质量提升、效率提升
- 识别优化模式特征
- 优化效果评估

#### 模式置信度评估
- 综合评估模式可靠性
- 考虑出现次数、时效性、稳定性
- 动态更新置信度分数
- 模式一致性检查

### 2. 完善最佳实践提取器

#### 代码最佳实践提取
- 从成功模式中提取代码实践
- 评估代码质量（复杂度、测试覆盖率、文档完整性）
- 生成实施步骤
- 识别收益和风险

#### 架构最佳实践提取
- 提取架构设计模式
- 评估架构质量（模块化、可扩展性、可维护性）
- 生成架构改进建议
- 识别架构风险

#### 流程最佳实践提取
- 提取工作流程优化实践
- 评估流程质量（自动化程度、效率、可靠性）
- 生成流程改进步骤
- 识别流程风险

#### 实践质量评估
- 多维度质量评估
- 考虑证据数量、验证次数、影响力、适用性
- 质量等级划分（excellent, good, acceptable, poor, critical）
- 实践验证机制

### 3. 优化知识库更新机制

#### 知识自动分类
- 基于关键词和内容的智能分类
- 支持8种知识类别（pattern, practice, solution, lesson, template, reference, guideline, anti_pattern）
- 分类规则可配置
- 分类置信度评估

#### 知识质量评估
- 综合质量评分算法
- 考虑应用次数、成功率、访问频率、时效性
- 质量等级自动调整
- 质量趋势跟踪

#### 知识去重和合并
- 多层次去重检测（标题、内容、相似度）
- 智能合并策略（merge, replace, append, version）
- 合并冲突解决
- 合并历史记录

#### 知识版本管理
- 完整的版本控制系统
- 版本回滚功能
- 变更历史跟踪
- 版本差异对比

### 4. 创建知识应用引擎

#### 知识检索和匹配
- 多维度相关性计算
- 上下文相似度匹配
- 标签和类别匹配
- 智能排序和过滤

#### 知识应用建议生成
- 基于上下文生成建议
- 相关性评分
- 适用性评估
- 优先级排序
- 风险识别

#### 知识应用效果跟踪
- 应用前后指标对比
- 改进率计算
- 有效性评分
- 问题识别
- 经验教训提取

#### 知识反馈收集
- 多类型反馈（positive, negative, neutral, suggestion）
- 评分系统
- 改进建议收集
- 反馈应用到知识库

## 使用示例

### 基础用法

```python
from learning import AutoLearner, LearningMode

# 创建自动学习器
learner = AutoLearner(learning_mode=LearningMode.ACTIVE)

# 从执行中学习
execution_data = {
    "status": "success",
    "success_rate": 0.95,
    "quality_score": 0.88,
    "code": "def example():\n    return True",
    "file_path": "example.py"
}

result = learner.learn_from_execution(execution_data)
print(f"识别的模式数: {len(result['patterns'])}")
```

### 模式识别

```python
from learning import PatternRecognizer, PatternType, PatternConfidence

recognizer = PatternRecognizer()

# 识别成功模式
success_data = {
    "status": "success",
    "success_rate": 0.92,
    "quality_score": 0.85
}

pattern = recognizer.recognize_success_pattern(success_data)

# 获取高质量模式
patterns = recognizer.get_patterns_by_type(
    PatternType.SUCCESS,
    min_confidence=PatternConfidence.HIGH
)
```

### 最佳实践提取

```python
from learning import BestPracticeExtractor, PracticeCategory

extractor = BestPracticeExtractor()

# 提取代码最佳实践
practice = extractor.extract_code_practice(
    pattern,
    code_analysis={"complexity": 8, "test_coverage": 85}
)

# 按类别获取实践
practices = extractor.get_practices_by_category(PracticeCategory.CODE)
```

### 知识管理

```python
from learning import KnowledgeUpdater, UpdateStrategy

updater = KnowledgeUpdater()

# 添加知识
entry = updater.add_knowledge({
    "title": "Python优化实践",
    "content": {"pattern": "list_comprehension"},
    "tags": ["python", "optimization"],
    "quality_score": 0.85
})

# 更新知识
updated = updater.update_knowledge(
    entry.entry_id,
    {"tags": ["python", "optimization", "best-practice"]},
    UpdateStrategy.VERSION
)

# 搜索知识
results = updater.search_knowledge("Python", limit=5)
```

### 知识应用

```python
from learning import (
    KnowledgeApplicationEngine,
    ApplicationContext,
    FeedbackType
)

engine = KnowledgeApplicationEngine()

# 创建应用上下文
context = ApplicationContext(
    context_id="ctx-001",
    project_type="web_application",
    technology_stack=["python", "django"],
    current_state={"performance": 75},
    objectives=["improve_performance"],
    constraints=["maintain_compatibility"]
)

# 生成建议
suggestions = engine.generate_suggestions(context, max_suggestions=3)

# 跟踪应用效果
result = engine.track_application_effect(
    suggestion.suggestion_id,
    metrics_before={"performance": 75},
    metrics_after={"performance": 85}
)

# 收集反馈
feedback = engine.collect_feedback(
    knowledge_id=suggestion.knowledge_id,
    result_id=result.result_id,
    feedback_type=FeedbackType.POSITIVE,
    rating=4,
    comment="效果很好"
)
```

### 学习报告

```python
# 生成学习报告
report = learner.generate_learning_report(period_days=7)

print(f"识别的模式数: {report.patterns_recognized}")
print(f"提取的实践数: {report.practices_extracted}")
print(f"有效性分数: {report.effectiveness_score:.2f}")

for rec in report.recommendations:
    print(f"建议: {rec}")
```

## 学习模式

系统支持四种学习模式：

1. **PASSIVE（被动模式）**
   - 高阈值，只学习高质量模式
   - 不自动提取实践
   - 不自动应用知识

2. **ACTIVE（主动模式）** - 默认
   - 中等阈值
   - 自动提取实践
   - 不自动应用知识

3. **AGGRESSIVE（激进模式）**
   - 低阈值，快速学习
   - 自动提取实践
   - 自动应用知识

4. **CUSTOM（自定义模式）**
   - 可配置所有参数
   - 灵活调整学习策略

## 统计信息

每个组件都提供统计信息：

```python
# 模式识别统计
pattern_stats = recognizer.get_statistics()

# 最佳实践统计
practice_stats = extractor.get_statistics()

# 知识管理统计
knowledge_stats = updater.get_statistics()

# 知识应用统计
application_stats = engine.get_statistics()

# 整体状态
status = learner.get_status()
```

## 数据持久化

所有组件都支持数据持久化：

```python
# 创建时指定存储路径
learner = AutoLearner(
    storage_dir="./learning_data",
    learning_mode=LearningMode.ACTIVE
)

# 导出学习数据
learner.export_learning_data("learning_export.json")

# 导入学习数据
learner.import_learning_data("learning_export.json", merge=True)
```

## 运行示例

```bash
cd d:\Projects\TraeProjects\skiller\.trae\skills\sanliu\skillscripts\learning
python example_usage.py
```

## 技术特性

- **线程安全**：所有组件都使用锁机制保证线程安全
- **类型安全**：使用 Python 类型注解和 dataclass
- **可扩展**：模块化设计，易于扩展新功能
- **可配置**：所有阈值和参数都可配置
- **持久化**：支持 JSON 格式的数据持久化
- **日志记录**：完整的日志记录系统

## 版本

- 版本：1.0.0
- 创建日期：2026-04-01
- 作者：Trae AI Assistant
