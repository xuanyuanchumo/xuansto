# CangjieSkills DocFlow 知识蒸馏集成参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

CangjieSkills DocFlow 是一套面向AI Agent的结构化知识蒸馏流程，通过将原始文档转化为精炼的结构化技能知识库，替代低效的原始文档检索模式。其核心目标是在保持知识完整性的前提下，实现60%以上的Token消耗降低。

---

## 知识蒸馏流程

### 流程架构

```
原始文档 ──→ 文档解析 ──→ 知识提取 ──→ 结构化蒸馏 ──→ 技能知识库
              │              │              │              │
          格式标准化    实体关系识别    冗余消除      索引构建
          元数据提取    概念层级构建    摘要生成      向量化存储
```

### 阶段一：文档解析（Document Parsing）

**输入：** 原始技术文档（Markdown、HTML、PDF、API Doc）

**处理步骤：**

1. 格式标准化：统一为结构化Markdown
2. 元数据提取：标题层级、代码块、表格、链接
3. 分块策略：按语义边界切分，每块200-500 Token

```yaml
parsing:
  input_formats: [markdown, html, pdf, openapi]
  chunking:
    strategy: semantic_boundary
    min_tokens: 200
    max_tokens: 500
    overlap: 50
  metadata:
    extract: [headers, code_blocks, tables, links, images]
    preserve_hierarchy: true
```

### 阶段二：知识提取（Knowledge Extraction）

**核心任务：**

- 实体识别：提取技术概念、API名称、配置项
- 关系映射：建立概念间的依赖、继承、引用关系
- 层级构建：组织为树状知识结构

```yaml
extraction:
  entities:
    types: [concept, api, config, pattern, anti_pattern]
    confidence_threshold: 0.85
  relations:
    types: [depends_on, extends, references, contradicts]
    bidirectional: true
  hierarchy:
    max_depth: 5
    merge_threshold: 0.9
```

### 阶段三：结构化蒸馏（Structured Distillation）

**Token优化策略：**

| 策略 | Token节省率 | 适用场景 |
|------|-----------|---------|
| 冗余消除 | 15-20% | 重复概念、同义表述 |
| 摘要生成 | 20-25% | 长篇描述、示例代码 |
| 模板提取 | 10-15% | 重复模式、通用结构 |
| 引用折叠 | 5-10% | 交叉引用、链接网络 |

**蒸馏规则：**

1. 同一概念仅保留最精炼表述，删除重复定义
2. 代码示例保留核心逻辑，移除样板代码
3. 表格数据压缩为键值对或结构化对象
4. 交叉引用替换为内部ID链接

```yaml
distillation:
  redundancy_elimination:
    enabled: true
    similarity_threshold: 0.92
  summarization:
    enabled: true
    max_summary_ratio: 0.3
  template_extraction:
    enabled: true
    min_occurrences: 2
  reference_collapse:
    enabled: true
    max_depth: 3
```

### 阶段四：技能知识库构建（Skill Knowledge Base）

**输出格式：**

```yaml
skill_entry:
  id: "skill:typescript-standards"
  category: coding_standards
  summary: "TypeScript编码规范精要"
  key_rules:
    - rule: "严格类型推断，禁止any"
      context: "类型安全"
    - rule: "接口优于类型别名用于对象定义"
      context: "API设计"
  patterns:
    - name: "依赖注入模式"
      template: "..."
  anti_patterns:
    - name: "God Object反模式"
      reason: "违反单一职责"
  references: ["typescript-handbook", "clean-code-ts"]
```

---

## 60% Token降低策略详解

### 对比分析

| 维度 | 原始文档检索 | 蒸馏知识库 |
|------|------------|-----------|
| 平均查询Token | 2000-3000 | 600-1200 |
| 命中精度 | 60-70% | 85-95% |
| 上下文相关性 | 中（含噪声） | 高（精准匹配） |
| 更新延迟 | 实时 | 批量（可接受） |

### Token节省来源

1. **冗余消除（~18%）：** 同一概念在多处重复定义时，仅保留最精炼版本
2. **摘要压缩（~22%）：** 长篇描述压缩为核心要点，示例代码仅保留关键行
3. **结构化替代（~12%）：** 自然语言描述转为YAML/JSON结构，信息密度更高
4. **引用优化（~8%）：** 交叉引用用ID替代完整路径，减少重复传输

