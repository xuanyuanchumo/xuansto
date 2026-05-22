# 知识库管理系统说明文档

> 📚 **知识积累，智慧共享** - 通过知识库管理实现跨项目知识共享和持续学习

---

## 概述

知识库管理系统是 sanliu 技能的核心知识管理组件，负责存储、检索、共享和更新系统学习到的知识。该系统支持跨项目知识共享，使得一个项目学习到的经验可以被其他项目复用。

### 核心特征

- **知识存储**：结构化存储各类知识条目
- **智能检索**：基于语义和标签的知识检索
- **跨项目共享**：支持多项目间的知识共享
- **持续学习**：自动从修复和优化中学习
- **知识质量评估**：评估知识的可靠性和适用性

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          知识库管理系统架构                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      知识存储层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 知识条目库   │  │ 索引数据库   │  │ 向量存储库   │              │   │
│   │  │  Knowledge   │  │   Index DB   │  │ Vector Store │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      知识管理层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 知识管理器   │  │ 知识检索器   │  │ 知识更新器   │              │   │
│   │  │   Manager    │  │   Retriever  │  │   Updater    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      知识学习层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 模式识别器   │  │ 最佳实践提取 │  │ 质量评估器   │              │   │
│   │  │   Pattern    │  │ BestPractice │  │   Quality    │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      知识共享层                                       │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│   │  │ 项目注册器   │  │ 知识同步器   │  │ 权限管理器   │              │   │
│   │  │  Registry    │  │   Sync       │  │   Permission │              │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 知识库管理器

知识库管理器是知识库系统的核心组件，负责知识的存储、检索和管理。

### 知识条目结构

```json
{
  "id": "KB-20240329-0001",
  "type": "fix_pattern",
  "title": "ImportError 修复模式",
  "description": "当遇到模块导入错误时，检查依赖安装和路径配置",
  "content": {
    "problem_pattern": "ImportError: No module named '(.+)'",
    "solution": "pip install $1 或 检查 PYTHONPATH",
    "code_example": "try:\n    import module\nexcept ImportError:\n    # 处理逻辑",
    "prerequisites": ["Python环境", "pip包管理器"],
    "side_effects": []
  },
  "metadata": {
    "created_at": "2024-03-29T10:00:00",
    "updated_at": "2024-03-29T10:00:00",
    "author": "system",
    "source_project": "project-a",
    "confidence": 0.95,
    "applicability": ["Python", "All"],
    "tags": ["import", "error", "fix", "python"]
  },
  "statistics": {
    "usage_count": 156,
    "success_rate": 0.92,
    "last_used": "2024-03-29T15:30:00",
    "feedback_positive": 145,
    "feedback_negative": 11
  },
  "relations": {
    "parent": null,
    "children": ["KB-20240329-0002"],
    "related": ["KB-20240320-0015", "KB-20240315-0008"]
  }
}
```

### 知识类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `fix_pattern` | 修复模式 | 错误修复方法、解决方案 |
| `best_practice` | 最佳实践 | 代码规范、设计模式 |
| `optimization` | 优化策略 | 性能优化、资源优化 |
| `anti_pattern` | 反模式 | 常见错误、应避免的做法 |
| `configuration` | 配置知识 | 环境配置、参数设置 |
| `workflow` | 工作流程 | 开发流程、部署流程 |

### 使用示例

#### 命令行操作

```bash
python scripts/knowledge_manager.py add \
  --type fix_pattern \
  --title "SQL注入防护模式" \
  --content '{"problem":"SQL注入风险","solution":"使用参数化查询"}' \
  --tags "security,sql,injection"

python scripts/knowledge_manager.py search \
  --query "导入错误修复" \
  --type fix_pattern \
  --limit 10

python scripts/knowledge_manager.py get \
  --id KB-20240329-0001

python scripts/knowledge_manager.py update \
  --id KB-20240329-0001 \
  --content '{"confidence":0.98}'

python scripts/knowledge_manager.py delete \
  --id KB-20240329-0001
```

#### 编程接口

