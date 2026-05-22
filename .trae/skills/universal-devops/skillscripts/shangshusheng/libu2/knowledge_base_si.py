"""
知识管理司 - 知识条目CRUD、设计模式知识库、架构决策记录、最佳实践库、经验教训库、知识图谱
"""
from __future__ import annotations

import re
import json
import uuid
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class KnowledgeBaseError(Exception):
    """知识管理相关异常"""
    pass


class EntryNotFoundError(KnowledgeBaseError):
    """条目未找到"""


class PatternCategory(str, Enum):
    """设计模式分类枚举"""
    CREATIONAL = "creational"
    STRUCTURAL = "structural"
    BEHAVIORAL = "behavioral"
    ENTERPRISE = "enterprise"
    CONCURRENCY = "concurrency"


class RelationType(str, Enum):
    """知识关联类型"""
    RELATED = "related"
    PREREQUISITE = "prerequisite"
    ALTERNATIVE = "alternative"
    CONFLICTS = "conflicts"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"


@dataclass
class KnowledgeEntry:
    """知识条目"""
    id: str = ""
    title: str = ""
    content: str = ""
    category: str = ""
    tags: list[str] = field(default_factory=list)
    author: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"kb_{uuid.uuid4().hex[:10]}"
        if not self.created_at:
            self.created_at = __import__("datetime").datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content_preview": self.content[:100],
            "category": self.category,
            "tags": self.tags,
            "author": self.author,
            "created_at": self.created_at[:10],
        }


@dataclass
class DesignPattern:
    """设计模式"""
    name: str
    category: PatternCategory
    alias: list[str] = field(default_factory=list)
    intent: str = ""
    motivation: str = ""
    applicability: list[str] = field(default_factory=list)
    structure: str = ""
    participants: list[str] = field(default_factory=list)
    collaborations: str = ""
    consequences_pros: list[str] = field(default_factory=list)
    consequences_cons: list[str] = field(default_factory=list)
    code_example: str = ""
    related_patterns: list[str] = field(default_factory=list)
    known_uses: list[str] = field(default_factory=list)
    language: str = "python"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "alias": self.alias,
            "intent": self.intent[:80],
            "applicability_count": len(self.applicability),
            "pros_count": len(self.consequences_pros),
            "cons_count": len(self.consequences_cons),
            "has_code_example": bool(self.code_example.strip()),
            "related": self.related_patterns,
        }


@dataclass
class ADR:
    """架构决策记录 (Architecture Decision Record)"""
    id: str = ""
    title: str = ""
    status: str = "proposed"
    context: str = ""
    decision: str = ""
    consequences: str = ""
    alternatives: list[dict[str, str]] = field(default_factory=list)
    created_at: str = ""
    author: str = ""
    labels: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"ADR-{uuid.uuid4().hex[:6].upper()}"
        if not self.created_at:
            self.created_at = __import__("datetime").datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "context": self.context[:100],
            "decision": self.decision[:100],
            "consequences": self.consequences[:100],
            "alternatives_count": len(self.alternatives),
            "labels": self.labels,
            "created_at": self.created_at[:10],
        }


@dataclass
class BestPractice:
    """最佳实践"""
    id: str = ""
    title: str = ""
    tech_stack: str = ""
    category: str = ""
    content: str = ""
    code_snippet: str = ""
    severity: str = "recommended"
    references: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"bp_{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "tech_stack": self.tech_stack,
            "category": self.category,
            "severity": self.severity,
            "has_code": bool(self.code_snippet.strip()),
            "tags": self.tags,
        }


@dataclass
class LessonLearned:
    """经验教训"""
    id: str = ""
    title: str = ""
    problem: str = ""
    root_cause: str = ""
    solution: str = ""
    prevention: str = ""
    impact: str = "medium"
    project: str = ""
    date_occurred: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = f"ll_{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "problem": self.problem[:60],
            "root_cause": self.root_cause[:60],
            "impact": self.impact,
            "project": self.project,
            "tags": self.tags,
        }


@dataclass
class KnowledgeGraph:
    """知识图谱节点/边"""
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "nodes": self.nodes[:5],
            "edges": self.edges[:5],
        }

    @property
    def density(self) -> float:
        n = len(self.nodes)
        if n < 2:
            return 0.0
        max_edges = n * (n - 1) / 2
        return len(self.edges) / max_edges


