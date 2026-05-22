#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
需求变更影响分析器
================

本模块实现了需求变更影响的全面分析功能，包括：
1. 变更影响分析 - 分析变更对系统的整体影响
2. 变更影响范围分析 - 分析变更的影响范围和传播路径
3. 受影响测试识别 - 识别需要更新的测试用例
4. 受影响代码识别 - 识别需要修改的代码元素

核心功能：
- 基于追溯链的影响分析
- 基于依赖关系的影响传播分析
- 风险评估和优先级排序
- 影响范围可视化支持
"""

import json
import sqlite3
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Set
from datetime import datetime
from enum import Enum
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """
    变更类型枚举
    
    定义了需求变更的所有可能类型：
    - ADD: 新增需求
    - MODIFY: 修改现有需求
    - DELETE: 删除需求
    - DEPRECATE: 废弃需求
    - SPLIT: 拆分需求
    - MERGE: 合并需求
    """
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    DEPRECATE = "deprecate"
    SPLIT = "split"
    MERGE = "merge"


class ImpactLevel(Enum):
    """
    影响等级枚举
    
    定义了变更影响的严重程度：
    - CRITICAL: 关键影响，可能导致系统核心功能失效
    - HIGH: 高影响，影响多个重要功能
    - MEDIUM: 中等影响，影响部分功能
    - LOW: 低影响，影响范围有限
    - MINIMAL: 最小影响，几乎不影响系统功能
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class ImpactCategory(Enum):
    """
    影响类别枚举
    
    定义了变更影响的不同类别：
    - TEST: 测试相关影响
    - CODE: 代码相关影响
    - REQUIREMENT: 需求相关影响
    - DOCUMENTATION: 文档相关影响
    - CONFIGURATION: 配置相关影响
    """
    TEST = "test"
    CODE = "code"
    REQUIREMENT = "requirement"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"


class ChangeStatus(Enum):
    """
    变更状态枚举
    
    定义了需求变更的生命周期状态：
    - PROPOSED: 已提议，待审核
    - APPROVED: 已批准，待实施
    - IN_PROGRESS: 实施中
    - COMPLETED: 已完成
    - REJECTED: 已拒绝
    """
    PROPOSED = "proposed"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class ImpactScopeType(Enum):
    """
    影响范围类型枚举
    
    定义了影响范围的类型：
    - DIRECT: 直接影响，与变更有直接追溯关系
    - INDIRECT: 间接影响，通过依赖关系传播
    - TRANSITIVE: 传递影响，通过多级依赖传播
    - POTENTIAL: 潜在影响，可能存在但不确定
    """
    DIRECT = "direct"
    INDIRECT = "indirect"
    TRANSITIVE = "transitive"
    POTENTIAL = "potential"


class PropagationPath(Enum):
    """
    影响传播路径枚举
    
    定义了影响传播的可能路径：
    - REQUIREMENT_TO_CODE: 需求到代码
    - REQUIREMENT_TO_TEST: 需求到测试
    - CODE_TO_CODE: 代码到代码（依赖关系）
    - CODE_TO_TEST: 代码到测试
    - TEST_TO_TEST: 测试到测试
    """
    REQUIREMENT_TO_CODE = "requirement_to_code"
    REQUIREMENT_TO_TEST = "requirement_to_test"
    CODE_TO_CODE = "code_to_code"
    CODE_TO_TEST = "code_to_test"
    TEST_TO_TEST = "test_to_test"


