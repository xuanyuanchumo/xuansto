# Agency Agents 桥接层 (Agency Integration)

## 概述

Agency Agents 桥接层是 Sanliu v4.0 与 `.trae/skills/agency-agents/` 生态的连接桥梁，使 Sanliu 能够调用144+专业智能体来完成特定领域的任务。该系统通过Agent注册表扫描、智能路由、调用接口和结果整合等子系统，实现跨Agent的协同工作。

### 核心理念

- **生态连接**: 打通Sanliu与agency-agents生态的连接
- **智能路由**: 根据任务描述自动推荐最优Agent组合
- **灵活调用**: 支持同步和异步调用模式
- **结果整合**: 智能整合多个Agent的输出，解决冲突
- **领域映射**: 建立Sanliu司/局与Agency Agent的映射关系

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                  Agency Agents 桥接层架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           Agent注册表扫描 (Registry Scanner)               │  │
│  │  ├─ 遍历agency-agents目录                                  │  │
│  │  ├─ 解析Agent元数据 (SKILL.md)                           │  │
│  │  ├─ 构建Agent索引 (按领域/能力分类)                       │  │
│  │  └─ 维护Agent状态 (可用/不可用)                            │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              智能路由器 (Smart Router)                     │  │
│  │  ├─ 任务关键词匹配                                         │  │
│  │  ├─ Agent能力评估                                         │  │
│  │  ├─ 最优组合推荐                                           │  │
│  │  └─ Sanliu→Agency映射                                     │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            Agent调用接口 (Invocation Interface)              │  │
│  │  ├─ 同步调用 (invoke_agent_sync)                          │  │
│  │  ├─ 异步调用 (invoke_agent_async)                          │  │
│  │  ├─ 上下文传递 (context passing)                           │  │
│  │  └─ 结果收集 (result collection)                           │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            结果整合器 (Result Aggregator)                  │  │
│  │  ├─ 多Agent输出收集                                       │  │
│  │  ├─ 冲突检测与解决                                         │  │
│  │  ├─ 综合报告生成                                           │  │
│  │  └─ 质量评分与排序                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           Sanliu → Agency 映射矩阵                          │  │
│  │  ├─ 中书省 (16司) → 8个Agent映射                         │  │
│  │  ├─ 门下省 (16司) → 10个Agent映射                        │  │
│  │  └─ 尚书省 (24司) → 5个Agent映射                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Agent注册表扫描

### 功能概述

Agent注册表扫描器负责扫描 `.trae/skills/agency-agents/` 目录，解析每个Agent的元数据，构建Agent索引。

### 目录结构

```
.trae/skills/agency-agents/
├── engineering/
│   ├── engineering-frontend-developer/
│   │   └── SKILL.md
│   ├── engineering-backend-architect/
│   │   └── SKILL.md
│   ├── engineering-security-engineer/
│   │   └── SKILL.md
│   └── engineering-senior-developer/
│       └── SKILL.md
├── design/
│   ├── design-ui-ux-designer/
│   │   └── SKILL.md
│   └── design-graphic-designer/
│       └── SKILL.md
├── testing/
│   ├── testing-qa-engineer/
│   │   └── SKILL.md
│   └── testing-test-automation/
│       └── SKILL.md
├── marketing/
│   └── ...
└── ...
```

### 核心方法

#### scan_agents() 方法

```python
class AgencyBridge:
    def scan_agents(self, agents_dir: str = '.trae/skills/agency-agents') -> List[AgentInfo]:
        """
        扫描所有可用的Agent

        Args:
            agents_dir: Agents目录路径

        Returns:
            List[AgentInfo]: Agent信息列表
        """
        agents = []
        agents_path = Path(agents_dir)

        if not agents_path.exists():
            logger.warning(f"Agents目录不存在: {agents_dir}")
            return agents

        # 遍历所有子目录
        for domain_dir in agents_path.iterdir():
            if not domain_dir.is_dir():
                continue

            # 遍历域下的Agent
            for agent_dir in domain_dir.iterdir():
                if not agent_dir.is_dir():
                    continue

                # 解析SKILL.md
                skill_file = agent_dir / 'SKILL.md'
                if skill_file.exists():
                    agent_info = self._parse_agent_skill(skill_file)
                    if agent_info:
                        agents.append(agent_info)

        # 构建索引
        self._build_agent_index(agents)

        return agents

    def _parse_agent_skill(self, skill_file: Path) -> Optional[AgentInfo]:
        """解析Agent的SKILL.md文件"""
        with open(skill_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取元数据
        metadata = self._extract_metadata(content)

        # 提取能力
        capabilities = self._extract_capabilities(content)

        # 提取触发关键词
        triggers = self._extract_triggers(content)

        return AgentInfo(
            id=metadata.get('id', skill_file.parent.name),
            name=metadata.get('name', skill_file.parent.name),
            domain=skill_file.parent.parent.name,
            description=metadata.get('description', ''),
            capabilities=capabilities,
            triggers=triggers,
            version=metadata.get('version', '1.0.0'),
            author=metadata.get('author', ''),
            skill_file=str(skill_file),
            available=True
        )
```

