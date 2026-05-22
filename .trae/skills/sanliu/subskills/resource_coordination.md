# MARC-Lite 资源协调系统 (Resource Coordination)

## 概述

MARC-Lite (Multi-Agent Resource Coordinator Lite) 是 Sanliu v4.0 的核心资源协调系统，专门解决多Agent并发执行时的资源竞争、死锁、饥饿等问题。该系统通过资源注册、锁管理、调度队列、死锁预防和配额管理等五大子系统，确保多个Agent能够高效、安全地共享系统资源。

### 核心理念

- **资源抽象**: 将系统资源抽象为统一的资源类型，便于管理和调度
- **锁机制**: 通过读写锁、乐观锁、悲观锁等机制保证资源访问的互斥性
- **公平调度**: 使用优先级队列和公平调度算法，防止资源饥饿
- **死锁预防**: 通过资源排序、等待图检测、超时回退等机制预防死锁
- **配额管理**: 通过per-agent和global两级配额限制，防止单个Agent占用过多资源

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                  MARC-Lite 资源协调系统架构                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              资源注册中心 (ResourceRegistry)               │  │
│  │  ├─ 资源类型定义 (FILE/API/COMPUTE/TERMINAL/SECRET)       │  │
│  │  ├─ 资源元数据 (名称、描述、容量、权限)                     │  │
│  │  └─ 资源状态跟踪 (可用/占用/锁定)                           │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 锁管理器 (LockManager)                      │  │
│  │  ├─ 读写锁 (Read/Write Lock)                               │  │
│  │  ├─ 乐观锁/悲观锁 (Optimistic/Pessimistic)                 │  │
│  │  ├─ 锁超时释放 (Timeout Release)                           │  │
│  │  └─ 锁清理线程 (Cleanup Thread)                            │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                调度队列 (SchedulerQueue)                     │  │
│  │  ├─ 优先级队列 (Priority Queue)                            │  │
│  │  ├─ 公平调度 (Fair Scheduling)                             │  │
│  │  ├─ 抢占式调度 (Preemptive Scheduling)                     │  │
│  │  └─ 批处理合并 (Batch Merge)                               │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               死锁预防器 (DeadlockPreventer)               │  │
│  │  ├─ 资源排序分配 (Resource Ordering)                       │  │
│  │  ├─ 等待图检测 (Wait Graph Detection)                      │  │
│  │  ├─ 超时回退 (Timeout Backoff)                             │  │
│  │  └─ 受害者选择 (Victim Selection)                          │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                配额管理器 (QuotaManager)                    │  │
│  │  ├─ Per-Agent配额 (文件锁/API调用/CPU/内存)                │  │
│  │  ├─ Global配额 (活跃Agent/总资源)                          │  │
│  │  ├─ 使用率监控 (Usage Monitoring)                          │  │
│  │  └─ 超限告警 (Over-limit Alert)                             │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              ResourceCoordinator 主协调器                   │  │
│  │  ├─ 资源注册/注销                                           │  │
│  │  ├─ 锁获取/释放                                             │  │
│  │  ├─ 任务调度                                               │  │
│  │  ├─ 死锁检测/恢复                                           │  │
│  │  ├─ 配额检查/更新                                           │  │
│  │  └─ 状态查询 (--status命令)                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 资源类型定义

### 支持的资源类型

MARC-Lite支持5种资源类型，每种类型有不同的特性和访问模式：

#### 1. FILE (文件资源)

**特性**:
- 支持读写锁：多个Agent可以同时读取，但写入时需要独占锁
- 支持路径匹配：可以按文件路径模式批量注册资源
- 支持临时文件：自动清理临时文件资源

**使用场景**:
- 代码文件读写
- 配置文件修改
- 文档生成
- 测试文件操作

**示例**:
```python
from resource_coordinator import ResourceCoordinator, ResourceType, LockType

coordinator = ResourceCoordinator()

# 注册文件资源
coordinator.register_resource(
    resource_id='src/main.py',
    type=ResourceType.FILE,
    metadata={
        'path': 'src/main.py',
        'size': 1024,
        'mode': 'rw'
    }
)

# 获取读锁（共享锁）
lock_token = coordinator.acquire_lock(
    resource_id='src/main.py',
    agent_id='code-reviewer',
    lock_type=LockType.SHARED
)

# 获取写锁（独占锁）
lock_token = coordinator.acquire_lock(
    resource_id='src/main.py',
    agent_id='code-generator',
    lock_type=LockType.EXCLUSIVE
)
```

#### 2. API (API端点资源)

**特性**:
- 支持并发限制：限制同时访问API的Agent数量
- 支持速率限制：限制单位时间内的API调用次数
- 支持重试机制：API调用失败时自动重试

**使用场景**:
- 外部API调用
- 微服务通信
- 第三方服务集成
- 数据获取

**示例**:
```python
# 注册API资源
coordinator.register_resource(
    resource_id='api/github',
    type=ResourceType.API,
    metadata={
        'endpoint': 'https://api.github.com',
        'rate_limit': 60,  # 每分钟60次
        'concurrent_limit': 5  # 最多5个并发请求
    }
)

# 获取API访问权限
lock_token = coordinator.acquire_lock(
    resource_id='api/github',
    agent_id='github-integrator',
    lock_type=LockType.SHARED
)
```

#### 3. COMPUTE (计算资源)

**特性**:
- 支持CPU配额：限制Agent的CPU使用率
- 支持内存配额：限制Agent的内存使用量
- 支持时间配额：限制Agent的执行时间

**使用场景**:
- 代码编译
- 测试执行
- 数据处理
- 模型训练

**示例**:
```python
# 注册计算资源
coordinator.register_resource(
    resource_id='compute/cpu',
    type=ResourceType.COMPUTE,
    metadata={
        'cpu_cores': 4,
        'memory_mb': 8192,
        'time_limit_seconds': 300
    }
)

# 获取计算资源
lock_token = coordinator.acquire_lock(
    resource_id='compute/cpu',
    agent_id='test-runner',
    lock_type=LockType.EXCLUSIVE
)
```

#### 4. TERMINAL (终端会话资源)

**特性**:
- 完全互斥：同一时间只能有一个Agent使用终端
- 支持会话隔离：每个Agent有独立的终端会话
- 支持输出捕获：捕获终端输出供Agent分析

**使用场景**:
- 命令执行
- 脚本运行
- 交互式操作
- 调试会话