**总计：~60% Token降低**

---

## 与xuansto-skill的集成

```yaml
cangjie_integration:
  distillation_pipeline:
    trigger: on_document_update
    schedule: daily
  knowledge_base:
    storage: ".knowledge/cangjie_skills"
    format: yaml
    index: bm25_hnsw
  query_interface:
    mode: structured_query
    fallback: raw_document_retrieval
    cache_ttl: 1800
```

| xuansto模块 | CangjieSkills功能 | 集成点 |
|------------|------------------|-------|
| Knowledge Base | 蒸馏知识库 | 统一存储与检索 |
| Agent Registry | 技能匹配 | Agent能力与知识库关联 |
| Quality Gates | 知识验证 | 蒸馏结果质量检查 |
| Token Optimizer | Token节省 | 共享Token预算管理 |

---

## 最佳实践

1. 蒸馏前先验证原始文档的完整性和准确性
2. 保持蒸馏知识库与原始文档的版本同步
3. 定期评估蒸馏质量，确保关键信息未丢失
4. 对高频查询场景优先蒸馏，最大化Token节省
5. 保留原始文档作为回退源，蒸馏知识库作为首选源

---

## DocFlow知识蒸馏详细过程设计

### 端到端流水线：原始文档 → 向量嵌入

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DocFlow Distillation Pipeline                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐        │
│  │ 原始文档  │──→│ 结构化   │──→│ 技能知识  │──→│ 向量嵌入  │        │
│  │ Raw Doc  │   │ 提取     │   │ 条目     │   │ Embedding │        │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘        │
│       │              │              │              │                 │
│   格式检测      实体识别       规则提取       向量化存储            │
│   编码统一      关系映射       模式提取       HNSW索引              │
│   分块切分      层级构建       反模式提取     BM25索引              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Step 1: 原始文档（Raw Doc）→ 结构化提取（Structured Extraction）

**输入：** 任意格式技术文档

**处理流程：**

1. **格式检测与标准化**
   - 自动检测文档格式（Markdown/HTML/PDF/OpenAPI/YAML）
   - 统一转换为内部中间格式（Canonical Markdown）
   - 编码统一为UTF-8，行尾统一为LF

2. **语义分块（Semantic Chunking）**
   - 按标题层级（H1-H6）进行初级分块
   - 代码块独立成块，保留语言标签
   - 表格独立成块，保留列定义
   - 分块参数：min_tokens=200, max_tokens=500, overlap=50

3. **实体与关系提取**
   - 技术概念识别：API名称、类名、配置项、协议术语
   - 关系类型：depends_on, extends, references, contradicts, implements
   - 置信度阈值：0.85（低于此阈值的提取结果标记为待人工确认）

4. **层级结构构建**
   - 最大层级深度：5层
   - 合并阈值：相似度>0.9的同级概念自动合并
   - 跨文档引用解析：内部ID替代外部URL

**输出格式：**

```yaml
structured_extraction:
  doc_id: "doc:typescript-standards-v4.2"
  source: "references/typescript-standards.md"
  chunks:
    - chunk_id: "chunk:ts-001"
      content: "严格类型推断规则..."
      entities:
        - name: "strictNullChecks"
          type: config
          confidence: 0.95
      relations:
        - target: "chunk:ts-002"
          type: depends_on
      hierarchy_level: 2
      token_count: 320
```

### Step 2: 结构化提取 → 技能知识条目（Skill Knowledge Entry）

**核心转换规则：**

| 原始结构 | 技能知识条目字段 | 转换逻辑 |
|----------|----------------|---------|
| 概念定义 | `key_rules[]` | 提取核心规则，附加上下文标签 |
| 代码示例 | `patterns[].template` | 保留核心逻辑，移除样板代码 |
| 注意事项/警告 | `anti_patterns[]` | 转换为反模式条目，附加原因 |
| 配置项 | `config_defaults[]` | 提取默认值和有效范围 |
| 交叉引用 | `references[]` | 替换为内部知识ID |

