#!/usr/bin/env python3
"""
技能调用记录脚本
记录技能调用到可视化系统，支持透明度数据记录
"""
import argparse
import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import requests

API_BASE = os.getenv("VISUAL_API_BASE", "http://localhost:8000/api")

def record_skill_call(
    skill_name, 
    status, 
    details=None, 
    parent_id=None, 
    caller=None,
    input_data=None,
    output_data=None,
    reasoning_log=None,
    decision_type=None,
    decision_basis=None,
    alternatives=None
):
    """记录技能调用（包含透明度数据）"""
    payload = {
        "skill_name": skill_name,
        "status": status,
        "details": details or {},
        "parent_call_id": parent_id,
        "caller": caller
    }
    
    try:
        resp = requests.post(f"{API_BASE}/skill_calls", json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        call_id = result.get("id")
        print(f"Skill call recorded: ID={call_id}, skill={skill_name}, status={status}")
        
        if call_id:
            transparency_updated = update_transparency_data(
                call_id, 
                input_data=input_data,
                output_data=output_data,
                reasoning_log=reasoning_log,
                decision_type=decision_type,
                decision_basis=decision_basis,
                alternatives=alternatives
            )
            if transparency_updated:
                print(f"Transparency data updated for call ID={call_id}")
        
        return call_id
    except requests.exceptions.RequestException as e:
        print(f"Error recording skill call: {e}", file=sys.stderr)
        return None

def update_skill_call(
    call_id, 
    status, 
    details=None, 
    end_time=None,
    input_data=None,
    output_data=None,
    reasoning_log=None,
    decision_type=None,
    decision_basis=None,
    alternatives=None
):
    """更新技能调用状态（包含透明度数据）"""
    payload = {
        "status": status,
        "details": details or {}
    }
    if end_time:
        payload["end_time"] = end_time
    
    try:
        resp = requests.put(f"{API_BASE}/skill_calls/{call_id}", json=payload, timeout=10)
        resp.raise_for_status()
        print(f"Skill call updated: ID={call_id}, status={status}")
        
        update_transparency_data(
            call_id,
            input_data=input_data,
            output_data=output_data,
            reasoning_log=reasoning_log,
            decision_type=decision_type,
            decision_basis=decision_basis,
            alternatives=alternatives
        )
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error updating skill call: {e}", file=sys.stderr)
        return False

def update_transparency_data(
    call_id,
    input_data=None,
    output_data=None,
    reasoning_log=None,
    decision_type=None,
    decision_basis=None,
    alternatives=None
):
    """更新技能调用的透明度数据"""
    has_data = any([
        input_data is not None,
        output_data is not None,
        reasoning_log is not None,
        decision_type is not None,
        decision_basis is not None,
        alternatives is not None
    ])
    
    if not has_data:
        return False
    
    payload = {}
    if input_data is not None:
        payload["input_data"] = input_data
    if output_data is not None:
        payload["output_data"] = output_data
    if reasoning_log is not None:
        payload["reasoning_log"] = reasoning_log
    if decision_type is not None:
        payload["decision_type"] = decision_type
    if decision_basis is not None:
        payload["decision_basis"] = decision_basis
    if alternatives is not None:
        payload["alternatives"] = alternatives
    
    try:
        resp = requests.put(f"{API_BASE}/skill_calls/{call_id}", json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error updating transparency data: {e}", file=sys.stderr)
        return False

def create_decision_log(
    skill_call_id,
    decision_type,
    decision_basis=None,
    reasoning_process=None,
    alternatives=None,
    final_decision=None
):
    """创建决策日志记录"""
    payload = {
        "skill_call_id": skill_call_id,
        "decision_type": decision_type
    }
    if decision_basis is not None:
        payload["decision_basis"] = decision_basis
    if reasoning_process is not None:
        payload["reasoning_process"] = reasoning_process
    if alternatives is not None:
        payload["alternatives"] = alternatives
    if final_decision is not None:
        payload["final_decision"] = final_decision
    
    try:
        resp = requests.post(f"{API_BASE}/decision_logs", json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        log_id = result.get("id")
        print(f"Decision log created: ID={log_id}, skill_call_id={skill_call_id}")
        return log_id
    except requests.exceptions.RequestException as e:
        print(f"Error creating decision log: {e}", file=sys.stderr)
        return None

def create_io_trace(
    skill_call_id,
    trace_type,
    data,
    data_type=None,
    source=None,
    target=None
):
    """创建输入输出追踪记录"""
    payload = {
        "skill_call_id": skill_call_id,
        "trace_type": trace_type,
        "data": data
    }
    if data_type is not None:
        payload["data_type"] = data_type
    if source is not None:
        payload["source"] = source
    if target is not None:
        payload["target"] = target
    
    try:
        resp = requests.post(f"{API_BASE}/input_output_traces", json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        trace_id = result.get("id")
        print(f"IO trace created: ID={trace_id}, type={trace_type}, skill_call_id={skill_call_id}")
        return trace_id
    except requests.exceptions.RequestException as e:
        print(f"Error creating IO trace: {e}", file=sys.stderr)
        return None

def parse_json_arg(value, arg_name):
    """解析 JSON 参数"""
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        print(f"Invalid JSON in {arg_name}: {value}", file=sys.stderr)
        return None


def record_test_execution(
    test_name,
    status,
    total_tests=0,
    passed=0,
    failed=0,
    skipped=0,
    duration=0.0,
    coverage=None,
    failed_tests=None,
    parent_skill_id=None,
    test_type="unit"
):
    """记录测试执行结果"""
    payload = {
        "skill_name": f"test_{test_name}",
        "status": status,
        "details": {
            "test_type": test_type,
            "total_tests": total_tests,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration,
            "coverage": coverage or {},
            "failed_tests": failed_tests or []
        },
        "parent_call_id": parent_skill_id,
        "caller": "test_runner"
    }
    
    try:
        resp = requests.post(f"{API_BASE}/skill_calls", json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        call_id = result.get("id")
        print(f"Test execution recorded: ID={call_id}, test={test_name}, status={status}")
        return call_id
    except requests.exceptions.RequestException as e:
        print(f"Error recording test execution: {e}", file=sys.stderr)
        return None


def update_test_execution(
    call_id,
    status,
    total_tests=None,
    passed=None,
    failed=None,
    skipped=None,
    duration=None,
    coverage=None,
    failed_tests=None
):
    """更新测试执行结果"""
    details = {}
    if total_tests is not None:
        details["total_tests"] = total_tests
    if passed is not None:
        details["passed"] = passed
    if failed is not None:
        details["failed"] = failed
    if skipped is not None:
        details["skipped"] = skipped
    if duration is not None:
        details["duration"] = duration
    if coverage is not None:
        details["coverage"] = coverage
    if failed_tests is not None:
        details["failed_tests"] = failed_tests
    
    payload = {
        "status": status,
        "details": details
    }
    
    try:
        resp = requests.put(f"{API_BASE}/skill_calls/{call_id}", json=payload, timeout=10)
        resp.raise_for_status()
        print(f"Test execution updated: ID={call_id}, status={status}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error updating test execution: {e}", file=sys.stderr)
        return False


def link_test_to_skill(
    test_call_id,
    skill_call_id,
    relationship_type="validates"
):
    """关联测试与技能调用"""
    payload = {
        "skill_name": "test_skill_link",
        "status": "completed",
        "details": {
            "test_call_id": test_call_id,
            "skill_call_id": skill_call_id,
            "relationship_type": relationship_type
        },
        "parent_call_id": skill_call_id,
        "caller": "test_linker"
    }
    
    try:
        resp = requests.post(f"{API_BASE}/skill_calls", json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        link_id = result.get("id")
        print(f"Test linked to skill: link_id={link_id}, test={test_call_id}, skill={skill_call_id}")
        return link_id
    except requests.exceptions.RequestException as e:
        print(f"Error linking test to skill: {e}", file=sys.stderr)
        return None


def record_coverage_result(
    project_name,
    line_rate,
    branch_rate=0,
    threshold=80,
    passed=False,
    uncovered_files=None,
    parent_skill_id=None
):
    """记录覆盖率验证结果"""
    payload = {
        "skill_name": f"coverage_{project_name}",
        "status": "completed" if passed else "failed",
        "details": {
            "line_rate": line_rate,
            "branch_rate": branch_rate,
            "threshold": threshold,
            "passed": passed,
            "uncovered_files_count": len(uncovered_files) if uncovered_files else 0,
            "uncovered_files": uncovered_files[:20] if uncovered_files else []
        },
        "parent_call_id": parent_skill_id,
        "caller": "coverage_validator"
    }
    
    try:
        resp = requests.post(f"{API_BASE}/skill_calls", json=payload, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        call_id = result.get("id")
        print(f"Coverage result recorded: ID={call_id}, project={project_name}, rate={line_rate:.2f}%")
        return call_id
    except requests.exceptions.RequestException as e:
        print(f"Error recording coverage result: {e}", file=sys.stderr)
        return None


def get_test_history(skill_name=None, limit=10):
    """获取测试执行历史"""
    params = {"limit": limit}
    if skill_name:
        params["skill_name"] = skill_name
    
    try:
        resp = requests.get(f"{API_BASE}/skill_calls", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting test history: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Record skill calls to the visualization system with transparency data"
    )
    
    parser.add_argument("--skill", help="Skill name")
    parser.add_argument("--status", 
                        choices=["started", "completed", "failed", "update"],
                        help="Call status")
    parser.add_argument("--details", type=str, default="{}", help="JSON details")
    parser.add_argument("--parent", type=int, help="Parent call ID")
    parser.add_argument("--caller", type=str, help="Caller identifier")
    parser.add_argument("--call-id", type=int, help="Call ID to update (for update status)")
    
    parser.add_argument("--input", type=str, help="Input data JSON (transparency)")
    parser.add_argument("--output", type=str, help="Output data JSON (transparency)")
    parser.add_argument("--reasoning", type=str, help="Reasoning log (transparency)")
    parser.add_argument("--decision-type", type=str, help="Decision type (transparency)")
    parser.add_argument("--decision-basis", type=str, help="Decision basis JSON (transparency)")
    parser.add_argument("--alternatives", type=str, help="Alternatives JSON (transparency)")
    
    parser.add_argument("--create-decision-log", action="store_true",
                        help="Create a separate decision log entry")
    parser.add_argument("--create-io-trace", action="store_true",
                        help="Create input/output trace entries")
    
    parser.add_argument("--record-test", action="store_true",
                        help="Record test execution result")
    parser.add_argument("--test-name", type=str, help="Test name")
    parser.add_argument("--test-type", type=str, default="unit", help="Test type (unit/e2e/integration)")
    parser.add_argument("--total-tests", type=int, default=0, help="Total number of tests")
    parser.add_argument("--passed", type=int, default=0, help="Number of passed tests")
    parser.add_argument("--failed", type=int, default=0, help="Number of failed tests")
    parser.add_argument("--skipped", type=int, default=0, help="Number of skipped tests")
    parser.add_argument("--duration", type=float, default=0.0, help="Test duration in seconds")
    parser.add_argument("--coverage", type=str, help="Coverage data JSON")
    parser.add_argument("--failed-tests", type=str, help="Failed test names JSON array")
    
    parser.add_argument("--record-coverage", action="store_true",
                        help="Record coverage validation result")
    parser.add_argument("--project-name", type=str, help="Project name for coverage")
    parser.add_argument("--line-rate", type=float, help="Line coverage rate")
    parser.add_argument("--branch-rate", type=float, default=0, help="Branch coverage rate")
    parser.add_argument("--threshold", type=float, default=80, help="Coverage threshold")
    parser.add_argument("--uncovered-files", type=str, help="Uncovered files JSON array")
    
    parser.add_argument("--link-test", action="store_true",
                        help="Link test to skill call")
    parser.add_argument("--test-call-id", type=int, help="Test call ID to link")
    parser.add_argument("--skill-call-id", type=int, help="Skill call ID to link")
    parser.add_argument("--relationship", type=str, default="validates", help="Relationship type")
    
    parser.add_argument("--get-history", action="store_true",
                        help="Get test execution history")
    parser.add_argument("--limit", type=int, default=10, help="Number of history entries")
    
    args = parser.parse_args()
    
    if args.record_test:
        if not args.test_name or not args.status:
            print("Error: --test-name and --status are required for test recording", file=sys.stderr)
            sys.exit(1)
        
        coverage_data = parse_json_arg(args.coverage, "coverage")
        failed_tests_list = parse_json_arg(args.failed_tests, "failed-tests")
        
        call_id = record_test_execution(
            test_name=args.test_name,
            status=args.status,
            total_tests=args.total_tests,
            passed=args.passed,
            failed=args.failed,
            skipped=args.skipped,
            duration=args.duration,
            coverage=coverage_data,
            failed_tests=failed_tests_list,
            parent_skill_id=args.parent,
            test_type=args.test_type
        )
        if call_id:
            print(call_id)
        else:
            sys.exit(1)
    
    elif args.record_coverage:
        if not args.project_name or args.line_rate is None:
            print("Error: --project-name and --line-rate are required for coverage recording", file=sys.stderr)
            sys.exit(1)
        
        uncovered_files_list = parse_json_arg(args.uncovered_files, "uncovered-files")
        
        call_id = record_coverage_result(
            project_name=args.project_name,
            line_rate=args.line_rate,
            branch_rate=args.branch_rate,
            threshold=args.threshold,
            passed=args.line_rate >= args.threshold,
            uncovered_files=uncovered_files_list,
            parent_skill_id=args.parent
        )
        if call_id:
            print(call_id)
        else:
            sys.exit(1)
    
    elif args.link_test:
        if not args.test_call_id or not args.skill_call_id:
            print("Error: --test-call-id and --skill-call-id are required for linking", file=sys.stderr)
            sys.exit(1)
        
        link_id = link_test_to_skill(
            test_call_id=args.test_call_id,
            skill_call_id=args.skill_call_id,
            relationship_type=args.relationship
        )
        if link_id:
            print(link_id)
        else:
            sys.exit(1)
    
    elif args.get_history:
        history = get_test_history(skill_name=args.skill, limit=args.limit)
        print(json.dumps(history, indent=2, ensure_ascii=False))
    
    elif args.skill and args.status:
        details = parse_json_arg(args.details, "details")
        if details is None and args.details != "{}":
            sys.exit(1)
        
        input_data = parse_json_arg(args.input, "input")
        output_data = parse_json_arg(args.output, "output")
        decision_basis = parse_json_arg(args.decision_basis, "decision-basis")
        alternatives = parse_json_arg(args.alternatives, "alternatives")
        
        if args.status == "update" and args.call_id:
            success = update_skill_call(
                args.call_id, 
                args.status, 
                details,
                input_data=input_data,
                output_data=output_data,
                reasoning_log=args.reasoning,
                decision_type=args.decision_type,
                decision_basis=decision_basis,
                alternatives=alternatives
            )
            if not success:
                sys.exit(1)
            
            if args.create_decision_log and args.decision_type:
                create_decision_log(
                    args.call_id,
                    args.decision_type,
                    decision_basis=decision_basis,
                    reasoning_process=args.reasoning,
                    alternatives=alternatives
                )
            
            if args.create_io_trace:
                if input_data:
                    create_io_trace(args.call_id, "input", input_data)
                if output_data:
                    create_io_trace(args.call_id, "output", output_data)
        else:
            call_id = record_skill_call(
                args.skill, 
                args.status, 
                details, 
                args.parent, 
                args.caller,
                input_data=input_data,
                output_data=output_data,
                reasoning_log=args.reasoning,
                decision_type=args.decision_type,
                decision_basis=decision_basis,
                alternatives=alternatives
            )
            if call_id:
                print(call_id)
                
                if args.create_decision_log and args.decision_type:
                    create_decision_log(
                        call_id,
                        args.decision_type,
                        decision_basis=decision_basis,
                        reasoning_process=args.reasoning,
                        alternatives=alternatives
                    )
                
                if args.create_io_trace:
                    if input_data:
                        create_io_trace(call_id, "input", input_data)
                    if output_data:
                        create_io_trace(call_id, "output", output_data)
            else:
                sys.exit(1)
    else:
        parser.print_help()