**示例**:
```python
# 注册终端资源
coordinator.register_resource(
    resource_id='terminal/main',
    type=ResourceType.TERMINAL,
    metadata={
        'shell': 'powershell',
        'working_dir': '/workspace'
    }
)

# 获取终端会话
lock_token = coordinator.acquire_lock(
    resource_id='terminal/main',
    agent_id='command-executor',
    lock_type=LockType.EXCLUSIVE
)
```

#### 5. SECRET (密钥资源)

**特性**:
- 只读访问：密钥资源只能读取，不能修改
- 一次性使用：密钥使用后立即失效，防止泄露
- 访问审计：记录所有密钥访问日志

**使用场景**:
- API密钥访问
- 数据库密码读取
- 加密密钥获取
- 认证令牌

**示例**:
```python
# 注册密钥资源
coordinator.register_resource(
    resource_id='secret/api_key',
    type=ResourceType.SECRET,
    metadata={
        'key_type': 'api_key',
        'service': 'github',
        'read_once': True
    }
)

# 获取密钥（一次性使用）
lock_token = coordinator.acquire_lock(
    resource_id='secret/api_key',
    agent_id='api-client',
    lock_type=LockType.SHARED
)

# 读取密钥
secret_value = coordinator.get_secret_value(lock_token)
```

## 资源注册中心 (ResourceRegistry)

### 功能概述

资源注册中心负责管理系统中的所有资源，包括资源的注册、注销、状态跟踪和元数据管理。

### 核心方法

#### 注册资源

```python
class ResourceRegistry:
    def register_resource(
        self,
        resource_id: str,
        type: ResourceType,
        metadata: Dict[str, Any],
        capacity: Optional[int] = None
    ) -> bool:
        """
        注册新资源

        Args:
            resource_id: 资源唯一标识
            type: 资源类型
            metadata: 资源元数据
            capacity: 资源容量（可选）

        Returns:
            bool: 注册是否成功
        """
        if resource_id in self.resources:
            raise ResourceAlreadyExistsError(resource_id)

        resource = Resource(
            id=resource_id,
            type=type,
            metadata=metadata,
            capacity=capacity,
            status=ResourceStatus.AVAILABLE,
            created_at=datetime.now()
        )

        self.resources[resource_id] = resource
        self._update_resource_index(resource)

        return True
```

#### 注销资源

```python
class ResourceRegistry:
    def unregister_resource(self, resource_id: str) -> bool:
        """
        注销资源

        Args:
            resource_id: 资源唯一标识

        Returns:
            bool: 注销是否成功
        """
        if resource_id not in self.resources:
            raise ResourceNotFoundError(resource_id)

        # 检查是否有锁
        if self.lock_manager.has_locks(resource_id):
            raise ResourceLockedError(resource_id)

        resource = self.resources.pop(resource_id)
        self._remove_from_index(resource)

        return True
```

#### 查询资源

```python
class ResourceRegistry:
    def get_resource(self, resource_id: str) -> Resource:
        """
        获取资源信息

        Args:
            resource_id: 资源唯一标识

        Returns:
            Resource: 资源对象
        """
        if resource_id not in self.resources:
            raise ResourceNotFoundError(resource_id)

        return self.resources[resource_id]

    def list_resources(
        self,
        type: Optional[ResourceType] = None,
        status: Optional[ResourceStatus] = None
    ) -> List[Resource]:
        """
        列出资源

        Args:
            type: 资源类型过滤（可选）
            status: 资源状态过滤（可选）

        Returns:
            List[Resource]: 资源列表
        """
        resources = list(self.resources.values())

        if type:
            resources = [r for r in resources if r.type == type]

        if status:
            resources = [r for r in resources if r.status == status]

        return resources

    def search_resources(self, query: str) -> List[Resource]:
        """
        搜索资源

        Args:
            query: 搜索查询（支持资源ID、元数据）

        Returns:
            List[Resource]: 匹配的资源列表
        """
        results = []

        for resource in self.resources.values():
            # 搜索资源ID
            if query.lower() in resource.id.lower():
                results.append(resource)
                continue

            # 搜索元数据
            for key, value in resource.metadata.items():
                if query.lower() in str(value).lower():
                    results.append(resource)
                    break

        return results
```

### 配置参数

```yaml
resource_registry:
  # 资源ID命名规范
  naming_convention:
    file: "file:{path}"
    api: "api:{service}:{endpoint}"
    compute: "compute:{resource_type}"
    terminal: "terminal:{name}"
    secret: "secret:{key_type}:{service}"

  # 资源元数据验证
  metadata_validation:
    file:
      required: ["path", "mode"]
      optional: ["size", "encoding"]
    api:
      required: ["endpoint"]
      optional: ["rate_limit", "concurrent_limit", "timeout"]
    compute:
      required: []
      optional: ["cpu_cores", "memory_mb", "time_limit_seconds"]
    terminal:
      required: ["shell"]
      optional: ["working_dir", "env_vars"]
    secret:
      required: ["key_type", "service"]
      optional: ["read_once"]
```

## 锁管理器 (LockManager)

### 功能概述

锁管理器负责管理资源的访问锁，支持多种锁类型和锁策略，确保资源访问的互斥性和一致性。

### 锁类型

#### 1. 共享锁 (SHARED)

**特性**:
- 多个Agent可以同时持有共享锁
- 用于读操作
- 与独占锁互斥

**使用场景**:
- 文件读取
- API查询
- 配置读取

#### 2. 独占锁 (EXCLUSIVE)

**特性**:
- 同一时间只能有一个Agent持有独占锁
- 与共享锁和独占锁都互斥
- 用于写操作

**使用场景**:
- 文件写入
- API修改
- 配置更新

### 核心方法

#### 获取锁

```python
class LockManager:
    def acquire_lock(
        self,
        resource_id: str,
        agent_id: str,
        lock_type: LockType,
        timeout: Optional[float] = None
    ) -> LockToken:
        """
        获取资源锁

        Args:
            resource_id: 资源唯一标识
            agent_id: Agent唯一标识
            lock_type: 锁类型（SHARED/EXCLUSIVE）
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            LockToken: 锁令牌

        Raises:
            ResourceNotFoundError: 资源不存在
            ResourceLockedError: 资源已被锁定且超时
            LockTimeoutError: 获取锁超时
        """
        # 检查资源是否存在
        if resource_id not in self.registry.resources:
            raise ResourceNotFoundError(resource_id)

        # 检查是否可以获取锁
        if not self._can_acquire_lock(resource_id, lock_type):
            if timeout is None:
                raise ResourceLockedError(resource_id)

            # 等待锁释放
            if not self._wait_for_lock(resource_id, lock_type, timeout):
                raise LockTimeoutError(resource_id, timeout)

        # 创建锁令牌
        lock_token = LockToken(
            token_id=self._generate_token_id(),
            resource_id=resource_id,
            agent_id=agent_id,
            lock_type=lock_type,
            acquired_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=self.default_timeout)
        )

        # 记录锁
        self.locks[lock_token.token_id] = lock_token
        self._update_resource_locks(resource_id, lock_token)

        return lock_token
```