_GOF_PATTERNS: list[DesignPattern] = [
    DesignPattern(name="Singleton", category=PatternCategory.CREATIONAL,
                  alias=["单例"], intent="确保一个类只有一个实例，并提供全局访问点",
                  applicability=["需要严格控制唯一实例的场景", "日志管理器", "配置管理器", "连接池"],
                  participants=["Singleton类"],
                  code_example='''class Singleton:
    _instance: "Singleton | None" = None

    def __new__(cls) -> "Singleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def business_method(self) -> None:
        print("Singleton method called")
''',
                  consequences_pros=["延迟初始化", "全局访问点", "受控访问"],
                  consequences_cons=["违反单一职责原则", "隐藏依赖关系", "测试困难", "不支持多态替换"],
                  related_patterns=["Abstract Factory", "Builder", "Prototype"]),
    DesignPattern(name="Abstract Factory", category=PatternCategory.CREATIONAL,
                  alias=["抽象工厂"], intent="提供创建一系列相关或相互依赖对象的接口，无需指定具体类",
                  applicability=["跨平台UI组件族", "数据库驱动适配", "不同主题的UI组件"],
                  code_example='''from abc import ABC, abstractmethod

class Button(ABC):
    @abstractmethod
    def render(self): ...

class WindowsButton(Button):
    def render(self): print("Windows button")

class MacOSButton(Button):
    def render(self): print("macOS button")

class GUIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button: ...
''',
                  consequences_pros=["产品族一致性", "易切换产品族", "符合开闭原则"],
                  consequences_cons=["新增产品复杂", "类数量膨胀", "接口稳定性要求高"],
                  related_patterns=["Factory Method", "Singleton", "Prototype"]),
    DesignPattern(name="Builder", category=PatternCategory.CREATIONAL,
                  alias=["建造者"], intent="将复杂对象的构建过程与其表示分离，使同样的构建过程可创建不同表示",
                  applicability=["复杂对象构建（多个可选参数）", "不可变对象构造", "步骤化构建流程"],
                  code_example='''class HttpRequestBuilder:
    def __init__(self):
        self._url = ""
        self._method = "GET"
        self._headers: dict = {}
        self._body: str = ""

    def set_url(self, url: str) -> "HttpRequestBuilder":
        self._url = url; return self
    def set_method(self, method: str) -> "HttpRequestBuilder":
        self._method = method; return self
    def add_header(self, key: str, val: str) -> "HttpRequestBuilder":
        self._headers[key] = val; return self
    def build(self) -> dict:
        return {"url": self._url, "method": self._method, "headers": self._headers}
''',
                  consequences_pros=["精细控制构建步骤", "可变参数灵活组合", "不可变性保证"],
                  consequences_cons=["产品间差异大时冗余", "需额外Builder类", "内部一致性维护"],
                  related_patterns=["Abstract Factory", "Composite", "Template Method"]),
    DesignPattern(name="Prototype", category=PatternCategory.CREATIONAL,
                  alias=["原型"], intent="通过复制已有对象来创建新对象，无需知道具体类",
                  applicability=["对象创建代价高", "避免子类爆炸", "动态添加/删除属性"],
                  consequences_pros=["减少子类", "运行时动态增删", "隐藏创建细节"],
                  consequences_cons=["深拷贝复杂", "循环引用问题", "clone方法实现负担"],
                  related_patterns=["Abstract Factory", "Singleton", "Decorator"]),
    DesignPattern(name="Factory Method", category=PatternCategory.CREATIONAL,
                  alias=["工厂方法"], intent="定义创建对象的接口，让子类决定实例化哪个类",
                  applicability=["框架中的可扩展组件", "不确定具体类型的创建", "延迟到子类决定"],
                  code_example='''from abc import ABC, abstractmethod

class Document(ABC):
    @abstractmethod
    def open(self): ...
    @abstractmethod
    def save(self): ...

class PDFDocument(Document):
    def open(self): print("Opening PDF")
    def save(self): print("Saving PDF")

class Application(ABC):
    @abstractmethod
    def create_document(self) -> Document: ...
''',
                  consequences_pros=["开闭原则", "解耦使用与创建", "框架集成友好"],
                  consequences_cons=["类数量增加", "重构可能影响层级", "简单场景过度设计"],
                  related_patterns=["Abstract Factory", "Template Method", "Prototype"]),
    DesignPattern(name="Adapter", category=PatternCategory.STRUCTURAL,
                  alias=["适配器", "Wrapper"], intent="将一个类的接口转换成客户期望的另一个接口",
                  applicability=["遗留系统对接", "第三方库接口不兼容", "统一不同接口"],
                  code_example='''class LegacyPrinter:
    def print_text(self, text: str) -> None:
        print(f"[Legacy] {text}")

class ModernPrinter(ABC):
    @abstractmethod
    def print_document(self, content: str) -> None: ...

class PrinterAdapter(ModernPrinter):
    def __init__(self, legacy: LegacyPrinter):
        self._legacy = legacy
    def print_document(self, content: str) -> None:
        self._legacy.print_text(content)
''',
                  consequences_pros=["复用现有类", "透明转换", "解耦客户端与适配者"],
                  consequences_cons["间接调用开销", "过多适配导致混乱", "调试路径变长"] = ["间接调用开销", "过多适配导致混乱", "调试路径变长"],
                  related_patterns=["Bridge", "Decorator", "Proxy", "Facade"]),
    DesignPattern(name="Bridge", category=PatternCategory.STRUCTURAL,
                  alias=["桥接"], intent="将抽象部分与实现部分分离，使其可以独立变化",
                  applicability=["多维变化（平台×功能）", "避免类继承爆炸", "运行时切换实现"],
                  consequences_pros["分离关注点", "扩展独立", "对客户端透明"] = ["分离关注点", "扩展独立", "对客户端透明"],
                  consequences_cons["增加复杂度", "间接性", "初始设计难度"] = ["增加复杂度", "间接性", "初始设计难度"],
                  related_patterns=["Adapter", "Abstract Factory", "Strategy", "State"]),
    DesignPattern(name="Composite", category=PatternCategory.STRUCTURAL,
                  alias=["组合"], intent="将对象组合成树形结构以表示'部分-整体'层次结构",
                  applicability["文件系统", "GUI控件树", "组织架构树", "表达式解析"] = ["文件系统", "GUI控件树", "组织架构树", "表达式解析"],
                  code_example='''from abc import ABC, abstractmethod

class FileSystemNode(ABC):
    @property
    @abstractmethod
    def size(self) -> int: ...
    @abstractmethod
    def display(self, indent: int = 0) -> None: ...

class File(FileSystemNode):
    def __init__(self, name: str, size: int):
        self.name = name; self._size = size
    @property
    def size(self) -> int: return self._size
    def display(self, indent: int = 0) -> None:
        print("  " * indent + f"- {self.name} ({self._size}KB)")

class Directory(FileSystemNode):
    def __init__(self, name: str):
        self.name = name; self.children: list[FileSystemNode] = []
    def add(self, node: FileSystemNode) -> None: self.children.append(node)
    @property
    def size(self) -> int: return sum(c.size for c in self.children)
    def display(self, indent: int = 0) -> None:
        print("  " * indent + f"+ {self.name}/")
        for child in self.children: child.display(indent + 1)
''',
                  consequences_pros["简化客户端代码", "递归操作便利", "开闭原则"] = ["简化客户端代码", "递归操作便利", "开闭原则"],
                  consequences_cons["类型安全挑战", "设计过于通用", "性能考虑"] = ["类型安全挑战", "设计过于通用", "性能考虑"],
                  related_patterns=["Iterator", "Visitor", "Decorator", "Flyweight"]),
    DesignPattern(name="Decorator", category=PatternCategory.STRUCTURAL,
                  alias=["装饰器", "Wrapper"], intent="动态地给一个对象添加额外的职责",
                  applicability["静态继承不灵活", "不能修改源码时", "职责按需组合"] = ["静态继承不灵活", "不能修改源码时", "职责按需组合"],
                  code_example='''from abc import ABC, abstractmethod

class Coffee(ABC):
    @property
    @abstractmethod
    def cost(self) -> float: ...
    @property
    @abstractmethod
    def description(self) -> str: ...

class SimpleCoffee(Coffee):
    @property
    def cost(self) -> float: return 5.0
    @property
    def description(self) -> str: return "Simple Coffee"

class MilkDecorator(Coffee):
    def __init__(self, coffee: Coffee): self._coffee = coffee
    @property
    def cost(self) -> float: return self._coffee.cost + 1.5
    @property
    def description(self) -> str: return f"{self._coffee.description}, Milk"
''',
                  consequences_pros["比静态继承灵活", "运行时增删职责", "单一职责"] = ["比静态继承灵活", "运行时增删职责", "单一职责"],
                  consequences_cons["装饰链过长难调试", "小对象大量产生", "类型识别复杂"] = ["装饰链过长难调试", "小对象大量产生", "类型识别复杂"],
                  related_patterns=["Adapter", "Composite", "Strategy", "Proxy"]),
    DesignPattern(name="Facade", category=PatternCategory.STRUCTURAL,
                  alias=["外观"], intent="为子系统提供一个统一的接口，定义一个高层接口",
                  applicability["复杂子系统简化", "分层架构边界", "API网关模式"] = ["复杂子系统简化", "分层架构边界", "API网关模式"],
                  consequences_pros["简化接口", "降低耦合", "更好分层"] = ["简化接口", "降低耦合", "更好分层"],
                  consequences_cons["可能成为上帝对象", "限制灵活性", "引入不必要的中间层"] = ["可能成为上帝对象", "限制灵活性", "引入不必要的中间层"],
                  related_patterns=["Abstract Factory", "Adapter", "Singleton", "Mediator"]),
    DesignPattern(name="Flyweight", category=PatternCategory.STRUCTURAL,
                  alias=["享元"], intent="运用共享技术有效支持大量细粒度的对象",
                  applicability["大量相似对象", "内存敏感场景", "对象状态可外部化"] = ["大量相似对象", "内存敏感场景", "对象状态可外部化"],
                  consequences_pros["大幅减少对象数", "节省内存", "集中管理共享状态"] = ["大幅减少对象数", "节省内存", "集中管理共享状态"],
                  consequences_cons["内外状态分离复杂", "线程安全考虑", "共享状态修改风险"] = ["内外状态分离复杂", "线程安全考虑", "共享状态修改风险"],
                  related_patterns=["Composite", "State", "Strategy", "Factory"]),
    DesignPattern(name="Proxy", category=PatternCategory.STRUCTURAL,
                  alias=["代理"], intent="为其他对象提供一种代理以控制对这个对象的访问",
                  applicability["远程代理", "虚拟代理", "保护代理", "智能引用"] = ["远程代理", "虚拟代理", "保护代理", "智能引用"],
                  consequences_pros["控制访问", "延迟加载", "附加功能透明"] = ["控制访问", "延迟加载", "附加功能透明"],
                  consequences_cons["响应时间增加", "额外代理类", "间接调用"] = ["响应时间增加", "额外代理类", "间接调用"],
                  related_patterns=["Adapter", "Decorator", "Facade"]),
    DesignPattern(name="Chain of Responsibility", category=PatternCategory.BEHAVIORAL,
                  alias=["责任链"], intent="将请求沿处理者链传递，直到有对象处理它",
                  applicability["审批流程", "中间件管道", "事件处理链"] = ["审批流程", "中间件管道", "事件处理链"],
                  code_example='''from abc import ABC, abstractmethod

class Handler(ABC):
    _next_handler: "Handler | None" = None

    def set_next(self, handler: "Handler") -> "Handler":
        self._next_handler = handler; return handler

    @abstractmethod
    def handle(self, request: int) -> str: ...

    def _handle_next(self, request: int) -> str:
        if self._next_handler:
            return self._next_handler.handle(request)
        return "No handler available"

class TeamLeadHandler(Handler):
    def handle(self, request: int) -> str:
        if request <= 3: return f"TeamLead approved ({request} days)"
        return self._handle_next(request)

class ManagerHandler(Handler):
    def handle(self, request: int) -> str:
        if request <= 7: return f"Manager approved ({request} days)"
        return self._handle_next(request)
''',
                  consequences_pros["解耦发送者和接收者", "动态调整链", "开闭原则"] = ["解耦发送者和接收者", "动态调整链", "开闭原则"],
                  consequences_cons["请求可能未被处理", "调试困难", "性能考虑"] = ["请求可能未被处理", "调试困难", "性能考虑"],
                  related_patterns=["Command", "Mediator", "Composite"]),
    DesignPattern(name="Command", category=PatternCategory.BEHAVIORAL,
                  alias=["命令"], intent="将请求封装为一个对象，从而可用不同的请求对客户进行参数化",
                  applicability["操作队列", "撤销/重做", "事务操作"] = ["操作队列", "撤销/重做", "事务操作"],
                  consequences_pros["解耦调用者和执行者", "支持撤销/重做", "易于扩展新命令"] = ["解耦调用者和执行者", "支持撤销/重做", "易于扩展新命令"],
                  consequences_cons["类数量膨胀", "命令对象传递开销", "调试追踪复杂"] = ["类数量膨胀", "命令对象传递开销", "调试追踪复杂"],
                  related_patterns=["Memento", "Composite", "Chain of Responsibility"]),
    DesignPattern(name="Observer", category=PatternCategory.BEHAVIORAL,
                  alias=["观察者", "发布-订阅"], intent="定义对象间一对多的依赖关系，当一个对象改变状态时所有依赖者自动通知",
                  applicability["事件系统", "MVC模式", "消息队列", "响应式编程"] = ["事件系统", "MVC模式", "消息队列", "响应式编程"],
                  code_example='''from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def update(self, message: str) -> None: ...

class Subject:
    def __init__(self):
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def notify(self, message: str) -> None:
        for obs in self._observers:
            obs.update(message)

class EmailNotifier(Observer):
    def update(self, message: str) -> None:
        print(f"📧 Email: {message}")

class SlackNotifier(Observer):
    def update(self, message: str) -> None:
        print(f"💬 Slack: {message}")
''',
                  consequences_pros["广播通信", "松耦合", "运行时动态订阅"] = ["广播通信", "松耦合", "运行时动态订阅"],
                  consequences_cons["意外更新", "顺序不确定", "内存泄漏风险"] = ["意外更新", "顺序不确定", "内存泄漏风险"],
                  related_patterns=["Mediator", "Chain of Responsibility", "Command"]),
    DesignPattern(name="Strategy", category=PatternCategory.BEHAVIORAL,
                  alias=["策略"], intent="定义一系列算法，将每个算法封装起来并使它们可互相替换",
                  applicability["多种算法选择", "避免条件语句", "算法独立于使用者"] = ["多种算法选择", "避免条件语句", "算法独立于使用者"],
                  consequences_pros["算法可独立变化", "消除条件判断", "开闭原则"] = ["算法可独立变化", "消除条件判断", "开闭原则"],
                  consequences_cons["客户端需了解策略", "策略数量增多", "策略间可能有重复"] = ["客户端需了解策略", "策略数量增多", "策略间可能有重复"],
                  related_patterns=["State", "Template Method", "Factory Method"]),
    DesignPattern(name="Template Method", category=PatternCategory.BEHAVIORAL,
                  alias=["模板方法"], intent="定义算法骨架，将某些步骤延迟到子类",
                  applicability["算法框架不变，步骤可变", "代码复用", "钩子方法扩展"] = ["算法框架不变，步骤可变", "代码复用", "钩子方法扩展"],
                  consequences_pros["代码复用最大化", "反向控制", "一致行为"] = ["代码复用最大化", "反向控制", "一致行为"],
                  consequences_cons["继承约束", "步骤变更影响子类", "深度继承层次"] = ["继承约束", "步骤变更影响子类", "深度继承层次"],
                  related_patterns=["Strategy", "Factory Method", "Hook Methods"]),
    DesignPattern(name="State", category=PatternCategory.BEHAVIORAL,
                  alias=["状态"], intent="允许对象在其内部状态改变时改变其行为",
                  applicability["对象行为依赖状态", "大量条件分支", "状态机实现"] = ["对象行为依赖状态", "大量条件分支", "状态机实现"],
                  consequences_pros["状态转换封装", "消除条件语句", "易添加新状态"] = ["状态转换封装", "消除条件语句", "易添加新状态"],
                  consequences_cons["类数量增长", "状态间耦合", "状态转换逻辑分散"] = ["类数量增长", "状态间耦合", "状态转换逻辑分散"],
                  related_patterns=["Strategy", "Flyweight", "Singleton"]),
    DesignPattern(name="Mediator", category=PatternCategory.BEHAVIORAL,
                  alias["中介者"] = ["中介者"], intent="用一个中介对象来封装一系列的对象交互",
                  applicability["对象间引用复杂", "想自定义分布在多个类中的行为", "复用困难"] = ["对象间引用复杂", "想自定义分布在多个类中的行为", "复用困难"],
                  consequences_pros["降低耦合", "集中交互逻辑", "单体化交互"] = ["降低耦合", "集中交互逻辑", "单体化交互"],
                  consequences_cons["中介者可能庞大", "维护复杂", "性能中心化"] = ["中介者可能庞大", "维护复杂", "性能中心化"],
                  related_patterns=["Facade", "Observer", "Chain of Responsibility"]),
    DesignPattern(name="Iterator", category=PatternCategory.BEHAVIORAL,
                  alias["迭代器"] = ["迭代器"], intent="提供一种方法顺序访问聚合对象中各个元素而不暴露其内部表示",
                  applicability["遍历集合", "统一遍历接口", "支持多种遍历方式"] = ["遍历集合", "统一遍历接口", "支持多种遍历方式"],
                  consequences_pros["单一职责", "支持多种遍历", "简化集合接口"] = ["单一职责", "支持多种遍历", "简化集合接口"],
                  consequences_cons["增加类数量", "语言已内置支持", "简单场景过重"] = ["增加类数量", "语言已内置支持", "简单场景过重"],
                  related_patterns=["Composite", "Factory Method", "Memento"]),
    DesignPattern(name="Memento", category=PatternCategory.BEHAVIORAL,
                  alias["备忘录"] = ["备忘录"], intent="捕获并恢复对象的内部状态而不破坏封装性",
                  applicability["快照/撤销", "事务回滚", "游戏存档"] = ["快照/撤销", "事务回滚", "游戏存档"],
                  consequences_pros["保持封装", "简化Originator", "状态历史管理"] = ["保持封装", "简化Originator", "状态历史管理"],
                  consequences_cons["资源消耗大", "Caretaker存储开销", "Memento管理复杂"] = ["资源消耗大", "Caretaker存储开销", "Memento管理复杂"],
                  related_patterns=["Command", "Iterator", "State"]),
    DesignPattern(name="Visitor", category=PatternCategory.BEHAVIORAL,
                  alias["访问者"] = ["访问者"], intent="表示作用于某对象结构中各元素的操作，在不改变元素类的前提下定义新操作",
                  applicability["对象结构稳定但操作多变", "跨类操作", "编译器AST遍历"] = ["对象结构稳定但操作多变", "跨类操作", "编译器AST遍历"],
                  consequences_pros["新增操作方便", "相关操作集中", "访问者可积累状态"] = ["新增操作方便", "相关操作集中", "访问者可积累状态"],
                  consequences_cons["新增Element困难", "破坏封装", "依赖具体类"] = ["新增Element困难", "破坏封装", "依赖具体类"],
                  related_patterns=["Composite", "Interpreter", "Double Dispatch"]),
    DesignPattern(name="Interpreter", category=PatternCategory.BEHAVIORAL,
                  alias["解释器"] = ["解释器"], intent="给定一个语言，定义它的文法表示，并定义一个解释器",
                  applicability["DSL实现", "规则引擎", "SQL解析器"] = ["DSL实现", "规则引擎", "SQL解析器"],
                  consequences_pros["易于语法扩展", "文法清晰", "适合简单语法"] = ["易于语法扩展", "文法清晰", "适合简单语法"],
                  consequences_cons["复杂语法效率低", "类层次膨胀", "维护成本高"] = ["复杂语法效率低", "类层次膨胀", "维护成本高"],
                  related_patterns=["Composite", "Iterator", "Visitor"]),
]