@dataclass
class RequirementChange:
    """
    需求变更数据类
    
    表示一个需求变更的完整信息，包括变更的基本属性、
    变更内容、审批信息和时间戳等。
    
    属性:
        id: 变更唯一标识符
        requirement_id: 关联的需求ID
        requirement_name: 需求名称
        change_type: 变更类型（新增/修改/删除等）
        description: 变更描述
        old_value: 变更前的值（可选）
        new_value: 变更后的值（可选）
        reason: 变更原因
        impact_level: 影响等级
        status: 变更状态
        proposed_by: 提议人
        approved_by: 审批人
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: str
    requirement_id: str
    requirement_name: str
    change_type: ChangeType
    description: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    reason: str = ""
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    status: ChangeStatus = ChangeStatus.PROPOSED
    proposed_by: str = ""
    approved_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """将变更对象转换为字典格式"""
        return {
            "id": self.id,
            "requirement_id": self.requirement_id,
            "requirement_name": self.requirement_name,
            "change_type": self.change_type.value,
            "description": self.description,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "impact_level": self.impact_level.value,
            "status": self.status.value,
            "proposed_by": self.proposed_by,
            "approved_by": self.approved_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


@dataclass
class ImpactResult:
    """
    影响结果数据类
    
    表示单个影响分析结果，记录变更对某个具体项目的影响详情。
    
    属性:
        id: 结果唯一标识符
        change_id: 关联的变更ID
        impact_category: 影响类别
        impact_level: 影响等级
        affected_item_id: 受影响项目ID
        affected_item_name: 受影响项目名称
        affected_item_type: 受影响项目类型
        impact_description: 影响描述
        recommended_actions: 建议措施列表
        confidence: 置信度（0-1）
        metadata: 额外元数据
    """
    id: str
    change_id: str
    impact_category: ImpactCategory
    impact_level: ImpactLevel
    affected_item_id: str
    affected_item_name: str
    affected_item_type: str
    impact_description: str
    recommended_actions: List[str] = field(default_factory=list)
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """将影响结果对象转换为字典格式"""
        return {
            "id": self.id,
            "change_id": self.change_id,
            "impact_category": self.impact_category.value,
            "impact_level": self.impact_level,
            "affected_item_id": self.affected_item_id,
            "affected_item_name": self.affected_item_name,
            "affected_item_type": self.affected_item_type,
            "impact_description": self.impact_description,
            "recommended_actions": self.recommended_actions,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


@dataclass
class AffectedTest:
    """
    受影响测试数据类
    
    表示一个受变更影响的测试用例，包含影响详情和建议措施。
    
    属性:
        test_id: 测试用例ID
        test_name: 测试用例名称
        test_type: 测试类型（单元测试/集成测试等）
        impact_level: 影响等级
        impact_reason: 影响原因
        trace_link_id: 关联的追溯链ID（可选）
        recommended_actions: 建议措施列表
        scope_type: 影响范围类型
        propagation_depth: 影响传播深度
    """
    test_id: str
    test_name: str
    test_type: str
    impact_level: ImpactLevel
    impact_reason: str
    trace_link_id: Optional[str] = None
    recommended_actions: List[str] = field(default_factory=list)
    scope_type: ImpactScopeType = ImpactScopeType.DIRECT
    propagation_depth: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """将受影响测试对象转换为字典格式"""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_type": self.test_type,
            "impact_level": self.impact_level.value,
            "impact_reason": self.impact_reason,
            "trace_link_id": self.trace_link_id,
            "recommended_actions": self.recommended_actions,
            "scope_type": self.scope_type.value,
            "propagation_depth": self.propagation_depth
        }


@dataclass
class AffectedCode:
    """
    受影响代码数据类
    
    表示一个受变更影响的代码元素，包含位置信息和影响详情。
    
    属性:
        code_id: 代码元素ID
        code_name: 代码元素名称
        code_type: 代码类型（函数/类/模块等）
        file_path: 文件路径
        line_start: 起始行号
        line_end: 结束行号
        impact_level: 影响等级
        impact_reason: 影响原因
        trace_link_id: 关联的追溯链ID（可选）
        recommended_actions: 建议措施列表
        scope_type: 影响范围类型
        propagation_depth: 影响传播深度
        dependencies: 依赖的代码元素列表
    """
    code_id: str
    code_name: str
    code_type: str
    file_path: str
    line_start: int
    line_end: int
    impact_level: ImpactLevel
    impact_reason: str
    trace_link_id: Optional[str] = None
    recommended_actions: List[str] = field(default_factory=list)
    scope_type: ImpactScopeType = ImpactScopeType.DIRECT
    propagation_depth: int = 0
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """将受影响代码对象转换为字典格式"""
        return {
            "code_id": self.code_id,
            "code_name": self.code_name,
            "code_type": self.code_type,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "impact_level": self.impact_level.value,
            "impact_reason": self.impact_reason,
            "trace_link_id": self.trace_link_id,
            "recommended_actions": self.recommended_actions,
            "scope_type": self.scope_type.value,
            "propagation_depth": self.propagation_depth,
            "dependencies": self.dependencies
        }


@dataclass
class ImpactScopeNode:
    """
    影响范围节点数据类
    
    表示影响传播图中的一个节点，用于构建影响范围树。
    
    属性:
        item_id: 项目ID
        item_name: 项目名称
        item_type: 项目类型
        scope_type: 影响范围类型
        impact_level: 影响等级
        propagation_path: 影响传播路径
        depth: 传播深度
        children: 子节点列表
    """
    item_id: str
    item_name: str
    item_type: str
    scope_type: ImpactScopeType
    impact_level: ImpactLevel
    propagation_path: Optional[PropagationPath] = None
    depth: int = 0
    children: List['ImpactScopeNode'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """将影响范围节点对象转换为字典格式"""
        return {
            "item_id": self.item_id,
            "item_name": self.item_name,
            "item_type": self.item_type,
            "scope_type": self.scope_type.value,
            "impact_level": self.impact_level.value,
            "propagation_path": self.propagation_path.value if self.propagation_path else None,
            "depth": self.depth,
            "children": [child.to_dict() for child in self.children]
        }


@dataclass
class ImpactScopeAnalysis:
    """
    影响范围分析结果数据类
    
    包含完整的影响范围分析结果，包括影响树、统计数据和传播路径。
    
    属性:
        change_id: 变更ID
        root_node: 影响范围树的根节点
        total_nodes: 总节点数
        max_depth: 最大传播深度
        scope_by_type: 按类型分组的范围统计
        scope_by_level: 按影响等级分组的范围统计
        propagation_paths: 所有传播路径列表
        critical_paths: 关键传播路径列表
    """
    change_id: str
    root_node: Optional[ImpactScopeNode] = None
    total_nodes: int = 0
    max_depth: int = 0
    scope_by_type: Dict[str, int] = field(default_factory=dict)
    scope_by_level: Dict[str, int] = field(default_factory=dict)
    propagation_paths: List[Dict[str, Any]] = field(default_factory=list)
    critical_paths: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """将影响范围分析结果转换为字典格式"""
        return {
            "change_id": self.change_id,
            "root_node": self.root_node.to_dict() if self.root_node else None,
            "total_nodes": self.total_nodes,
            "max_depth": self.max_depth,
            "scope_by_type": self.scope_by_type,
            "scope_by_level": self.scope_by_level,
            "propagation_paths": self.propagation_paths,
            "critical_paths": self.critical_paths
        }


@dataclass
class ImpactAnalysisReport:
    """
    影响分析报告数据类
    
    包含完整的影响分析报告，汇总所有分析结果和建议。
    
    属性:
        change_id: 变更ID
        requirement_change: 需求变更对象
        affected_tests: 受影响测试列表
        affected_code: 受影响代码列表
        impact_scope: 影响范围分析结果
        impact_summary: 影响摘要统计
        risk_assessment: 风险评估结果
        recommendations: 建议措施列表
        generated_at: 报告生成时间
    """
    change_id: str
    requirement_change: RequirementChange
    affected_tests: List[AffectedTest]
    affected_code: List[AffectedCode]
    impact_scope: Optional[ImpactScopeAnalysis] = None
    impact_summary: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """将影响分析报告转换为字典格式"""
        return {
            "change_id": self.change_id,
            "requirement_change": self.requirement_change.to_dict(),
            "affected_tests": [t.to_dict() for t in self.affected_tests],
            "affected_code": [c.to_dict() for c in self.affected_code],
            "impact_scope": self.impact_scope.to_dict() if self.impact_scope else None,
            "impact_summary": self.impact_summary,
            "risk_assessment": self.risk_assessment,
            "recommendations": self.recommendations,
            "generated_at": self.generated_at
        }


class RequirementChangeImpactAnalyzer:
    """
    需求变更影响分析器
    
    核心分析器类，提供需求变更影响的全面分析功能。
    
    主要功能:
    1. 变更影响分析 - 分析变更对系统的整体影响
    2. 变更影响范围分析 - 分析变更的影响范围和传播路径
    3. 受影响测试识别 - 识别需要更新的测试用例
    4. 受影响代码识别 - 识别需要修改的代码元素
    
    属性:
        trace_db_path: 追溯数据库路径
        IMPACT_WEIGHTS: 变更类型对应的影响权重
        KEYWORD_IMPACT_BOOST: 关键词对应的影响加成
        PROPAGATION_DECAY: 影响传播衰减因子
    """
    
    IMPACT_WEIGHTS = {
        ChangeType.DELETE: 1.0,
        ChangeType.MODIFY: 0.8,
        ChangeType.SPLIT: 0.7,
        ChangeType.MERGE: 0.7,
        ChangeType.DEPRECATE: 0.6,
        ChangeType.ADD: 0.3,
    }
    
    KEYWORD_IMPACT_BOOST = {
        "关键": 0.3,
        "核心": 0.3,
        "重要": 0.2,
        "必须": 0.2,
        "critical": 0.3,
        "core": 0.3,
        "important": 0.2,
        "mandatory": 0.2,
    }
    
    PROPAGATION_DECAY = {
        ImpactScopeType.DIRECT: 1.0,
        ImpactScopeType.INDIRECT: 0.7,
        ImpactScopeType.TRANSITIVE: 0.5,
        ImpactScopeType.POTENTIAL: 0.3,
    }
    
    MAX_PROPAGATION_DEPTH = 5
    
    def __init__(self, trace_db_path: str = "requirement_trace.db"):
        """
        初始化需求变更影响分析器
        
        参数:
            trace_db_path: 追溯数据库路径
        """
        self.trace_db_path = trace_db_path
        self._init_database()
        logger.info(f"需求变更影响分析器初始化完成: {trace_db_path}")
    
    def _get_trace_connection(self) -> sqlite3.Connection:
        """获取追溯数据库连接"""
        conn = sqlite3.connect(self.trace_db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_trace_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requirement_changes (
                id TEXT PRIMARY KEY,
                requirement_id TEXT NOT NULL,
                requirement_name TEXT,
                change_type TEXT NOT NULL,
                description TEXT,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                impact_level TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'proposed',
                proposed_by TEXT,
                approved_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS impact_results (
                id TEXT PRIMARY KEY,
                change_id TEXT NOT NULL,
                impact_category TEXT NOT NULL,
                impact_level TEXT NOT NULL,
                affected_item_id TEXT NOT NULL,
                affected_item_name TEXT,
                affected_item_type TEXT,
                impact_description TEXT,
                recommended_actions TEXT,
                confidence REAL DEFAULT 1.0,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (change_id) REFERENCES requirement_changes(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS impact_scope_cache (
                id TEXT PRIMARY KEY,
                change_id TEXT NOT NULL,
                scope_type TEXT NOT NULL,
                item_id TEXT NOT NULL,
                item_name TEXT,
                item_type TEXT,
                impact_level TEXT NOT NULL,
                propagation_path TEXT,
                depth INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (change_id) REFERENCES requirement_changes(id)
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_change_req ON requirement_changes(requirement_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_impact_change ON impact_results(change_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_impact_item ON impact_results(affected_item_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scope_change ON impact_scope_cache(change_id)')
        
        conn.commit()
        conn.close()
    
    def _generate_id(self, prefix: str = "CH") -> str:
        """生成唯一标识符"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        return f"{prefix}-{timestamp}"
    
    def register_change(self,
                        requirement_id: str,
                        requirement_name: str,
                        change_type: ChangeType,
                        description: str,
                        old_value: str = None,
                        new_value: str = None,
                        reason: str = "",
                        proposed_by: str = "") -> RequirementChange:
        """
        注册需求变更
        
        创建并记录一个新的需求变更，自动计算影响等级。
        
        参数:
            requirement_id: 需求ID
            requirement_name: 需求名称
            change_type: 变更类型
            description: 变更描述
            old_value: 变更前的值（可选）
            new_value: 变更后的值（可选）
            reason: 变更原因
            proposed_by: 提议人
        
        返回:
            RequirementChange: 创建的需求变更对象
        """
        change_id = self._generate_id("CH")
        now = datetime.now().isoformat()
        
        impact_level = self._calculate_impact_level(change_type, description)
        
        try:
            conn = self._get_trace_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO requirement_changes 
                (id, requirement_id, requirement_name, change_type, description, old_value, new_value, 
                 reason, impact_level, status, proposed_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (change_id, requirement_id, requirement_name, change_type.value, description,
                  old_value, new_value, reason, impact_level.value, ChangeStatus.PROPOSED.value,
                  proposed_by, now, now))
            
            conn.commit()
            conn.close()
            
            logger.info(f"注册需求变更: {change_id} - {requirement_name}")
            
            return RequirementChange(
                id=change_id,
                requirement_id=requirement_id,
                requirement_name=requirement_name,
                change_type=change_type,
                description=description,
                old_value=old_value,
                new_value=new_value,
                reason=reason,
                impact_level=impact_level,
                proposed_by=proposed_by
            )
            
        except Exception as e:
            logger.error(f"注册需求变更失败: {e}")
            raise
    
    def _calculate_impact_level(self, change_type: ChangeType, description: str) -> ImpactLevel:
        """
        计算变更影响等级
        
        基于变更类型和描述内容计算影响等级。
        
        参数:
            change_type: 变更类型
            description: 变更描述
        
        返回:
            ImpactLevel: 计算得出的影响等级
        """
        base_weight = self.IMPACT_WEIGHTS.get(change_type, 0.5)
        
        keyword_boost = 0.0
        desc_lower = description.lower()
        for keyword, boost in self.KEYWORD_IMPACT_BOOST.items():
            if keyword.lower() in desc_lower:
                keyword_boost = max(keyword_boost, boost)
        
        total_weight = min(base_weight + keyword_boost, 1.0)
        
        if total_weight >= 0.9:
            return ImpactLevel.CRITICAL
        elif total_weight >= 0.7:
            return ImpactLevel.HIGH
        elif total_weight >= 0.5:
            return ImpactLevel.MEDIUM
        elif total_weight >= 0.3:
            return ImpactLevel.LOW
        else:
            return ImpactLevel.MINIMAL
    
    def analyze_test_impact(self, change: RequirementChange, 
                            max_depth: int = 3) -> List[AffectedTest]:
        """
        分析测试影响
        
        识别受变更影响的测试用例，包括直接和间接影响。
        
        分析策略:
        1. 通过追溯链识别直接关联的测试
        2. 通过关键词匹配识别间接关联的测试
        3. 通过测试依赖关系识别传递影响的测试
        4. 计算影响传播深度和范围类型
        
        参数:
            change: 需求变更对象
            max_depth: 最大传播深度（默认3）
        
        返回:
            List[AffectedTest]: 受影响测试列表
        """
        affected_tests = []
        visited_tests = set()
        
        try:
            conn = self._get_trace_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT tl.id as trace_id, tc.id as test_id, tc.name as test_name, 
                       tc.test_type, tl.status as trace_status, tc.dependencies
                FROM trace_links tl
                JOIN test_cases tc ON tl.target_id = tc.id
                WHERE tl.source_id = ? AND tl.trace_type = 'requirement_to_test'
            ''', (change.requirement_id,))
            
            direct_tests = cursor.fetchall()
            
            for row in direct_tests:
                if row['test_id'] in visited_tests:
                    continue
                visited_tests.add(row['test_id'])
                
                impact_level = self._map_change_impact_to_test(change.impact_level, row['trace_status'])
                
                affected_test = AffectedTest(
                    test_id=row['test_id'],
                    test_name=row['test_name'],
                    test_type=row['test_type'],
                    impact_level=impact_level,
                    impact_reason=f"直接追溯于需求 {change.requirement_name}",
                    trace_link_id=row['trace_id'],
                    recommended_actions=self._generate_test_recommendations(change.change_type, impact_level),
                    scope_type=ImpactScopeType.DIRECT,
                    propagation_depth=0
                )
                affected_tests.append(affected_test)
                
                if max_depth > 0:
                    self._propagate_test_impact(
                        cursor, row['test_id'], row['test_name'], 
                        affected_tests, visited_tests, 1, max_depth
                    )
            
            cursor.execute('''
                SELECT DISTINCT tc.id, tc.name, tc.test_type, tc.dependencies
                FROM test_cases tc
                WHERE tc.description LIKE ? OR tc.scenario LIKE ? OR tc.given LIKE ? 
                   OR tc."when" LIKE ? OR tc."then" LIKE ?
            ''', (f'%{change.requirement_name}%', f'%{change.requirement_name}%',
                  f'%{change.requirement_name}%', f'%{change.requirement_name}%',
                  f'%{change.requirement_name}%'))
            
            indirect_tests = cursor.fetchall()
            
            for row in indirect_tests:
                if row['id'] in visited_tests:
                    continue
                visited_tests.add(row['id'])
                
                affected_test = AffectedTest(
                    test_id=row['id'],
                    test_name=row['name'],
                    test_type=row['test_type'],
                    impact_level=ImpactLevel.LOW,
                    impact_reason=f"间接关联于需求 {change.requirement_name}",
                    recommended_actions=["验证测试是否需要更新"],
                    scope_type=ImpactScopeType.INDIRECT,
                    propagation_depth=1
                )
                affected_tests.append(affected_test)
            
            keywords = self._extract_keywords(change.description)
            for keyword in keywords:
                cursor.execute('''
                    SELECT DISTINCT tc.id, tc.name, tc.test_type, tc.dependencies
                    FROM test_cases tc
                    WHERE tc.name LIKE ? OR tc.description LIKE ? OR tc.scenario LIKE ?
                ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
                
                potential_tests = cursor.fetchall()
                
                for row in potential_tests:
                    if row['id'] in visited_tests:
                        continue
                    visited_tests.add(row['id'])
                    
                    affected_test = AffectedTest(
                        test_id=row['id'],
                        test_name=row['name'],
                        test_type=row['test_type'],
                        impact_level=ImpactLevel.MINIMAL,
                        impact_reason=f"潜在关联于关键词 '{keyword}'",
                        recommended_actions=["评估测试是否受影响"],
                        scope_type=ImpactScopeType.POTENTIAL,
                        propagation_depth=2
                    )
                    affected_tests.append(affected_test)
            
            conn.close()
            logger.info(f"分析测试影响: 发现 {len(affected_tests)} 个受影响测试")
            
        except Exception as e:
            logger.error(f"分析测试影响失败: {e}")
        
        return affected_tests
    
    def _propagate_test_impact(self, cursor, source_test_id: str, source_test_name: str,
                                affected_tests: List[AffectedTest], visited_tests: Set[str],
                                current_depth: int, max_depth: int) -> None:
        """
        传播测试影响
        
        递归分析测试依赖关系，识别传递影响的测试。
        
        参数:
            cursor: 数据库游标
            source_test_id: 源测试ID
            source_test_name: 源测试名称
            affected_tests: 受影响测试列表
            visited_tests: 已访问测试集合
            current_depth: 当前传播深度
            max_depth: 最大传播深度
        """
        if current_depth > max_depth:
            return
        
        cursor.execute('''
            SELECT id, name, test_type, dependencies
            FROM test_cases
            WHERE dependencies LIKE ?
        ''', (f'%{source_test_name}%',))
        
        dependent_tests = cursor.fetchall()
        
        for row in dependent_tests:
            if row['id'] in visited_tests:
                continue
            visited_tests.add(row['id'])
            
            decay_factor = self.PROPAGATION_DECAY.get(ImpactScopeType.TRANSITIVE, 0.5)
            impact_level = self._decay_impact_level(ImpactLevel.MEDIUM, decay_factor * (1 - current_depth * 0.1))
            
            affected_test = AffectedTest(
                test_id=row['id'],
                test_name=row['name'],
                test_type=row['test_type'],
                impact_level=impact_level,
                impact_reason=f"依赖于测试 {source_test_name}",
                recommended_actions=["检查依赖测试是否需要更新"],
                scope_type=ImpactScopeType.TRANSITIVE,
                propagation_depth=current_depth
            )
            affected_tests.append(affected_test)
            
            self._propagate_test_impact(
                cursor, row['id'], row['name'],
                affected_tests, visited_tests, current_depth + 1, max_depth
            )
    
    def _decay_impact_level(self, base_level: ImpactLevel, decay_factor: float) -> ImpactLevel:
        """
        根据衰减因子降低影响等级
        
        参数:
            base_level: 基础影响等级
            decay_factor: 衰减因子（0-1）
        
        返回:
            ImpactLevel: 衰减后的影响等级
        """
        level_order = [
            ImpactLevel.MINIMAL, ImpactLevel.LOW, ImpactLevel.MEDIUM, 
            ImpactLevel.HIGH, ImpactLevel.CRITICAL
        ]
        base_index = level_order.index(base_level)
        decayed_index = max(0, int(base_index * decay_factor))
        return level_order[decayed_index]
    
    def _map_change_impact_to_test(self, change_impact: ImpactLevel, trace_status: str) -> ImpactLevel:
        """
        将变更影响等级映射到测试影响等级
        
        根据追溯链状态调整影响等级。
        
        参数:
            change_impact: 变更影响等级
            trace_status: 追溯链状态
        
        返回:
            ImpactLevel: 映射后的测试影响等级
        """
        if trace_status in ['failed', 'pending']:
            if change_impact == ImpactLevel.CRITICAL:
                return ImpactLevel.CRITICAL
            elif change_impact == ImpactLevel.HIGH:
                return ImpactLevel.HIGH
            return ImpactLevel.MEDIUM
        
        if change_impact == ImpactLevel.CRITICAL:
            return ImpactLevel.HIGH
        elif change_impact == ImpactLevel.HIGH:
            return ImpactLevel.MEDIUM
        return ImpactLevel.LOW
    
    def _generate_test_recommendations(self, change_type: ChangeType, impact_level: ImpactLevel) -> List[str]:
        """
        生成测试相关建议措施
        
        根据变更类型和影响等级生成针对性的建议。
        
        参数:
            change_type: 变更类型
            impact_level: 影响等级
        
        返回:
            List[str]: 建议措施列表
        """
        recommendations = []
        
        if change_type == ChangeType.DELETE:
            recommendations.extend([
                "删除或禁用此测试用例",
                "更新相关测试套件配置",
                "检查是否有其他测试依赖此测试"
            ])
        elif change_type == ChangeType.MODIFY:
            recommendations.extend([
                "更新测试用例以匹配新的需求",
                "重新验证测试预期结果",
                "检查测试数据是否需要更新"
            ])
        elif change_type == ChangeType.ADD:
            recommendations.extend([
                "为此需求创建新的测试用例",
                "验证新需求的可测试性"
            ])
        elif change_type == ChangeType.DEPRECATE:
            recommendations.extend([
                "标记测试用例为待废弃",
                "计划测试用例的迁移或删除"
            ])
        elif change_type == ChangeType.SPLIT:
            recommendations.extend([
                "拆分测试用例以匹配拆分后的需求",
                "确保每个子需求都有对应的测试"
            ])
        elif change_type == ChangeType.MERGE:
            recommendations.extend([
                "合并相关测试用例",
                "验证合并后的测试覆盖度"
            ])
        
        if impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
            recommendations.append("优先处理此测试变更")
        
        return recommendations
    
    def analyze_code_impact(self, change: RequirementChange, 
                            max_depth: int = 5) -> List[AffectedCode]:
        """
        分析代码影响
        
        识别受变更影响的代码元素，包括直接和间接影响。
        
        分析策略:
        1. 通过追溯链识别直接实现的代码
        2. 通过关键词匹配识别可能涉及的代码
        3. 通过代码依赖关系识别传递影响的代码
        4. 计算影响传播深度和范围类型
        
        参数:
            change: 需求变更对象
            max_depth: 最大传播深度（默认5）
        
        返回:
            List[AffectedCode]: 受影响代码列表
        """
        affected_code = []
        visited_code = set()
        
        try:
            conn = self._get_trace_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT tl.id as trace_id, ce.id as code_id, ce.name as code_name, 
                       ce.element_type, ce.file_path, ce.line_start, ce.line_end,
                       ce.dependencies
                FROM trace_links tl
                JOIN code_elements ce ON tl.target_id = ce.id
                WHERE tl.source_id = ? AND tl.trace_type = 'requirement_to_code'
            ''', (change.requirement_id,))
            
            direct_code = cursor.fetchall()
            
            for row in direct_code:
                if row['code_id'] in visited_code:
                    continue
                visited_code.add(row['code_id'])
                
                impact_level = self._map_change_impact_to_code(change.impact_level)
                
                affected_code_item = AffectedCode(
                    code_id=row['code_id'],
                    code_name=row['code_name'],
                    code_type=row['element_type'],
                    file_path=row['file_path'],
                    line_start=row['line_start'],
                    line_end=row['line_end'],
                    impact_level=impact_level,
                    impact_reason=f"直接实现需求 {change.requirement_name}",
                    trace_link_id=row['trace_id'],
                    recommended_actions=self._generate_code_recommendations(change.change_type, impact_level),
                    scope_type=ImpactScopeType.DIRECT,
                    propagation_depth=0,
                    dependencies=self._parse_dependencies(row['dependencies'])
                )
                affected_code.append(affected_code_item)
                
                if max_depth > 0:
                    self._propagate_code_impact(
                        cursor, row['code_id'], row['code_name'],
                        affected_code, visited_code, 1, max_depth
                    )
            
            keywords = self._extract_keywords(change.description)
            for keyword in keywords:
                cursor.execute('''
                    SELECT id, name, element_type, file_path, line_start, line_end, dependencies
                    FROM code_elements
                    WHERE name LIKE ? OR docstring LIKE ? OR keywords LIKE ?
                ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
                
                indirect_code = cursor.fetchall()
                
                for row in indirect_code:
                    if row['id'] in visited_code:
                        continue
                    visited_code.add(row['id'])
                    
                    affected_code_item = AffectedCode(
                        code_id=row['id'],
                        code_name=row['name'],
                        code_type=row['element_type'],
                        file_path=row['file_path'],
                        line_start=row['line_start'],
                        line_end=row['line_end'],
                        impact_level=ImpactLevel.LOW,
                        impact_reason=f"可能涉及关键词 '{keyword}'",
                        recommended_actions=["检查代码是否需要更新"],
                        scope_type=ImpactScopeType.INDIRECT,
                        propagation_depth=1,
                        dependencies=self._parse_dependencies(row['dependencies'])
                    )
                    affected_code.append(affected_code_item)
            
            conn.close()
            logger.info(f"分析代码影响: 发现 {len(affected_code)} 个受影响代码元素")
            
        except Exception as e:
            logger.error(f"分析代码影响失败: {e}")
        
        return affected_code
    
    def _propagate_code_impact(self, cursor, source_code_id: str, source_code_name: str,
                                affected_code: List[AffectedCode], visited_code: Set[str],
                                current_depth: int, max_depth: int) -> None:
        """
        传播代码影响
        
        递归分析代码依赖关系，识别传递影响的代码。
        
        参数:
            cursor: 数据库游标
            source_code_id: 源代码ID
            source_code_name: 源代码名称
            affected_code: 受影响代码列表
            visited_code: 已访问代码集合
            current_depth: 当前传播深度
            max_depth: 最大传播深度
        """
        if current_depth > max_depth:
            return
        
        cursor.execute('''
            SELECT id, name, element_type, file_path, line_start, line_end, dependencies
            FROM code_elements
            WHERE dependencies LIKE ?
        ''', (f'%{source_code_name}%',))
        
        dependent_code = cursor.fetchall()
        
        for row in dependent_code:
            if row['id'] in visited_code:
                continue
            visited_code.add(row['id'])
            
            decay_factor = self.PROPAGATION_DECAY.get(ImpactScopeType.TRANSITIVE, 0.5)
            impact_level = self._decay_impact_level(ImpactLevel.MEDIUM, decay_factor * (1 - current_depth * 0.15))
            
            dep_code = AffectedCode(
                code_id=row['id'],
                code_name=row['name'],
                code_type=row['element_type'],
                file_path=row['file_path'],
                line_start=row['line_start'],
                line_end=row['line_end'],
                impact_level=impact_level,
                impact_reason=f"依赖于 {source_code_name}",
                recommended_actions=self._generate_dependency_recommendations(current_depth),
                scope_type=ImpactScopeType.TRANSITIVE,
                propagation_depth=current_depth,
                dependencies=self._parse_dependencies(row['dependencies'])
            )
            affected_code.append(dep_code)
            
            self._propagate_code_impact(
                cursor, row['id'], row['name'],
                affected_code, visited_code, current_depth + 1, max_depth
            )
    
    def _parse_dependencies(self, dependencies_str: Optional[str]) -> List[str]:
        """
        解析依赖字符串为列表
        
        参数:
            dependencies_str: 依赖字符串（JSON格式或逗号分隔）
        
        返回:
            List[str]: 依赖列表
        """
        if not dependencies_str:
            return []
        
        try:
            deps = json.loads(dependencies_str)
            if isinstance(deps, list):
                return deps
        except (json.JSONDecodeError, TypeError):
            if ',' in dependencies_str:
                return [d.strip() for d in dependencies_str.split(',') if d.strip()]
            return [dependencies_str] if dependencies_str else []
        
        return []
    
    def _generate_dependency_recommendations(self, depth: int) -> List[str]:
        """
        根据依赖深度生成建议措施
        
        参数:
            depth: 依赖深度
        
        返回:
            List[str]: 建议措施列表
        """
        if depth == 1:
            return [
                "检查直接依赖代码是否需要更新",
                "验证接口兼容性"
            ]
        elif depth == 2:
            return [
                "评估间接依赖的影响",
                "考虑是否需要重构"
            ]
        else:
            return [
                "评估深层依赖的影响",
                "考虑架构层面的调整"
            ]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词
        
        使用正则表达式提取中文和英文关键词。
        
        参数:
            text: 输入文本
        
        返回:
            List[str]: 关键词列表
        """
        keywords = []
        
        patterns = [
            r'[a-zA-Z_][a-zA-Z0-9_]*',
            r'[\u4e00-\u9fa5]{2,}',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            keywords.extend(matches)
        
        stop_words = {'的', '是', '在', '和', '与', '或', '等', '及', '将', '被', '为', '到', '从', '对', '按'}
        keywords = [k for k in keywords if k.lower() not in stop_words and len(k) >= 2]
        
        return list(set(keywords))[:10]
    
    def _map_change_impact_to_code(self, change_impact: ImpactLevel) -> ImpactLevel:
        """
        将变更影响等级映射到代码影响等级
        
        参数:
            change_impact: 变更影响等级
        
        返回:
            ImpactLevel: 代码影响等级
        """
        return change_impact
    
    def _generate_code_recommendations(self, change_type: ChangeType, impact_level: ImpactLevel) -> List[str]:
        """
        生成代码相关建议措施
        
        根据变更类型和影响等级生成针对性的建议。
        
        参数:
            change_type: 变更类型
            impact_level: 影响等级
        
        返回:
            List[str]: 建议措施列表
        """
        recommendations = []
        
        if change_type == ChangeType.DELETE:
            recommendations.extend([
                "删除或注释相关代码",
                "更新调用此代码的其他模块",
                "检查是否有其他代码依赖此功能"
            ])
        elif change_type == ChangeType.MODIFY:
            recommendations.extend([
                "更新代码实现以匹配新需求",
                "更新相关单元测试",
                "检查API接口是否需要更新"
            ])
        elif change_type == ChangeType.ADD:
            recommendations.extend([
                "实现新功能的代码",
                "添加相应的单元测试",
                "更新模块文档"
            ])
        elif change_type == ChangeType.DEPRECATE:
            recommendations.extend([
                "标记代码为待废弃",
                "提供替代实现方案"
            ])
        elif change_type == ChangeType.SPLIT:
            recommendations.extend([
                "拆分代码模块以匹配拆分后的需求",
                "确保每个子模块职责单一"
            ])
        elif change_type == ChangeType.MERGE:
            recommendations.extend([
                "合并相关代码模块",
                "重构以消除重复代码"
            ])
        
        if impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
            recommendations.append("优先处理此代码变更")
            recommendations.append("进行代码审查")
        
        return recommendations
    
    def analyze_impact(self, change: RequirementChange,
                       include_scope: bool = True) -> ImpactAnalysisReport:
        """
        分析变更影响
        
        执行完整的变更影响分析，包括测试影响、代码影响和影响范围分析。
        
        参数:
            change: 需求变更对象
            include_scope: 是否包含影响范围分析（默认True）
        
        返回:
            ImpactAnalysisReport: 影响分析报告
        """
        logger.info(f"开始分析变更影响: {change.id}")
        
        affected_tests = self.analyze_test_impact(change)
        affected_code = self.analyze_code_impact(change)
        
        impact_scope = None
        if include_scope:
            impact_scope = self.analyze_impact_scope(change, affected_tests, affected_code)
        
        impact_summary = self._generate_impact_summary(affected_tests, affected_code, impact_scope)
        risk_assessment = self._assess_risk(change, affected_tests, affected_code, impact_scope)
        recommendations = self._generate_overall_recommendations(change, affected_tests, affected_code, impact_scope)
        
        self._save_impact_results(change.id, affected_tests, affected_code)
        
        report = ImpactAnalysisReport(
            change_id=change.id,
            requirement_change=change,
            affected_tests=affected_tests,
            affected_code=affected_code,
            impact_scope=impact_scope,
            impact_summary=impact_summary,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )
        
        logger.info(f"影响分析完成: {len(affected_tests)} 测试, {len(affected_code)} 代码元素受影响")
        
        return report
    
    def analyze_impact_scope(self, change: RequirementChange,
                              affected_tests: List[AffectedTest],
                              affected_code: List[AffectedCode]) -> ImpactScopeAnalysis:
        """
        分析变更影响范围
        
        构建影响传播树，分析影响的范围、深度和传播路径。
        
        分析内容:
        1. 构建影响范围树
        2. 计算最大传播深度
        3. 识别关键传播路径
        4. 统计影响范围分布
        
        参数:
            change: 需求变更对象
            affected_tests: 受影响测试列表
            affected_code: 受影响代码列表
        
        返回:
            ImpactScopeAnalysis: 影响范围分析结果
        """
        logger.info(f"开始分析影响范围: {change.id}")
        
        root_node = ImpactScopeNode(
            item_id=change.requirement_id,
            item_name=change.requirement_name,
            item_type="requirement",
            scope_type=ImpactScopeType.DIRECT,
            impact_level=change.impact_level,
            depth=0
        )
        
        test_nodes = []
        for test in affected_tests:
            node = ImpactScopeNode(
                item_id=test.test_id,
                item_name=test.test_name,
                item_type="test",
                scope_type=test.scope_type,
                impact_level=test.impact_level,
                propagation_path=PropagationPath.REQUIREMENT_TO_TEST,
                depth=test.propagation_depth + 1
            )
            test_nodes.append(node)
        root_node.children.extend(test_nodes)
        
        code_nodes = []
        for code in affected_code:
            node = ImpactScopeNode(
                item_id=code.code_id,
                item_name=code.code_name,
                item_type="code",
                scope_type=code.scope_type,
                impact_level=code.impact_level,
                propagation_path=PropagationPath.REQUIREMENT_TO_CODE,
                depth=code.propagation_depth + 1
            )
            code_nodes.append(node)
        root_node.children.extend(code_nodes)
        
        total_nodes = 1 + len(test_nodes) + len(code_nodes)
        max_depth = 0
        if test_nodes:
            max_depth = max(max_depth, max(n.depth for n in test_nodes))
        if code_nodes:
            max_depth = max(max_depth, max(n.depth for n in code_nodes))
        
        scope_by_type = {
            "test": len(test_nodes),
            "code": len(code_nodes),
            "requirement": 1
        }
        
        scope_by_level = {}
        all_nodes = [root_node] + test_nodes + code_nodes
        for node in all_nodes:
            level = node.impact_level.value
            if level not in scope_by_level:
                scope_by_level[level] = 0
            scope_by_level[level] += 1
        
        propagation_paths = self._extract_propagation_paths(root_node)
        critical_paths = self._identify_critical_paths(propagation_paths)
        
        analysis = ImpactScopeAnalysis(
            change_id=change.id,
            root_node=root_node,
            total_nodes=total_nodes,
            max_depth=max_depth,
            scope_by_type=scope_by_type,
            scope_by_level=scope_by_level,
            propagation_paths=propagation_paths,
            critical_paths=critical_paths
        )
        
        self._save_scope_cache(change.id, analysis)
        
        logger.info(f"影响范围分析完成: 总节点 {total_nodes}, 最大深度 {max_depth}")
        
        return analysis
    
    def _extract_propagation_paths(self, root: ImpactScopeNode) -> List[Dict[str, Any]]:
        """
        提取所有传播路径
        
        从影响范围树中提取所有的传播路径。
        
        参数:
            root: 影响范围树根节点
        
        返回:
            List[Dict[str, Any]]: 传播路径列表
        """
        paths = []
        
        def traverse(node: ImpactScopeNode, current_path: List[str]):
            current_path.append(f"{node.item_type}:{node.item_name}")
            
            if not node.children:
                paths.append({
                    "path": " -> ".join(current_path),
                    "depth": node.depth,
                    "impact_level": node.impact_level.value,
                    "scope_type": node.scope_type.value
                })
            else:
                for child in node.children:
                    traverse(child, current_path.copy())
        
        traverse(root, [])
        return paths
    
    def _identify_critical_paths(self, paths: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        识别关键传播路径
        
        从所有传播路径中识别关键路径（高影响等级或深度传播）。
        
        参数:
            paths: 所有传播路径列表
        
        返回:
            List[Dict[str, Any]]: 关键传播路径列表
        """
        critical_paths = []
        
        for path in paths:
            is_critical = False
            
            if path["impact_level"] in ["critical", "high"]:
                is_critical = True
            elif path["depth"] >= 3:
                is_critical = True
            elif path["scope_type"] == "transitive" and path["depth"] >= 2:
                is_critical = True
            
            if is_critical:
                critical_paths.append(path)
        
        return critical_paths
    
    def _save_scope_cache(self, change_id: str, analysis: ImpactScopeAnalysis) -> None:
        """
        保存影响范围分析结果到缓存
        
        参数:
            change_id: 变更ID
            analysis: 影响范围分析结果
        """
        try:
            conn = self._get_trace_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            def save_node(node: ImpactScopeNode, parent_id: str = None):
                cache_id = self._generate_id("SC")
                cursor.execute('''
                    INSERT INTO impact_scope_cache 
                    (id, change_id, scope_type, item_id, item_name, item_type, 
                     impact_level, propagation_path, depth, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (cache_id, change_id, node.scope_type.value, node.item_id,
                      node.item_name, node.item_type, node.impact_level.value,
                      node.propagation_path.value if node.propagation_path else None,
                      node.depth, now))
                
                for child in node.children:
                    save_node(child, node.item_id)
            
            save_node(analysis.root_node)
            
            conn.commit()
            conn.close()
            
            logger.info(f"保存影响范围缓存: {analysis.total_nodes} 个节点")
            
        except Exception as e:
            logger.error(f"保存影响范围缓存失败: {e}")
    
    def _generate_impact_summary(self, affected_tests: List[AffectedTest], 
                                  affected_code: List[AffectedCode],
                                  impact_scope: Optional[ImpactScopeAnalysis] = None) -> Dict[str, Any]:
        """
        生成影响摘要
        
        汇总受影响测试和代码的统计信息。
        
        参数:
            affected_tests: 受影响测试列表
            affected_code: 受影响代码列表
            impact_scope: 影响范围分析结果（可选）
        
        返回:
            Dict[str, Any]: 影响摘要
        """
        test_by_level = {}
        for test in affected_tests:
            level = test.impact_level.value
            if level not in test_by_level:
                test_by_level[level] = 0
            test_by_level[level] += 1
        
        code_by_level = {}
        for code in affected_code:
            level = code.impact_level.value
            if level not in code_by_level:
                code_by_level[level] = 0
            code_by_level[level] += 1
        
        code_by_type = {}
        for code in affected_code:
            code_type = code.code_type
            if code_type not in code_by_type:
                code_by_type[code_type] = 0
            code_by_type[code_type] += 1
        
        test_by_scope = {}
        for test in affected_tests:
            scope = test.scope_type.value
            if scope not in test_by_scope:
                test_by_scope[scope] = 0
            test_by_scope[scope] += 1
        
        code_by_scope = {}
        for code in affected_code:
            scope = code.scope_type.value
            if scope not in code_by_scope:
                code_by_scope[scope] = 0
            code_by_scope[scope] += 1
        
        summary = {
            "total_affected_tests": len(affected_tests),
            "total_affected_code": len(affected_code),
            "tests_by_impact_level": test_by_level,
            "code_by_impact_level": code_by_level,
            "code_by_type": code_by_type,
            "tests_by_scope_type": test_by_scope,
            "code_by_scope_type": code_by_scope,
            "unique_files": len(set(c.file_path for c in affected_code))
        }
        
        if impact_scope:
            summary["max_propagation_depth"] = impact_scope.max_depth
            summary["total_impact_nodes"] = impact_scope.total_nodes
            summary["critical_path_count"] = len(impact_scope.critical_paths)
        
        return summary
    
    def _assess_risk(self, change: RequirementChange, 
                     affected_tests: List[AffectedTest],
                     affected_code: List[AffectedCode],
                     impact_scope: Optional[ImpactScopeAnalysis] = None) -> Dict[str, Any]:
        """
        评估变更风险
        
        基于受影响项目和影响范围计算风险等级。
        
        风险计算因素:
        1. 关键/高影响项目数量
        2. 变更本身的影响等级
        3. 影响传播深度
        4. 关键传播路径数量
        
        参数:
            change: 需求变更对象
            affected_tests: 受影响测试列表
            affected_code: 受影响代码列表
            impact_scope: 影响范围分析结果（可选）
        
        返回:
            Dict[str, Any]: 风险评估结果
        """
        risk_score = 0.0
        
        critical_tests = sum(1 for t in affected_tests if t.impact_level == ImpactLevel.CRITICAL)
        high_tests = sum(1 for t in affected_tests if t.impact_level == ImpactLevel.HIGH)
        critical_code = sum(1 for c in affected_code if c.impact_level == ImpactLevel.CRITICAL)
        high_code = sum(1 for c in affected_code if c.impact_level == ImpactLevel.HIGH)
        
        risk_score += critical_tests * 0.3
        risk_score += high_tests * 0.2
        risk_score += critical_code * 0.25
        risk_score += high_code * 0.15
        
        if change.impact_level == ImpactLevel.CRITICAL:
            risk_score += 0.2
        elif change.impact_level == ImpactLevel.HIGH:
            risk_score += 0.1
        
        if impact_scope:
            if impact_scope.max_depth >= 4:
                risk_score += 0.15
            elif impact_scope.max_depth >= 3:
                risk_score += 0.1
            
            if len(impact_scope.critical_paths) >= 5:
                risk_score += 0.1
            elif len(impact_scope.critical_paths) >= 3:
                risk_score += 0.05
        
        transitive_tests = sum(1 for t in affected_tests if t.scope_type == ImpactScopeType.TRANSITIVE)
        transitive_code = sum(1 for c in affected_code if c.scope_type == ImpactScopeType.TRANSITIVE)
        if transitive_tests + transitive_code > 5:
            risk_score += 0.1
        
        risk_score = min(risk_score, 1.0)
        
        if risk_score >= 0.8:
            risk_level = "critical"
            risk_description = "极高风险：需要立即处理，可能影响系统核心功能"
        elif risk_score >= 0.6:
            risk_level = "high"
            risk_description = "高风险：需要优先处理，可能影响多个关键功能"
        elif risk_score >= 0.4:
            risk_level = "medium"
            risk_description = "中等风险：需要计划处理，可能影响部分功能"
        elif risk_score >= 0.2:
            risk_level = "low"
            risk_description = "低风险：可以正常处理，影响范围有限"
        else:
            risk_level = "minimal"
            risk_description = "最小风险：影响范围很小"
        
        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "risk_description": risk_description,
            "critical_items": critical_tests + critical_code,
            "high_items": high_tests + high_code,
            "transitive_items": transitive_tests + transitive_code
        }
    
    def _generate_overall_recommendations(self, change: RequirementChange,
                                           affected_tests: List[AffectedTest],
                                           affected_code: List[AffectedCode],
                                           impact_scope: Optional[ImpactScopeAnalysis] = None) -> List[str]:
        """
        生成整体建议措施
        
        基于分析结果生成综合性的建议措施。
        
        参数:
            change: 需求变更对象
            affected_tests: 受影响测试列表
            affected_code: 受影响代码列表
            impact_scope: 影响范围分析结果（可选）
        
        返回:
            List[str]: 建议措施列表
        """
        recommendations = []
        
        recommendations.append(f"变更类型: {change.change_type.value}")
        recommendations.append(f"建议影响等级: {change.impact_level.value}")
        
        critical_tests = [t for t in affected_tests if t.impact_level == ImpactLevel.CRITICAL]
        if critical_tests:
            recommendations.append(f"优先处理 {len(critical_tests)} 个关键测试用例")
        
        critical_code = [c for c in affected_code if c.impact_level == ImpactLevel.CRITICAL]
        if critical_code:
            recommendations.append(f"优先更新 {len(critical_code)} 个关键代码元素")
        
        unique_files = set(c.file_path for c in affected_code)
        if len(unique_files) > 5:
            recommendations.append(f"变更涉及 {len(unique_files)} 个文件，建议分批次处理")
        
        if impact_scope:
            if impact_scope.max_depth >= 3:
                recommendations.append(f"影响传播深度达到 {impact_scope.max_depth} 层，建议仔细评估深层影响")
            
            if len(impact_scope.critical_paths) > 0:
                recommendations.append(f"发现 {len(impact_scope.critical_paths)} 条关键传播路径，建议重点关注")
        
        transitive_items = [t for t in affected_tests if t.scope_type == ImpactScopeType.TRANSITIVE]
        transitive_items.extend([c for c in affected_code if c.scope_type == ImpactScopeType.TRANSITIVE])
        if len(transitive_items) > 3:
            recommendations.append(f"存在 {len(transitive_items)} 个传递影响项，建议检查依赖链")
        
        if change.change_type == ChangeType.DELETE:
            recommendations.append("删除操作需要特别谨慎，建议先标记为废弃")
        elif change.change_type == ChangeType.SPLIT:
            recommendations.append("拆分操作需要确保子需求的完整性和独立性")
        elif change.change_type == ChangeType.MERGE:
            recommendations.append("合并操作需要验证合并后的需求一致性")
        
        if change.impact_level in [ImpactLevel.CRITICAL, ImpactLevel.HIGH]:
            recommendations.append("建议进行全面的回归测试")
            recommendations.append("建议进行代码审查")
            recommendations.append("建议制定详细的变更实施计划")
        
        return recommendations
    
    def _save_impact_results(self, change_id: str, 
                             affected_tests: List[AffectedTest],
                             affected_code: List[AffectedCode]) -> None:
        """
        保存影响分析结果到数据库
        
        参数:
            change_id: 变更ID
            affected_tests: 受影响测试列表
            affected_code: 受影响代码列表
        """
        try:
            conn = self._get_trace_connection()
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            for test in affected_tests:
                result_id = self._generate_id("IR")
                cursor.execute('''
                    INSERT INTO impact_results 
                    (id, change_id, impact_category, impact_level, affected_item_id, 
                     affected_item_name, affected_item_type, impact_description, 
                     recommended_actions, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (result_id, change_id, ImpactCategory.TEST.value, test.impact_level.value,
                      test.test_id, test.test_name, test.test_type, test.impact_reason,
                      json.dumps(test.recommended_actions, ensure_ascii=False), 1.0, now))
            
            for code in affected_code:
                result_id = self._generate_id("IR")
                cursor.execute('''
                    INSERT INTO impact_results 
                    (id, change_id, impact_category, impact_level, affected_item_id, 
                     affected_item_name, affected_item_type, impact_description, 
                     recommended_actions, confidence, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (result_id, change_id, ImpactCategory.CODE.value, code.impact_level.value,
                      code.code_id, code.code_name, code.code_type, code.impact_reason,
                      json.dumps(code.recommended_actions, ensure_ascii=False), 1.0, now))
            
            conn.commit()
            conn.close()
            
            logger.info(f"保存影响分析结果: {len(affected_tests) + len(affected_code)} 条记录")
            
        except Exception as e:
            logger.error(f"保存影响分析结果失败: {e}")
    
    def get_change_history(self, requirement_id: str) -> List[RequirementChange]:
        """
        获取需求变更历史
        
        查询指定需求的所有变更记录。
        
        参数:
            requirement_id: 需求ID
        
        返回:
            List[RequirementChange]: 变更历史列表
        """
        try:
            conn = self._get_trace_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM requirement_changes 
                WHERE requirement_id = ? 
                ORDER BY created_at DESC
            ''', (requirement_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            changes = []
            for row in rows:
                changes.append(RequirementChange(
                    id=row['id'],
                    requirement_id=row['requirement_id'],
                    requirement_name=row['requirement_name'],
                    change_type=ChangeType(row['change_type']),
                    description=row['description'],
                    old_value=row['old_value'],
                    new_value=row['new_value'],
                    reason=row['reason'],
                    impact_level=ImpactLevel(row['impact_level']),
                    status=ChangeStatus(row['status']),
                    proposed_by=row['proposed_by'],
                    approved_by=row['approved_by'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                ))
            
            return changes
            
        except Exception as e:
            logger.error(f"获取变更历史失败: {e}")
            return []
    
    def update_change_status(self, change_id: str, status: ChangeStatus, 
                             approved_by: str = "") -> Optional[RequirementChange]:
        """
        更新变更状态
        
        更新需求变更的处理状态。
        
        参数:
            change_id: 变更ID
            status: 新状态
            approved_by: 审批人（可选）
        
        返回:
            RequirementChange: 更新后的变更对象，失败返回None
        """
        try:
            conn = self._get_trace_connection()
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            cursor.execute('''
                UPDATE requirement_changes 
                SET status = ?, approved_by = ?, updated_at = ? 
                WHERE id = ?
            ''', (status.value, approved_by, now, change_id))
            
            conn.commit()
            
            cursor.execute('SELECT * FROM requirement_changes WHERE id = ?', (change_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return RequirementChange(
                    id=row['id'],
                    requirement_id=row['requirement_id'],
                    requirement_name=row['requirement_name'],
                    change_type=ChangeType(row['change_type']),
                    description=row['description'],
                    old_value=row['old_value'],
                    new_value=row['new_value'],
                    reason=row['reason'],
                    impact_level=ImpactLevel(row['impact_level']),
                    status=ChangeStatus(row['status']),
                    proposed_by=row['proposed_by'],
                    approved_by=row['approved_by'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None
            
        except Exception as e:
            logger.error(f"更新变更状态失败: {e}")
            return None
    
    def generate_impact_report(self, report: ImpactAnalysisReport, format: str = "markdown") -> str:
        """
        生成影响分析报告
        
        将影响分析结果转换为指定格式的报告。
        
        参数:
            report: 影响分析报告对象
            format: 输出格式（markdown/json）
        
        返回:
            str: 格式化的报告内容
        """
        if format == "markdown":
            return self._report_to_markdown(report)
        elif format == "json":
            return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _report_to_markdown(self, report: ImpactAnalysisReport) -> str:
        """
        将影响分析报告转换为Markdown格式
        
        参数:
            report: 影响分析报告对象
        
        返回:
            str: Markdown格式的报告内容
        """
        lines = [
            "# 需求变更影响分析报告",
            "",
            f"**生成时间**: {report.generated_at}",
            "",
            "## 变更概述",
            "",
            f"- **变更ID**: {report.requirement_change.id}",
            f"- **需求ID**: {report.requirement_change.requirement_id}",
            f"- **需求名称**: {report.requirement_change.requirement_name}",
            f"- **变更类型**: {report.requirement_change.change_type.value}",
            f"- **影响等级**: {report.requirement_change.impact_level.value}",
            f"- **变更状态**: {report.requirement_change.status.value}",
            "",
            f"**变更描述**: {report.requirement_change.description}",
            "",
        ]
        
        if report.requirement_change.old_value or report.requirement_change.new_value:
            lines.extend([
                "**变更详情**:",
                "",
                "| 属性 | 值 |",
                "|------|-----|",
            ])
            if report.requirement_change.old_value:
                lines.append(f"| 旧值 | {report.requirement_change.old_value} |")
            if report.requirement_change.new_value:
                lines.append(f"| 新值 | {report.requirement_change.new_value} |")
            lines.append("")
        
        lines.extend([
            "## 影响摘要",
            "",
            f"- **受影响测试用例**: {report.impact_summary.get('total_affected_tests', 0)}",
            f"- **受影响代码元素**: {report.impact_summary.get('total_affected_code', 0)}",
            f"- **涉及文件数**: {report.impact_summary.get('unique_files', 0)}",
        ])
        
        if report.impact_summary.get('max_propagation_depth'):
            lines.append(f"- **最大传播深度**: {report.impact_summary.get('max_propagation_depth', 0)}")
        if report.impact_summary.get('critical_path_count'):
            lines.append(f"- **关键传播路径数**: {report.impact_summary.get('critical_path_count', 0)}")
        
        lines.append("")
        
        if report.impact_scope:
            lines.extend([
                "## 影响范围分析",
                "",
                f"- **总影响节点数**: {report.impact_scope.total_nodes}",
                f"- **最大传播深度**: {report.impact_scope.max_depth}",
                "",
                "### 按类型统计",
                "",
            ])
            for item_type, count in report.impact_scope.scope_by_type.items():
                lines.append(f"- {item_type}: {count}")
            
            lines.extend([
                "",
                "### 按影响等级统计",
                "",
            ])
            for level, count in report.impact_scope.scope_by_level.items():
                lines.append(f"- {level}: {count}")
            
            if report.impact_scope.critical_paths:
                lines.extend([
                    "",
                    "### 关键传播路径",
                    "",
                ])
                for i, path in enumerate(report.impact_scope.critical_paths[:10], 1):
                    lines.append(f"{i}. {path['path']}")
                    lines.append(f"   - 深度: {path['depth']}, 影响等级: {path['impact_level']}")
        
        lines.extend([
            "",
            "## 风险评估",
            "",
            f"- **风险等级**: {report.risk_assessment.get('risk_level', 'unknown')}",
            f"- **风险分数**: {report.risk_assessment.get('risk_score', 0):.2f}",
            f"- **风险描述**: {report.risk_assessment.get('risk_description', '')}",
            f"- **关键项目数**: {report.risk_assessment.get('critical_items', 0)}",
            f"- **高优先级项目数**: {report.risk_assessment.get('high_items', 0)}",
        ])
        
        if report.risk_assessment.get('transitive_items'):
            lines.append(f"- **传递影响项数**: {report.risk_assessment.get('transitive_items', 0)}")
        
        lines.extend([
            "",
            "## 受影响测试用例",
            "",
            "| 测试ID | 测试名称 | 类型 | 影响等级 | 范围类型 | 原因 |",
            "|--------|----------|------|----------|----------|------|",
        ])
        
        for test in report.affected_tests:
            lines.append(
                f"| {test.test_id} | {test.test_name} | {test.test_type} | "
                f"{test.impact_level.value} | {test.scope_type.value} | {test.impact_reason} |"
            )
        
        lines.extend([
            "",
            "## 受影响代码元素",
            "",
            "| 代码ID | 名称 | 类型 | 文件 | 影响等级 | 范围类型 | 原因 |",
            "|--------|------|------|------|----------|----------|------|",
        ])
        
        for code in report.affected_code:
            lines.append(
                f"| {code.code_id} | {code.code_name} | {code.code_type} | "
                f"{code.file_path}:{code.line_start}-{code.line_end} | "
                f"{code.impact_level.value} | {code.scope_type.value} | {code.impact_reason} |"
            )
        
        lines.extend([
            "",
            "## 建议措施",
            ""
        ])
        
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"{i}. {rec}")
        
        return '\n'.join(lines)


def main():
    """
    主函数 - 测试需求变更影响分析器
    
    演示分析器的主要功能：
    1. 注册需求变更
    2. 执行影响分析
    3. 生成影响报告
    """
    analyzer = RequirementChangeImpactAnalyzer("test_impact_analysis.db")
    
    print("="*60)
    print("需求变更影响分析器测试")
    print("="*60)
    
    change = analyzer.register_change(
        requirement_id="REQ-001",
        requirement_name="用户登录功能",
        change_type=ChangeType.MODIFY,
        description="修改用户登录验证逻辑，增加双因素认证支持",
        old_value="用户名+密码登录",
        new_value="用户名+密码+双因素认证登录",
        reason="提升系统安全性，满足合规要求",
        proposed_by="张三"
    )
    print(f"\n注册变更: {change.id}")
    print(f"影响等级: {change.impact_level.value}")
    
    print("\n" + "="*60)
    print("执行影响分析")
    print("="*60)
    
    report = analyzer.analyze_impact(change, include_scope=True)
    
    print(f"\n影响摘要:")
    print(json.dumps(report.impact_summary, ensure_ascii=False, indent=2))
    
    if report.impact_scope:
        print(f"\n影响范围分析:")
        print(f"  - 总节点数: {report.impact_scope.total_nodes}")
        print(f"  - 最大深度: {report.impact_scope.max_depth}")
        print(f"  - 关键路径数: {len(report.impact_scope.critical_paths)}")
    
    print(f"\n风险评估:")
    print(json.dumps(report.risk_assessment, ensure_ascii=False, indent=2))
    
    print(f"\n受影响测试: {len(report.affected_tests)}")
    for test in report.affected_tests[:3]:
        print(f"  - {test.test_name} ({test.impact_level.value}, {test.scope_type.value})")
    
    print(f"\n受影响代码: {len(report.affected_code)}")
    for code in report.affected_code[:3]:
        print(f"  - {code.code_name} @ {code.file_path} ({code.impact_level.value}, {code.scope_type.value})")
    
    print("\n" + "="*60)
    print("影响分析报告 (Markdown)")
    print("="*60)
    
    md_report = analyzer.generate_impact_report(report, "markdown")
    print(md_report[:2000])
    
    import os
    if os.path.exists("test_impact_analysis.db"):
        os.remove("test_impact_analysis.db")
        print("\n清理测试数据库")


if __name__ == "__main__":
    main()