#### 释放锁

```python
class LockManager:
    def release_lock(self, lock_token: LockToken) -> bool:
        """
        释放资源锁

        Args:
            lock_token: 锁令牌

        Returns:
            bool: 释放是否成功

        Raises:
            LockNotFoundError: 锁不存在
            LockExpiredError: 锁已过期
        """
        # 检查锁是否存在
        if lock_token.token_id not in self.locks:
            raise LockNotFoundError(lock_token.token_id)

        # 检查锁是否过期
        if lock_token.expires_at < datetime.now():
            self.locks.pop(lock_token.token_id)
            raise LockExpiredError(lock_token.token_id)

        # 释放锁
        self.locks.pop(lock_token.token_id)
        self._remove_resource_lock(lock_token.resource_id, lock_token.token_id)

        return True
```

#### 检查锁状态

```python
class LockManager:
    def has_locks(self, resource_id: str) -> bool:
        """
        检查资源是否有锁

        Args:
            resource_id: 资源唯一标识

        Returns:
            bool: 是否有锁
        """
        return len(self._get_resource_locks(resource_id)) > 0

    def get_locks(self, resource_id: str) -> List[LockToken]:
        """
        获取资源的所有锁

        Args:
            resource_id: 资源唯一标识

        Returns:
            List[LockToken]: 锁列表
        """
        return self._get_resource_locks(resource_id)

    def get_agent_locks(self, agent_id: str) -> List[LockToken]:
        """
        获取Agent持有的所有锁

        Args:
            agent_id: Agent唯一标识

        Returns:
            List[LockToken]: 锁列表
        """
        return [
            lock for lock in self.locks.values()
            if lock.agent_id == agent_id
        ]
```

### 锁清理线程

```python
class LockManager:
    def _start_cleanup_thread(self):
        """
        启动锁清理线程
        """
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_expired_locks,
            daemon=True
        )
        self.cleanup_thread.start()

    def _cleanup_expired_locks(self):
        """
        清理过期锁
        """
        while True:
            try:
                time.sleep(self.cleanup_interval)

                now = datetime.now()
                expired_tokens = [
                    token_id
                    for token_id, lock in self.locks.items()
                    if lock.expires_at < now
                ]

                for token_id in expired_tokens:
                    lock = self.locks.pop(token_id)
                    self._remove_resource_lock(lock.resource_id, token_id)

                    logger.info(f"清理过期锁: {token_id}")

            except Exception as e:
                logger.error(f"锁清理线程异常: {e}")
```

### 配置参数

```yaml
lock_manager:
  # 默认锁超时时间（秒）
  default_timeout: 300

  # 锁清理间隔（秒）
  cleanup_interval: 60

  # 乐观锁配置
  optimistic_locking:
    enabled: true
    max_retries: 3
    retry_delay: 1

  # 悲观锁配置
  pessimistic_locking:
    enabled: true
    timeout: 30
```

## 调度队列 (SchedulerQueue)

### 功能概述

调度队列负责管理待执行的任务，使用优先级队列和公平调度算法，确保任务按照优先级和公平性原则执行。

### 优先级定义

```python
class Priority(Enum):
    """任务优先级"""
    HIGH = "high"      # 高优先级：紧急任务
    MEDIUM = "medium"  # 中优先级：普通任务
    LOW = "low"        # 低优先级：后台任务
```

### 核心方法

#### 添加任务

```python
class SchedulerQueue:
    def add_task(
        self,
        task: Task,
        priority: Priority = Priority.MEDIUM
    ) -> str:
        """
        添加任务到队列

        Args:
            task: 任务对象
            priority: 任务优先级

        Returns:
            str: 任务ID
        """
        task_id = self._generate_task_id()
        task.id = task_id
        task.priority = priority
        task.created_at = datetime.now()
        task.status = TaskStatus.PENDING

        # 添加到优先级队列
        self._add_to_priority_queue(task)

        # 添加到公平队列
        self._add_to_fair_queue(task)

        return task_id
```

#### 获取下一个任务

```python
class SchedulerQueue:
    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个待执行任务

        Returns:
            Optional[Task]: 任务对象，如果队列为空返回None
        """
        # 优先从高优先级队列获取
        for priority in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            if self.priority_queues[priority]:
                task = self._pop_from_priority_queue(priority)
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                return task

        # 如果优先级队列为空，从公平队列获取
        if self.fair_queue:
            task = self._pop_from_fair_queue()
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            return task

        return None
```

#### 完成任务

```python
class SchedulerQueue:
    def complete_task(self, task_id: str, result: Any = None) -> bool:
        """
        标记任务为完成

        Args:
            task_id: 任务ID
            result: 任务结果

        Returns:
            bool: 是否成功
        """
        if task_id not in self.tasks:
            raise TaskNotFoundError(task_id)

        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result = result

        # 更新Agent统计
        self._update_agent_stats(task.agent_id, task)

        return True
```

#### 批处理合并

```python
class SchedulerQueue:
    def merge_batch_tasks(self, task_ids: List[str]) -> str:
        """
        合并批处理任务

        Args:
            task_ids: 任务ID列表

        Returns:
            str: 合并后的任务ID
        """
        if not task_ids:
            raise ValueError("任务ID列表不能为空")

        # 检查所有任务是否可以合并
        tasks = [self.tasks[tid] for tid in task_ids]
        if not self._can_merge_tasks(tasks):
            raise TasksCannotMergeError(task_ids)

        # 创建合并任务
        merged_task = Task(
            type=TaskType.BATCH,
            agent_id=tasks[0].agent_id,
            resources=[r for t in tasks for r in t.resources],
            metadata={'merged_from': task_ids}
        )

        # 添加合并任务
        merged_task_id = self.add_task(merged_task, tasks[0].priority)

        # 标记原任务为已合并
        for tid in task_ids:
            self.tasks[tid].status = TaskStatus.MERGED
            self.tasks[tid].merged_into = merged_task_id

        return merged_task_id
```