#### build_agent_index() 方法

```python
class AgencyBridge:
    def _build_agent_index(self, agents: List[AgentInfo]):
        """
        构建Agent索引

        Args:
            agents: Agent信息列表
        """
        self.agent_index = {
            'by_id': {},
            'by_domain': {},
            'by_capability': {},
            'by_trigger': {}
        }

        for agent in agents:
            # 按ID索引
            self.agent_index['by_id'][agent.id] = agent

            # 按域索引
            if agent.domain not in self.agent_index['by_domain']:
                self.agent_index['by_domain'][agent.domain] = []
            self.agent_index['by_domain'][agent.domain].append(agent)

            # 按能力索引
            for capability in agent.capabilities:
                if capability not in self.agent_index['by_capability']:
                    self.agent_index['by_capability'][capability] = []
                self.agent_index['by_capability'][capability].append(agent)

            # 按触发关键词索引
            for trigger in agent.triggers:
                if trigger not in self.agent_index['by_trigger']:
                    self.agent_index['by_trigger'][trigger] = []
                self.agent_index['by_trigger'][trigger].append(agent)
```

## 智能路由器

### 功能概述

智能路由器根据任务描述自动推荐最优的Agent组合。

### Sanliu → Agency 映射矩阵

#### 中书省映射 (8个映射)

| Sanliu司 | Agency Agent | 说明 |
|----------|--------------|------|
| 用户研究司 | design-user-researcher | 用户需求调研 |
| 需求拆解司 | engineering-senior-developer | 需求分析 |
| 验收标准司 | testing-qa-engineer | 验收标准制定 |
| 优先级排序司 | engineering-project-manager | 优先级评估 |
| 系统架构司 | engineering-backend-architect | 系统架构设计 |
| 技术选型司 | engineering-tech-lead | 技术栈选择 |
| 接口定义司 | engineering-api-designer | API接口设计 |
| ADR记录司 | engineering-senior-developer | 架构决策记录 |

#### 门下省映射 (10个映射)

| Sanliu司 | Agency Agent | 说明 |
|----------|--------------|------|
| 静态分析司 | engineering-senior-developer | 代码静态分析 |
| 安全扫描司 | engineering-security-engineer | 安全漏洞扫描 |
| 性能审计司 | engineering-performance-engineer | 性能分析与优化 |
| 审查报告司 | engineering-code-reviewer | 代码审查报告 |
| 策略制定司 | testing-qa-lead | 测试策略制定 |
| 用例设计司 | testing-test-designer | 测试用例设计 |
| 执行管理司 | testing-test-automation | 测试执行管理 |
| 覆盖分析司 | testing-coverage-analyst | 代码覆盖率分析 |
| 指标采集司 | engineering-devops-engineer | 质量指标采集 |
| 趋势分析司 | engineering-data-analyst | 质量趋势分析 |

#### 尚书省映射 (5个映射)

| Sanliu司 | Agency Agent | 说明 |
|----------|--------------|------|
| 代码生成司 | engineering-frontend-developer + engineering-backend-developer | 前后端代码生成 |
| UI/UX设计司 | design-ui-ux-designer | UI/UX设计 |
| 数据库设计司 | engineering-database-architect | 数据库设计 |
| API设计司 | engineering-api-designer | API设计 |
| TDD执行司 | testing-tdd-expert | TDD测试驱动开发 |

### 核心方法

#### recommend_agents() 方法

