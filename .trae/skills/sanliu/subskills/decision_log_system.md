# Decision Log 决策日志系统 (Decision Log System)

## 概述

Decision Log 决策日志系统是 Sanliu v4.0 的透明化决策记录基础设施，基于 **OpenCode** 开源理念的哲学内化，实现决策全生命周期的记录、追踪、评估和统计。该系统确保每一个重要的技术选择、架构决策和方案取舍都有据可查，支持团队协作和项目演进。

### 核心理念

- **透明化**: 所有重要决策公开记录，可追溯、可审计
- **结构化**: 使用统一的格式记录决策的各个方面
- **可评估**: 支持对决策效果进行事后评估
- **持续学习**: 从历史决策中积累经验，指导未来选择
- **OpenCode哲学**: 借鉴开源项目的透明决策实践

### 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                  Decision Log 决策日志系统架构                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           决策生成 (Decision Generation)                   │  │
│  │  ├─ DEC-YYYYMMDD-NNN ID格式                               │  │
│  │  ├─ 标题与描述                                           │  │
│  │  ├─ 备选方案 (Alternatives)                              │  │
│  │  ├─ 选择理由 (Rationale)                                 │  │
│  │  ├─ 影响范围 (Impact)                                    │  │
│  │  └─ 风险评估 (Risk Assessment)                            │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          决策存储 (Decision Storage)                      │  │
│  │  ├─ Markdown格式 (.md) - 人可读                          │  │
│  │  ├─ JSON格式 (.json) - 程序可读                           │  │
│  │  ├─ 持久化计数器 (Persistent Counter)                    │  │
│  │  └─ 目录组织: logs/decision_logs/                        │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         决策查询 (Decision Query)                         │  │
│  │  ├─ 按ID查询                                             │  │
│  │  ├─ 按关键词搜索                                         │  │
│  │  ├─ 按日期范围筛选                                       │  │
│  │  ├─ 按状态筛选 (pending/accepted/rejected/superseded)   │  │
│  │  └─ 按影响范围筛选                                       │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │        效果评估 (Outcome Evaluation)                      │  │
│  │  ├─ 记录实际结果                                         │  │
│  │  ├─ 对比预期 vs 实际                                     │  │
│  │  ├─ 评分 (1-5星)                                         │  │
│  │  ├─ 经验教训提取                                         │  │
│  │  └─ 后续行动建议                                         │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         ↓                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          统计分析 (Statistics & Analytics)                │  │
│  │  ├─ 决策数量趋势                                         │  │
│  │  ├─ 决策类型分布                                         │  │
│  │  ├─ 成功率统计                                           │  │
│  │  ├─ 影响范围分布                                         │  │
│  │  └─ 决策周期分析                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              OpenCode 透明化哲学                          │  │
│  │  ├─ 决策链路可视化                                        │  │
│  │  ├─ 依赖关系追踪                                         │  │
│  │  ├─ 变更影响分析                                         │  │
│  │  └─ 社区参与记录                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Decision Log 数据模型

### 决策ID格式

```
DEC-YYYYMMDD-NNN

示例:
- DEC-20240101-001  # 2024年第一个决策
- DEC-20240115-023  # 2024年第23个决策
- DEC-20240228-156  # 2024年第156个决策
```

### 数据类定义

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
import json

class DecisionStatus(Enum):
    """决策状态"""
    PENDING = "pending"           # 待定
    ACCEPTED = "accepted"         # 已采纳
    REJECTED = "rejected"         # 已拒绝
    SUPERSEDED = "superseded"     # 已被替代
    DEPRECATED = "deprecated"     # 已废弃

class DecisionCategory(Enum):
    """决策类别"""
    ARCHITECTURE = "architecture"       # 架构设计
    TECHNOLOGY = "technology"           # 技术选型
    API_DESIGN = "api_design"           # API设计
    DATABASE = "database"               # 数据库
    SECURITY = "security"               # 安全
    PERFORMANCE = "performance"         # 性能
    DEPLOYMENT = "deployment"           # 部署
    PROCESS = "process"                 # 流程
    FEATURE = "feature"                 # 功能
    REFACTORING = "refactoring"         # 重构