```python
from scripts.knowledge_manager import KnowledgeManager, KnowledgeType

km = KnowledgeManager(knowledge_base_path='./.evolution/knowledge')

knowledge = km.add_knowledge(
    type=KnowledgeType.FIX_PATTERN,
    title="ImportError 修复模式",
    description="模块导入错误的通用修复方法",
    content={
        "problem_pattern": "ImportError: No module named '(.+)'",
        "solution": "pip install $1",
        "code_example": "pip install requests"
    },
    tags=["import", "error", "fix"],
    source_project="my-project"
)

print(f"知识已添加: {knowledge.id}")

results = km.search_knowledge(
    query="导入错误",
    knowledge_type=KnowledgeType.FIX_PATTERN,
    limit=5
)

for result in results:
    print(f"[{result.confidence:.2f}] {result.title}")
    print(f"  {result.description}")

knowledge = km.get_knowledge("KB-20240329-0001")
print(f"知识详情: {knowledge.title}")
print(f"使用次数: {knowledge.statistics.usage_count}")

km.update_knowledge(
    knowledge_id="KB-20240329-0001",
    updates={
        "metadata.confidence": 0.98,
        "content.solution": "pip install $1 --upgrade"
    }
)

km.record_usage(
    knowledge_id="KB-20240329-0001",
    success=True,
    feedback="positive"
)
```

### 知识管理配置

```yaml
knowledge_manager:
  storage:
    type: sqlite
    path: "./.evolution/knowledge/knowledge.db"
    vector_store:
      enabled: true
      type: faiss
      path: "./.evolution/knowledge/vectors"
  
  indexing:
    auto_index: true
    index_fields:
      - title
      - description
      - tags
      - content
    vector_embedding:
      enabled: true
      model: sentence-transformers/all-MiniLM-L6-v2
  
  retention:
    max_knowledge_count: 10000
    auto_cleanup: true
    cleanup_interval: 604800
    keep_high_confidence: true
  
  quality:
    min_confidence: 0.5
    require_validation: true
    auto_quality_check: true
```

---

## 知识学习系统

知识学习系统负责从系统运行过程中自动提取和积累知识。

### 学习流程

```
知识学习流程:

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   数据收集 ──▶ 模式识别 ──▶ 知识提取 ──▶ 质量评估 ──▶ 知识存储              │
│       │           │           │           │           │                    │
│       ▼           ▼           ▼           ▼           ▼                    │
│   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐              │
│   │修复   │   │错误   │   │结构   │   │置信度 │   │索引   │              │
│   │记录   │   │模式   │   │化     │   │计算   │   │创建   │              │
│   │日志   │   │匹配   │   │知识   │   │验证   │   │关联   │              │
│   │指标   │   │聚类   │   │条目   │   │评估   │   │存储   │              │
│   └───────┘   └───────┘   └───────┘   └───────┘   └───────┘              │
│                                                                             │
│   学习来源:                                                                  │
│   - 成功的修复操作                                                          │
│   - 性能优化结果                                                            │
│   - 代码审查反馈                                                            │
│   - 用户使用数据                                                            │
│   - 外部知识导入                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 学习类型

| 学习类型 | 数据来源 | 学习内容 | 学习频率 |
|----------|----------|----------|----------|
| `fix_learning` | 修复记录 | 修复模式、解决方案 | 每次修复后 |
| `optimization_learning` | 优化结果 | 优化策略、效果数据 | 每次优化后 |
| `pattern_learning` | 代码分析 | 代码模式、最佳实践 | 定期分析 |
| `feedback_learning` | 用户反馈 | 知识质量、适用性 | 收到反馈时 |
| `failure_learning` | 失败记录 | 反模式、失败原因 | 每次失败后 |

### 使用示例

#### 自动学习

```bash
python scripts/knowledge_learner.py learn \
  --source fix_records \
  --auto-extract \
  --min-confidence 0.8

python scripts/knowledge_learner.py learn \
  --source optimization_results \
  --type optimization_learning
```

**输出示例：**
```
=== 知识学习报告 ===

学习来源: fix_records
学习时间: 2024-03-29T16:00:00

提取的知识:
  1. [NEW] ImportError 修复模式
     - 来源: 15 次成功修复
     - 置信度: 0.92
     - 状态: 已存储
  
  2. [UPDATED] 语法错误修复模式
     - 来源: 更新现有知识
     - 新置信度: 0.95 (原: 0.90)
     - 状态: 已更新
  
  3. [SKIPPED] 低置信度模式
     - 来源: 3 次修复记录
     - 置信度: 0.65 (阈值: 0.80)
     - 状态: 跳过存储

学习统计:
  新增知识: 1 条
  更新知识: 1 条
  跳过知识: 1 条
  总处理: 3 条
```

#### 编程接口

```python
from scripts.knowledge_learner import KnowledgeLearner, LearningSource

learner = KnowledgeLearner(knowledge_base_path='./.evolution/knowledge')

fix_records = [
    {
        "error_type": "ImportError",
        "error_message": "No module named 'requests'",
        "fix_applied": "pip install requests",
        "success": True,
        "context": {"file": "api/client.py", "line": 15}
    },
    {
        "error_type": "SyntaxError",
        "error_message": "invalid syntax",
        "fix_applied": "Added missing colon",
        "success": True,
        "context": {"file": "utils/parser.py", "line": 42}
    }
]

