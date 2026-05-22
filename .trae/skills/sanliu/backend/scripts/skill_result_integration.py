#!/usr/bin/env python3
"""
技能调用结果整合脚本
实现技能调用结果整合、结果验证、结果转换

功能:
- 技能调用结果整合（整合多个技能的调用结果）
- 结果验证（验证调用结果的有效性）
- 结果转换（转换结果格式以适应不同需求）
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ResultStatus(Enum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ResultType(Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    BINARY = "binary"
    STRUCTURED = "structured"


class ValidationLevel(Enum):
    STRICT = "strict"
    NORMAL = "normal"
    LOOSE = "loose"


@dataclass
class SkillCallResult:
    call_id: str
    skill_name: str
    timestamp: str
    status: ResultStatus
    result_type: ResultType
    content: Any
    metadata: Dict[str, Any] = None
    duration_ms: float = 0.0
    error_message: str = ""
    error_code: str = ""
    warnings: List[str] = None
    validation_passed: bool = True
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.warnings is None:
            self.warnings = []
        if self.validation_errors is None:
            self.validation_errors = []


@dataclass
class IntegratedResult:
    integration_id: str
    timestamp: str
    source_results: List[str]
    status: ResultStatus
    content: Dict[str, Any]
    summary: str
    statistics: Dict[str, Any]
    conflicts: List[Dict[str, Any]] = None
    recommendations: List[str] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []
        if self.recommendations is None:
            self.recommendations = []


@dataclass
class ValidationResult:
    is_valid: bool
    level: ValidationLevel
    errors: List[str]
    warnings: List[str]
    score: float
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class ResultValidator:
    """结果验证器"""
    
    def __init__(self, level: ValidationLevel = ValidationLevel.NORMAL):
        self.level = level
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ResultValidator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def validate(self, result: SkillCallResult, 
                 schema: Dict[str, Any] = None) -> ValidationResult:
        errors = []
        warnings = []
        score = 1.0
        
        if result.status == ResultStatus.FAILURE:
            errors.append(f"技能调用失败: {result.error_message}")
            score -= 0.5
        
        if result.status == ResultStatus.TIMEOUT:
            warnings.append("技能调用超时")
            score -= 0.2
        
        if result.content is None:
            if self.level == ValidationLevel.STRICT:
                errors.append("结果内容为空")
                score -= 0.3
            else:
                warnings.append("结果内容为空")
                score -= 0.1
        
        if result.result_type == ResultType.JSON and result.content:
            json_errors = self._validate_json_content(result.content, schema)
            errors.extend(json_errors)
            score -= len(json_errors) * 0.1
        
        if result.result_type == ResultType.TEXT and result.content:
            text_warnings = self._validate_text_content(result.content)
            warnings.extend(text_warnings)
            score -= len(text_warnings) * 0.05
        
        score = max(0.0, min(1.0, score))
        
        is_valid = len(errors) == 0
        
        if self.level == ValidationLevel.LOOSE:
            is_valid = score >= 0.5
        elif self.level == ValidationLevel.STRICT:
            is_valid = score >= 0.8
        
        return ValidationResult(
            is_valid=is_valid,
            level=self.level,
            errors=errors,
            warnings=warnings,
            score=score
        )
    
    def _validate_json_content(self, content: Any, 
                               schema: Dict[str, Any] = None) -> List[str]:
        errors = []
        
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except json.JSONDecodeError as e:
                errors.append(f"JSON解析失败: {str(e)}")
                return errors
        
        if schema:
            required_fields = schema.get('required', [])
            for field in required_fields:
                if field not in content:
                    errors.append(f"缺少必需字段: {field}")
            
            field_types = schema.get('properties', {})
            for field, expected_type in field_types.items():
                if field in content:
                    actual_type = type(content[field]).__name__
                    if actual_type != expected_type:
                        errors.append(f"字段 '{field}' 类型错误: 期望 {expected_type}, 实际 {actual_type}")
        
        return errors
    
    def _validate_text_content(self, content: str) -> List[str]:
        warnings = []
        
        if len(content.strip()) == 0:
            warnings.append("文本内容为空")
        
        if len(content) < 10:
            warnings.append("文本内容过短")
        
        return warnings


class ResultTransformer:
    """结果转换器"""
    
    def __init__(self):
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ResultTransformer')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def transform(self, result: SkillCallResult, 
                  target_type: ResultType) -> SkillCallResult:
        if result.result_type == target_type:
            return result
        
        transformed_content = result.content
        new_result_type = target_type
        
        try:
            if target_type == ResultType.JSON:
                transformed_content = self._to_json(result.content, result.result_type)
            elif target_type == ResultType.TEXT:
                transformed_content = self._to_text(result.content, result.result_type)
            elif target_type == ResultType.MARKDOWN:
                transformed_content = self._to_markdown(result.content, result.result_type)
            elif target_type == ResultType.HTML:
                transformed_content = self._to_html(result.content, result.result_type)
            elif target_type == ResultType.STRUCTURED:
                transformed_content = self._to_structured(result.content, result.result_type)
        except Exception as e:
            self.logger.error(f"转换失败: {e}")
            transformed_content = str(result.content)
            new_result_type = ResultType.TEXT
        
        return SkillCallResult(
            call_id=result.call_id,
            skill_name=result.skill_name,
            timestamp=result.timestamp,
            status=result.status,
            result_type=new_result_type,
            content=transformed_content,
            metadata=result.metadata,
            duration_ms=result.duration_ms,
            error_message=result.error_message,
            error_code=result.error_code,
            warnings=result.warnings + [f"结果已从 {result.result_type.value} 转换为 {new_result_type.value}"]
        )
    
    def _to_json(self, content: Any, source_type: ResultType) -> Any:
        if source_type == ResultType.JSON:
            return content
        
        if isinstance(content, str):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"text": content}
        
        if isinstance(content, dict):
            return content
        
        if isinstance(content, list):
            return {"items": content}
        
        return {"data": str(content)}
    
    def _to_text(self, content: Any, source_type: ResultType) -> str:
        if source_type == ResultType.TEXT:
            return content
        
        if isinstance(content, str):
            return content
        
        if isinstance(content, (dict, list)):
            return json.dumps(content, ensure_ascii=False, indent=2)
        
        return str(content)
    
    def _to_markdown(self, content: Any, source_type: ResultType) -> str:
        if source_type == ResultType.MARKDOWN:
            return content
        
        if isinstance(content, dict):
            lines = ["# 结果\n"]
            
            for key, value in content.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"## {key}\n")
                    lines.append(f"```json\n{json.dumps(value, ensure_ascii=False, indent=2)}\n```\n")
                else:
                    lines.append(f"- **{key}**: {value}\n")
            
            return '\n'.join(lines)
        
        if isinstance(content, list):
            lines = ["# 结果列表\n"]
            for i, item in enumerate(content, 1):
                lines.append(f"{i}. {item}\n")
            return '\n'.join(lines)
        
        return str(content)
    
    def _to_html(self, content: Any, source_type: ResultType) -> str:
        if source_type == ResultType.HTML:
            return content
        
        md_content = self._to_markdown(content, source_type)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>结果</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
        code {{ background: #f4f4f4; padding: 2px 5px; }}
        pre {{ background: #f4f4f4; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
{self._markdown_to_html(md_content)}
</body>
</html>"""
        
        return html
    
    def _to_structured(self, content: Any, source_type: ResultType) -> Dict[str, Any]:
        if source_type == ResultType.STRUCTURED:
            return content
        
        json_content = self._to_json(content, source_type)
        
        return {
            "data": json_content,
            "type": source_type.value,
            "transformed_at": datetime.now().isoformat()
        }
    
    def _markdown_to_html(self, md: str) -> str:
        html = md
        
        html = html.replace('# ', '<h1>').replace('\n# ', '</h1>\n<h1>')
        html = html.replace('## ', '<h2>').replace('\n## ', '</h2>\n<h2>')
        html = html.replace('### ', '<h3>').replace('\n### ', '</h3>\n<h3>')
        
        html = html.replace('```json\n', '<pre><code class="json">')
        html = html.replace('```\n', '</code></pre>')
        
        html = html.replace('- **', '<li><strong>').replace('**: ', '</strong>: ')
        html = html.replace('\n- ', '</li>\n<li> ')
        
        return html