### 配置参数

```yaml
scheduler_queue:
  # 队列容量
  queue_capacity: 1000

  # 公平调度配置
  fair_scheduling:
    enabled: true
    agent_weight: 1.0  # Agent权重，用于公平调度

  # 抢占式调度配置
  preemptive_scheduling:
    enabled: true
    allow_preemption: true  # 允许抢占低优先级任务
    preemption_grace_period: 10  # 抢占宽限期（秒）

  # 批处理配置
  batch_processing:
    enabled: true
    max_batch_size: 10
    batch_timeout: 30  # 批处理超时（秒）
```

## 死锁预防器 (DeadlockPreventer)

### 功能概述

死锁预防器通过资源排序、等待图检测、超时回退和受害者选择等机制，预防和解决死锁问题。

### 死锁预防策略

#### 1. 资源排序分配

**原理**: 为所有资源分配一个全局排序号，要求Agent按固定顺序获取资源，打破循环等待条件。

**实现**:
```python
class DeadlockPreventer:
    def __init__(self):
        # 资源排序映射
        self.resource_order = {
            ResourceType.SECRET: 1,
            ResourceType.TERMINAL: 2,
            ResourceType.API: 3,
            ResourceType.FILE: 4,
            ResourceType.COMPUTE: 5
        }

    def check_resource_order(self, resource_ids: List[str]) -> bool:
        """
        检查资源获取顺序是否符合排序规则

        Args:
            resource_ids: 资源ID列表

        Returns:
            bool: 是否符合排序规则
        """
        if len(resource_ids) <= 1:
            return True

        # 获取资源类型
        resource_types = [
            self.registry.get_resource(rid).type
            for rid in resource_ids
        ]

        # 检查是否按升序排列
        for i in range(len(resource_types) - 1):
            if self.resource_order[resource_types[i]] > self.resource_order[resource_types[i + 1]]:
                return False

        return True
```

#### 2. 等待图检测

**原理**: 构建Agent等待图，检测是否存在环，如果存在环则说明可能发生死锁。

**实现**:
```python
class DeadlockPreventer:
    def detect_deadlock(self) -> Set[str]:
        """
        检测死锁

        Returns:
            Set[str]: 涉及死锁的Agent ID集合
        """
        # 构建等待图
        wait_graph = self._build_wait_graph()

        # 检测环
        cycles = self._find_cycles(wait_graph)

        if not cycles:
            return set()

        # 收集涉及死锁的Agent
        deadlocked_agents = set()
        for cycle in cycles:
            deadlocked_agents.update(cycle)

        return deadlocked_agents

    def _build_wait_graph(self) -> Dict[str, Set[str]]:
        """
        构建等待图

        Returns:
            Dict[str, Set[str]]: 等待图，key为Agent ID，value为等待的Agent集合
        """
        wait_graph = {}

        # 遍历所有锁
        for lock in self.lock_manager.locks.values():
            # 找出等待该资源的Agent
            waiting_agents = self._get_waiting_agents(lock.resource_id)

            # 添加到等待图
            if lock.agent_id not in wait_graph:
                wait_graph[lock.agent_id] = set()
            wait_graph[lock.agent_id].update(waiting_agents)

        return wait_graph

    def _find_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """
        使用DFS检测环

        Args:
            graph: 等待图

        Returns:
            List[List[str]]: 环列表
        """
        cycles = []
        visited = set()
        recursion_stack = set()

        def dfs(node: str, path: List[str]):
            if node in recursion_stack:
                # 找到环
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return

            if node in visited:
                return

            visited.add(node)
            recursion_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                dfs(neighbor, path.copy())

            recursion_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles
```

#### 3. 超时回退

**原理**: 为每个锁请求设置超时时间，如果超时则自动释放已获取的锁并回退。

**实现**:
```python
class DeadlockPreventer:
    def acquire_with_timeout(
        self,
        resource_ids: List[str],
        agent_id: str,
        lock_type: LockType,
        timeout: float
    ) -> List[LockToken]:
        """
        带超时的锁获取

        Args:
            resource_ids: 资源ID列表
            agent_id: Agent ID
            lock_type: 锁类型
            timeout: 超时时间（秒）

        Returns:
            List[LockToken]: 锁令牌列表

        Raises:
            LockTimeoutError: 获取锁超时
        """
        acquired_locks = []
        start_time = time.time()

        try:
            for resource_id in resource_ids:
                remaining_time = timeout - (time.time() - start_time)
                if remaining_time <= 0:
                    raise LockTimeoutError(resource_id, timeout)

                lock_token = self.lock_manager.acquire_lock(
                    resource_id,
                    agent_id,
                    lock_type,
                    remaining_time
                )
                acquired_locks.append(lock_token)

            return acquired_locks

        except Exception as e:
            # 回退：释放已获取的锁
            for lock in acquired_locks:
                self.lock_manager.release_lock(lock)

            raise e
```

#### 4. 受害者选择

**原理**: 当检测到死锁时，选择一个或多个Agent作为受害者，回退其操作以解除死锁。

**实现**:
```python
class DeadlockPreventer:
    def select_victim(self, deadlocked_agents: Set[str]) -> str:
        """
        选择受害者

        Args:
            deadlocked_agents: 涉及死锁的Agent集合

        Returns:
            str: 受害者Agent ID
        """
        # 评估每个Agent的回退成本
        agent_costs = {}
        for agent_id in deadlocked_agents:
            cost = self._calculate_rollback_cost(agent_id)
            agent_costs[agent_id] = cost

        # 选择回退成本最低的Agent
        victim = min(agent_costs, key=agent_costs.get)

        logger.warning(f"选择受害者: {victim} (回退成本: {agent_costs[victim]})")

        return victim

    def _calculate_rollback_cost(self, agent_id: str) -> float:
        """
        计算回退成本

        Args:
            agent_id: Agent ID

        Returns:
            float: 回退成本
        """
        # 获取Agent持有的锁
        locks = self.lock_manager.get_agent_locks(agent_id)

        # 计算成本
        cost = 0.0
        for lock in locks:
            # 持锁时间越长，成本越高
            hold_time = (datetime.now() - lock.acquired_at).total_seconds()
            cost += hold_time

            # 独占锁成本高于共享锁
            if lock.lock_type == LockType.EXCLUSIVE:
                cost *= 2

        return cost
```