result = learner.learn_from_fixes(
    fix_records=fix_records,
    auto_store=True,
    min_confidence=0.8
)

print(f"学习完成: {result['learned_count']} 条知识")
print(f"新增: {result['new_count']}, 更新: {result['updated_count']}")

optimization_records = [
    {
        "type": "cache_optimization",
        "target": "api/client.py",
        "improvement": 0.45,
        "before": {"response_time": 200},
        "after": {"response_time": 110}
    }
]

result = learner.learn_from_optimizations(
    optimization_records=optimization_records,
    auto_store=True
)

print(f"优化知识学习: {result['learned_count']} 条")
```

### 学习配置

```yaml
knowledge_learning:
  enabled: true
  
  sources:
    fix_records:
      enabled: true
      min_occurrences: 3
      confidence_threshold: 0.8
    optimization_results:
      enabled: true
      min_improvement: 0.1
    code_analysis:
      enabled: true
      analysis_interval: 86400
    user_feedback:
      enabled: true
      feedback_types:
        - positive
        - negative
        - correction
  
  extraction:
    auto_extract: true
    pattern_recognition: true
    clustering_enabled: true
    min_cluster_size: 3
  
  quality:
    min_confidence: 0.7
    validation_required: true
    cross_validation: true
    expert_review_threshold: 0.9
  
  storage:
    auto_store: true
    deduplication: true
    version_control: true
```

---

## 跨项目知识共享

跨项目知识共享系统允许多个项目之间共享和同步知识，实现知识的最大化利用。

### 共享架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        跨项目知识共享架构                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      中心知识库                                       │   │
│   │                    Central Knowledge Base                            │   │
│   │  ┌──────────────────────────────────────────────────────────────┐   │   │
│   │  │                    共享知识存储                                │   │   │
│   │  │  - 修复模式库    - 最佳实践库    - 优化策略库                 │   │   │
│   │  └──────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│              ┌─────────────────────┼─────────────────────┐                 │
│              │                     │                     │                 │
│              ▼                     ▼                     ▼                 │
│   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐        │
│   │   项目 A        │   │   项目 B        │   │   项目 C        │        │
│   │                 │   │                 │   │                 │        │
│   │  ┌───────────┐  │   │  ┌───────────┐  │   │  ┌───────────┐  │        │
│   │  │ 本地知识库 │  │   │  │ 本地知识库 │  │   │  │ 本地知识库 │  │        │
│   │  └───────────┘  │   │  └───────────┘  │   │  └───────────┘  │        │
│   │        │        │   │        │        │   │        │        │        │
│   │        ▼        │   │        ▼        │   │        ▼        │        │
│   │  ┌───────────┐  │   │  ┌───────────┐  │   │  ┌───────────┐  │        │
│   │  │ 同步代理  │◄─┼───┼─▶│ 同步代理  │◄─┼───┼─▶│ 同步代理  │  │        │
│   │  └───────────┘  │   │  └───────────┘  │   │  └───────────┘  │        │
│   └─────────────────┘   └─────────────────┘   └─────────────────┘        │
│                                                                             │
│   同步模式:                                                                  │
│   - 推送 (Push): 本地知识 → 中心库                                          │
│   - 拉取 (Pull): 中心库知识 → 本地                                          │
│   - 双向 (Sync): 双向同步                                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 项目注册

#### 注册新项目

```bash
python scripts/knowledge_sharing.py register \
  --project-id "my-project" \
  --project-name "我的项目" \
  --project-path "/path/to/project" \
  --knowledge-scope "fix_pattern,best_practice"
```

#### 查看已注册项目

```bash
python scripts/knowledge_sharing.py list-projects
```

**输出示例：**
```
=== 已注册项目列表 ===

项目ID          项目名称          知识范围                    注册时间
─────────────────────────────────────────────────────────────────────────
my-project      我的项目          fix_pattern, best_practice  2024-03-29
project-b       项目B             all                         2024-03-28
project-c       项目C             optimization                2024-03-27

总计: 3 个项目
```

### 知识同步

#### 推送知识到中心库

```bash
python scripts/knowledge_sharing.py push \
  --project-id "my-project" \
  --knowledge-ids "KB-20240329-0001,KB-20240329-0002" \
  --scope "fix_pattern"
```

#### 从中心库拉取知识

```bash
python scripts/knowledge_sharing.py pull \
  --project-id "my-project" \
  --scope "fix_pattern,best_practice" \
  --min-confidence 0.8
