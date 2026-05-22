#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化流水线编排器 - Automated Pipeline Orchestrator

整合测试、文档生成、UI校验、代码审查及流程闭环的自动化流水线
支持SDD+TDD循环开发模式，实现从需求到交付的完整闭环

使用示例:
    python automated_pipeline_orchestrator.py --mode full --version 2.5.0
    python automated_pipeline_orchestrator.py --stage test --dry-run
    python automated_pipeline_orchestrator.py --stage docs --report
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    PREPARE = "prepare"
    ANALYZE = "analyze"
    TEST = "test"
    BUILD = "build"
    DOCUMENT = "document"
    REVIEW = "review"
    DEPLOY = "deploy"
    VERIFY = "verify"


class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


@dataclass
class StageResult:
    stage: PipelineStage
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: int = 0
    output: str = ""
    error: str = ""
    artifacts: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "output": self.output,
            "error": self.error,
            "artifacts": self.artifacts,
            "metrics": self.metrics
        }


@dataclass
class PipelineResult:
    pipeline_id: str
    version: str
    status: PipelineStatus
    stages: List[StageResult]
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: int = 0
    report_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "version": self.version,
            "status": self.status.value,
            "stages": [s.to_dict() for s in self.stages],
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": self.total_duration_ms,
            "report_path": self.report_path
        }