```python
class AgencyBridge:
    def recommend_agents(self, task_description: str, context: dict = None) -> List[AgentRecommendation]:
        """
        推荐Agent组合

        Args:
            task_description: 任务描述
            context: 上下文信息

        Returns:
            List[AgentRecommendation]: Agent推荐列表
        """
        context = context or {}
        recommendations = []

        # 1. 任务关键词匹配
        matched_agents = self._match_by_keywords(task_description)

        # 2. Sanliu司/局映射
        if context.get('sanliu_department'):
            mapped_agents = self._map_from_sanliu(context['sanliu_department'])
            matched_agents.extend(mapped_agents)

        # 3. 能力匹配
        capability_agents = self._match_by_capabilities(task_description)
        matched_agents.extend(capability_agents)

        # 4. 去重和评分
        agent_scores = {}
        for agent in matched_agents:
            if agent.id not in agent_scores:
                agent_scores[agent.id] = {
                    'agent': agent,
                    'score': 0,
                    'reasons': []
                }

            # 计算匹配分数
            score_info = agent_scores[agent.id]
            score_info['score'] += self._calculate_match_score(agent, task_description)

        # 5. 排序并生成推荐
        sorted_agents = sorted(agent_scores.values(), key=lambda x: x['score'], reverse=True)

        for agent_info in sorted_agents[:10]:  # 返回前10个
            recommendations.append(AgentRecommendation(
                agent=agent_info['agent'],
                confidence=agent_info['score'],
                reasons=agent_info['reasons']
            ))

        return recommendations

    def _match_by_keywords(self, task_description: str) -> List[AgentInfo]:
        """基于关键词匹配Agent"""
        matched = []

        for trigger, agents in self.agent_index['by_trigger'].items():
            if trigger.lower() in task_description.lower():
                matched.extend(agents)

        return matched

    def _map_from_sanliu(self, department: str) -> List[AgentInfo]:
        """从Sanliu司/局映射到Agent"""
        # SANLIU_AGENCY_MAPPING定义
        if department in self.SANLIU_AGENCY_MAPPING:
            agent_ids = self.SANLIU_AGENCY_MAPPING[department]
            return [self.agent_index['by_id'].get(id) for id in agent_ids if id in self.agent_index['by_id']]
        return []
```

### 任务关键词映射

```python
class AgencyBridge:
    TASK_KEYWORD_MAPPING = {
        # 前端开发
        'frontend': ['engineering-frontend-developer', 'design-ui-ux-designer'],
        'react': ['engineering-frontend-developer'],
        'vue': ['engineering-frontend-developer'],
        'angular': ['engineering-frontend-developer'],
        'ui': ['design-ui-ux-designer', 'engineering-frontend-developer'],
        'ux': ['design-ui-ux-designer'],

        # 后端开发
        'backend': ['engineering-backend-developer', 'engineering-backend-architect'],
        'api': ['engineering-api-designer', 'engineering-backend-developer'],
        'database': ['engineering-database-architect'],
        'microservice': ['engineering-backend-architect'],

        # 安全
        'security': ['engineering-security-engineer'],
        'authentication': ['engineering-security-engineer'],
        'authorization': ['engineering-security-engineer'],
        'vulnerability': ['engineering-security-engineer'],

        # 测试
        'test': ['testing-qa-engineer', 'testing-test-automation'],
        'tdd': ['testing-tdd-expert'],
        'coverage': ['testing-coverage-analyst'],
        'qa': ['testing-qa-engineer', 'testing-qa-lead'],

        # DevOps
        'deploy': ['engineering-devops-engineer'],
        'ci': ['engineering-devops-engineer'],
        'cd': ['engineering-devops-engineer'],
        'docker': ['engineering-devops-engineer'],
        'kubernetes': ['engineering-devops-engineer'],

        # 设计
        'design': ['design-ui-ux-designer', 'design-graphic-designer'],
        'graphic': ['design-graphic-designer'],
        'wireframe': ['design-ui-ux-designer'],

        # 数据
        'data': ['engineering-data-engineer', 'engineering-data-analyst'],
        'analytics': ['engineering-data-analyst'],
        'etl': ['engineering-data-engineer'],

        # 项目管理
        'project': ['engineering-project-manager'],
        'agile': ['engineering-project-manager'],
        'scrum': ['engineering-project-manager']
    }
```

## Agent调用接口

### 功能概述

Agent调用接口提供同步和异步两种调用模式，支持上下文传递和结果收集。

### 同步调用