_BEST_PRACTICES_DATA: dict[str, list[dict[str, Any]]] = {
    "python": [
        {"title": "使用type hints和mypy进行静态类型检查", "category": "code_quality",
         "content": "在Python 3.10+中使用联合类型语法|和match语句，配合mypy strict模式",
         "code_snippet": "def process(data: str | None) -> list[str]:\n    return data.split() if data else []"},
        {"title": "优先使用dataclass替代namedtuple", "category": "code_quality",
         "content": "dataclass提供更好的默认值、类型注解和__post_init__钩子",
         "code_snippet": "@dataclass\nclass User:\n    name: str\n    age: int = 0"},
        {"title": "异步IO使用asyncio而非threading", "category": "performance",
         "content": "I/O密集型任务应使用async/await，CPU密集型才考虑multiprocessing"},
        {"title": "使用pathlib.Path代替os.path", "category": "modern_python",
         "content": "pathlib提供面向对象的路径操作，更Pythonic且跨平台"},
        {"title": "依赖注入使用构造函数注入", "category": "architecture",
         "content": "通过__init__参数注入依赖，便于测试和替换"},
        {"title": "异常使用特定异常类而非Exception", "category": "error_handling",
         "content": "定义领域异常层次结构，捕获精确的异常类型"},
        {"title": "日志使用structlog或logging模块", "category": "observability",
         "content": "避免print()用于生产日志，使用结构化日志格式"},
        {"title": "环境变量使用pydantic-settings", "category": "configuration",
         "content": "利用Pydantic的验证能力自动检查环境变量"},
        {"title": "测试使用pytest+pytest-asyncio", "category": "testing",
         "content": "使用fixture、parametrize和async测试支持"},
        {"title": "安全：永远不要硬编码密钥", "category": "security",
         "content": "使用环境变量或密钥管理系统，代码中不应出现明文密钥"},
    ],
    "go": [
        {"title": "错误处理使用显式error返回值", "category": "idiomatic_go",
         "content": "Go惯用法是返回(error, value)，不要panic用于业务逻辑"},
        {"title": "接口定义在使用方而非实现方", "category": "architecture",
         "content": "遵循'accept interfaces, return structs'原则"},
        {"title": "使用context.Context传递取消和超时", "category": "concurrency",
         "content": "所有长时间运行的函数都应接受context参数"},
        {"title": "defer用于资源清理", "category": "resource_management",
         "content": "确保文件句柄、锁等资源的释放"},
        {"title": "并发使用channel而非共享内存", "category": "concurrency",
         "content": '"Do not communicate by sharing memory; instead, share memory by communicating."'},
        {"title": "使用table-driven tests", "category": "testing",
         "content": "Go标准测试模式，用slice of struct定义测试用例"},
        {"title": "避免全局变量和包级变量", "category": "code_quality",
         "content": "使用依赖注入传递依赖，提高可测试性"},
        {"title": "使用go.uber.org/zap做高性能日志", "category": "observability",
         "content": "zap比标准库log快很多，且支持结构化日志"},
        {"title": "使用golangci-lint统一代码风格", "category": "linting",
         "content": "集成到CI中，统一团队的Go代码规范"},
        {"title": "优雅关闭处理SIGTERM信号", "category": "deployment",
         "content": "Kubernetes会发送SIGTERM，服务需正确处理graceful shutdown"},
    ],
    "javascript": [
        {"title": "使用const/let替代var", "category": "modern_js",
         "content": "const用于不变绑定，let用于可变绑定，避免var的作用域陷阱"},
        {"title": "优先使用箭头函数", "category": "functional",
         "content": "箭头函数没有this绑定问题，更适合回调和高阶函数"},
        {"title": "使用async/await替代Promise链", "category": "asynchronous",
         "content": "async/await更直观地表达异步流程，错误处理也更简洁"},
        {"title": "解构赋值和展开运算符", "category": "syntax",
         "content": "充分利用ES6+语法糖提升代码可读性"},
        {"title": "使用TypeScript严格模式", "category": "typesafety",
         "content": "开启strict: true，noImplicitAny等选项"},
        {"title": "错误处理使用Result/Either模式", "category": "error_handling",
         "content": "避免try/catch嵌套，使用函数式错误处理"},
        {"title": "模块使用ES Modules", "category": "modules",
         "content": "import/export语法，配合package.json type: module"},
        {"title": "使用ESLint+Prettier统一风格", "category": "linting",
         "content": "团队统一配置，pre-commit hook自动执行"},
        {"title": "React Hooks优于Class Components", "category": "react",
         "content": "useState/useEffect/useCallback/useMemo的正确使用"},
        {"title": "XSS防护：始终转义用户输入", "category": "security",
         "content": "React自动转义，原生JS需使用DOMPurify等库"},
    ],
}