class StageExecutor:
    def __init__(self, base_path: Path, skillscripts_path: Path):
        self.base_path = base_path
        self.skillscripts_path = skillscripts_path
        self._register_executors()
    
    def _register_executors(self):
        self._executors: Dict[PipelineStage, Callable] = {
            PipelineStage.PREPARE: self._execute_prepare,
            PipelineStage.ANALYZE: self._execute_analyze,
            PipelineStage.TEST: self._execute_test,
            PipelineStage.BUILD: self._execute_build,
            PipelineStage.DOCUMENT: self._execute_document,
            PipelineStage.REVIEW: self._execute_review,
            PipelineStage.DEPLOY: self._execute_deploy,
            PipelineStage.VERIFY: self._execute_verify,
        }
    
    def execute(self, stage: PipelineStage, dry_run: bool = False) -> StageResult:
        start_time = datetime.now()
        
        executor = self._executors.get(stage)
        if not executor:
            return StageResult(
                stage=stage,
                status=PipelineStatus.SKIPPED,
                start_time=start_time,
                error=f"未找到阶段执行器: {stage.value}"
            )
        
        try:
            if dry_run:
                logger.info(f"[DRY-RUN] 跳过执行阶段: {stage.value}")
                return StageResult(
                    stage=stage,
                    status=PipelineStatus.SKIPPED,
                    start_time=start_time,
                    output="Dry-run模式，跳过执行"
                )
            
            return executor(start_time)
        except Exception as e:
            logger.error(f"阶段执行失败 {stage.value}: {e}")
            return StageResult(
                stage=stage,
                status=PipelineStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error=str(e)
            )
    
    def _execute_prepare(self, start_time: datetime) -> StageResult:
        logger.info("执行准备阶段...")
        artifacts = []
        metrics = {}
        
        env_check_script = self.skillscripts_path / "core" / "check_environment.py"
        if env_check_script.exists():
            result = self._run_script(str(env_check_script), ["--full"])
            if result["success"]:
                artifacts.append("environment_report.json")
                metrics["environment_check"] = "passed"
            else:
                metrics["environment_check"] = "warning"
        
        return StageResult(
            stage=PipelineStage.PREPARE,
            status=PipelineStatus.SUCCESS,
            start_time=start_time,
            end_time=datetime.now(),
            output="环境准备完成",
            artifacts=artifacts,
            metrics=metrics
        )
    
    def _execute_analyze(self, start_time: datetime) -> StageResult:
        logger.info("执行分析阶段...")
        artifacts = []
        metrics = {}
        
        arch_check = self.skillscripts_path / "analysis" / "architecture_check.py"
        if arch_check.exists():
            result = self._run_script(str(arch_check), ["--full"])
            metrics["architecture_score"] = result.get("score", 0)
        
        code_smell = self.skillscripts_path / "analysis" / "intelligent_code_smell_detector.py"
        if code_smell.exists():
            result = self._run_script(str(code_smell), ["--output", "code_smell_report.json"])
            if result["success"]:
                artifacts.append("code_smell_report.json")
        
        return StageResult(
            stage=PipelineStage.ANALYZE,
            status=PipelineStatus.SUCCESS,
            start_time=start_time,
            end_time=datetime.now(),
            output="代码分析完成",
            artifacts=artifacts,
            metrics=metrics
        )
    
    def _execute_test(self, start_time: datetime) -> StageResult:
        logger.info("执行测试阶段...")
        artifacts = []
        metrics = {}
        
        test_types = [
            ("unit", "unit_test_enhancer.py"),
            ("integration", "integration_test_enhancer.py"),
            ("e2e", "e2e_test_enhancer.py"),
            ("performance", "performance_test_enhancer.py"),
            ("security", "security_scanner.py"),
        ]
        
        total_passed = 0
        total_failed = 0
        
        for test_type, script_name in test_types:
            script_path = self.skillscripts_path / "test" / script_name
            if script_path.exists():
                result = self._run_script(str(script_path), ["--report"])
                total_passed += result.get("passed", 0)
                total_failed += result.get("failed", 0)
                artifacts.append(f"{test_type}_test_report.json")
        
        metrics["tests_passed"] = total_passed
        metrics["tests_failed"] = total_failed
        metrics["coverage"] = self._calculate_coverage()
        
        status = PipelineStatus.SUCCESS if total_failed == 0 else PipelineStatus.FAILED
        
        return StageResult(
            stage=PipelineStage.TEST,
            status=status,
            start_time=start_time,
            end_time=datetime.now(),
            output=f"测试完成: 通过 {total_passed}, 失败 {total_failed}",
            artifacts=artifacts,
            metrics=metrics
        )
    
    def _execute_build(self, start_time: datetime) -> StageResult:
        logger.info("执行构建阶段...")
        artifacts = []
        metrics = {}
        
        build_result = self._run_command([sys.executable, "-m", "pip", "install", "-e", "."])
        metrics["build_success"] = build_result["success"]
        
        return StageResult(
            stage=PipelineStage.SUCCESS if build_result["success"] else PipelineStage.FAILED,
            status=PipelineStatus.SUCCESS if build_result["success"] else PipelineStatus.FAILED,
            start_time=start_time,
            end_time=datetime.now(),
            output=build_result["output"],
            artifacts=artifacts,
            metrics=metrics
        )
    
    def _execute_document(self, start_time: datetime) -> StageResult:
        logger.info("执行文档生成阶段...")
        artifacts = []
        metrics = {}
        
        doc_gen = self.skillscripts_path / "pipeline" / "doc_generator.py"
        if doc_gen.exists():
            result = self._run_script(str(doc_gen), ["--all"])
            if result["success"]:
                artifacts.append("docs/libs/")
        
        api_doc = self.skillscripts_path / "pipeline" / "sdd_api_doc_generator.py"
        if api_doc.exists():
            result = self._run_script(str(api_doc), [])
            if result["success"]:
                artifacts.append("api_docs/")
        
        return StageResult(
            stage=PipelineStage.DOCUMENT,
            status=PipelineStatus.SUCCESS,
            start_time=start_time,
            end_time=datetime.now(),
            output="文档生成完成",
            artifacts=artifacts,
            metrics=metrics
        )
    
    def _execute_review(self, start_time: datetime) -> StageResult:
        logger.info("执行代码审查阶段...")
        artifacts = []
        metrics = {}
        
        review_script = self.skillscripts_path / "pipeline" / "code_review_automation.py"
        if review_script.exists():
            result = self._run_script(str(review_script), ["--auto"])
            metrics["review_score"] = result.get("score", 0)
            if result["success"]:
                artifacts.append("review_report.json")
        
        return StageResult(
            stage=PipelineStage.REVIEW,
            status=PipelineStatus.SUCCESS,
            start_time=start_time,
            end_time=datetime.now(),
            output="代码审查完成",
            artifacts=artifacts,
            metrics=metrics
        )
    
    def _execute_deploy(self, start_time: datetime) -> StageResult:
        logger.info("执行部署阶段...")
        artifacts = []
        metrics = {}
        
        deploy_script = self.skillscripts_path / "core" / "start_services.py"
        if deploy_script.exists():
            result = self._run_script(str(deploy_script), [])
            metrics["deploy_success"] = result["success"]
        
        return StageResult(
            stage=PipelineStage.DEPLOY,
            status=PipelineStatus.SUCCESS,
            start_time=start_time,
            end_time=datetime.now(),
            output="部署完成",
            artifacts=artifacts,
            metrics=metrics
        )
    
    def _execute_verify(self, start_time: datetime) -> StageResult:
        logger.info("执行验证阶段...")
        artifacts = []
        metrics = {}
        
        health_check = self.skillscripts_path / "core" / "health_check.py"
        if health_check.exists():
            result = self._run_script(str(health_check), [])
            metrics["health_status"] = "healthy" if result["success"] else "unhealthy"
        
        return StageResult(
            stage=PipelineStage.VERIFY,
            status=PipelineStatus.SUCCESS,
            start_time=start_time,
            end_time=datetime.now(),
            output="验证完成",
            artifacts=artifacts,
            metrics=metrics
        )
    
    def _run_script(self, script_path: str, args: List[str]) -> Dict[str, Any]:
        try:
            cmd = [sys.executable, script_path] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.base_path)
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "脚本执行超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _run_command(self, cmd: List[str]) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(self.base_path)
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_coverage(self) -> float:
        return 0.0