```python
class AgencyBridge:
    def invoke_agent_sync(
        self,
        agent_id: str,
        task: str,
        context: dict = None,
        timeout: int = 300
    ) -> AgentResult:
        """
        同步调用Agent

        Args:
            agent_id: Agent ID
            task: 任务描述
            context: 上下文信息
            timeout: 超时时间（秒）

        Returns:
            AgentResult: Agent执行结果
        """
        agent = self.agent_index['by_id'].get(agent_id)
        if not agent:
            raise AgentNotFoundError(agent_id)

        if not agent.available:
            raise AgentUnavailableError(agent_id)

        # 准备调用上下文
        invoke_context = {
            'task': task,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }

        # 调用Agent
        try:
            start_time = time.time()

            # 使用subprocess调用Agent
            result = self._execute_agent(agent, invoke_context, timeout)

            elapsed_time = time.time() - start_time

            return AgentResult(
                agent_id=agent_id,
                agent_name=agent.name,
                success=result['success'],
                output=result.get('output', ''),
                error=result.get('error', ''),
                execution_time=elapsed_time,
                metadata=result.get('metadata', {})
            )

        except TimeoutError:
            return AgentResult(
                agent_id=agent_id,
                agent_name=agent.name,
                success=False,
                output='',
                error=f'Agent执行超时 ({timeout}s)',
                execution_time=timeout,
                metadata={}
            )
        except Exception as e:
            return AgentResult(
                agent_id=agent_id,
                agent_name=agent.name,
                success=False,
                output='',
                error=str(e),
                execution_time=0,
                metadata={}
            )

    def _execute_agent(self, agent: AgentInfo, context: dict, timeout: int) -> dict:
        """执行Agent"""
        # 这里实现实际的Agent调用逻辑
        # 可能是通过subprocess调用，或者通过API调用

        # 示例：通过subprocess调用
        cmd = [
            'python', '-m', 'trae.skills.agency-agents.' + agent.id,
            '--task', context['task'],
            '--context', json.dumps(context['context'])
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout,
                'metadata': {}
            }
        else:
            return {
                'success': False,
                'error': result.stderr,
                'metadata': {}
            }
```

### 异步调用

```python
class AgencyBridge:
    def invoke_agent_async(
        self,
        agent_id: str,
        task: str,
        context: dict = None,
        callback: callable = None
    ) -> Future:
        """
        异步调用Agent

        Args:
            agent_id: Agent ID
            task: 任务描述
            context: 上下文信息
            callback: 回调函数

        Returns:
            Future: Future对象
        """
        executor = ThreadPoolExecutor(max_workers=1)

        future = executor.submit(
            self.invoke_agent_sync,
            agent_id,
            task,
            context
        )

        if callback:
            future.add_done_callback(callback)

        return future
```

### 并行调用

```python
class AgencyBridge:
    def invoke_agents_parallel(
        self,
        agent_tasks: List[Tuple[str, str, dict]],
        max_workers: int = 5
    ) -> List[AgentResult]:
        """
        并行调用多个Agent

        Args:
            agent_tasks: Agent任务列表 [(agent_id, task, context), ...]
            max_workers: 最大并发数

        Returns:
            List[AgentResult]: Agent执行结果列表
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self.invoke_agent_sync,
                    agent_id,
                    task,
                    context
                ): agent_id
                for agent_id, task, context in agent_tasks
            }

            for future in as_completed(futures):
                agent_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(AgentResult(
                        agent_id=agent_id,
                        agent_name=agent_id,
                        success=False,
                        output='',
                        error=str(e),
                        execution_time=0,
                        metadata={}
                    ))

        return results
```

## 结果整合器

### 功能概述

结果整合器负责收集多个Agent的输出，检测并解决冲突，生成综合报告。

### 核心方法

#### aggregate_results() 方法