class ResultIntegrator:
    """结果整合器"""
    
    def __init__(self):
        self.validator = ResultValidator()
        self.transformer = ResultTransformer()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('ResultIntegrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def integrate(self, results: List[SkillCallResult], 
                  strategy: str = "merge") -> IntegratedResult:
        if not results:
            return IntegratedResult(
                integration_id=f"INT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.now().isoformat(),
                source_results=[],
                status=ResultStatus.FAILURE,
                content={},
                summary="无结果可整合",
                statistics={"total": 0, "success": 0, "failure": 0}
            )
        
        validated_results = []
        for result in results:
            validation = self.validator.validate(result)
            if validation.is_valid or validation.score >= 0.5:
                validated_results.append(result)
        
        status = self._determine_integrated_status(results)
        
        if strategy == "merge":
            content = self._merge_results(validated_results)
        elif strategy == "first_success":
            content = self._first_success_result(validated_results)
        elif strategy == "best_score":
            content = self._best_score_result(validated_results)
        else:
            content = self._merge_results(validated_results)
        
        conflicts = self._detect_conflicts(validated_results)
        
        statistics = self._calculate_statistics(results)
        
        summary = self._generate_summary(validated_results, status, statistics)
        
        recommendations = self._generate_recommendations(results, conflicts)
        
        return IntegratedResult(
            integration_id=f"INT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            source_results=[r.call_id for r in results],
            status=status,
            content=content,
            summary=summary,
            statistics=statistics,
            conflicts=conflicts,
            recommendations=recommendations
        )
    
    def _determine_integrated_status(self, results: List[SkillCallResult]) -> ResultStatus:
        if not results:
            return ResultStatus.FAILURE
        
        success_count = sum(1 for r in results if r.status == ResultStatus.SUCCESS)
        failure_count = sum(1 for r in results if r.status == ResultStatus.FAILURE)
        
        if success_count == len(results):
            return ResultStatus.SUCCESS
        elif success_count > 0:
            return ResultStatus.PARTIAL_SUCCESS
        else:
            return ResultStatus.FAILURE
    
    def _merge_results(self, results: List[SkillCallResult]) -> Dict[str, Any]:
        merged = {
            "skills": {},
            "combined_data": {},
            "timeline": []
        }
        
        for result in results:
            skill_data = {
                "status": result.status.value,
                "content": result.content,
                "duration_ms": result.duration_ms,
                "warnings": result.warnings
            }
            merged["skills"][result.skill_name] = skill_data
            
            if isinstance(result.content, dict):
                for key, value in result.content.items():
                    if key not in merged["combined_data"]:
                        merged["combined_data"][key] = value
                    elif isinstance(merged["combined_data"][key], list):
                        if isinstance(value, list):
                            merged["combined_data"][key].extend(value)
                        else:
                            merged["combined_data"][key].append(value)
                    else:
                        merged["combined_data"][key] = [merged["combined_data"][key], value]
            
            merged["timeline"].append({
                "skill": result.skill_name,
                "timestamp": result.timestamp,
                "duration_ms": result.duration_ms
            })
        
        return merged
    
    def _first_success_result(self, results: List[SkillCallResult]) -> Dict[str, Any]:
        for result in results:
            if result.status == ResultStatus.SUCCESS:
                return {
                    "skill": result.skill_name,
                    "content": result.content,
                    "timestamp": result.timestamp
                }
        
        return {"error": "无成功结果"}
    
    def _best_score_result(self, results: List[SkillCallResult]) -> Dict[str, Any]:
        best_result = None
        best_score = -1
        
        for result in results:
            validation = self.validator.validate(result)
            if validation.score > best_score:
                best_score = validation.score
                best_result = result
        
        if best_result:
            return {
                "skill": best_result.skill_name,
                "content": best_result.content,
                "score": best_score,
                "timestamp": best_result.timestamp
            }
        
        return {"error": "无有效结果"}
    
    def _detect_conflicts(self, results: List[SkillCallResult]) -> List[Dict[str, Any]]:
        conflicts = []
        
        content_by_key = defaultdict(list)
        
        for result in results:
            if isinstance(result.content, dict):
                for key, value in result.content.items():
                    content_by_key[key].append({
                        "skill": result.skill_name,
                        "value": value
                    })
        
        for key, sources in content_by_key.items():
            if len(sources) > 1:
                values = [s["value"] for s in sources]
                unique_values = set(str(v) for v in values)
                
                if len(unique_values) > 1:
                    conflicts.append({
                        "key": key,
                        "sources": sources,
                        "conflict_type": "value_mismatch"
                    })
        
        return conflicts
    
    def _calculate_statistics(self, results: List[SkillCallResult]) -> Dict[str, Any]:
        total = len(results)
        success = sum(1 for r in results if r.status == ResultStatus.SUCCESS)
        failure = sum(1 for r in results if r.status == ResultStatus.FAILURE)
        partial = sum(1 for r in results if r.status == ResultStatus.PARTIAL_SUCCESS)
        timeout = sum(1 for r in results if r.status == ResultStatus.TIMEOUT)
        
        durations = [r.duration_ms for r in results if r.duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total": total,
            "success": success,
            "failure": failure,
            "partial_success": partial,
            "timeout": timeout,
            "success_rate": success / total if total > 0 else 0,
            "avg_duration_ms": avg_duration,
            "total_duration_ms": sum(durations)
        }
    
    def _generate_summary(self, results: List[SkillCallResult], 
                          status: ResultStatus, 
                          statistics: Dict[str, Any]) -> str:
        skill_names = [r.skill_name for r in results]
        
        if status == ResultStatus.SUCCESS:
            return f"成功整合 {len(results)} 个技能的调用结果: {', '.join(skill_names)}"
        elif status == ResultStatus.PARTIAL_SUCCESS:
            return f"部分成功整合 {statistics['success']}/{statistics['total']} 个技能的调用结果"
        else:
            return f"整合失败，所有 {statistics['total']} 个技能调用均未成功"
    
    def _generate_recommendations(self, results: List[SkillCallResult], 
                                   conflicts: List[Dict[str, Any]]) -> List[str]:
        recommendations = []
        
        failed_skills = [r.skill_name for r in results if r.status == ResultStatus.FAILURE]
        if failed_skills:
            recommendations.append(f"检查失败技能: {', '.join(failed_skills)}")
        
        if conflicts:
            recommendations.append(f"发现 {len(conflicts)} 个结果冲突，建议人工审核")
        
        slow_skills = [r.skill_name for r in results if r.duration_ms > 5000]
        if slow_skills:
            recommendations.append(f"优化慢速技能: {', '.join(slow_skills)}")
        
        return recommendations