### 配置参数

```yaml
deadlock_preventer:
  # 资源排序配置
  resource_ordering:
    enabled: true
    enforce_order: true  # 强制执行资源顺序

  # 等待图检测配置
  wait_graph_detection:
    enabled: true
    detection_interval: 10  # 检测间隔（秒）

  # 超时回退配置
  timeout_backoff:
    enabled: true
    default_timeout: 30  # 默认超时（秒）
    max_retries: 3  # 最大重试次数

  # 受害者选择配置
  victim_selection:
    strategy: "min_rollback_cost"  # 回退成本最低
    log_victim_selection: true
```

## 配额管理器 (QuotaManager)

### 功能概述

配额管理器通过per-agent和global两级配额限制，防止单个Agent占用过多资源，确保资源公平分配。

### 配额类型

#### 1. Per-Agent配额

**定义**: 每个Agent的资源使用配额

**配额项**:
- 文件锁数量
- API调用次数
- CPU使用率
- 内存使用量

**示例**:
```python
from resource_coordinator import QuotaManager, ResourceType

quota_manager = QuotaManager()

# 设置Agent配额
quota_manager.set_agent_quota(
    agent_id='code-generator',
    quotas={
        ResourceType.FILE: {'max_locks': 10},
        ResourceType.API: {'max_calls': 100},
        ResourceType.COMPUTE: {'max_cpu_percent': 50, 'max_memory_mb': 1024}
    }
)
```

#### 2. Global配额

**定义**: 全局资源使用配额

**配额项**:
- 活跃Agent数量
- 总文件锁数量
- 总API调用次数
- 总CPU使用率

**示例**:
```python
# 设置全局配额
quota_manager.set_global_quota({
    'max_active_agents': 10,
    'max_file_locks': 100,
    'max_api_calls': 1000,
    'max_cpu_percent': 80
})
```

### 核心方法

#### 检查配额

```python
class QuotaManager:
    def check_quota(
        self,
        agent_id: str,
        resource_type: ResourceType,
        amount: int = 1
    ) -> bool:
        """
        检查配额是否足够

        Args:
            agent_id: Agent ID
            resource_type: 资源类型
            amount: 请求数量

        Returns:
            bool: 配额是否足够
        """
        # 检查Agent配额
        if not self._check_agent_quota(agent_id, resource_type, amount):
            return False

        # 检查全局配额
        if not self._check_global_quota(resource_type, amount):
            return False

        return True
```

#### 更新配额

```python
class QuotaManager:
    def update_quota(
        self,
        agent_id: str,
        resource_type: ResourceType,
        amount: int
    ) -> bool:
        """
        更新配额使用量

        Args:
            agent_id: Agent ID
            resource_type: 资源类型
            amount: 使用量（正数增加，负数减少）

        Returns:
            bool: 更新是否成功
        """
        # 更新Agent配额
        if not self._update_agent_quota(agent_id, resource_type, amount):
            return False

        # 更新全局配额
        if not self._update_global_quota(resource_type, amount):
            return False

        return True
```

#### 使用率监控

```python
class QuotaManager:
    def get_usage_rate(self, agent_id: str) -> Dict[str, float]:
        """
        获取Agent配额使用率

        Args:
            agent_id: Agent ID

        Returns:
            Dict[str, float]: 使用率字典
        """
        usage_rates = {}

        for resource_type in ResourceType:
            agent_quota = self.agent_quotas.get(agent_id, {}).get(resource_type, {})
            agent_usage = self.agent_usage.get(agent_id, {}).get(resource_type, 0)

            if agent_quota:
                max_value = agent_quota.get('max_locks', agent_quota.get('max_calls', 0))
                if max_value > 0:
                    usage_rates[resource_type.value] = agent_usage / max_value

        return usage_rates

    def get_global_usage_rate(self) -> Dict[str, float]:
        """
        获取全局配额使用率

        Returns:
            Dict[str, float]: 使用率字典
        """
        usage_rates = {}

        for key, quota in self.global_quota.items():
            usage = self.global_usage.get(key, 0)
            if quota > 0:
                usage_rates[key] = usage / quota

        return usage_rates
```

#### 超限告警

```python
class QuotaManager:
    def check_over_limit(self, agent_id: str) -> List[OverLimitAlert]:
        """
        检查是否超限

        Args:
            agent_id: Agent ID

        Returns:
            List[OverLimitAlert]: 超限告警列表
        """
        alerts = []

        # 检查Agent配额
        for resource_type in ResourceType:
            usage_rate = self.get_usage_rate(agent_id).get(resource_type.value, 0)
            if usage_rate > 0.9:  # 超过90%
                alerts.append(OverLimitAlert(
                    agent_id=agent_id,
                    resource_type=resource_type,
                    usage_rate=usage_rate,
                    severity=AlertSeverity.HIGH if usage_rate > 1.0 else AlertSeverity.MEDIUM
                ))

        # 检查全局配额
        for key, quota in self.global_quota.items():
            usage = self.global_usage.get(key, 0)
            usage_rate = usage / quota if quota > 0 else 0
            if usage_rate > 0.9:
                alerts.append(OverLimitAlert(
                    agent_id='global',
                    resource_type=key,
                    usage_rate=usage_rate,
                    severity=AlertSeverity.HIGH if usage_rate > 1.0 else AlertSeverity.MEDIUM
                ))

        return alerts
```

### 配置参数

```yaml
quota_manager:
  # Agent默认配额
  default_agent_quotas:
    file:
      max_locks: 10
    api:
      max_calls: 100
    compute:
      max_cpu_percent: 50
      max_memory_mb: 1024
    terminal:
      max_sessions: 1
    secret:
      max_reads: 50

  # 全局配额
  global_quotas:
    max_active_agents: 10
    max_file_locks: 100
    max_api_calls: 1000
    max_cpu_percent: 80
    max_memory_mb: 8192

  # 告警配置
  alerts:
    enabled: true
    warning_threshold: 0.9  # 90%
    critical_threshold: 1.0  # 100%
```

## ResourceCoordinator 主协调器

### 功能概述

ResourceCoordinator是MARC-Lite的主协调器，整合了资源注册中心、锁管理器、调度队列、死锁预防器和配额管理器，提供统一的资源协调接口。

### 核心方法

#### 资源注册/注销