```python
class AgencyBridge:
    def aggregate_results(self, results: List[AgentResult]) -> AggregatedResult:
        """
        整合多个Agent的结果

        Args:
            results: Agent执行结果列表

        Returns:
            AggregatedResult: 整合后的结果
        """
        aggregated = AggregatedResult(
            total_agents=len(results),
            successful_agents=sum(1 for r in results if r.success),
            failed_agents=sum(1 for r in results if not r.success),
            conflicts=[],
            suggestions=[],
            final_output=''
        )

        # 1. 检测冲突
        conflicts = self._detect_conflicts(results)
        aggregated.conflicts = conflicts

        # 2. 解决冲突
        resolved_results = self._resolve_conflicts(results, conflicts)

        # 3. 生成综合报告
        report = self._generate_report(resolved_results)
        aggregated.final_output = report

        # 4. 生成建议
        suggestions = self._generate_suggestions(resolved_results, conflicts)
        aggregated.suggestions = suggestions

        return aggregated

    def _detect_conflicts(self, results: List[AgentResult]) -> List[Conflict]:
        """检测Agent结果中的冲突"""
        conflicts = []

        # 检测输出冲突
        outputs = [(r.agent_id, r.output) for r in results if r.success]
        for i, (id1, output1) in enumerate(outputs):
            for id2, output2 in outputs[i+1:]:
                similarity = self._calculate_similarity(output1, output2)
                if similarity < 0.5:  # 相似度低于50%视为冲突
                    conflicts.append(Conflict(
                        type='output_conflict',
                        agents=[id1, id2],
                        description=f"{id1}和{id2}的输出差异较大",
                        similarity=similarity
                    ))

        return conflicts

    def _resolve_conflicts(
        self,
        results: List[AgentResult],
        conflicts: List[Conflict]
    ) -> List[AgentResult]:
        """解决冲突"""
        # 简单策略：选择成功率最高的Agent
        successful_results = [r for r in results if r.success]

        # 按执行时间排序（越快越好）
        successful_results.sort(key=lambda r: r.execution_time)

        return successful_results
```

## 使用示例

### 示例1: 查询可用Agent

```python
from integration.agency_bridge import AgencyBridge

# 初始化
bridge = AgencyBridge()

# 扫描所有Agent
agents = bridge.scan_agents()

print(f"找到 {len(agents)} 个Agent:")
for agent in agents:
    print(f"  - {agent.id}: {agent.name} ({agent.domain})")
```

### 示例2: 推荐Agent

```python
# 推荐Agent
recommendations = bridge.recommend_agents(
    task_description="开发一个用户认证模块，支持OAuth2.0登录",
    context={'sanliu_department': '代码生成司'}
)

print(f"推荐 {len(recommendations)} 个Agent:")
for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec.agent.name} (置信度: {rec.confidence:.2%})")
    print(f"   原因: {'; '.join(rec.reasons)}")
```

### 示例3: 同步调用Agent

```python
# 同步调用
result = bridge.invoke_agent_sync(
    agent_id='engineering-frontend-developer',
    task='创建一个登录页面组件，包含用户名和密码输入框',
    context={'framework': 'React', 'styling': 'Tailwind CSS'}
)

if result.success:
    print("✅ Agent执行成功")
    print(f"输出:\n{result.output}")
    print(f"执行时间: {result.execution_time:.2f}s")
else:
    print(f"❌ Agent执行失败: {result.error}")
```

### 示例4: 并行调用多个Agent

```python
# 并行调用多个Agent
agent_tasks = [
    ('engineering-frontend-developer', '创建登录页面UI', {'framework': 'React'}),
    ('engineering-backend-developer', '实现OAuth2.0认证API', {'language': 'Python'}),
    ('engineering-security-engineer', '审查认证模块安全性', {})
]

results = bridge.invoke_agents_parallel(agent_tasks, max_workers=3)

print(f"并行调用完成:")
for result in results:
    status = "✅" if result.success else "❌"
    print(f"{status} {result.agent_name}: {result.execution_time:.2f}s")
```

### 示例5: 整合多个Agent结果

```python
# 整合结果
aggregated = bridge.aggregate_results(results)

print(f"整合结果:")
print(f"  总Agent数: {aggregated.total_agents}")
print(f"  成功: {aggregated.successful_agents}")
print(f"  失败: {aggregated.failed_agents}")

if aggregated.conflicts:
    print(f"\n发现 {len(aggregated.conflicts)} 个冲突:")
    for conflict in aggregated.conflicts:
        print(f"  - {conflict.description}")

print(f"\n综合报告:\n{aggregated.final_output}")

if aggregated.suggestions:
    print(f"\n建议:")
    for suggestion in aggregated.suggestions:
        print(f"  - {suggestion}")
```

### 示例6: 通过Sanliu司/局调用

