#!/usr/bin/env python3
"""
Agent选择器 - 根据任务类型和项目上下文自动选择合适的Agency-Agent

功能：
1. 根据部门映射选择Agent
2. 根据项目类型筛选Agent
3. 根据TDD阶段推荐Agent
4. 生成Agent调用记录
"""

import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AgentSelector:
    """Agency-Agent选择器"""
    
    def __init__(self, integration_config_path: str = None):
        self.integration_config = self._load_integration_config(integration_config_path)
        self.agent_registry = self._build_agent_registry()
    
    def _load_integration_config(self, config_path: str) -> Dict:
        """加载集成配置"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            "departments": {
                "libu": {
                    "name": "吏部",
                    "role": "人员调度",
                    "agents": [
                        {"name": "Senior Project Manager", "skill": "任务分解、范围管理", "scenarios": ["项目启动", "任务分配"]},
                        {"name": "Software Architect", "skill": "系统设计、DDD", "scenarios": ["架构设计阶段"]},
                        {"name": "Senior Developer", "skill": "技术决策、代码质量", "scenarios": ["复杂实现任务"]}
                    ]
                },
                "hubu": {
                    "name": "户部",
                    "role": "资源管理",
                    "agents": [
                        {"name": "DevOps Automator", "skill": "CI/CD、云基础设施", "scenarios": ["部署配置", "环境搭建"]},
                        {"name": "Database Optimizer", "skill": "查询优化、索引策略", "scenarios": ["数据库性能调优"]},
                        {"name": "SRE", "skill": "可靠性、监控", "scenarios": ["生产环境保障"]}
                    ]
                },
                "libu_li": {
                    "name": "礼部",
                    "role": "规范制定",
                    "agents": [
                        {"name": "Technical Writer", "skill": "API文档、教程编写", "scenarios": ["文档生成", "知识库建设"]},
                        {"name": "UI Designer", "skill": "设计系统、组件库", "scenarios": ["UI规范制定"]},
                        {"name": "UX Architect", "skill": "技术架构、CSS系统", "scenarios": ["前端架构设计"]}
                    ]
                },
                "bingbu": {
                    "name": "兵部",
                    "role": "测试先行",
                    "agents": [
                        {"name": "Evidence Collector", "skill": "视觉验证、截图QA", "scenarios": ["UI测试", "视觉验证"]},
                        {"name": "Reality Checker", "skill": "质量门禁、生产就绪", "scenarios": ["发布前验证"]},
                        {"name": "Performance Benchmarker", "skill": "性能测试、负载测试", "scenarios": ["性能优化阶段"]},
                        {"name": "API Tester", "skill": "API验证、集成测试", "scenarios": ["API测试"]},
                        {"name": "Accessibility Auditor", "skill": "WCAG审计、无障碍测试", "scenarios": ["可访问性合规"]}
                    ]
                },
                "xingbu": {
                    "name": "刑部",
                    "role": "持续重构",
                    "agents": [
                        {"name": "Code Reviewer", "skill": "代码质量、安全审查", "scenarios": ["PR审查", "代码质量门禁"]},
                        {"name": "Security Engineer", "skill": "威胁建模、安全架构", "scenarios": ["安全审计", "漏洞评估"]},
                        {"name": "Git Workflow Master", "skill": "分支策略、提交规范", "scenarios": ["版本控制优化"]}
                    ]
                },
                "gongbu": {
                    "name": "工部",
                    "role": "开发执行",
                    "agents": [
                        {"name": "Frontend Developer", "skill": "React/Vue/Angular、UI实现", "scenarios": ["前端开发任务"]},
                        {"name": "Backend Architect", "skill": "API设计、数据库架构", "scenarios": ["后端开发任务"]},
                        {"name": "Mobile App Builder", "skill": "iOS/Android、React Native", "scenarios": ["移动应用开发"]},
                        {"name": "AI Engineer", "skill": "ML模型、AI集成", "scenarios": ["AI功能开发"]},
                        {"name": "Rapid Prototyper", "skill": "MVP、POC开发", "scenarios": ["快速验证想法"]}
                    ]
                }
            },
            "project_types": {
                "web": {
                    "name": "Web应用",
                    "stages": {
                        "需求分析": ["Product Manager", "UX Researcher"],
                        "架构设计": ["Software Architect", "Backend Architect"],
                        "前端开发": ["Frontend Developer", "UI Designer"],
                        "后端开发": ["Backend Architect", "Senior Developer"],
                        "测试验证": ["Evidence Collector", "API Tester"],
                        "部署上线": ["DevOps Automator", "SRE"]
                    }
                },
                "mobile": {
                    "name": "移动应用",
                    "stages": {
                        "需求分析": ["Product Manager", "UX Researcher"],
                        "设计阶段": ["UI Designer", "UX Architect"],
                        "开发阶段": ["Mobile App Builder", "Senior Developer"],
                        "测试阶段": ["Evidence Collector", "Performance Benchmarker"],
                        "上线发布": ["DevOps Automator"]
                    }
                },
                "ai_ml": {
                    "name": "AI/ML项目",
                    "stages": {
                        "需求分析": ["Product Manager", "AI Engineer"],
                        "数据准备": ["Data Engineer", "AI Data Remediation Engineer"],
                        "模型开发": ["AI Engineer", "Senior Developer"],
                        "测试验证": ["Model QA Specialist", "API Tester"],
                        "部署监控": ["DevOps Automator", "SRE"]
                    }
                }
            },
            "tdd_phases": {
                "red": {
                    "name": "红 - 编写测试",
                    "department": "bingbu",
                    "agents": ["Evidence Collector", "API Tester", "Performance Benchmarker"]
                },
                "green": {
                    "name": "绿 - 实现代码",
                    "department": "gongbu",
                    "agents": ["Frontend Developer", "Backend Architect", "Senior Developer"]
                },
                "refactor": {
                    "name": "重构 - 优化代码",
                    "department": "xingbu",
                    "agents": ["Code Reviewer", "Security Engineer", "Database Optimizer"]
                }
            }
        }
    
    def _build_agent_registry(self) -> Dict:
        """构建Agent注册表"""
        registry = {}
        for dept_id, dept_info in self.integration_config.get("departments", {}).items():
            for agent in dept_info.get("agents", []):
                registry[agent["name"]] = {
                    "department": dept_id,
                    "department_name": dept_info["name"],
                    "skill": agent["skill"],
                    "scenarios": agent["scenarios"]
                }
        return registry
    
    def select_by_department(self, department: str) -> List[Dict]:
        """根据部门选择Agent"""
        dept_info = self.integration_config["departments"].get(department)
        if not dept_info:
            return []
        
        return dept_info.get("agents", [])
    
    def select_by_task_type(self, task_type: str) -> List[Dict]:
        """根据任务类型选择Agent"""
        task_dept_map = {
            "frontend": "gongbu",
            "backend": "gongbu",
            "testing": "bingbu",
            "devops": "hubu",
            "documentation": "libu_li",
            "security": "xingbu",
            "management": "libu"
        }
        
        department = task_dept_map.get(task_type.lower())
        if not department:
            return []
        
        return self.select_by_department(department)
    
    def select_by_project_stage(self, project_type: str, stage: str) -> List[str]:
        """根据项目类型和阶段选择Agent"""
        project = self.integration_config["project_types"].get(project_type.lower())
        if not project:
            return []
        
        return project["stages"].get(stage, [])
    
    def select_by_tdd_phase(self, phase: str) -> Dict:
        """根据TDD阶段选择Agent"""
        phase_info = self.integration_config["tdd_phases"].get(phase.lower())
        if not phase_info:
            return {}
        
        return {
            "phase": phase_info["name"],
            "department": phase_info["department"],
            "recommended_agents": phase_info["agents"]
        }
    
    def select_best_agent(self, task_description: str, context: Dict) -> Dict:
        """智能选择最佳Agent"""
        task_lower = task_description.lower()
        
        candidates = []
        
        for agent_name, agent_info in self.agent_registry.items():
            score = 0
            
            for scenario in agent_info["scenarios"]:
                if scenario.lower() in task_lower:
                    score += 2
            
            for keyword in agent_info["skill"].split("、"):
                if keyword.lower() in task_lower:
                    score += 1
            
            if context.get("tech_stack"):
                tech_stack = context["tech_stack"].lower()
                if any(tech in agent_info["skill"].lower() for tech in tech_stack.split()):
                    score += 3
            
            if score > 0:
                candidates.append({
                    "name": agent_name,
                    "score": score,
                    "department": agent_info["department_name"],
                    "skill": agent_info["skill"],
                    "scenarios": agent_info["scenarios"]
                })
        
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "best_match": candidates[0] if candidates else None,
            "alternatives": candidates[1:4] if len(candidates) > 1 else []
        }
    
    def generate_call_record(self, agent_name: str, task: str, context: Dict, result: Dict = None) -> Dict:
        """生成Agent调用记录"""
        agent_info = self.agent_registry.get(agent_name, {})
        
        return {
            "call_id": f"CALL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "caller": agent_info.get("department_name", "未知"),
            "agent": agent_name,
            "task": task,
            "context": context,
            "result": result or {
                "status": "pending",
                "deliverables": [],
                "quality_metrics": {}
            }
        }


def main():
    parser = argparse.ArgumentParser(
        description="Agency-Agent选择器 - 智能选择最适合的Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 按部门选择Agent
  python agent_selector.py --department libu
  
  # 按任务类型选择Agent
  python agent_selector.py --task-type frontend
  
  # 按TDD阶段选择Agent
  python agent_selector.py --tdd-phase red
  
  # 按项目类型和阶段选择Agent
  python agent_selector.py --project-type web --stage "前端开发"
  
  # 智能选择Agent（使用文件输入上下文）
  python agent_selector.py --task-description "实现用户登录界面" --context-file context.json
  
  # 生成完整报告
  python agent_selector.py --report --output report.json
        """
    )
    
    parser.add_argument("--department", "-d", help="按部门选择Agent (libu/hubu/libu_li/bingbu/xingbu/gongbu)")
    parser.add_argument("--task-type", "-t", help="按任务类型选择Agent (frontend/backend/testing/devops/documentation/security/management)")
    parser.add_argument("--project-type", "-p", help="项目类型 (web/mobile/ai_ml)")
    parser.add_argument("--stage", "-s", help="项目阶段")
    parser.add_argument("--tdd-phase", help="TDD阶段 (red/green/refactor)")
    parser.add_argument("--task-description", help="任务描述，用于智能选择")
    parser.add_argument("--context", help="项目上下文（JSON字符串）")
    parser.add_argument("--context-file", help="项目上下文文件（JSON格式）")
    parser.add_argument("--report", "-r", action="store_true", help="生成完整报告")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    selector = AgentSelector()
    
    result = {}
    
    if args.department:
        result = {
            "type": "department_selection",
            "department": args.department,
            "agents": selector.select_by_department(args.department)
        }
    elif args.task_type:
        result = {
            "type": "task_type_selection",
            "task_type": args.task_type,
            "agents": selector.select_by_task_type(args.task_type)
        }
    elif args.project_type and args.stage:
        result = {
            "type": "project_stage_selection",
            "project_type": args.project_type,
            "stage": args.stage,
            "agents": selector.select_by_project_stage(args.project_type, args.stage)
        }
    elif args.tdd_phase:
        result = {
            "type": "tdd_phase_selection",
            **selector.select_by_tdd_phase(args.tdd_phase)
        }
    elif args.task_description:
        context = {}
        
        if args.context:
            try:
                context = json.loads(args.context)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse context JSON: {e}")
                context = {}
        
        if args.context_file:
            try:
                with open(args.context_file, 'r', encoding='utf-8') as f:
                    context = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Failed to load context file: {e}")
        
        result = {
            "type": "intelligent_selection",
            "task_description": args.task_description,
            "context": context,
            **selector.select_best_agent(args.task_description, context)
        }
    elif args.report:
        result = {
            "type": "complete_report",
            "departments": selector.integration_config["departments"],
            "project_types": selector.integration_config.get("project_types", {}),
            "tdd_phases": selector.integration_config.get("tdd_phases", {}),
            "agent_registry": selector.agent_registry
        }
    else:
        result = {
            "type": "all_departments",
            "departments": selector.integration_config["departments"]
        }
    
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"结果已保存到: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