```python
class ResourceCoordinator:
    def register_resource(
        self,
        resource_id: str,
        type: ResourceType,
        metadata: Dict[str, Any],
        capacity: Optional[int] = None
    ) -> bool:
        """
        注册资源

        Args:
            resource_id: 资源唯一标识
            type: 资源类型
            metadata: 资源元数据
            capacity: 资源容量

        Returns:
            bool: 注册是否成功
        """
        return self.registry.register_resource(
            resource_id,
            type,
            metadata,
            capacity
        )

    def unregister_resource(self, resource_id: str) -> bool:
        """
        注销资源

        Args:
            resource_id: 资源唯一标识

        Returns:
            bool: 注销是否成功
        """
        return self.registry.unregister_resource(resource_id)
```

#### 锁获取/释放

```python
class ResourceCoordinator:
    def acquire_lock(
        self,
        resource_id: str,
        agent_id: str,
        lock_type: LockType,
        timeout: Optional[float] = None
    ) -> LockToken:
        """
        获取资源锁

        Args:
            resource_id: 资源唯一标识
            agent_id: Agent唯一标识
            lock_type: 锁类型
            timeout: 超时时间

        Returns:
            LockToken: 锁令牌
        """
        # 检查配额
        if not self.quota_manager.check_quota(agent_id, ResourceType[lock_type.name]):
            raise QuotaExceededError(agent_id, ResourceType[lock_type.name])

        # 获取锁
        lock_token = self.lock_manager.acquire_lock(
            resource_id,
            agent_id,
            lock_type,
            timeout
        )

        # 更新配额
        self.quota_manager.update_quota(agent_id, ResourceType[lock_type.name], 1)

        return lock_token

    def release_lock(self, lock_token: LockToken) -> bool:
        """
        释放资源锁

        Args:
            lock_token: 锁令牌

        Returns:
            bool: 释放是否成功
        """
        # 释放锁
        success = self.lock_manager.release_lock(lock_token)

        if success:
            # 更新配额
            self.quota_manager.update_quota(
                lock_token.agent_id,
                ResourceType[lock_token.lock_type.name],
                -1
            )

        return success
```

#### 任务调度

```python
class ResourceCoordinator:
    def schedule_task(
        self,
        task: Task,
        priority: Priority = Priority.MEDIUM
    ) -> str:
        """
        调度任务

        Args:
            task: 任务对象
            priority: 任务优先级

        Returns:
            str: 任务ID
        """
        return self.scheduler.add_task(task, priority)

    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个待执行任务

        Returns:
            Optional[Task]: 任务对象
        """
        return self.scheduler.get_next_task()

    def complete_task(self, task_id: str, result: Any = None) -> bool:
        """
        完成任务

        Args:
            task_id: 任务ID
            result: 任务结果

        Returns:
            bool: 是否成功
        """
        return self.scheduler.complete_task(task_id, result)
```

#### 死锁检测/恢复

```python
class ResourceCoordinator:
    def detect_deadlock(self) -> Set[str]:
        """
        检测死锁

        Returns:
            Set[str]: 涉及死锁的Agent集合
        """
        return self.deadlock_preventer.detect_deadlock()

    def resolve_deadlock(self) -> bool:
        """
        解决死锁

        Returns:
            bool: 是否成功
        """
        # 检测死锁
        deadlocked_agents = self.detect_deadlock()

        if not deadlocked_agents:
            return True

        # 选择受害者
        victim = self.deadlock_preventer.select_victim(deadlocked_agents)

        # 回退受害者
        return self._rollback_agent(victim)
```

#### 状态查询

```python
class ResourceCoordinator:
    def get_status(self) -> ResourceStatusReport:
        """
        获取资源状态报告

        Returns:
            ResourceStatusReport: 状态报告
        """
        report = ResourceStatusReport()

        # 资源统计
        report.total_resources = len(self.registry.resources)
        report.available_resources = len([
            r for r in self.registry.resources.values()
            if r.status == ResourceStatus.AVAILABLE
        ])
        report.locked_resources = len([
            r for r in self.registry.resources.values()
            if r.status == ResourceStatus.LOCKED
        ])

        # 锁统计
        report.total_locks = len(self.lock_manager.locks)
        report.shared_locks = len([
            l for l in self.lock_manager.locks.values()
            if l.lock_type == LockType.SHARED
        ])
        report.exclusive_locks = len([
            l for l in self.lock_manager.locks.values()
            if l.lock_type == LockType.EXCLUSIVE
        ])

        # 任务统计
        report.total_tasks = len(self.scheduler.tasks)
        report.pending_tasks = len([
            t for t in self.scheduler.tasks.values()
            if t.status == TaskStatus.PENDING
        ])
        report.running_tasks = len([
            t for t in self.scheduler.tasks.values()
            if t.status == TaskStatus.RUNNING
        ])

        # 配额使用率
        report.global_usage_rate = self.quota_manager.get_global_usage_rate()

        # 告警
        report.alerts = self.quota_manager.check_over_limit('global')

        return report

    def print_status(self):
        """
        打印资源状态（--status命令）
        """
        report = self.get_status()

        print("=" * 60)
        print("MARC-Lite 资源协调系统状态")
        print("=" * 60)
        print()
        print("资源统计:")
        print(f"  总资源数: {report.total_resources}")
        print(f"  可用资源: {report.available_resources}")
        print(f"  锁定资源: {report.locked_resources}")
        print()
        print("锁统计:")
        print(f"  总锁数: {report.total_locks}")
        print(f"  共享锁: {report.shared_locks}")
        print(f"  独占锁: {report.exclusive_locks}")
        print()
        print("任务统计:")
        print(f"  总任务数: {report.total_tasks}")
        print(f"  待执行: {report.pending_tasks}")
        print(f"  执行中: {report.running_tasks}")
        print()
        print("全局配额使用率:")
        for key, rate in report.global_usage_rate.items():
            status = "🟢" if rate < 0.7 else "🟡" if rate < 0.9 else "🔴"
            print(f"  {status} {key}: {rate:.1%}")
        print()
        if report.alerts:
            print("告警:")
            for alert in report.alerts:
                print(f"  ⚠️  {alert.agent_id} - {alert.resource_type}: {alert.usage_rate:.1%}")
        print()
        print("=" * 60)
```

## 使用示例

### 示例1: 基本资源使用