```python
# 通过Sanliu司/局映射调用
department = 'UI/UX设计司'
mapped_agents = bridge._map_from_sanliu(department)

print(f"{department} 映射到以下Agent:")
for agent in mapped_agents:
    print(f"  - {agent.name}")

# 调用第一个Agent
if mapped_agents:
    result = bridge.invoke_agent_sync(
        agent_id=mapped_agents[0].id,
        task='设计一个现代化的仪表板界面',
        context={'type': 'dashboard', 'theme': 'dark'}
    )
```

## 配置参数

```yaml
agency_bridge:
  # Agent目录配置
  agents_dir: ".trae/skills/agency-agents"

  # 扫描配置
  scanning:
    enabled: true
    scan_interval: 300  # 5分钟重新扫描一次
    cache_enabled: true
    cache_ttl: 3600  # 1小时缓存

  # 调用配置
  invocation:
    default_timeout: 300  # 5分钟
    max_retries: 3
    retry_delay: 5  # 秒
    parallel_max_workers: 5

  # 路由配置
  routing:
    enable_keyword_matching: true
    enable_sanliu_mapping: true
    enable_capability_matching: true
    max_recommendations: 10

  # 结果整合配置
  aggregation:
    conflict_detection: true
    conflict_threshold: 0.5  # 相似度阈值
    resolution_strategy: "fastest"  # fastest/highest_confidence/majority_vote
```

## 最佳实践

### 1. 合理使用并行调用

对于独立任务，使用并行调用提高效率。

```python
# 推荐：并行调用独立任务
agent_tasks = [
    ('engineering-frontend-developer', '创建登录页面', {}),
    ('engineering-backend-developer', '创建登录API', {}),
    ('testing-qa-engineer', '编写测试用例', {})
]
results = bridge.invoke_agents_parallel(agent_tasks)

# 不推荐：串行调用
for agent_id, task, context in agent_tasks:
    result = bridge.invoke_agent_sync(agent_id, task, context)
```

### 2. 处理Agent失败

始终检查Agent执行结果，处理失败情况。

```python
result = bridge.invoke_agent_sync(agent_id, task, context)

if not result.success:
    # 记录错误
    logger.error(f"Agent {agent_id} 执行失败: {result.error}")

    # 尝试备用Agent
    backup_agents = bridge.recommend_agents(task)
    if len(backup_agents) > 1:
        backup_result = bridge.invoke_agent_sync(
            backup_agents[1].agent.id,
            task,
            context
        )
```

### 3. 利用上下文传递

充分利用上下文传递，提高Agent执行效果。

```python
# 丰富的上下文
context = {
    'project_name': 'my-app',
    'tech_stack': ['React', 'Python', 'PostgreSQL'],
    'coding_standards': 'ESLint + PEP8',
    'previous_context': '之前已经实现了用户注册功能',
    'requirements': ['OAuth2.0', 'JWT', 'Refresh Token'],
    'constraints': ['响应式设计', '支持暗色模式']
}

result = bridge.invoke_agent_sync(agent_id, task, context)
```

### 4. 定期扫描Agent

定期扫描Agent目录，更新Agent索引。

```python
import time

bridge = AgencyBridge()

while True:
    # 扫描Agent
    agents = bridge.scan_agents()
    print(f"扫描到 {len(agents)} 个Agent")

    # 等待下次扫描
    time.sleep(300)  # 5分钟
```

### 5. 监控Agent性能

监控Agent的执行时间和成功率，优化Agent选择。

```python
# 记录Agent性能
performance_stats = {}

for result in results:
    agent_id = result.agent_id
    if agent_id not in performance_stats:
        performance_stats[agent_id] = {
            'total_calls': 0,
            'successful_calls': 0,
            'total_time': 0
        }

    stats = performance_stats[agent_id]
    stats['total_calls'] += 1
    stats['total_time'] += result.execution_time
    if result.success:
        stats['successful_calls'] += 1

# 计算成功率
for agent_id, stats in performance_stats.items():
    success_rate = stats['successful_calls'] / stats['total_calls']
    avg_time = stats['total_time'] / stats['total_calls']
    print(f"{agent_id}: 成功率 {success_rate:.2%}, 平均时间 {avg_time:.2f}s")
```

## 与其他模块的集成

### 与资源协调器的集成

Agency Bridge使用MARC资源协调器管理Agent调用资源。