class SkillResultManager:
    """技能结果管理器"""
    
    def __init__(self, storage_path: str = "."):
        self.storage_path = Path(storage_path) / "results"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.validator = ResultValidator()
        self.transformer = ResultTransformer()
        self.integrator = ResultIntegrator()
        
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SkillResultManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def save_result(self, result: SkillCallResult) -> str:
        result_file = self.storage_path / f"{result.call_id}.json"
        result_file.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), 
                              encoding='utf-8')
        
        self.logger.info(f"结果已保存: {result.call_id}")
        return str(result_file)
    
    def load_result(self, call_id: str) -> Optional[SkillCallResult]:
        result_file = self.storage_path / f"{call_id}.json"
        
        if not result_file.exists():
            return None
        
        try:
            data = json.loads(result_file.read_text(encoding='utf-8'))
            data['status'] = ResultStatus(data['status'])
            data['result_type'] = ResultType(data['result_type'])
            return SkillCallResult(**data)
        except Exception as e:
            self.logger.error(f"加载结果失败: {e}")
            return None
    
    def create_result(self, skill_name: str, content: Any, 
                      status: ResultStatus = ResultStatus.SUCCESS,
                      result_type: ResultType = ResultType.JSON,
                      duration_ms: float = 0.0,
                      metadata: Dict[str, Any] = None) -> SkillCallResult:
        call_id = f"CALL-{skill_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return SkillCallResult(
            call_id=call_id,
            skill_name=skill_name,
            timestamp=datetime.now().isoformat(),
            status=status,
            result_type=result_type,
            content=content,
            metadata=metadata or {},
            duration_ms=duration_ms
        )
    
    def integrate_results(self, call_ids: List[str], 
                          strategy: str = "merge") -> IntegratedResult:
        results = []
        
        for call_id in call_ids:
            result = self.load_result(call_id)
            if result:
                results.append(result)
        
        return self.integrator.integrate(results, strategy)
    
    def transform_result(self, call_id: str, 
                         target_type: ResultType) -> Optional[SkillCallResult]:
        result = self.load_result(call_id)
        
        if not result:
            return None
        
        transformed = self.transformer.transform(result, target_type)
        self.save_result(transformed)
        
        return transformed
    
    def validate_result(self, call_id: str, 
                        schema: Dict[str, Any] = None) -> Optional[ValidationResult]:
        result = self.load_result(call_id)
        
        if not result:
            return None
        
        return self.validator.validate(result, schema)
    
    def get_result_summary(self, call_id: str) -> str:
        result = self.load_result(call_id)
        
        if not result:
            return f"结果 {call_id} 不存在"
        
        lines = [
            f"# 结果摘要: {result.call_id}",
            "",
            f"- **技能**: {result.skill_name}",
            f"- **状态**: {result.status.value}",
            f"- **类型**: {result.result_type.value}",
            f"- **时间**: {result.timestamp}",
            f"- **耗时**: {result.duration_ms:.0f}ms",
        ]
        
        if result.error_message:
            lines.append(f"- **错误**: {result.error_message}")
        
        if result.warnings:
            lines.append(f"- **警告**: {len(result.warnings)}")
        
        return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='技能调用结果整合脚本')
    
    parser.add_argument('--storage', '-s', default='.', help='存储路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    create_parser = subparsers.add_parser('create', help='创建结果')
    create_parser.add_argument('--skill', required=True, help='技能名称')
    create_parser.add_argument('--content', required=True, help='结果内容(JSON格式)')
    create_parser.add_argument('--status', choices=[s.value for s in ResultStatus], 
                               default='success', help='状态')
    create_parser.add_argument('--type', choices=[t.value for t in ResultType], 
                               default='json', help='结果类型')
    create_parser.add_argument('--duration', type=float, default=0, help='执行时间(ms)')
    
    integrate_parser = subparsers.add_parser('integrate', help='整合结果')
    integrate_parser.add_argument('--call-ids', required=True, help='调用ID列表(逗号分隔)')
    integrate_parser.add_argument('--strategy', choices=['merge', 'first_success', 'best_score'],
                                  default='merge', help='整合策略')
    
    transform_parser = subparsers.add_parser('transform', help='转换结果')
    transform_parser.add_argument('--call-id', required=True, help='调用ID')
    transform_parser.add_argument('--target-type', choices=[t.value for t in ResultType],
                                  required=True, help='目标类型')
    
    validate_parser = subparsers.add_parser('validate', help='验证结果')
    validate_parser.add_argument('--call-id', required=True, help='调用ID')
    validate_parser.add_argument('--schema', help='验证Schema(JSON格式)')
    
    summary_parser = subparsers.add_parser('summary', help='获取结果摘要')
    summary_parser.add_argument('--call-id', required=True, help='调用ID')
    
    args = parser.parse_args()
    
    manager = SkillResultManager(args.storage)
    
    if args.command == 'create':
        try:
            content = json.loads(args.content)
        except json.JSONDecodeError:
            content = args.content
        
        result = manager.create_result(
            skill_name=args.skill,
            content=content,
            status=ResultStatus(args.status),
            result_type=ResultType(args.type),
            duration_ms=args.duration
        )
        
        file_path = manager.save_result(result)
        print(f"结果已创建: {result.call_id}")
        print(f"保存路径: {file_path}")
    
    elif args.command == 'integrate':
        call_ids = [c.strip() for c in args.call_ids.split(',')]
        integrated = manager.integrate_results(call_ids, args.strategy)
        
        print(f"\n整合结果: {integrated.integration_id}")
        print(f"状态: {integrated.status.value}")
        print(f"摘要: {integrated.summary}")
        print(f"\n统计:")
        for key, value in integrated.statistics.items():
            print(f"  {key}: {value}")
        
        if integrated.conflicts:
            print(f"\n冲突 ({len(integrated.conflicts)}):")
            for conflict in integrated.conflicts[:5]:
                print(f"  - {conflict['key']}: {conflict['conflict_type']}")
    
    elif args.command == 'transform':
        transformed = manager.transform_result(args.call_id, ResultType(args.target_type))
        
        if transformed:
            print(f"结果已转换: {transformed.call_id}")
            print(f"新类型: {transformed.result_type.value}")
        else:
            print(f"结果不存在: {args.call_id}")
    
    elif args.command == 'validate':
        schema = None
        if args.schema:
            try:
                schema = json.loads(args.schema)
            except json.JSONDecodeError:
                pass
        
        validation = manager.validate_result(args.call_id, schema)
        
        if validation:
            print(f"\n验证结果:")
            print(f"有效: {validation.is_valid}")
            print(f"分数: {validation.score:.2f}")
            
            if validation.errors:
                print(f"\n错误:")
                for error in validation.errors:
                    print(f"  - {error}")
            
            if validation.warnings:
                print(f"\n警告:")
                for warning in validation.warnings:
                    print(f"  - {warning}")
        else:
            print(f"结果不存在: {args.call_id}")
    
    elif args.command == 'summary':
        summary = manager.get_result_summary(args.call_id)
        print(summary)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