```

#### 双向同步

```bash
python scripts/knowledge_sharing.py sync \
  --project-id "my-project" \
  --mode bidirectional \
  --conflict-resolution "newer"
```

**输出示例：**
```
=== 知识同步报告 ===

项目: my-project
同步模式: bidirectional
同步时间: 2024-03-29T17:00:00

推送知识:
  ✓ KB-20240329-0001: ImportError 修复模式 (新增)
  ✓ KB-20240329-0002: 语法错误修复模式 (更新)

拉取知识:
  ✓ KB-20240328-0015: SQL注入防护模式 (新增)
  ✓ KB-20240327-0008: 性能优化策略 (新增)

冲突处理:
  ○ KB-20240320-0010: 使用中心库版本 (较新)

同步统计:
  推送: 2 条
  拉取: 2 条
  冲突: 1 条 (已解决)
  总计: 5 条
```

### 编程接口

```python
from scripts.knowledge_sharing import KnowledgeSharing, SyncMode

sharing = KnowledgeSharing(
    central_knowledge_base="./central_knowledge",
    project_id="my-project"
)

sharing.register_project(
    project_name="我的项目",
    project_path="/path/to/project",
    knowledge_scope=["fix_pattern", "best_practice"]
)

sharing.push_knowledge(
    knowledge_ids=["KB-20240329-0001"],
    scope="fix_pattern"
)

results = sharing.pull_knowledge(
    scope=["fix_pattern", "best_practice"],
    min_confidence=0.8,
    limit=50
)

print(f"拉取知识: {len(results)} 条")

sync_result = sharing.sync_knowledge(
    mode=SyncMode.BIDIRECTIONAL,
    conflict_resolution="newer"
)

print(f"推送: {sync_result['pushed_count']} 条")
print(f"拉取: {sync_result['pulled_count']} 条")
print(f"冲突: {sync_result['conflict_count']} 条")
```

### 权限管理

```yaml
knowledge_sharing:
  permissions:
    my-project:
      read:
        - fix_pattern
        - best_practice
        - optimization
      write:
        - fix_pattern
        - best_practice
      admin: false
    
    project-b:
      read:
        - all
      write:
        - all
      admin: true
  
  access_control:
    enabled: true
    authentication: token
    authorization: rbac
  
  audit:
    enabled: true
    log_access: true
    log_modifications: true
    retention_days: 90
```

### 共享配置

```yaml
knowledge_sharing:
  enabled: true
  
  central_knowledge_base:
    type: distributed
    nodes:
      - host: knowledge-server-1
        port: 8080
      - host: knowledge-server-2
        port: 8080
    replication: 2
  
  sync:
    mode: bidirectional
    interval: 3600
    batch_size: 100
    conflict_resolution: newer
  
  scope:
    default: all
    project_overrides:
      my-project:
        - fix_pattern
        - best_practice
  
  quality_filter:
    min_confidence: 0.7
    min_success_rate: 0.8
    exclude_types:
      - anti_pattern
  
  notification:
    on_sync_complete: true
    on_conflict: true
    on_error: true
```

---

## 知识质量评估

知识质量评估系统确保存储的知识具有高质量和可靠性。

### 评估维度

| 维度 | 说明 | 权重 | 计算方式 |
|------|------|------|----------|
| `confidence` | 置信度 | 30% | 基于成功应用次数 |
| `applicability` | 适用性 | 25% | 基于适用场景覆盖 |
| `freshness` | 新鲜度 | 15% | 基于最后更新时间 |
| `feedback` | 反馈质量 | 20% | 基于用户反馈 |
| `validation` | 验证状态 | 10% | 是否经过验证 |

### 质量评估示例

```python
from scripts.knowledge_quality import KnowledgeQualityAssessor

assessor = KnowledgeQualityAssessor()

quality = assessor.assess_knowledge("KB-20240329-0001")

print(f"总体质量分数: {quality.overall_score:.2f}")
print(f"置信度: {quality.confidence:.2f}")
print(f"适用性: {quality.applicability:.2f}")
print(f"新鲜度: {quality.freshness:.2f}")
print(f"反馈质量: {quality.feedback:.2f}")

recommendations = assessor.get_improvement_recommendations("KB-20240329-0001")
for rec in recommendations:
    print(f"建议: {rec['description']}")
```

### 质量配置

```yaml
knowledge_quality:
  assessment:
    enabled: true
    interval: 86400
    auto_update_scores: true
  
  thresholds:
    excellent: 0.9
    good: 0.8
    acceptable: 0.7
    poor: 0.6
  
  actions:
    on_poor_quality:
      - flag_for_review
      - reduce_visibility
    on_excellent_quality:
      - promote_to_featured
      - increase_visibility
  
  cleanup:
    enabled: true
    remove_below_threshold: 0.5
    archive_after_days: 365