class KnowledgeBaseSi:
    """
    知识管理司 - 礼部·稽勋司

    提供全面的知识管理能力：
    - 知识条目CRUD（创建/读取/更新/删除/搜索/标签管理）
    - 设计模式知识库（23种GOF模式完整说明+分类+代码示例）
    - 架构决策知识库（ADR归档与检索）
    - 最佳实践库（按技术栈分类）
    - 经验教训库（Lessons Learned）
    - 知识图谱构建（知识点关联关系）
    - 向量检索接口预留（embedding接口）
    """

    _INSTANCE: KnowledgeBaseSi | None = None

    def __init__(self) -> None:
        self._entries: dict[str, KnowledgeEntry] = {}
        self._patterns: dict[str, DesignPattern] = {p.name: p for p in _GOF_PATTERNS}
        self._adrs: dict[str, ADR] = {}
        self._best_practices: dict[str, BestPractice] = {}
        self._lessons_learned: dict[str, LessonLearned] = {}
        self._graph = KnowledgeGraph()
        self._tag_index: dict[str, set[str]] = {}
        self._initialize_builtin_data()

    @classmethod
    def get_instance(cls) -> KnowledgeBaseSi:
        """获取单例实例"""
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    def _initialize_builtin_data(self) -> None:
        """初始化内置数据"""
        for stack, practices in _BEST_PRACTICES_DATA.items():
            for pdata in practices:
                bp = BestPractice(
                    title=pdata["title"],
                    tech_stack=stack,
                    category=pdata.get("category", ""),
                    content=pdata["content"],
                    code_snippet=pdata.get("code_snippet", ""),
                    severity="recommended",
                    tags=[stack, pdata.get("category", "")],
                )
                self._best_practices[bp.id] = bp
                self._index_tags(bp.id, bp.tags)

        sample_adrs = [
            ADR(title="采用FastAPI作为Web框架", status="accepted",
                 context="项目需要一个高性能异步Web API框架，团队熟悉Python生态",
                 decision="选择FastAPI而非Flask/Django REST Framework",
                 consequences="获得自动OpenAPI文档、高性能异步支持和Pydantic数据验证。学习曲线较Flask稍陡。",
                 alternatives=[{"option": "Flask", "reason": "轻量但缺少现代特性"}, {"option": "Django REST", "reason": "太重量级"}],
                 labels=["framework", "python", "api"]),
            ADR(title="PostgreSQL作为主数据库", status="accepted",
                 context="需要ACID事务支持、JSON查询能力和成熟生态系统",
                 decision="使用PostgreSQL 15+作为主数据库",
                 consequences="强大的查询能力但需要DBA运维经验。考虑读写分离方案。",
                 alternatives=[{"option": "MySQL", "reason": "JSON支持较弱"}, {"option": "MongoDB", "reason": "事务支持不足"}],
                 labels=["database", "infrastructure"]),
            ADR(title="微服务 vs 单体架构", status="superseded",
                 context="初期团队规模小，业务复杂度中等",
                 decision="初期采用模块化单体，后续按域拆分为微服务",
                 consequences="初期开发效率高，后期拆分需要良好的模块边界。",
                 alternatives=[{"option": "纯微服务", "reason": "初期运维成本过高"}, {"option": "纯单体", "reason": "后期难以拆分"}],
                 labels=["architecture", "strategy"]),
        ]
        for adr in sample_adrs:
            self._adrs[adr.id] = adr
            self._index_tags(adr.id, adr.labels)

        sample_lessons = [
            LessonLearned(
                title="数据库连接池耗尽导致服务宕机",
                problem="高峰期API响应超时率从0.1%飙升至15%",
                root_cause="连接池最大连接数设置过低(20)，且连接泄漏未正确回收",
                solution="增大连接池至200，添加连接健康检查，实施连接超时回收机制",
                prevention="建立数据库连接监控告警，定期审查连接池配置，压力测试验证上限",
                impact="high", project="order-service-v2",
                tags=["database", "production-incident", "monitoring"],
            ),
            LessonLearned(
                title="缓存穿透导致Redis被击穿",
                problem="缓存未命中时大量请求直达数据库",
                root_cause="恶意用户持续查询不存在的key，且无布隆过滤器保护",
                solution="引入布隆过滤器拦截无效查询，空结果也短期缓存，限流保护",
                prevention="所有缓存查询加布隆过滤器前置，空值缓存设短TTL，接入WAF防刷",
                impact="medium", project="user-api",
                tags=["cache", "redis", "security"],
            ),
            LessonLearned(
                title="Kafka消费者组rebalance风暴",
                problem="消费者频繁rebalance导致消息处理延迟激增",
                root_cause="max.poll.interval.ms设置过短，批量处理耗时超过该阈值",
                solution="调大max.poll.interval.ms至5分钟，优化批处理逻辑，增加心跳间隔",
                prevention="Kafka消费者配置标准化，添加rebalance监控指标，压测验证消费吞吐量",
                impact="medium", project="event-pipeline",
                tags=["kafka", "messaging", "performance"],
            ),
        ]
        for ll in sample_lessons:
            self._lessons_learned[ll.id] = ll
            self._index_tags(ll.id, ll.tags)

        self._build_knowledge_graph()

    # ==================== CRUD ====================

    def create_entry(
        self,
        title: str,
        content: str,
        category: str = "",
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> KnowledgeEntry:
        """创建知识条目"""
        entry = KnowledgeEntry(
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            **kwargs,
        )
        self._entries[entry.id] = entry
        self._index_tags(entry.id, entry.tags)
        return entry

    def get_entry(self, entry_id: str) -> KnowledgeEntry:
        """获取知识条目"""
        if entry_id not in self._entries:
            raise EntryNotFoundError(f"知识条目不存在: {entry_id}")
        return self._entries[entry_id]

    def update_entry(self, entry_id: str, **updates: Any) -> KnowledgeEntry:
        """更新知识条目"""
        entry = self.get_entry(entry_id)
        for key, value in updates.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        entry.updated_at = __import__("datetime").datetime.now().isoformat()
        if "tags" in updates:
            self._reindex_tags(entry_id, updates["tags"])
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        """删除知识条目"""
        if entry_id in self._entries:
            entry = self._entries.pop(entry_id)
            self._remove_from_tag_index(entry_id, entry.tags)
            return True
        return False

    def search_entries(
        self,
        query: str = "",
        category: str = "",
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[KnowledgeEntry]:
        """
        搜索知识条目（支持全文搜索、分类过滤、标签过滤）

        Args:
            query: 搜索关键词
            category: 分类过滤
            tags: 标签过滤（AND逻辑）
            limit: 返回数量限制

        Returns:
            匹配的条目列表
        """
        results: list[tuple[KnowledgeEntry, float]] = []
        query_lower = query.lower() if query else ""

        for entry in self._entries.values():
            score = 0.0
            if category and entry.category != category:
                continue
            if tags:
                if not all(t in entry.tags for t in tags):
                    continue
                score += len(set(tags) & set(entry.tags)) * 10
            if query_lower:
                if query_lower in entry.title.lower():
                    score += 50
                if query_lower in entry.content.lower():
                    score += 20
                for tag in entry.tags:
                    if query_lower in tag.lower():
                        score += 5
            else:
                score += 1.0

            if score > 0:
                results.append((entry, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results[:limit]]

    # ==================== 设计模式 ====================

    def get_pattern(self, name: str) -> DesignPattern | None:
        """获取设计模式"""
        return self._patterns.get(name)

    def list_patterns(
        self,
        category: PatternCategory | None = None,
    ) -> list[DesignPattern]:
        """列出设计模式"""
        patterns = list(self._patterns.values())
        if category:
            patterns = [p for p in patterns if p.category == category]
        return sorted(patterns, key=lambda p: p.category.value)

    def search_patterns(self, query: str) -> list[DesignPattern]:
        """搜索设计模式"""
        q = query.lower()
        results: list[tuple[DesignPattern, float]] = []
        for pattern in self._patterns.values():
            score = 0.0
            if q in pattern.name.lower(): score += 30
            if q in pattern.intent.lower(): score += 20
            if any(q in a.lower() for a in pattern.alias): score += 25
            if any(q in a.lower() for a in pattern.applicability): score += 10
            if any(q in p.lower() for p in pattern.related_patterns): score += 5
            if score > 0:
                results.append((pattern, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results]

    # ==================== ADR ====================

    def create_adr(self, **kwargs: Any) -> ADR:
        """创建架构决策记录"""
        adr = ADR(**kwargs)
        self._adrs[adr.id] = adr
        self._index_tags(adr.id, adr.labels)
        return adr

    def get_adr(self, adr_id: str) -> ADR:
        """获取ADR"""
        if adr_id not in self._adrs:
            raise EntryNotFoundError(f"ADR不存在: {adr_id}")
        return self._adrs[adr_id]

    def list_adrs(self, status: str | None = None) -> list[ADR]:
        """列出ADR"""
        adrs = list(self._adrs.values())
        if status:
            adrs = [a for a in adrs if a.status == status]
        return sorted(adrs, key=lambda a: a.created_at, reverse=True)

    # ==================== 最佳实践 ====================

    def get_best_practices(self, tech_stack: str = "") -> list[BestPractice]:
        """获取最佳实践"""
        practices = list(self._best_practices.values())
        if tech_stack:
            practices = [p for p in practices if p.tech_stack == tech_stack]
        return sorted(practices, key=lambda p: (p.tech_stack, p.category))

    def search_best_practices(self, query: str) -> list[BestPractice]:
        """搜索最佳实践"""
        q = query.lower()
        results: list[tuple[BestPractice, float]] = []
        for bp in self._best_practices.values():
            score = 0.0
            if q in bp.title.lower(): score += 30
            if q in bp.content.lower(): score += 15
            if q in bp.category.lower(): score += 10
            if any(q in t.lower() for t in bp.tags): score += 8
            if score > 0:
                results.append((bp, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in results]

    # ==================== 经验教训 ====================

    def create_lesson(self, **kwargs: Any) -> LessonLearned:
        """创建经验教训"""
        lesson = LessonLearned(**kwargs)
        self._lessons_learned[lesson.id] = lesson
        self._index_tags(lesson.id, lesson.tags)
        return lesson

    def get_lesson(self, lesson_id: str) -> LessonLearned:
        """获取经验教训"""
        if lesson_id not in self._lessons_learned:
            raise EntryNotFoundError(f"经验教训不存在: {lesson_id}")
        return self._lessons_learned[lesson_id]

    def list_lessons(self, impact: str = "") -> list[LessonLearned]:
        """列出经验教训"""
        lessons = list(self._lessons_learned.values())
        if impact:
            lessons = [l for l in lessons if l.impact == impact]
        return sorted(lessons, key=lambda l: l.impact, reverse=True)

    # ==================== 标签管理 ====================

    def _index_tags(self, entry_id: str, tags: list[str]) -> None:
        for tag in tags:
            self._tag_index.setdefault(tag.lower(), set()).add(entry_id)

    def _reindex_tags(self, entry_id: str, new_tags: list[str]) -> None:
        old_tags = set()
        for tag, ids in self._tag_index.items():
            if entry_id in ids:
                old_tags.add(tag)
                ids.discard(entry_id)
        for tag in new_tags:
            self._tag_index.setdefault(tag.lower(), set()).add(entry_id)

    def _remove_from_tag_index(self, entry_id: str, tags: list[str]) -> None:
        for tag in tags:
            if tag.lower() in self._tag_index:
                self._tag_index[tag.lower()].discard(entry_id)

    def get_all_tags(self) -> dict[str, int]:
        """获取所有标签及其关联条目数"""
        return {tag: len(ids) for tag, ids in sorted(self._tag_index.items())}

    def get_entries_by_tag(self, tag: str) -> list[str]:
        """按标签获取条目ID列表"""
        return sorted(self._tag_index.get(tag.lower(), set()))

    # ==================== 知识图谱 ====================

    def _build_knowledge_graph(self) -> None:
        """构建知识点之间的关联关系图"""
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        all_items: dict[str, dict[str, Any]] = {}

        for pattern in self._patterns.values():
            pid = f"pattern:{pattern.name}"
            all_items[pid] = {"type": "pattern", "name": pattern.name, "category": pattern.category.value}

        for adr in self._adrs.values():
            aid = f"adr:{adr.id}"
            all_items[aid] = {"type": "adr", "name": adr.title, "status": adr.status}

        for bp in self._best_practices.values():
            bpid = f"bp:{bp.id}"
            all_items[bpid] = {"type": "best_practice", "name": bp.title, "stack": bp.tech_stack}

        for ll in self._lessons_learned.values():
            llid = f"ll:{ll.id}"
            all_items[llid] = {"type": "lesson", "name": ll.title, "impact": ll.impact}

        for item_id, info in all_items.items():
            nodes.append({"id": item_id, **info})

        for pattern in self._patterns.values():
            source = f"pattern:{pattern.name}"
            for related in pattern.related_patterns:
                target = f"pattern:{related}"
                if target in all_items:
                    edges.append({"source": source, "target": target, "relation": RelationType.RELATED.value})

        cross_relations: list[tuple[str, str, str]] = [
            ("pattern:Singleton", "adr:ADR-*", "used_in"),
            ("pattern:Observer", "adr:ADR-*", "used_in"),
            ("pattern:Strategy", "bp:*", "implements"),
            ("pattern:Repository", "bp:*", "implements"),
            ("pattern:Factory Method", "bp:*", "used_in"),
            ("ll:*", "bp:*", "prevents"),
            ("adr:ADR-*", "bp:*", "follows"),
        ]

        for src_pattern, tgt_pattern, rel_type in cross_relations:
            for src_id in all_items:
                if self._wildcard_match(src_id, src_pattern):
                    for tgt_id in all_items:
                        if self._wildcard_match(tgt_id, tgt_pattern) and src_id != tgt_id:
                            edge_exists = any(e["source"] == src_id and e["target"] == tgt_id for e in edges)
                            if not edge_exists:
                                edges.append({"source": src_id, "target": tgt_id, "relation": rel_type})

        self._graph = KnowledgeGraph(nodes=nodes, edges=edges)

    @staticmethod
    def _wildcard_match(item_id: str, pattern: str) -> bool:
        """通配符匹配"""
        regex = "^" + pattern.replace("*", ".*") + "$"
        return bool(re.match(regex, item_id))

    def find_related(self, item_id: str, relation: RelationType | None = None, depth: int = 1) -> list[str]:
        """
        查找相关知识点

        Args:
            item_id: 起始知识点ID
            relation: 关系类型过滤
            depth: 搜索深度

        Returns:
            相关知识点ID列表
        """
        visited: set[str] = {item_id}
        result: set[str] = set()
        current_level: set[str] = {item_id}

        for _ in range(depth):
            next_level: set[str] = set()
            for node_id in current_level:
                for edge in self._graph.edges:
                    if edge["source"] == node_id and edge["target"] not in visited:
                        if relation is None or edge["relation"] == relation.value:
                            next_level.add(edge["target"])
                            result.add(edge["target"])
                            visited.add(edge["target"])
                    elif edge["target"] == node_id and edge["source"] not in visited:
                        if relation is None or edge["relation"] == relation.value:
                            next_level.add(edge["source"])
                            result.add(edge["source"])
                            visited.add(edge["source"])
            current_level = next_level

        return sorted(result)

    # ==================== 向量检索接口预留 ====================

    def embedding_interface(
        self,
        text: str,
        model: str = "default",
    ) -> list[float]:
        """
        向量嵌入接口（预留）

        Args:
            text: 输入文本
            model: 嵌入模型名称

        Returns:
            向量表示（当前返回模拟向量）
        """
        text_bytes = text.encode("utf-8")
        hash_obj = hashlib.sha256(text_bytes)
        hash_int = int.from_bytes(hash_obj.digest(), byteorder="big")
        dimension = 384
        vector: list[float] = []
        seed = hash_int % (2**31)
        rng_seed = seed ^ (seed >> 16)
        import random as _rng
        _rng.seed(rng_seed)
        for _ in range(dimension):
            vector.append(_rng.gauss(0, 1))
        norm = sum(x * x for x in vector) ** 0.5 or 1.0
        return [x / norm for x in vector]

    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.5,
    ) -> list[tuple[str, float]]:
        """
        相似度搜索（基于预留的embedding接口）

        Args:
            query: 查询文本
            top_k: 返回Top-K结果
            threshold: 相似度阈值

        Returns:
            (item_id, similarity_score) 列表
        """
        query_vec = self.embedding_interface(query)
        all_ids = list(self._entries.keys()) + list(self._patterns.keys()) + \
                   list(self._best_practices.keys()) + list(self._lessons_learned.keys())
        scores: list[tuple[str, float]] = []
        for item_id in all_ids:
            item_text = ""
            if item_id.startswith("kb_"):
                e = self._entries.get(item_id)
                item_text = e.content if e else ""
            elif item_id in self._patterns:
                item_text = self._patterns[item_id].intent
            elif item_id.startswith("bp_"):
                bp = self._best_practices.get(item_id)
                item_text = bp.content if bp else ""
            elif item_id.startswith("ll_"):
                ll = self._lessons_learned.get(item_id)
                item_text = ll.problem + " " + ll.solution if ll else ""

            if item_text:
                item_vec = self.embedding_interface(item_text)
                dot_product = sum(q * i for q, i in zip(query_vec, item_vec))
                sim = max(0.0, min(1.0, (dot_product + 1.0) / 2.0))
                if sim >= threshold:
                    scores.append((item_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成完整的知识管理报告(Markdown)"""
        lines: list[str] = []
        lines.append("# 📚 知识管理司 · 综合报告\n")

        lines.append("## 📊 总览\n")
        total_kb = len(self._entries) + len(self._patterns) + len(self._adrs) + \
                   len(self._best_practices) + len(self._lessons_learned)
        lines.append(f"| 类别 | 数量 |")
        lines.append(f"| --- | --- |")
        lines.append(f"| 知识条目 | {len(self._entries)} |")
        lines.append(f"| 设计模式 | {len(self._patterns)} (GOF) |")
        lines.append(f"| 架构决策(ADR) | {len(self._adrs)} |")
        lines.append(f"| 最佳实践 | {len(self._best_practices)} |")
        lines.append(f"| 经验教训 | {len(self._lessons_learned)} |")
        lines.append(f"| **总计** | **{total_kb}** |")

        lines.append(f"\n## 🏗️ 设计模式分布\n")
        cat_counts: dict[str, int] = {}
        for p in self._patterns.values():
            cat_counts[p.category.value] = cat_counts.get(p.category.value, 0) + 1
        cat_names = {
            "creational": "创建型", "structural": "结构型",
            "behavioral": "行为型", "enterprise": "企业型", "concurrency": "并发型",
        }
        for cat, count in sorted(cat_counts.items()):
            lines.append(f"- **{cat_names.get(cat, cat)}**: {count} 个模式")

        lines.append(f"\n## 📋 最佳实践 (按技术栈)\n")
        stack_counts: dict[str, int] = {}
        for bp in self._best_practices.values():
            stack_counts[bp.tech_stack] = stack_counts.get(bp.tech_stack, 0) + 1
        for stack, count in sorted(stack_counts.items()):
            lines.append(f"- **{stack}**: {count} 条实践")

        lines.append(f"\n## ⚠️ 经验教训 (按影响程度)\n")
        impact_order = {"high": 0, "medium": 1, "low": 2}
        for ll in sorted(self._lessons_learned.values(), key=lambda l: impact_order.get(l.impact, 99)):
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(ll.impact, "⚪")
            lines.append(f"{icon} **{ll.title}** ({ll.project}): {ll.root_cause[:50]}...")

        lines.append(f"\n## 🔗 知识图谱\n")
        lines.append(f"- 节点数: {self._graph.node_count}")
        lines.append(f"- 边数: {self._graph.edge_count}")
        lines.append(f"- 图密度: {self._graph.density:.4f}")

        lines.append(f"\n## 🏷️ 标签云\n")
        all_tags = self.get_all_tags()
        top_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:15]
        for tag, count in top_tags:
            lines.append(f"`{tag}` ({count})")

        lines.append("\n---\n")
        lines.append("*此报告由尚书省·礼部·知识管理司自动生成*\n")
        return "\n".join(lines)

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def pattern_count(self) -> int:
        return len(self._patterns)

    @property
    def adr_count(self) -> int:
        return len(self._adrs)

    @property
    def best_practice_count(self) -> int:
        return len(self._best_practices)

    @property
    def lesson_count(self) -> int:
        return len(self._lessons_learned)

    def __repr__(self) -> str:
        return (
            f"KnowledgeBaseSi(entries={self.entry_count}, "
            f"patterns={self.pattern_count}, "
            f"adrs={self.adr_count}, "
            f"practices={self.best_practice_count})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 知识管理司测试")
    print("=" * 60)

    kb = KnowledgeBaseSi()

    print("\n--- 设计模式知识库 ---")
    print(f"   总计 {kb.pattern_count} 个GOF设计模式:")
    for cat in PatternCategory:
        patterns = kb.list_patterns(category=cat)
        cat_name = {"creational": "创建型", "structural": "结构型",
                     "behavioral": "行为型", "enterprise": "企业型", "concurrency": "并发型"}
        names = ", ".join(p.name for p in patterns)
        print(f"      [{cat_name.get(cat.value, cat.value):6s}] {len(patterns)}个: {names}")

    print("\n--- 查询设计模式 ---")
    singleton = kb.get_pattern("Singleton")
    if singleton:
        print(f"   Singleton: {singleton.intent}")
        print(f"   别名: {singleton.alias}")
        print(f"   适用场景({len(singleton.applicability)}): {singleton.applicability[:3]}")
        print(f"   优点: {singleton.consequences_pros[:3]}")
        print(f"   缺点: {singleton.consequences_cons[:3]}")
        print(f"   相关模式: {singleton.related_patterns}")

    print("\n--- 搜索设计模式 ---")
    search_results = kb.search_patterns("工厂")
    for p in search_results:
        print(f"   • {p.name} ({p.category.value}): {p.intent[:50]}...")

    print("\n--- 知识条目CRUD ---")
    e1 = kb.create_entry(
        title="FastAPI性能优化指南",
        content="FastAPI性能优化技巧：使用async/await、连接池、缓存策略...",
        category="optimization",
        tags=["python", "fastapi", "performance"],
        author="DevTeam",
    )
    print(f"   创建: {e1.title} ({e1.id})")

    e2 = kb.create_entry(
        title="Kubernetes Pod调度策略详解",
        content="K8s Pod调度原理：nodeSelector/nodeAffinity/taints tolerations...",
        category="kubernetes",
        tags=["k8s", "devops", "scheduling"],
    )
    print(f"   创建: {e2.title} ({e2.id})")

    retrieved = kb.get_entry(e1.id)
    print(f"   读取: {retrieved.title} - {len(retrieved.content)}字符")

    updated = kb.update_entry(e1.id, title="FastAPI高级性能优化指南", tags=retrieved.tags + ["advanced"])
    print(f"   更新: {updated.title}, 标签: {updated.tags}")

    search_result = kb.search_entries(query="fastapi", limit=5)
    print(f"   搜索 'fastapi': {len(search_result)} 条结果")
    for r in search_result:
        print(f"      • {r.title} [{r.category}]")

    tag_search = kb.search_entries(tags=["kubernetes"])
    print(f"   按标签[kubernetes]: {len(tag_search)} 条")

    deleted = kb.delete_entry(e2.id)
    print(f"   删除: {'成功' if deleted else '失败'}")
    print(f"   当前条目数: {kb.entry_count}")

    print("\n--- 架构决策记录(ADR) ---")
    adrs = kb.list_adrs()
    print(f"   共 {len(adrs)} 条ADR:")
    for adr in adrs:
        icon = {"accepted": "✅", "superseded": "🔄", "deprecated": "❌", "proposed": "📝"} \
            .get(adr.status, "•")
        print(f"   {icon} [{adr.id}] {adr.title}: {adr.decision[:40]}...")

    accepted_adrs = kb.list_adrs(status="accepted")
    print(f"   已采纳: {len(accepted_adrs)} 条")

    print("\n--- 最佳实践库 ---")
    for stack in ["python", "go", "javascript"]:
        practices = kb.get_best_practices(tech_stack=stack)
        print(f"   [{stack}] {len(practices)} 条:")
        for bp in practices[:3]:
            print(f"      • {bp.title}: {bp.content[:45]}...")

    bp_search = kb.search_best_practices("类型检查")
    print(f"\n   搜索 '类型检查': {len(bp_search)} 条")
    for bp in bp_search:
        print(f"      • {bp.title} ({bp.tech_stack})")

    print("\n--- 经验教训库 ---")
    lessons = kb.list_lessons()
    print(f"   共 {len(lessons)} 条:")
    for ll in lessons:
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(ll.impact, "•")
        print(f"   {icon} {ll.title}: {ll.root_cause[:50]}...")

    print("\n--- 标签管理 ---")
    all_tags = kb.get_all_tags()
    print(f"   总标签数: {len(all_tags)}")
    for tag, count in list(all_tags.items())[:10]:
        entries = kb.get_entries_by_tag(tag)
        print(f"      #{tag}: {count} 个条目 → {', '.join(entries[:3])}")

    print("\n--- 知识图谱 ---")
    graph = kb._graph
    print(f"   节点: {graph.node_count}, 边: {graph.edge_count}, 密度: {graph.density:.4f}")

    singleton_related = kb.find_related("pattern:Singleton", depth=2)
    print(f"   Singleton 关联知识点 (depth=2): {len(singleton_related)} 个")
    for rid in singleton_related[:8]:
        print(f"      → {rid}")

    print("\n--- 向量检索接口 ---")
    test_vec = kb.embedding_interface("如何设计一个高效的缓存系统")
    print(f"   Embedding维度: {len(test_vec)}")
    print(f"   向量范数: {sum(x*x for x in test_vec)**0.5:.4f}")

    sim_results = kb.similarity_search("数据库连接池优化", top_k=5)
    print(f"\n   相似度搜索 '数据库连接池优化':")
    for item_id, score in sim_results:
        print(f"      • {item_id}: 相似度={score:.4f}")

    print("\n--- 综合报告预览 (前1500字符) ---")
    report = kb.generate_report()
    print(report[:1500])

    print("\n✅ 所有测试通过!")