**蒸馏优化策略执行顺序：**

1. 冗余消除（similarity_threshold=0.92）→ 同义概念合并
2. 摘要压缩（max_summary_ratio=0.3）→ 长描述压缩为核心要点
3. 模板提取（min_occurrences=2）→ 重复模式抽象为模板
4. 引用折叠（max_depth=3）→ 交叉引用替换为内部ID

**输出格式：**

```yaml
skill_knowledge_entry:
  id: "skill:typescript-standards"
  version: "4.2"
  category: coding_standards
  summary: "TypeScript编码规范精要"
  key_rules:
    - rule: "严格类型推断，禁止any"
      context: "类型安全"
      source_chunk: "chunk:ts-001"
    - rule: "接口优于类型别名用于对象定义"
      context: "API设计"
      source_chunk: "chunk:ts-003"
  patterns:
    - name: "依赖注入模式"
      template: "constructor(private dep: DepType) {}"
      source_chunk: "chunk:ts-007"
  anti_patterns:
    - name: "God Object反模式"
      reason: "违反单一职责"
      source_chunk: "chunk:ts-012"
  config_defaults:
    - key: "strictNullChecks"
      default: true
      valid_range: "boolean"
  references:
    - id: "skill:clean-code-ts"
      type: extends
  distillation_metadata:
    original_token_count: 8500
    distilled_token_count: 3200
    compression_ratio: 0.62
    distillation_timestamp: "2026-05-06T10:00:00Z"
```

### Step 3: 技能知识条目 → 向量嵌入（Vector Embedding）

**嵌入策略：**

1. **条目级嵌入**：对整个技能知识条目生成摘要向量
   - 模型：text-embedding-3-small
   - 维度：1536
   - 用途：语义相似度检索（HNSW索引）

2. **规则级嵌入**：对每条key_rule生成独立向量
   - 模型：text-embedding-3-small
   - 维度：1536
   - 用途：精确规则匹配检索

3. **关键词索引**：BM25倒排索引
   - 分词器：jieba（中文）+ whitespace（英文）
   - 用途：精确关键词匹配检索

**存储结构：**

```
.knowledge/
├── cangjie_skills/
│   ├── entries/
│   │   ├── skill:typescript-standards.yaml
│   │   └── skill:python-standards.yaml
│   ├── index/
│   │   ├── bm25_inverted.json
│   │   ├── hnsw_entry.bin
│   │   └── hnsw_rule.bin
│   └── distillation_log.jsonl
├── bm25_index/          # 全局BM25索引
└── hnsw_index/          # 全局HNSW索引
```

**融合检索策略：**

```python
async def distillation_search(
    query: str,
    top_k: int = 5,
    min_relevance: float = 0.7
) -> list[DistilledEntry]:
    bm25_results = bm25_index.search(query, top_k * 2)
    hnsw_entry_results = hnsw_entry_index.search(query_embedding, top_k * 2)
    hnsw_rule_results = hnsw_rule_index.search(query_embedding, top_k * 2)
    fused = reciprocal_rank_fusion(
        [bm25_results, hnsw_entry_results, hnsw_rule_results],
        k=60
    )
    return [r for r in fused[:top_k] if r.relevance >= min_relevance]
```

### 蒸馏质量门禁

| 门禁 | 检查项 | 通过标准 |
|------|--------|---------|
| DISTILL-COMPLETE | 蒸馏流程4阶段全部完成 | 100% |
| DISTILL-ACCURACY | 关键信息保留率 | > 95% |
| DISTILL-COMPRESSION | Token压缩率 | > 50% |
| DISTILL-INDEX | 索引构建完整性 | BM25+HNSW双索引就绪 |
| DISTILL-NO-LOSS | 反向验证：蒸馏条目可还原原始文档核心内容 | > 90% |

### 蒸馏触发机制

```yaml
distillation_triggers:
  on_demand:
    - command: "/learn --distill"
    - agent_request: Knowledge Manager主动触发
  scheduled:
    - cron: "0 2 * * *"
    - condition: "待蒸馏文档队列非空"
  event_driven:
    - on_document_update: "references/目录下文件变更"
    - on_knowledge_gap: "检索命中率连续3天<80%"
```

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