```

---

## API 接口

### REST API

#### 知识管理

```bash
GET /api/knowledge?query=导入错误&type=fix_pattern&limit=10

GET /api/knowledge/{knowledge_id}

POST /api/knowledge
Content-Type: application/json
{
  "type": "fix_pattern",
  "title": "知识标题",
  "description": "知识描述",
  "content": {...},
  "tags": ["tag1", "tag2"]
}

PUT /api/knowledge/{knowledge_id}
Content-Type: application/json
{
  "content": {...},
  "tags": ["updated-tag"]
}

DELETE /api/knowledge/{knowledge_id}
```

#### 知识学习

```bash
POST /api/knowledge/learn
Content-Type: application/json
{
  "source": "fix_records",
  "records": [...],
  "auto_store": true
}

GET /api/knowledge/learn/status/{learning_id}
```

#### 知识共享

```bash
POST /api/knowledge/sharing/register
Content-Type: application/json
{
  "project_id": "my-project",
  "project_name": "我的项目",
  "knowledge_scope": ["fix_pattern"]
}

POST /api/knowledge/sharing/sync
Content-Type: application/json
{
  "project_id": "my-project",
  "mode": "bidirectional"
}

GET /api/knowledge/sharing/projects
```

### WebSocket API

```javascript
const ws = new WebSocket('ws://localhost:8000/api/knowledge/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'knowledge_added':
      console.log('新知识已添加:', message.data);
      break;
    case 'knowledge_updated':
      console.log('知识已更新:', message.data);
      break;
    case 'sync_complete':
      console.log('同步完成:', message.data);
      break;
    case 'learning_complete':
      console.log('学习完成:', message.data);
      break;
  }
};

ws.send(JSON.stringify({
  type: 'subscribe',
  events: ['knowledge_added', 'sync_complete']
}));
```

---

## 最佳实践

### 1. 知识分类管理

```yaml
knowledge_organization:
  categories:
    - name: error_fixes
      types: [fix_pattern]
      tags: [error, fix, bug]
    - name: optimizations
      types: [optimization]
      tags: [performance, optimization]
    - name: best_practices
      types: [best_practice]
      tags: [pattern, practice]
  
  tagging:
    required_tags: true
    max_tags: 10
    suggest_tags: true
```

### 2. 知识生命周期管理

```python
from scripts.knowledge_lifecycle import KnowledgeLifecycleManager

lifecycle = KnowledgeLifecycleManager()

lifecycle.define_lifecycle(
    stages=["draft", "validated", "published", "deprecated"],
    transitions={
        "draft": ["validated"],
        "validated": ["published", "draft"],
        "published": ["deprecated", "validated"],
        "deprecated": []
    }
)

lifecycle.transition("KB-20240329-0001", "validated")
```

### 3. 知识备份与恢复

```bash
python scripts/knowledge_manager.py backup \
  --output ./backups/knowledge_20240329.tar.gz \
  --include-stats

python scripts/knowledge_manager.py restore \
  --input ./backups/knowledge_20240329.tar.gz \
  --merge-strategy overwrite
```

---

## 故障排除

### 常见问题

**Q: 知识检索结果不准确？**

```bash
python scripts/knowledge_manager.py reindex --force

python scripts/knowledge_manager.py search --query "导入错误" --explain
```

**Q: 知识同步失败？**

```bash
python scripts/knowledge_sharing.py diagnose \
  --project-id "my-project"

python scripts/knowledge_sharing.py sync \
  --project-id "my-project" \
  --mode push \
  --force
```

**Q: 知识质量分数过低？**

```bash
python scripts/knowledge_quality.py analyze \
  --knowledge-id "KB-20240329-0001"

python scripts/knowledge_quality.py improve \
  --knowledge-id "KB-20240329-0001" \
  --auto-fix
```

---

## 总结

知识库管理系统通过以下能力实现知识的有效管理：

1. **知识存储** - 结构化存储各类知识条目
2. **智能检索** - 基于语义和标签的高效检索
3. **自动学习** - 从系统运行中自动提取知识
4. **跨项目共享** - 支持多项目间的知识共享
5. **质量评估** - 确保知识的可靠性和适用性

通过与持续演化系统和自迭代机制的深度集成，知识库管理系统形成了完整的知识驱动自我进化能力。

---

## 相关文档

- [持续演化系统](continuous_evolution.md)
- [自迭代机制](self_iteration.md)
- [白盒化流水线](baihehua_liushuixian.md)
- [版本管理](version_management.md)