```python
from resource_coordinator import ResourceCoordinator, ResourceType, LockType, Priority

# 初始化协调器
coordinator = ResourceCoordinator()

# 注册资源
coordinator.register_resource(
    resource_id='file:src/main.py',
    type=ResourceType.FILE,
    metadata={'path': 'src/main.py', 'mode': 'rw'}
)

coordinator.register_resource(
    resource_id='api:github',
    type=ResourceType.API,
    metadata={'endpoint': 'https://api.github.com', 'rate_limit': 60}
)

# Agent获取锁
lock_token = coordinator.acquire_lock(
    resource_id='file:src/main.py',
    agent_id='code-reviewer',
    lock_type=LockType.SHARED
)

try:
    # 使用资源
    with open('src/main.py', 'r') as f:
        content = f.read()
    print(f"文件内容: {len(content)} 字符")
finally:
    # 释放锁
    coordinator.release_lock(lock_token)
```

### 示例2: 多Agent并发执行

```python
from concurrent.futures import ThreadPoolExecutor

def review_code(agent_id: str, file_path: str):
    """代码审查任务"""
    coordinator = ResourceCoordinator()

    # 获取文件锁
    lock_token = coordinator.acquire_lock(
        resource_id=f'file:{file_path}',
        agent_id=agent_id,
        lock_type=LockType.SHARED
    )

    try:
        # 执行审查
        print(f"{agent_id} 开始审查 {file_path}")
        # ... 审查逻辑
        print(f"{agent_id} 完成审查")
    finally:
        # 释放锁
        coordinator.release_lock(lock_token)

# 并发执行多个Agent
with ThreadPoolExecutor(max_workers=3) as executor:
    executor.submit(review_code, 'frontend-reviewer', 'src/main.py')
    executor.submit(review_code, 'security-reviewer', 'src/main.py')
    executor.submit(review_code, 'performance-reviewer', 'src/main.py')
```

### 示例3: 死锁检测与恢复

```python
# 检测死锁
deadlocked_agents = coordinator.detect_deadlock()

if deadlocked_agents:
    print(f"检测到死锁，涉及Agent: {deadlocked_agents}")

    # 自动解决死锁
    success = coordinator.resolve_deadlock()
    if success:
        print("死锁已解决")
    else:
        print("死锁解决失败")
```

### 示例4: 配额管理

```python
# 设置Agent配额
coordinator.quota_manager.set_agent_quota(
    agent_id='code-generator',
    quotas={
        ResourceType.FILE: {'max_locks': 10},
        ResourceType.API: {'max_calls': 100}
    }
)

# 检查配额
if coordinator.quota_manager.check_quota('code-generator', ResourceType.FILE):
    print("配额充足，可以获取锁")
else:
    print("配额不足")

# 查看使用率
usage_rate = coordinator.quota_manager.get_usage_rate('code-generator')
print(f"配额使用率: {usage_rate}")

# 检查超限告警
alerts = coordinator.quota_manager.check_over_limit('code-generator')
for alert in alerts:
    print(f"⚠️  告警: {alert.resource_type} 使用率 {alert.usage_rate:.1%}")
```

### 示例5: 状态查询

```python
# 查看系统状态
coordinator.print_status()

# 或者获取状态报告
report = coordinator.get_status()
print(f"总资源数: {report.total_resources}")
print(f"总锁数: {report.total_locks}")
print(f"待执行任务: {report.pending_tasks}")
```

## 最佳实践

### 1. 合理设置资源容量

根据实际需求设置资源容量，避免过度分配或不足。

```python
# 好的做法
coordinator.register_resource(
    resource_id='compute:cpu',
    type=ResourceType.COMPUTE,
    metadata={
        'cpu_cores': 4,  # 实际CPU核心数
        'memory_mb': 8192  # 实际内存大小
    }
)

# 不好的做法
coordinator.register_resource(
    resource_id='compute:cpu',
    type=ResourceType.COMPUTE,
    metadata={
        'cpu_cores': 100,  # 过度分配
        'memory_mb': 102400  # 超出实际容量
    }
)
```

### 2. 使用try-finally确保锁释放

始终使用try-finally确保锁被释放，避免死锁。

```python
lock_token = coordinator.acquire_lock(
    resource_id='file:src/main.py',
    agent_id='code-reviewer',
    lock_type=LockType.SHARED
)

try:
    # 使用资源
    # ...
finally:
    # 确保锁被释放
    coordinator.release_lock(lock_token)
```

### 3. 合理设置锁超时

为锁请求设置合理的超时时间，避免无限等待。

```python
# 好的做法
lock_token = coordinator.acquire_lock(
    resource_id='file:src/main.py',
    agent_id='code-reviewer',
    lock_type=LockType.SHARED,
    timeout=30  # 30秒超时
)

# 不好的做法
lock_token = coordinator.acquire_lock(
    resource_id='file:src/main.py',
    agent_id='code-reviewer',
    lock_type=LockType.SHARED,
    timeout=None  # 无限等待，可能导致死锁
)
```

### 4. 定期检查配额使用率

定期检查配额使用率，及时发现和解决资源争用问题。

```python
# 定期检查
import time

while True:
    alerts = coordinator.quota_manager.check_over_limit('global')
    if alerts:
        print("发现超限告警:")
        for alert in alerts:
            print(f"  {alert.resource_type}: {alert.usage_rate:.1%}")
    time.sleep(60)  # 每分钟检查一次
```

### 5. 使用批处理减少锁竞争

对于批量操作，使用批处理合并减少锁竞争。

```python
# 不好的做法：逐个获取锁
for file_path in file_paths:
    lock_token = coordinator.acquire_lock(
        resource_id=f'file:{file_path}',
        agent_id='code-reviewer',
        lock_type=LockType.SHARED
    )
    # ... 处理文件
    coordinator.release_lock(lock_token)

# 好的做法：批处理
task_ids = []
for file_path in file_paths:
    task_id = coordinator.schedule_task(
        Task(
            type=TaskType.FILE_REVIEW,
            agent_id='code-reviewer',
            resources=[f'file:{file_path}']
        )
    )
    task_ids.append(task_id)

# 合并批处理任务
merged_task_id = coordinator.scheduler.merge_batch_tasks(task_ids)
```

## 与其他模块的集成

### 与四维防线的集成

四维防线使用MARC-Lite管理资源，避免资源竞争。