class PipelineOrchestrator:
    DEFAULT_STAGES = [
        PipelineStage.PREPARE,
        PipelineStage.ANALYZE,
        PipelineStage.TEST,
        PipelineStage.BUILD,
        PipelineStage.DOCUMENT,
        PipelineStage.REVIEW,
        PipelineStage.DEPLOY,
        PipelineStage.VERIFY,
    ]
    
    def __init__(
        self,
        base_path: str,
        version: str = "0.1.0",
        stages: Optional[List[PipelineStage]] = None
    ):
        self.base_path = Path(base_path)
        self.version = version
        self.stages = stages or self.DEFAULT_STAGES
        self.skillscripts_path = self.base_path / "skillscripts"
        
        self.executor = StageExecutor(self.base_path, self.skillscripts_path)
        self.pipeline_id = f"PIPE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._stage_results: List[StageResult] = []
    
    def run(self, dry_run: bool = False, stop_on_failure: bool = True) -> PipelineResult:
        logger.info(f"启动流水线: {self.pipeline_id}")
        logger.info(f"版本: {self.version}")
        logger.info(f"阶段: {[s.value for s in self.stages]}")
        
        start_time = datetime.now()
        overall_status = PipelineStatus.SUCCESS
        
        for stage in self.stages:
            logger.info(f"执行阶段: {stage.value}")
            result = self.executor.execute(stage, dry_run)
            self._stage_results.append(result)
            
            if result.status == PipelineStatus.FAILED:
                overall_status = PipelineStatus.FAILED
                if stop_on_failure:
                    logger.error(f"阶段失败，停止流水线: {stage.value}")
                    break
        
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        pipeline_result = PipelineResult(
            pipeline_id=self.pipeline_id,
            version=self.version,
            status=overall_status,
            stages=self._stage_results,
            start_time=start_time,
            end_time=end_time,
            total_duration_ms=duration_ms
        )
        
        return pipeline_result
    
    def run_single_stage(self, stage: PipelineStage, dry_run: bool = False) -> StageResult:
        logger.info(f"执行单个阶段: {stage.value}")
        return self.executor.execute(stage, dry_run)
    
    def generate_report(
        self,
        result: PipelineResult,
        output_path: Optional[str] = None,
        format: str = "markdown"
    ) -> str:
        if format == "json":
            return self._generate_json_report(result, output_path)
        return self._generate_markdown_report(result, output_path)
    
    def _generate_markdown_report(
        self,
        result: PipelineResult,
        output_path: Optional[str] = None
    ) -> str:
        lines = [
            "# 自动化流水线报告",
            "",
            f"**流水线ID**: {result.pipeline_id}",
            f"**版本**: {result.version}",
            f"**状态**: {result.status.value}",
            f"**开始时间**: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**结束时间**: {result.end_time.strftime('%Y-%m-%d %H:%M:%S') if result.end_time else 'N/A'}",
            f"**总耗时**: {result.total_duration_ms}ms",
            "",
            "## 阶段详情",
            "",
        ]
        
        for stage_result in result.stages:
            status_emoji = {
                PipelineStatus.SUCCESS: "✅",
                PipelineStatus.FAILED: "❌",
                PipelineStatus.SKIPPED: "⏭️",
                PipelineStatus.RUNNING: "🔄",
                PipelineStatus.PENDING: "⏳",
                PipelineStatus.ROLLED_BACK: "↩️",
            }.get(stage_result.status, "❓")
            
            lines.extend([
                f"### {status_emoji} {stage_result.stage.value}",
                "",
                f"- **状态**: {stage_result.status.value}",
                f"- **耗时**: {stage_result.duration_ms}ms",
                f"- **输出**: {stage_result.output[:200]}..." if len(stage_result.output) > 200 else f"- **输出**: {stage_result.output}",
            ])
            
            if stage_result.error:
                lines.append(f"- **错误**: {stage_result.error}")
            
            if stage_result.metrics:
                lines.append("- **指标**:")
                for key, value in stage_result.metrics.items():
                    lines.append(f"  - {key}: {value}")
            
            if stage_result.artifacts:
                lines.append(f"- **产物**: {', '.join(stage_result.artifacts)}")
            
            lines.append("")
        
        report = "\n".join(lines)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"报告已保存: {output_path}")
        
        return report
    
    def _generate_json_report(
        self,
        result: PipelineResult,
        output_path: Optional[str] = None
    ) -> str:
        report = json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"报告已保存: {output_path}")
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description="自动化流水线编排器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--base-path",
        type=str,
        default=".",
        help="项目基础路径"
    )
    parser.add_argument(
        "--version",
        type=str,
        default="0.1.0",
        help="版本号"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "test", "docs", "deploy", "custom"],
        default="full",
        help="流水线模式"
    )
    parser.add_argument(
        "--stage",
        type=str,
        help="执行单个阶段 (prepare/analyze/test/build/document/review/deploy/verify)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式，不实际执行"
    )
    parser.add_argument(
        "--no-stop-on-failure",
        action="store_true",
        help="阶段失败后继续执行"
    )
    parser.add_argument(
        "--report",
        type=str,
        help="报告输出路径"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="报告格式"
    )
    
    args = parser.parse_args()
    
    base_path = Path(args.base_path).resolve()
    
    if not base_path.exists():
        print(f"错误: 基础路径不存在: {base_path}")
        sys.exit(1)
    
    mode_stages = {
        "full": PipelineOrchestrator.DEFAULT_STAGES,
        "test": [PipelineStage.PREPARE, PipelineStage.TEST],
        "docs": [PipelineStage.PREPARE, PipelineStage.DOCUMENT],
        "deploy": [PipelineStage.PREPARE, PipelineStage.DEPLOY, PipelineStage.VERIFY],
        "custom": None,
    }
    
    if args.stage:
        try:
            stage = PipelineStage(args.stage)
            stages = [stage]
        except ValueError:
            print(f"错误: 无效的阶段名称: {args.stage}")
            print(f"有效阶段: {[s.value for s in PipelineStage]}")
            sys.exit(1)
    else:
        stages = mode_stages.get(args.mode)
    
    orchestrator = PipelineOrchestrator(
        base_path=str(base_path),
        version=args.version,
        stages=stages
    )
    
    print(f"\n{'='*60}")
    print(f"自动化流水线编排器")
    print(f"{'='*60}")
    print(f"流水线ID: {orchestrator.pipeline_id}")
    print(f"基础路径: {base_path}")
    print(f"版本: {args.version}")
    print(f"模式: {args.mode}")
    print(f"阶段: {[s.value for s in orchestrator.stages]}")
    print(f"{'='*60}\n")
    
    if args.stage:
        result = orchestrator.run_single_stage(stage, args.dry_run)
        print(f"\n阶段执行结果: {result.status.value}")
        if result.output:
            print(f"输出: {result.output[:500]}")
        if result.error:
            print(f"错误: {result.error}")
    else:
        result = orchestrator.run(
            dry_run=args.dry_run,
            stop_on_failure=not args.no_stop_on_failure
        )
        
        print(f"\n{'='*60}")
        print(f"流水线执行完成")
        print(f"{'='*60}")
        print(f"状态: {result.status.value}")
        print(f"总耗时: {result.total_duration_ms}ms")
        print(f"{'='*60}\n")
        
        if args.report:
            orchestrator.generate_report(result, args.report, args.format)
        else:
            report = orchestrator.generate_report(result, format=args.format)
            print(report)
    
    return 0 if result.status == PipelineStatus.SUCCESS else 1


if __name__ == "__main__":
    sys.exit(main())