```python
from resource_coordinator import ResourceCoordinator

coordinator = ResourceCoordinator()

# 注册Agent调用资源
coordinator.register_resource(
    resource_id='agency:invocation',
    type=ResourceType.COMPUTE,
    metadata={'max_concurrent': 5}
)

# 调用Agent前获取资源
lock_token = coordinator.acquire_lock(
    resource_id='agency:invocation',
    agent_id='sanliu-coordinator',
    lock_type=LockType.SHARED
)

try:
    result = bridge.invoke_agent_sync(agent_id, task, context)
finally:
    coordinator.release_lock(lock_token)
```

### 与四维防线的集成

四维防线可以调用Agency Bridge获取专业Agent的审查意见。

```python
from four_d_defense import RuleValidationLayer

class RuleValidationLayer:
    def run_agent_review(self, output: str, task_type: str) -> AgentReviewResult:
        """调用专业Agent进行审查"""
        bridge = AgencyBridge()

        # 推荐审查Agent
        agents = bridge.recommend_agents(f"审查{task_type}代码")

        # 并行调用多个Agent
        agent_tasks = [
            (agent.agent.id, f"审查以下{task_type}代码:\n{output}", {})
            for agent in agents[:3]
        ]
        results = bridge.invoke_agents_parallel(agent_tasks)

        # 整合审查意见
        aggregated = bridge.aggregate_results(results)

        return AgentReviewResult(
            agents=agents,
            results=results,
            aggregated=aggregated
        )
```

### 与操作优先级控制器的集成

操作优先级控制器可以基于Agent能力调整操作优先级。

```python
from operation_priority import OperationPriorityController

# 获取Agent推荐
recommendations = bridge.recommend_agents(task_description)

# 如果有高置信度的Agent推荐，降低操作优先级
if recommendations and recommendations[0].confidence > 0.9:
    # 使用Agent，优先级降低
    priority = Priority.SCRIPT
else:
    # 手动操作，优先级提高
    priority = Priority.MANUAL
```

## 故障排查

### 问题1: Agent调用超时

**症状**: Agent执行超时。

**排查步骤**:
1. 检查Agent是否可用
2. 检查任务是否过于复杂
3. 检查网络连接
4. 增加超时时间

**解决方案**:
```python
# 增加超时时间
result = bridge.invoke_agent_sync(
    agent_id,
    task,
    context,
    timeout=600  # 10分钟
)

# 或者使用异步调用
future = bridge.invoke_agent_async(agent_id, task, context)
result = future.result(timeout=600)
```

### 问题2: Agent结果冲突

**症状**: 多个Agent的输出不一致。

**解决方案**:
```python
# 使用不同的冲突解决策略
aggregated = bridge.aggregate_results(results)

# 查看冲突详情
for conflict in aggregated.conflicts:
    print(f"冲突: {conflict.description}")
    print(f"  相似度: {conflict.similarity:.2%}")
    print(f"  涉及Agent: {', '.join(conflict.agents)}")

# 手动选择最佳结果
best_agent = input("选择最佳Agent: ")
best_result = next(r for r in results if r.agent_id == best_agent)
```

### 问题3: Agent不可用

**症状**: Agent返回不可用错误。

**排查步骤**:
1. 检查Agent目录是否存在
2. 检查SKILL.md文件是否有效
3. 检查Agent依赖是否安装

**解决方案**:
```python
# 重新扫描Agent
agents = bridge.scan_agents()

# 检查特定Agent
agent = bridge.get_agent_spec(agent_id)
print(f"Agent状态: {'可用' if agent.available else '不可用'}")

# 如果不可用，尝试使用备用Agent
if not agent.available:
    recommendations = bridge.recommend_agents(task)
    if recommendations:
        backup_agent = recommendations[0].agent
        result = bridge.invoke_agent_sync(backup_agent.id, task, context)
```

## 总结

Agency Agents桥接层是Sanliu v4.0与agency-agents生态的连接桥梁，通过Agent注册表扫描、智能路由、调用接口和结果整合等子系统，实现跨Agent的协同工作。该系统具有以下特点:

- **生态连接**: 打通Sanliu与144+专业Agent的连接
- **智能路由**: 基于关键词、能力、Sanliu映射等多维度推荐
- **灵活调用**: 支持同步、异步、并行等多种调用模式
- **结果整合**: 自动检测冲突并生成综合报告
- **可扩展性**: 易于添加新的Agent和映射关系

通过合理配置和使用Agency Bridge，可以显著扩展Sanliu的能力范围，调用专业Agent完成特定领域的复杂任务。