```python
from four_d_defense import FourDimensionalDefense

# 初始化
defense = FourDimensionalDefense()
coordinator = ResourceCoordinator()

# 注册资源
coordinator.register_resource(
    resource_id='four_d_defense:compute',
    type=ResourceType.COMPUTE,
    metadata={'cpu_cores': 2, 'memory_mb': 4096}
)

# 执行检查时获取资源
lock_token = coordinator.acquire_lock(
    resource_id='four_d_defense:compute',
    agent_id='defense-agent',
    lock_type=LockType.EXCLUSIVE
)

try:
    result = defense.run_full_check(input_data)
finally:
    coordinator.release_lock(lock_token)
```

### 与操作优先级控制器的集成

MARC-Lite根据操作优先级调整资源分配策略。

```python
from operation_priority import OperationPriorityController

# 获取操作优先级
priority, reason = OperationPriorityController.decide(task_context)

# 根据优先级调整配额
if priority == OperationPriority.MANUAL:
    # 手动操作，分配更多资源
    coordinator.quota_manager.set_agent_quota(
        agent_id='manual-agent',
        quotas={
            ResourceType.FILE: {'max_locks': 20},
            ResourceType.COMPUTE: {'max_cpu_percent': 80}
        }
    )
elif priority == OperationPriority.SCRIPT:
    # 脚本操作，使用标准配额
    coordinator.quota_manager.set_agent_quota(
        agent_id='script-agent',
        quotas={
            ResourceType.FILE: {'max_locks': 10},
            ResourceType.COMPUTE: {'max_cpu_percent': 50}
        }
    )
```

### 与密钥管理系统的集成

MARC-Lite管理密钥资源的访问，确保密钥安全。

```python
from secrets_manager import SecretsManager

# 注册密钥资源
coordinator.register_resource(
    resource_id='secret:api_key:github',
    type=ResourceType.SECRET,
    metadata={
        'key_type': 'api_key',
        'service': 'github',
        'read_once': True
    }
)

# 获取密钥
lock_token = coordinator.acquire_lock(
    resource_id='secret:api_key:github',
    agent_id='api-client',
    lock_type=LockType.SHARED
)

try:
    # 读取密钥
    secrets_manager = SecretsManager()
    secrets_manager.load()
    api_key = secrets_manager.get('GITHUB_API_KEY')
    print(f"API密钥: {api_key[:10]}...")
finally:
    # 释放锁（密钥自动失效）
    coordinator.release_lock(lock_token)
```

## 故障排查

### 问题1: 频繁死锁

**症状**: 系统频繁检测到死锁。

**排查步骤**:
1. 检查资源获取顺序是否一致
2. 检查锁超时设置是否合理
3. 检查是否有Agent长时间持有锁
4. 检查资源容量是否充足

**解决方案**:
```python
# 1. 强制执行资源顺序
coordinator.deadlock_preventer.resource_ordering.enforce_order = True

# 2. 设置合理的锁超时
coordinator.lock_manager.default_timeout = 30

# 3. 启用锁清理
coordinator.lock_manager._start_cleanup_thread()
```

### 问题2: 配额超限

**症状**: Agent频繁遇到配额超限错误。

**排查步骤**:
1. 检查配额设置是否合理
2. 检查是否有Agent占用过多资源
3. 检查是否有资源泄漏

**解决方案**:
```python
# 1. 调整配额
coordinator.quota_manager.set_agent_quota(
    agent_id='code-generator',
    quotas={
        ResourceType.FILE: {'max_locks': 20},  # 从10增加到20
        ResourceType.API: {'max_calls': 200}  # 从100增加到200
    }
)

# 2. 检查资源泄漏
locks = coordinator.lock_manager.get_agent_locks('code-generator')
print(f"Agent持有的锁数量: {len(locks)}")

# 3. 清理过期锁
coordinator.lock_manager._cleanup_expired_locks()
```

### 问题3: 任务积压

**症状**: 调度队列中任务积压严重。

**排查步骤**:
1. 检查任务执行时间是否过长
2. 检查是否有任务卡死
3. 检查资源是否充足

**解决方案**:
```python
# 1. 查看任务状态
report = coordinator.get_status()
print(f"待执行任务: {report.pending_tasks}")
print(f"执行中任务: {report.running_tasks}")

# 2. 启用抢占式调度
coordinator.scheduler.preemptive_scheduling.enabled = True

# 3. 增加资源容量
coordinator.register_resource(
    resource_id='compute:cpu:worker2',
    type=ResourceType.COMPUTE,
    metadata={'cpu_cores': 4, 'memory_mb': 8192}
)
```

## 性能优化

### 1. 使用连接池

对于频繁使用的资源（如API连接），使用连接池减少创建开销。

```python
class APIConnectionPool:
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()

    def get_connection(self) -> APIConnection:
        with self.lock:
            if self.connections:
                return self.connections.pop()
            return APIConnection()

    def return_connection(self, connection: APIConnection):
        with self.lock:
            if len(self.connections) < self.max_connections:
                self.connections.append(connection)
```

### 2. 异步锁获取

使用异步方式获取锁，提高并发性能。

```python
import asyncio

async def acquire_lock_async(
    coordinator: ResourceCoordinator,
    resource_id: str,
    agent_id: str,
    lock_type: LockType
) -> LockToken:
    """异步获取锁"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        coordinator.acquire_lock,
        resource_id,
        agent_id,
        lock_type
    )
```

### 3. 批量操作

对于批量操作，使用批处理接口减少锁获取次数。

```python
# 批量获取锁
lock_tokens = []
for resource_id in resource_ids:
    lock_token = coordinator.acquire_lock(
        resource_id,
        agent_id,
        lock_type
    )
    lock_tokens.append(lock_token)

try:
    # 批量操作
    # ...
finally:
    # 批量释放锁
    for lock_token in lock_tokens:
        coordinator.release_lock(lock_token)
```

## 总结

MARC-Lite资源协调系统是Sanliu v4.0的核心组件，通过资源注册、锁管理、调度队列、死锁预防和配额管理等五大子系统，有效解决了多Agent并发执行时的资源竞争、死锁、饥饿等问题。该系统具有以下特点:

- **全面性**: 覆盖资源管理的全生命周期
- **灵活性**: 支持多种资源类型和锁策略
- **可靠性**: 内置死锁预防和恢复机制
- **可扩展性**: 易于添加新的资源类型和调度策略
- **高性能**: 支持连接池、异步操作和批量处理

通过合理配置和使用MARC-Lite系统，可以显著提高多Agent系统的并发性能和稳定性。