class ImpactLevel(Enum):
    """影响级别"""
    LOW = "low"             # 低: 仅影响单个模块
    MEDIUM = "medium"       # 中: 影响多个模块
    HIGH = "high"           # 高: 影响整个系统
    CRITICAL = "critical"   # 严重: 影响核心功能或安全

class RiskLevel(Enum):
    """风险等级"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class Alternative:
    """备选方案"""
    name: str                        # 方案名称
    description: str                 # 方案描述
    pros: List[str] = field(default_factory=list)     # 优点
    cons: List[str] = field(default_factory=list)     # 缺点
    risk_level: RiskLevel = RiskLevel.MEDIUM          # 风险等级
    effort_estimate: str = ""        # 工作量估算

@dataclass
class Decision:
    """决策记录"""
    decision_id: str                 # 决策ID (DEC-YYYYMMDD-NNN)
    title: str                      # 决策标题
    description: str                 # 详细描述
    category: DecisionCategory      # 类别
    status: DecisionStatus = DecisionStatus.PENDING
    
    # 决策内容
    context: str = ""               # 背景上下文
    alternatives: List[Alternative] = field(default_factory=list)
    selected_alternative: Optional[str] = None  # 选中的方案名
    rationale: str = ""              # 选择理由
    impact: ImpactLevel = ImpactLevel.MEDIUM  # 影响范围
    risk_assessment: str = ""       # 风险评估
    
    # 元数据
    author: str = ""                 # 决策者
    reviewers: List[str] = field(default_factory=list)  # 审核者
    stakeholders: List[str] = field(default_factory=list)  # 利益相关者
    related_decisions: List[str] = field(default_factory=list)  # 关联决策
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    decided_at: Optional[datetime] = None
    
    # 效果评估
    outcome: Optional[str] = None   # 实际结果
    outcome_rating: Optional[int] = None  # 效果评分 (1-5)
    lessons_learned: str = ""       # 经验教训
    follow_up_actions: List[str] = field(default_factory=list)  # 后续行动
    
    # 附件
    attachments: List[str] = field(default_factory=list)  # 附件路径
    references: List[str] = field(default_factory=list)   # 参考资料

@dataclass
class OutcomeEvaluation:
    """效果评估"""
    decision_id: str
    evaluated_at: datetime = field(default_factory=datetime.now)
    evaluator: str = ""
    
    # 结果对比
    expected_outcome: str = ""
    actual_outcome: str = ""
    outcome_match: bool = False
    
    # 评分维度
    technical_correctness: int = 3   # 技术正确性 (1-5)
    business_value: int = 3          # 业务价值 (1-5)
    implementation_ease: int = 3     # 实现难度 (1-5)
    long_term_sustainability: int = 3  # 可持续性 (1-5)
    
    overall_rating: int = 3          # 总体评分 (1-5)
    
    # 反思
    what_went_well: str = ""         # 做得好的地方
    what_could_improve: str = ""     # 可以改进的地方
    would_change_decision: bool = False  # 是否会改变决策
    alternative_if_changed: str = ""  # 如果改变会选择什么
    
    recommendations: List[str] = field(default_factory=list)

@dataclass
class DecisionStatistics:
    """决策统计"""
    total_decisions: int = 0
    by_status: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    by_impact: Dict[str, int] = field(default_factory=dict)
    
    success_rate: float = 0.0       # 成功率（基于outcome rating >= 3）
    average_rating: float = 0.0     # 平均评分
    
    decisions_this_month: int = 0
    decisions_this_quarter: int = 0
    avg_decision_cycle_days: float = 0.0  # 平均决策周期
```

## 核心API接口

### DecisionLog 主类

```python
class DecisionLog:
    """
    Decision Log 决策日志系统主类
    
    基于OpenCode透明化理念，提供完整的决策生命周期管理
    """
    
    def __init__(self, log_dir: str = 'logs/decision_logs'):
        """
        初始化DecisionLog
        
        Args:
            log_dir: 日志存储目录
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载计数器
        self._load_counter()
        
        # 加载索引
        self._load_index()
    
    def generate(
        self,
        title: str,
        description: str,
        category: Union[DecisionCategory, str],
        context: str = "",
        alternatives: List[Dict] = None,
        selected: Optional[int] = None,
        rationale: str = "",
        impact: Union[ImpactLevel, str] = ImpactLevel.MEDIUM,
        risk_assessment: str = "",
        author: str = "",
        metadata: dict = None
    ) -> Decision:
        """
        生成新的决策记录
        
        Args:
            title: 决策标题
            description: 详细描述
            category: 决策类别
            context: 背景上下文
            alternatives: 备选方案列表
            selected: 选中的方案索引（从0开始）
            rationale: 选择理由
            impact: 影响级别
            risk_assessment: 风险评估
            author: 决策者
            metadata: 其他元数据
            
        Returns:
            Decision: 创建的决策对象
        """
        # 生成唯一ID
        decision_id = self._generate_id()
        
        # 解析类别
        if isinstance(category, str):
            category = DecisionCategory(category.lower())
        
        # 解析影响级别
        if isinstance(impact, str):
            impact = ImpactLevel(impact.lower())
        
        # 构建备选方案
        alt_objects = []
        if alternatives:
            for alt in alternatives:
                alt_objects.append(Alternative(
                    name=alt.get('name', ''),
                    description=alt.get('description', ''),
                    pros=alt.get('pros', []),
                    cons=alt.get('cons', []),
                    risk_level=RiskLevel(alt.get('risk_level', 'medium')),
                    effort_estimate=alt.get('effort_estimate', '')
                ))
        
        # 获取选中的方案名
        selected_name = None
        if selected is not None and selected < len(alt_objects):
            selected_name = alt_objects[selected].name
        
        # 创建决策对象
        now = datetime.now()
        decision = Decision(
            decision_id=decision_id,
            title=title,
            description=description,
            category=category,
            status=DecisionStatus.ACCEPTED if selected is not None else DecisionStatus.PENDING,
            context=context,
            alternatives=alt_objects,
            selected_alternative=selected_name,
            rationale=rationale,
            impact=impact,
            risk_assessment=risk_assessment,
            author=author or self._get_default_author(),
            created_at=now,
            updated_at=now,
            decided_at=now if selected is not None else None,
            **(metadata or {})
        )
        
        # 保存决策
        self._save_decision(decision)
        
        return decision
    
    def get(self, decision_id: str) -> Optional[Decision]:
        """
        获取决策记录
        
        Args:
            decision_id: 决策ID
            
        Returns:
            Optional[Decision]: 决策对象，如果不存在返回None
        """
        md_path = self.log_dir / f"{decision_id}.md"
        json_path = self.log_dir / f"{decision_id}.json"
        
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._dict_to_decision(data)
        
        if md_path.exists():
            return self._parse_markdown(md_path)
        
        return None
    
    def list_decisions(
        self,
        status: Optional[DecisionStatus] = None,
        category: Optional[DecisionCategory] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        keyword: Optional[str] = None,
        limit: int = 50
    ) -> List[Decision]:
        """
        列出决策记录
        
        Args:
            status: 按状态筛选
            category: 按类别筛选
            start_date: 开始日期
            end_date: 结束日期
            keyword: 关键词搜索
            limit: 返回数量限制
            
        Returns:
            List[Decision]: 决策列表
        """
        decisions = []
        
        for json_file in sorted(self.log_dir.glob("*.json")):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                decision = self._dict_to_decision(data)
                
                # 应用筛选条件
                if status and decision.status != status:
                    continue
                if category and decision.category != category:
                    continue
                if start_date and decision.created_at < start_date:
                    continue
                if end_date and decision.created_at > end_date:
                    continue
                if keyword:
                    search_text = f"{decision.title} {decision.description}".lower()
                    if keyword.lower() not in search_text:
                        continue
                
                decisions.append(decision)
                
                if len(decisions) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"读取决策文件失败 {json_file}: {e}")
        
        # 按创建时间倒序排列
        decisions.sort(key=lambda d: d.created_at, reverse=True)
        
        return decisions
    
    def evaluate_outcome(
        self,
        decision_id: str,
        outcome: str,
        rating: int,
        evaluator: str = "",
        lessons: str = "",
        follow_ups: List[str] = None
    ) -> OutcomeEvaluation:
        """
        评估决策效果
        
        Args:
            decision_id: 决策ID
            outcome: 实际结果描述
            rating: 效果评分 (1-5)
            evaluator: 评估者
            lessons: 经验教训
            follow_ups: 后续行动
            
        Returns:
            OutcomeEvaluation: 评估结果
        """
        decision = self.get(decision_id)
        if not decision:
            raise DecisionNotFoundError(decision_id)
        
        # 创建评估
        evaluation = OutcomeEvaluation(
            decision_id=decision_id,
            evaluated_at=datetime.now(),
            evaluator=evaluator,
            expected_outcome=decision.description,
            actual_outcome=outcome,
            outcome_match=self._assess_outcome_match(decision, outcome),
            overall_rating=rating,
            lessons_learned=lessons,
            follow_up_actions=follow_ups or []
        )
        
        # 更新决策记录
        decision.outcome = outcome
        decision.outcome_rating = rating
        decision.lessons_learned = lessons
        decision.follow_up_actions = follow_ups or []
        decision.updated_at = datetime.now()
        
        # 保存更新
        self._save_decision(decision)
        self._save_evaluation(evaluation)
        
        return evaluation
    
    def get_statistics(self) -> DecisionStatistics:
        """
        获取决策统计信息
        
        Returns:
            DecisionStatistics: 统计数据
        """
        all_decisions = self.list_decisions(limit=10000)
        
        stats = DecisionStatistics(total_decisions=len(all_decisions))
        
        # 按状态统计
        for decision in all_decisions:
            status_key = decision.status.value
            stats.by_status[status_key] = stats.by_status.get(status_key, 0) + 1
            
            cat_key = decision.category.value
            stats.by_category[cat_key] = stats.by_category.get(cat_key, 0) + 1
            
            imp_key = decision.impact.value
            stats.by_impact[imp_key] = stats.by_impact.get(imp_key, 0) + 1
        
        # 计算成功率
        rated_decisions = [d for d in all_decisions if d.outcome_rating is not None]
        if rated_decisions:
            successful = sum(1 for d in rated_decisions if d.outcome_rating >= 3)
            stats.success_rate = successful / len(rated_decisions)
            
            ratings = [d.outcome_rating for d in rated_decisions]
            stats.average_rating = sum(ratings) / len(ratings)
        
        # 时间统计
        now = datetime.now()
        month_ago = now.replace(day=1)
        quarter_ago = now.replace(month=((now.month - 1) // 3 * 3 + 1), day=1)
        
        stats.decisions_this_month = sum(
            1 for d in all_decisions if d.created_at >= month_ago
        )
        stats.decisions_this_quarter = sum(
            1 for d in all_decisions if d.created_at >= quarter_ago
        )
        
        # 平均决策周期
        decided = [d for d in all_decisions if d.decided_at and d.created_at]
        if decided:
            cycles = [(d.decided_at - d.created_at).days for d in decided]
            stats.avg_decision_cycle_days = sum(cycles) / len(cycles)
        
        return stats
```

### 内部方法

#### _generate_id() 方法

```python
def _generate_id(self) -> str:
    """生成唯一的决策ID"""
    today = datetime.now().strftime('%Y%m%d')
    
    # 更新计数器
    date_key = today
    if date_key not in self.counter:
        self.counter[date_key] = 0
    
    self.counter[date_key] += 1
    sequence = self.counter[date_key]
    
    # 保存计数器
    self._save_counter()
    
    return f"DEC-{today}-{sequence:03d}"
```

#### _save_decision() 方法

```python
def _save_decision(self, decision: Decision):
    """保存决策到Markdown和JSON两种格式"""
    base_path = self.log_dir / decision.decision_id
    
    # 保存JSON格式
    json_data = self._decision_to_dict(decision)
    with open(f"{base_path}.json", 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
    
    # 保存Markdown格式
    markdown_content = self._decision_to_markdown(decision)
    with open(f"{base_path}.md", 'w', encoding='utf-8', newline='') as f:
        f.write(markdown_content)
    
    # 更新索引
    self._update_index(decision)
```

#### _decision_to_markdown() 方法

```python
def _decision_to_markdown(self, decision: Decision) -> str:
    """将决策转换为Markdown格式"""
    lines = []
    
    # 头部
    lines.append(f"# {decision.decision_id}: {decision.title}")
    lines.append("")
    lines.append(f"> **状态**: `{decision.status.value}` | **类别**: `{decision.category.value}` | **影响**: `{decision.impact.value}`")
    lines.append(f"> **作者**: {decision.author} | **创建时间**: {decision.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if decision.decided_at:
        lines.append(f"> **决定时间**: {decision.decided_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    
    # 描述
    lines.append("## 描述")
    lines.append("")
    lines.append(decision.description)
    lines.append("")
    
    # 背景
    if decision.context:
        lines.append("## 背景")
        lines.append("")
        lines.append(decision.context)
        lines.append("")
    
    # 备选方案
    if decision.alternatives:
        lines.append("## 备选方案")
        lines.append("")
        for i, alt in enumerate(decision.alternatives):
            selected_marker = " ✅" if alt.name == decision.selected_alternative else ""
            lines.append(f"### 方案{i+1}: {alt.name}{selected_marker}")
            lines.append("")
            lines.append(alt.description)
            lines.append("")
            if alt.pros:
                lines.append("**优点**:")
                for pro in alt.pros:
                    lines.append(f"- {pro}")
                lines.append("")
            if alt.cons:
                lines.append("**缺点**:")
                for con in alt.cons:
                    lines.append(f"- {con}")
                lines.append("")
            lines.append(f"- **风险等级**: `{alt.risk_level.value}`")
            if alt.effort_estimate:
                lines.append(f"- **工作量估算**: {alt.effort_estimate}")
            lines.append("")
    
    # 选择理由
    if decision.rationale:
        lines.append("## 选择理由")
        lines.append("")
        lines.append(decision.rationale)
        lines.append("")
    
    # 风险评估
    if decision.risk_assessment:
        lines.append("## 风险评估")
        lines.append("")
        lines.append(decision.risk_assessment)
        lines.append("")
    
    # 效果评估
    if decision.outcome:
        lines.append("## 效果评估")
        lines.append("")
        lines.append(f"**实际结果**: {decision.outcome}")
        if decision.outcome_rating:
            stars = "⭐" * decision.outcome_rating
            lines.append(f"**评分**: {stars} ({decision.outcome_rating}/5)")
        if decision.lessons_learned:
            lines.append("")
            lines.append("**经验教训**:")
            lines.append(decision.lessons_learned)
        lines.append("")
    
    # 元数据
    lines.append("---")
    lines.append(f"*Decision ID: {decision.decision_id}*")
    if decision.related_decisions:
        lines.append(f"*关联决策: {', '.join(decision.related_decisions)}*")
    if decision.references:
        lines.append("*参考资料*:")
        for ref in decision.references:
            lines.append(f"- {ref}")
    
    return '\n'.join(lines)
```

## 使用示例

### 示例1: 创建架构决策

```python
from core.decision_log import DecisionLog, DecisionCategory, ImpactLevel, RiskLevel

# 初始化
dl = DecisionLog()

# 创建架构决策
decision = dl.generate(
    title="采用微服务架构替代单体应用",
    description="将当前的单体应用拆分为用户服务、订单服务、支付服务等独立微服务，以提高系统的可扩展性和维护性",
    category=DecisionCategory.ARCHITECTURE,
    context="当前单体应用已超过50万行代码，部署时间长（15分钟+），新功能开发周期长。团队规模扩大到20人后，代码冲突频繁。",
    alternatives=[
        {
            "name": "微服务架构",
            "description": "按业务领域拆分为多个独立服务",
            "pros": ["独立部署", "技术栈灵活", "故障隔离"],
            "cons": ["分布式复杂性", "运维成本增加", "数据一致性挑战"],
            "risk_level": "high",
            "effort_estimate": "6个月"
        },
        {
            "name": "模块化单体",
            "description": "保持单体但内部模块化",
            "pros": ["简单过渡", "共享数据库", "统一部署"],
            "cons": ["扩展性有限", "耦合风险"],
            "risk_level": "medium",
            "effort_estimate": "2个月"
        },
        {
            "name": "渐进式迁移",
            "description": "逐步将部分功能拆分为服务",
            "pros": ["风险可控", "渐进式学习", "业务连续性"],
            "cons": ["混合架构复杂", "迁移期长"],
            "risk_level": "medium",
            "effort_estimate": "9个月"
        }
    ],
    selected=0,  # 选择微服务架构
    rationale="考虑到业务的快速扩展需求和团队的长期发展，微服务架构虽然初期投入较大，但能更好地支撑未来的增长。我们已有K8s基础设施，可以降低运维复杂度。",
    impact=ImpactLevel.HIGH,
    risk_assessment="主要风险包括：服务间通信延迟、分布式事务处理、监控告警体系建设。将通过引入Service Mesh和事件驱动架构来缓解这些风险。",
    author="架构委员会"
)

print(f"✅ 决策已创建: {decision.decision_id}")
print(f"标题: {decision.title}")
print(f"状态: {decision.status.value}")
```

### 示例2: 查询和搜索决策

```python
# 查询特定决策
decision = dl.get("DEC-20240101-001")

if decision:
    print(f"=== {decision.decision_id} ===")
    print(f"标题: {decision.title}")
    print(f"类别: {decision.category.value}")
    print(f"状态: {decision.status.value}")

# 列出所有架构决策
architectures = dl.list_decisions(category=DecisionCategory.ARCHITECTURE)
print(f"\n找到 {len(architectures)} 个架构决策:")
for dec in architectures[:10]:
    print(f"  [{dec.decision_id}] {dec.title}")

# 搜索包含"数据库"的决策
db_decisions = dl.list_decisions(keyword="数据库")
print(f"\n找到 {len(db_decisions)} 个相关决策:")

# 本月决策
this_month = dl.list_decisions(limit=100)
this_month = [d for d in this_month 
               if d.created_at.month == datetime.now().month]
print(f"\n本月共 {len(this_month)} 个决策")
```

### 示例3: 效果评估

```python
# 6个月后评估决策效果
evaluation = dl.evaluate_outcome(
    decision_id="DEC-20240101-001",
    outcome="微服务架构成功实施，部署时间从15分钟降低到2分钟，新功能开发效率提升40%。但发现服务间调试困难，需要加强链路追踪能力。",
    rating=4,
    evaluator="CTO",
    lessons="1. 应该更早建立统一的日志和追踪标准\n2. API网关的选择非常关键\n3. 团队需要更多分布式系统培训",
    follow_ups=[
        "引入Jaeger进行分布式追踪",
        "建立统一的API规范",
        "组织分布式系统培训"
    ]
)

print(f"=== 效果评估 ===")
print(f"评分: {'⭐' * evaluation.overall_rating} ({evaluation.overall_rating}/5)")
print(f"预期与实际匹配: {'是' if evaluation.outcome_match else '否'}")
print(f"经验教训: {evaluation.lessons_learned[:100]}...")
```

### 示例4: 统计分析

```python
# 获取统计数据
stats = dl.get_statistics()

print("=== 决策统计分析 ===")
print(f"总决策数: {stats.total_decisions}")
print(f"\n按状态分布:")
for status, count in stats.by_status.items():
    print(f"  {status}: {count}")

print(f"\n按类别分布:")
for category, count in stats.by_category.items():
    print(f"  {category}: {count}")

print(f"\n按影响级别分布:")
for impact, count in stats.by_impact.items():
    print(f"  {impact}: {count}")

if stats.success_rate > 0:
    print(f"\n成功率: {stats.success_rate:.1%}")
    print(f"平均评分: {stats.average_rating:.2f}/5")

print(f"\n本月决策数: {stats.decisions_this_month}")
print(f"本季度决策数: {stats.decisions_this_quarter}")
if stats.avg_decision_cycle_days > 0:
    print(f"平均决策周期: {stats.avg_decision_cycle_days:.1f} 天")
```

### 示例5: 在中书省方案审议局中使用

Decision Log系统主要集成在**中书省-方案审议局-决策记录司**中：

```python
# 在方案审议流程中自动记录决策
from sanliu.workflows import ProposalReviewWorkflow

workflow = ProposalReviewWorkflow()

# 审议提案时自动创建决策记录
review_result = workflow.review_proposal(
    proposal_id="PROP-2024-001",
    proposal_content="...",
    auto_record_decision=True  # 自动记录决策
)

if review_result.decision_created:
    print(f"决策已记录: {review_result.decision_id}")
    print(f"查看详情: logs/decision_logs/{review_result.decision_id}.md")
```

## 配置参数

```yaml
decision_log:
  # 存储配置
  storage:
    log_dir: "logs/decision_logs"
    formats:
      - "markdown"  # 人可读
      - "json"     # 程序可读
    backup_enabled: true
    backup_retention_days: 365
  
  # ID配置
  id_format: "DEC-YYYYMMDD-NNN"
  counter_file: ".decision_counter.json"
  
  # 默认值
  defaults:
    author: "auto-detected"  # 自动检测作者
    status: "pending"
    impact: "medium"
  
  # 评估配置
  evaluation:
    min_rating: 1
    max_rating: 5
    require_evaluator: false
    auto_remind_after_days: 180  # 6个月后提醒评估
  
  # 统计配置
  statistics:
    cache_enabled: true
    cache_ttl: 300  # 5分钟缓存
    
  # OpenCode集成
  opencode:
    transparency_mode: true
    link_to_adr: true  # 链接到Architecture Decision Records
    community_review: false  # 是否允许社区评审
```

## 最佳实践

### 1. 重要决策必须记录

对于以下类型的决策，必须使用Decision Log记录：
- 架构变更（如从单体到微服务）
- 技术栈选型（如框架、语言、数据库）
- API设计决策（如REST vs GraphQL）
- 安全相关决策（如认证方式、加密算法）
- 性能优化策略（如缓存策略、CDN使用）

```python
# 好的做法
dl.generate(
    title="采用PostgreSQL作为主数据库",
    description="...",
    category=DecisionCategory.DATABASE,
    ...
)

# 不好的做法：只在代码注释里写
# // We chose PostgreSQL because it's good
```

### 2. 记录备选方案和权衡

不要只记录最终决定，要记录考虑过的所有选项及其优缺点。

```python
# 推荐：完整记录备选方案
dl.generate(
    ...,
    alternatives=[
        {"name": "PostgreSQL", "pros": [...], "cons": [...]},
        {"name": "MySQL", "pros": [...], "cons": [...]},
        {"name": "MongoDB", "pros": [...], "cons": [...]},
    ],
    selected=0,
    rationale="选择了PostgreSQL因为..."
)
```

### 3. 定期评估决策效果

在决策实施后的合理时间点（通常3-6个月）进行效果评估。

```python
# 定期任务：检查未评估的决策
from datetime import timedelta

decisions = dl.list_decisions(status=DecisionStatus.ACCEPTED)
three_months_ago = datetime.now() - timedelta(days=90)

for decision in decisions:
    if (not decision.outcome and 
        decision.created_at < three_months_ago):
        print(f"⚠️  待评估: {decision.decision_id} - {decision.title}")
        print(f"   创建于: {decision.created_at.strftime('%Y-%m-%d')}")
```

### 4. 利用决策关联

通过`related_decisions`字段建立决策之间的关联关系。

```python
# 创建关联决策
dl.generate(
    title="采用Redis作为缓存层",
    ...,
    related_decisions=["DEC-20240101-001"]  # 关联到之前的数据库选型决策
)
```

### 5. 导出和分享决策

Decision Log支持导出为多种格式，便于分享和归档。

```python
# 导出为完整报告
def export_report(output_path: str, format: str = 'markdown'):
    decisions = dl.list_decisions(limit=100)
    stats = dl.get_statistics()
    
    # 生成报告...
```

## 与其他模块的集成

### 与四维防线的集成

四维防线可以在输出质量不达标时自动创建决策日志。

```python
from four_d_defense import FallbackRecoveryLayer

class FallbackRecoveryLayer:
    def process(self, output, metadata):
        result = super().process(output, metadata)
        
        if result.status == LayerStatus.DEGRADED:
            # 自动记录降级决策
            dl = DecisionLog()
            dl.generate(
                title=f"降级策略触发: {metadata.get('task_type', 'unknown')}",
                description=f"四维防线第4层触发降级，原因: 质量评分不足",
                category=DecisionCategory.PROCESS,
                context=f"原始评分: {result.metadata.get('quality_score')}",
                rationale="为避免阻塞开发流程，允许降级模式运行",
                impact=ImpactLevel.LOW
            )
        
        return result
```

### 与操作优先级控制器的集成

当操作优先级控制器做出非默认选择时，记录决策。

```python
from operation_priority import OperationPriorityController

original_priority = Priority.COMMAND
recommended_priority = Priority.MANUAL

if recommended_priority != original_priority:
    dl = DecisionLog()
    dl.generate(
        title=f"操作优先级调整: {task_context['description'][:30]}...",
        description=f"根据任务特征，推荐优先级从{original_priority}调整为{recommended_priority}",
        category=DecisionCategory.PROCESS,
        context=f"任务上下文: {task_context}",
        alternatives=[
            {"name": "命令操作", "cons": ["预演检查耗时"]},
            {"name": "手动操作", "pros": ["精确控制", "可追溯"]}
        ],
        selected=1,
        rationale=f"任务特征: {reason}"
    )
```

### 与Agency Bridge的集成

调用专业Agent的建议也可以作为决策记录的一部分。

```python
from integration.agency_bridge import AgencyBridge

bridge = AgencyBridge()
recommendations = bridge.recommend_agents(task_description)

dl = DecisionLog()
dl.generate(
    title=f"Agent选择: {task_description[:30]}...",
    description="基于任务描述推荐的Agent组合",
    category=DecisionCategory.PROCESS,
    context=f"推荐结果: {[a.agent.name for a in recommendations]}",
    alternatives=[],
    selected=0,
    rationale="选择置信度最高的Agent组合"
)
```

## 故障排查

### 问题1: 决策ID冲突

**症状**: 生成的决策ID与现有记录冲突。

**解决方案**:
```python
# 手动重置计数器
dl = DecisionLog()
dl._reset_counter(date="20240101")  # 重置指定日期的计数器

# 或手动设置下一个序列号
dl.counter["20240101"] = 150
dl._save_counter()
```

### 问题2: 文件编码问题

**症状**: Markdown或JSON文件出现乱码。

**解决方案**:
```python
# 确保使用UTF-8 No BOM编码保存
import os

# 检查文件编码
file_path = Path("logs/decision_logs/DEC-20240101-001.md")
with open(file_path, 'rb') as f:
    raw = f.read(4)
    
bom_markers = {
    b'\xef\xbb\xbf': 'UTF-8 BOM',
    b'\xff\xfe': 'UTF-16 LE',
    b'\xfe\xff': 'UTF-16 BE'
}

for marker, enc in bom_markers.items():
    if raw.startswith(marker):
        print(f"检测到BOM标记: {enc}")
        break
```

### 问题3: 性能问题（大量决策时）

**症状**: 列表查询变慢。

**解决方案**:
```python
# 启用索引缓存
dl = DecisionLog(config={'statistics': {'cache_enabled': True}})

# 或限制查询范围
recent = dl.list_decisions(start_date=datetime.now() - timedelta(days=30))

# 或只查询特定类别
arch = dl.list_decisions(category=DecisionCategory.ARCHITECTURE)
```

## 总结

Decision Log决策日志系统是Sanliu v4.0的透明化决策基础设施，基于OpenCode开源理念，提供完整的决策生命周期管理能力。该系统具有以下特点:

- **透明化**: 所有重要决策公开记录，支持追溯和审计
- **结构化**: 统一的格式记录决策的各个方面（背景、方案、理由、影响、风险）
- **双格式存储**: 同时保存Markdown（人可读）和JSON（程序可读）格式
- **可评估**: 支持事后效果评估，积累经验教训
- **统计分析**: 提供丰富的统计数据，帮助理解决策模式和趋势
- **OpenCode集成**: 支持ADR（Architecture Decision Records）标准和社区协作

通过合理使用Decision Log系统，可以提高团队的技术决策质量，增强项目的可维护性和可追溯性。
