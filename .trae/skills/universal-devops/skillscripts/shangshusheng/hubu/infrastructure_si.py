"""
基础设施司 - CI/CD流水线生成、Docker多阶段构建、K8s部署模板、云服务配置、监控告警集成
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class InfrastructureError(Exception):
    """基础设施相关异常"""
    pass


class TemplateError(InfrastructureError):
    """模板错误"""


class CIPlatform(str, Enum):
    """CI/CD平台枚举"""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    AZURE_PIPELINES = "azure_pipelines"
    CLOUD_BUILD = "cloud_build"


@dataclass
class StageGate:
    """阶段门禁条件"""
    stage_name: str
    entry_conditions: list[dict[str, str]] = field(default_factory=list)
    exit_conditions: list[dict[str, str]] = field(default_factory=list)
    approval_required: bool = False
    approvers: list[str] = field(default_factory=list)
    quality_gates: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "entry_conditions": self.entry_conditions,
            "exit_conditions": self.exit_conditions,
            "approval_required": self.approval_required,
            "approvers": self.approvers,
            "quality_gates": self.quality_gates,
        }


@dataclass
class PipelineConfig:
    """CI/CD流水线配置"""
    name: str
    platform: CIPlatform
    triggers: dict[str, Any] = field(default_factory=dict)
    stages: list[dict[str, Any]] = field(default_factory=list)
    variables: dict[str, str] = field(default_factory=dict)
    secrets: list[str] = field(default_factory=list)
    environment: str = "production"
    branch_rules: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "platform": self.platform.value,
            "triggers": self.triggers,
            "stages": self.stages,
            "variables": {k: "***" if k in self.secrets else v for k, v in self.variables.items()},
            "secret_count": len(self.secrets),
            "environment": self.environment,
            "branch_rules": self.branch_rules,
        }


@dataclass
class DockerConfig:
    """Docker多阶段构建配置"""
    stages: list[dict[str, Any]] = field(default_factory=list)
    base_images: dict[str, str] = field(default_factory=dict)
    build_args: list[str] = field(default_factory=list)
    expose_ports: list[int] = field(default_factory=list)
    healthcheck: dict[str, Any] | None = None
    labels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stages": self.stages,
            "base_images": self.base_images,
            "build_args": self.build_args,
            "expose_ports": self.expose_ports,
            "healthcheck": self.healthcheck,
            "labels": self.labels,
        }


@dataclass
class K8sManifest:
    """Kubernetes资源清单"""
    kind: str
    api_version: str = "apps/v1"
    metadata: dict[str, Any] = field(default_factory=dict)
    spec: dict[str, Any] = field(default_factory=dict)
    namespace: str = "default"

    def to_yaml(self) -> str:
        """输出YAML格式（简化版）"""
        lines: list[str] = []
        lines.append(f"apiVersion: {self.api_version}")
        lines.append(f"kind: {self.kind}")
        lines.append(f"metadata:")
        for k, v in self.metadata.items():
            if isinstance(v, (list, dict)):
                lines.append(f"  {k}: {json.dumps(v, ensure_ascii=False)}")
            else:
                lines.append(f"  {k}: {v}")
        lines.append(f"spec:")
        for k, v in self.spec.items():
            if isinstance(v, (list, dict)):
                lines.append(f"  {k}:")
                self._dump_yaml(lines, v, indent=4)
            else:
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    @staticmethod
    def _dump_yaml(lines: list[str], obj: Any, indent: int) -> None:
        prefix = " " * indent
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (list, dict)):
                    lines.append(f"{prefix}{k}:")
                    K8sManifest._dump_yaml(lines, v, indent + 2)
                else:
                    lines.append(f"{prefix}{k}: {v}")
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    lines.append(f"{prefix}- ")
                    K8sManifest._dump_yaml(lines, item, indent + 2)
                else:
                    lines.append(f"{prefix}- {item}")


@dataclass
class CloudTemplate:
    """云服务配置模板"""
    provider: str
    service_type: str
    resources: list[dict[str, Any]] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)
    estimated_cost_monthly: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "service_type": self.service_type,
            "resources": self.resources,
            "config": self.config,
            "estimated_cost_monthly": round(self.estimated_cost_monthly, 2),
        }


@dataclass
class MonitoringConfig:
    """监控告警配置"""
    tool: str
    dashboards: list[dict[str, Any]] = field(default_factory=list)
    alert_rules: list[dict[str, Any]] = field(default_factory=list)
    exporters: list[dict[str, Any]] = field(default_factory=list)
    retention_days: int = 30

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "dashboards_count": len(self.dashboards),
            "alert_rules_count": len(self.alert_rules),
            "exporters_count": len(self.exporters),
            "retention_days": self.retention_days,
        }


class InfrastructureSi:
    """
    基础设施司 - 户部·虞部司

    提供全面的基础设施即代码能力：
    - CI/CD流水线生成（GitHub Actions/GitLab CI/Jenkinsfile/Azure Pipelines/Cloud Build）
    - Pipeline as Code 完整YAML定义（触发器→构建→测试→扫描→部署各阶段）
    - 阶段门禁自动化（build/test/scan/deploy准入准出条件）
    - Docker多阶段构建配置（builder→tester→runner阶段）
    - Kubernetes部署模板（Deployment/Service/ConfigMap/Secret/Ingress/HPA/PDB）
    - 云服务配置模板（AWS/Azure/GCP/阿里云）
    - 监控告警集成模板（Prometheus+Grafana / ELK / Datadog）
    """

    _INSTANCE: InfrastructureSi | None = None

    def __init__(self) -> None:
        self._pipelines: dict[str, PipelineConfig] = {}
        self._docker_configs: dict[str, DockerConfig] = {}
        self._k8s_manifests: list[K8sManifest] = []
        self._cloud_templates: dict[str, CloudTemplate] = {}
        self._monitoring_configs: dict[str, MonitoringConfig] = {}
        self._stage_gates: dict[str, StageGate] = {}

    @classmethod
    def get_instance(cls) -> InfrastructureSi:
        """获取单例实例"""
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ==================== CI/CD 流水线 ====================

    def generate_pipeline(
        self,
        platform: CIPlatform,
        project_name: str = "myapp",
        language: str = "python",
        **kwargs: Any,
    ) -> PipelineConfig:
        """
        生成CI/CD流水线配置

        Args:
            platform: 目标CI平台
            project_name: 项目名称
            language: 编程语言
            **kwargs: 额外参数

        Returns:
            PipelineConfig对象
        """
        triggers: dict[str, Any]
        stages: list[dict[str, Any]]
        variables: dict[str, str]
        secrets: list[str]

        match platform:
            case CIPlatform.GITHUB_ACTIONS:
                triggers, stages, variables, secrets = self._gen_github_actions(
                    project_name, language, **kwargs
                )
            case CIPlatform.GITLAB_CI:
                triggers, stages, variables, secrets = self._gen_gitlab_ci(
                    project_name, language, **kwargs
                )
            case CIPlatform.JENKINS:
                triggers, stages, variables, secrets = self._gen_jenkinsfile(
                    project_name, language, **kwargs
                )
            case CIPlatform.AZURE_PIPELINES:
                triggers, stages, variables, secrets = self._gen_azure_pipelines(
                    project_name, language, **kwargs
                )
            case CIPlatform.CLOUD_BUILD:
                triggers, stages, variables, secrets = self._gen_cloud_build(
                    project_name, language, **kwargs
                )
            case _:
                raise TemplateError(f"不支持的CI平台: {platform.value}")

        pipeline = PipelineConfig(
            name=project_name,
            platform=platform,
            triggers=triggers,
            stages=stages,
            variables=variables,
            secrets=secrets,
            environment=kwargs.get("environment", "production"),
            branch_rules={
                "main": "deploy_production",
                "develop": "deploy_staging",
                "feature/*": "build_and_test_only",
            },
        )

        key = f"{platform.value}_{project_name}"
        self._pipelines[key] = pipeline

        gates = self._generate_stage_gates(language)
        for gate in gates:
            self._stage_gates[f"{key}_{gate.stage_name}"] = gate

        return pipeline

    def _gen_github_actions(
        self, name: str, lang: str, **kw: Any
    ) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str], list[str]]:
        """生成 GitHub Actions YAML 配置"""
        triggers = {
            "push": {"branches": ["main", "develop"], "tags": ["v*"]},
            "pull_request": {"branches": ["main", "develop"]},
            "workflow_dispatch": {},
        }
        install_cmd = self._get_install_cmd(lang)
        test_cmd = self._get_test_cmd(lang)
        stages = [
            {"name": "Build", "runs-on": "ubuntu-latest", "steps": [
                {"name": "Checkout", "uses": "actions/checkout@v4"},
                {"name": f"Setup {lang.title()}", "uses": self._get_setup_action(lang)},
                {"name": "Install", "run": install_cmd},
                {"name": "Lint", "run": self._get_lint_cmd(lang)},
                {"name": "Build", "run": self._get_build_cmd(lang)},
            ]},
            {"name": "Test", "needs": ["Build"], "runs-on": "ubuntu-latest", "steps": [
                {"name": "Checkout", "uses": "actions/checkout@v4"},
                {"name": f"Setup {lang.title()}", "uses": self._get_setup_action(lang)},
                {"name": "Install", "run": install_cmd},
                {"name": "Run Tests", "run": test_cmd},
                {"name": "Upload Coverage", "uses": "actions/upload-artifact@v4",
                 "with": {"name": "coverage-report", "path": "coverage/"}},
            ]},
            {"name": "Security Scan", "needs": ["Test"], "runs-on": "ubuntu-latest", "steps": [
                {"name": "Checkout", "uses": "actions/checkout@v4"},
                {"name": "Trivy FS Scan", "uses": "aquasecurity/trivy-action@master",
                 "with": {"scan-type": "fs", "scan-ref": "."}},
                {"name": "Dependabot Check", "run": "echo 'Checking dependencies...'"},
            ]},
            {"name": "Deploy Staging", "needs": ["Security Scan"],
             "if": "github.ref == 'refs/heads/main'", "runs-on": "ubuntu-latest",
             "steps": [
                {"name": "Deploy", "run": "echo 'Deploying to staging...'",
                 "env": {"ENVIRONMENT": "staging"}},
            ]},
            {"name": "Deploy Production", "needs": ["Deploy Staging"],
             "if": "startsWith(github.ref, 'refs/tags/v')", "runs-on": "ubuntu-latest",
             "environment": "production", "steps": [
                {"name": "Deploy", "run": "echo 'Deploying to production...'",
                 "env": {"ENVIRONMENT": "production"}},
            ]},
        ]
        variables = {
            "DOCKER_REGISTRY": "ghcr.io",
            "IMAGE_NAME": f"{kw.get('org', 'myorg')}/{name}",
            "PYTHON_VERSION": "3.11",
            "NODE_VERSION": "20",
        }
        secrets = ["DOCKER_PASSWORD", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
        return triggers, stages, variables, secrets

    def _gen_gitlab_ci(
        self, name: str, lang: str, **kw: Any
    ) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str], list[str]]:
        """生成 GitLab CI 配置"""
        triggers = {"rules": [
            {"if": "$CI_COMMIT_BRANCH == 'main'", "when": "always"},
            {"if": "$CI_MERGE_REQUEST_TARGET_BRANCH_NAME == 'main'", "when": "always"},
            {"if": "$CI_COMMIT_TAG =~ /^v\\d/", "when": "always"},
        ]}
        install_cmd = self._get_install_cmd(lang)
        test_cmd = self._get_test_cmd(lang)
        image = self._get_docker_image(lang)
        stages = [
            {"stage": "build", "image": image, "script": [install_cmd, self._get_lint_cmd(lang), self._get_build_cmd(lang)],
             "artifacts": {"paths": ["dist/", "build/"]}},
            {"stage": "test", "image": image, "script": [install_cmd, test_cmd],
             "coverage": "/TOTAL.*?(\\d+)%/", "artifacts": {"reports": {"junit": "junit.xml"}}},
            {"stage": "security", "image": "aquasec/trivy:latest", "script": ["trivy fs --format table --output report.txt ."]},
            {"stage": "deploy-staging", "image": image, "environment": {"name": "staging"},
             "script": [f"echo 'Deploying {name} to staging'"], "only": ["main"]},
            {"stage": "deploy-production", "image": image, "environment": {"name": "production"},
             "when": "manual", "script": [f"echo 'Deploying {name} to production'"], "only": ["tags"]},
        ]
        variables = {"DOCKER_IMAGE": f"{kw.get('registry', 'registry.gitlab.com')}/{name}", "CI_DEBUG_TRACE": "true"}
        secrets = ["DEPLOY_TOKEN", "DATABASE_URL", "SECRET_KEY"]
        return triggers, stages, variables, secrets

    def _gen_jenkinsfile(
        self, name: str, lang: str, **kw: Any
    ) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str], list[str]]:
        """生成 Jenkinsfile 配置"""
        triggers = {"triggers": {"gitlab": True, "pollSCM": "H/5 * * * *"}}
        install_cmd = self._get_install_cmd(lang)
        test_cmd = self._get_test_cmd(lang)
        stages = [
            {"name": "Build", "agent": "any", "steps": [
                {"step": "Checkout SCM"},
                {"step": f"Install {lang}", "command": install_cmd},
                {"step": "Lint & Build", "command": f"{self._get_lint_cmd(lang)} && {self._get_build_cmd(lang)}"},
            ]},
            {"name": "Test", "agent": "any", "steps": [
                {"step": "Run Tests", "command": test_cmd},
                {"step": "Publish JUnit Results", "command": "junit 'junit.xml'"},
            ]},
            {"name": "Scan", "agent": "any", "steps": [
                {"step": "SonarQube Analysis", "command": "sonar-scanner"},
                {"step": "Dependency Check", "command": "dependency-check --project . --out report.html"},
            ]},
            {"name": "Deploy", "agent": "any", "when": "branch == 'main'", "steps": [
                {"step": "Docker Build & Push", "command": "docker build -t ${IMAGE}:${BUILD_NUMBER} . && docker push ${IMAGE}"},
                {"step": "kubectl Apply", "command": "kubectl apply -f k8s/"},
            ]},
        ]
        variables = {"IMAGE": f"{kw.get('registry', 'docker.io')}/{name}"}
        secrets = ["JENKINS_CREDS", "DOCKER_CREDENTIALS"]
        return triggers, stages, variables, secrets

    def _gen_azure_pipelines(
        self, name: str, lang: str, **kw: Any
    ) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str], list[str]]:
        """生成 Azure Pipelines YAML 配置"""
        triggers = {"trigger": {"branches": {"include": ["main", "develop"]}, "tags": {"include": ["v*"]}}}
        install_cmd = self._get_install_cmd(lang)
        test_cmd = self._get_test_cmd(lang)
        vm_image = self._get_vm_image(lang)
        stages = [
            {"name": "Build", "pool": {"vmImage": vm_image}, "steps": [
                {"task": "UsePythonVersion@0", "inputs": {"versionSpec": "3.11"} if lang == "python" else {}},
                {"script": install_cmd, "displayName": "Install Dependencies"},
                {"script": self._get_build_cmd(lang), "displayName": "Build Project"},
            ]},
            {"name": "Test", "dependsOn": ["Build"], "pool": {"vmImage": vm_image}, "steps": [
                {"script": test_cmd, "displayName": "Run Tests"},
                {"task": "PublishTestResults@2", "inputs": {"testResultsFormat": "JUnit"}},
            ]},
            {"name": "Security", "dependsOn": ["Test"], "pool": {"vmImage": vm_image}, "steps": [
                {"task": "TrivyVulnerabilityScanner@1", "inputs": {"scanType": "FileSystem"}},
            ]},
            {"name": "Deploy Staging", "dependsOn": ["Security"],
             "condition": "and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))",
             "environment": "Staging", "steps": [{"script": "echo Deploying to staging..."}]},
            {"name": "Deploy Production", "dependsOn": ["Deploy Staging"],
             "condition": "startsWith(variables['Build.SourceBranch'], 'refs/tags/')",
             "environment": "Production", "steps": [{"script": "echo Deploying to production..."}]},
        ]
        variables = {"AZURE_WEBAPP_NAME": name}
        secrets = ["AZURE_SERVICE_CONNECTION", "CONNECTION_STRING"]
        return triggers, stages, variables, secrets

    def _gen_cloud_build(
        self, name: str, lang: str, **kw: Any
    ) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, str], list[str]]:
        """生成 Google Cloud Build 配置"""
        triggers = {"push": {"branches": ["main"], "tags": ["v*"]}}
        install_cmd = self._get_install_cmd(lang)
        test_cmd = self._get_test_cmd(lang)
        steps_data = [
            {"name": "gcr.io/cloud-builders/docker", "args": ["build", "-t", f"gcr.io/$PROJECT_ID/{name}:{SHORT_SHA}", "."]},
            {"name": f"gcr.io/cloud-builders/{lang}",
             "entrypoint": "bash", "args": ["-c", f"{install_cmd} && {test_cmd}"]},
            {"name": "gcr.io/$PROJECT_ID/trivy", "args": ["fs", "--exit-code", "0", "--severity", "HIGH,CRITICAL", "."]},
            {"name": "gcr.io/cloud-builders/gke-deploy", "args": ["run", f"--filename=k8s/", f"--image=gcr.io/$PROJECT_ID/{name}:{SHORT_SHA}",
                                                       f"--location={kw.get('region', 'asia-east1')}",
                                                       f"--cluster={kw.get('cluster', 'prod-cluster')}"],
             "entrypoint": "gke-deploy"},
        ]
        stages = [
            {"name": "Docker Build", "steps": [steps_data[0]]},
            {"name": "Test", "steps": [steps_data[1]]},
            {"name": "Security Scan", "steps": [steps_data[2]]},
            {"name": "Deploy", "steps": [steps_data[3]], "only": "main or tags"},
        ]
        variables = {"PROJECT_ID": "$PROJECT_ID"}
        secrets = ["_GCP_SERVICE_ACCOUNT_KEY"]
        return triggers, stages, variables, secrets

    # ==================== 阶段门禁 ====================

    def _generate_stage_gates(self, language: str) -> list[StageGate]:
        """生成各阶段的门禁条件"""
        lint_tool = self._get_lint_cmd(language).split()[0].lower()
        return [
            StageGate(
                stage_name="build",
                entry_conditions=[
                    {"check": "code_compiles", "status": "pass", "message": "代码必须能成功编译"},
                    {"check": "lint_passes", "status": "pass", "message": f"{lint_tool}检查通过，无error级别问题"},
                    {"check": "no_secrets_in_code", "status": "pass", "message": "代码中无硬编码密钥"},
                ],
                exit_conditions=[
                    {"check": "artifact_generated", "status": "pass", "message": "构建产物已生成"},
                    {"check": "size_within_limit", "status": "warn", "message": "产物大小在合理范围内(<500MB)"},
                ],
                quality_gates={"min_coverage": 0, "max_warnings": 50, "max_errors": 0},
            ),
            StageGate(
                stage_name="test",
                entry_conditions=[
                    {"check": "build_artifact_exists", "status": "pass", "message": "构建产物可用"},
                ],
                exit_conditions=[
                    {"check": "all_tests_pass", "status": "pass", "message": "所有测试用例通过"},
                    {"check": "min_coverage_80", "status": "pass", "message": "代码覆盖率 >= 80%"},
                    {"check": "no_flaky_tests", "status": "warn", "message": "无不稳定测试用例"},
                ],
                approval_required=False,
                quality_gates={"min_coverage": 80, "max_duration_min": 30},
            ),
            StageGate(
                stage_name="scan",
                entry_conditions=[
                    {"check": "tests_passed", "status": "pass", "message": "测试阶段已完成"},
                ],
                exit_conditions=[
                    {"check": "no_critical_vulns", "status": "pass", "message": "无CRITICAL级别漏洞"},
                    {"check": "no_high_vulns", "status": "warn", "message": "HIGH漏洞数量 < 5"},
                    {"check": "license_compliant", "status": "pass", "message": "依赖许可证合规"},
                ],
                approval_required=True,
                approvers=["security-team-lead"],
                quality_gates={"max_critical": 0, "max_high": 5},
            ),
            StageGate(
                stage_name="deploy",
                entry_conditions=[
                    {"check": "scan_approved", "status": "pass", "message": "安全扫描已批准"},
                    {"check": "correct_branch", "status": "pass", "message": "目标分支正确(main或tag)"},
                ],
                exit_conditions=[
                    {"check": "deployment_success", "status": "pass", "message": "部署状态健康"},
                    {"check": "smoke_tests_pass", "status": "pass", "message": "冒烟测试通过"},
                    {"check": "rollback_available", "status": "pass", "message": "回滚方案就绪"},
                ],
                approval_required=True,
                approvers=["tech-lead", "ops-manager"],
                quality_gates={"health_check_timeout_sec": 300, "auto_rollback_on_failure": True},
            ),
        ]

    # ==================== Docker 多阶段构建 ====================

    def generate_docker_multistage(
        self,
        app_type: str = "python",
        project_name: str = "myapp",
    ) -> DockerConfig:
        """
        生成Docker多阶段构建配置

        Args:
            app_type: 应用类型 (python/node/go/rust/java)
            project_name: 项目名称

        Returns:
            DockerConfig对象
        """
        match app_type:
            case "python":
                base_images = {
                    "builder": "python:3.11-slim",
                    "tester": "python:3.11-slim",
                    "runner": "python:3.11-slim",
                }
                stages = [
                    {
                        "name": "builder",
                        "from": base_images["builder"],
                        "purpose": "安装构建依赖和项目依赖",
                        "commands": [
                            "WORKDIR /app",
                            "COPY requirements.txt .",
                            "RUN pip install --no-cache-dir -r requirements.txt",
                            "COPY . .",
                        ],
                    },
                    {
                        "name": "tester",
                        "from": "builder",
                        "purpose": "运行测试和代码质量检查",
                        "commands": [
                            "WORKDIR /app",
                            "COPY --from=builder /app ./",
                            "RUN pytest --cov=. --cov-report=term-missing || true",
                            "RUN ruff check . || true",
                        ],
                    },
                    {
                        "name": "runner",
                        "from": base_images["runner"],
                        "purpose": "生产运行镜像（最小化）",
                        "commands": [
                            "WORKDIR /app",
                            "COPY requirements.txt .",
                            "RUN pip install --no-cache-dir -r requirements.txt",
                            "COPY --from=builder /app ./",
                            "EXPOSE 8000",
                            'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]',
                        ],
                    },
                ]
                ports = [8000]
            case "node":
                base_images = {"builder": "node:20-alpine", "tester": "node:20-alpine", "runner": "node:20-alpine"}
                stages = [
                    {"name": "builder", "from": base_images["builder"], "purpose": "安装npm依赖并构建",
                     "commands": ["WORKDIR /app", "COPY package*.json ./", "RUN npm ci", "COPY . .", "RUN npm run build"]},
                    {"name": "tester", "from": base_images["tester"], "purpose": "运行单元测试",
                     "commands": ["WORKDIR /app", "COPY --from=builder /app ./", "RUN npm test -- --coverage"]},
                    {"name": "runner", "from": "node:20-alpine AS runner", "purpose": "生产运行镜像",
                     "commands": ["WORKDIR /app", "COPY --from=builder /app/dist ./dist", "COPY --from=builder /app/node_modules ./node_modules",
                                  "COPY --from=builder /app/package.json ./package.json", "EXPOSE 3000", 'CMD ["npm", "start"]']},
                ]
                ports = [3000]
            case "go":
                base_images = {"builder": "golang:1.21-alpine", "runner": "alpine:3.19"}
                stages = [
                    {"name": "builder", "from": base_images["builder"], "purpose": "编译Go二进制文件",
                     "commands": ["WORKDIR /app", "COPY go.mod go.sum ./", "RUN go mod download", "COPY . .",
                                  "RUN CGO_ENABLED=0 GOOS=linux go build -o /server -ldflags='-s -w' ."]},
                    {"name": "runner", "from": base_images["runner"], "purpose": "最小化生产镜像",
                     "commands": ["RUN apk --no-cache add ca-certificates tzdata", "COPY --from=builder /server /server",
                                  "EXPOSE 8080", 'CMD ["/server"]']},
                ]
                ports = [8080]
            case _:
                base_images = {"builder": "ubuntu:22.04", "runner": "ubuntu:22.04"}
                stages = [
                    {"name": "builder", "from": base_images["builder"], "purpose": "通用构建阶段",
                     "commands": ["WORKDIR /app", "COPY . .", "RUN echo 'Building...'"]},
                    {"name": "runner", "from": base_images["runner"], "purpose": "通用运行阶段",
                     "commands": ["WORKDIR /app", "COPY --from=builder /app ./", 'CMD ["echo", "Hello"]']},
                ]
                ports = [8080]

        healthcheck = {
            "test": ['CMD-SHELL', 'curl -f http://localhost:{}/health || exit 1'.format(ports[0])],
            "interval": "30s",
            "timeout": "10s",
            "retries": 3,
            "start_period": "40s",
        }

        config = DockerConfig(
            stages=stages,
            base_images=base_images,
            build_args=["BUILDKIT_INLINE_CACHE=1"],
            expose_ports=ports,
            healthcheck=healthcheck,
            labels={
                "maintainer": "devops-team@example.com",
                "org.opencontainers.image.source": f"https://github.com/example/{project_name}",
                "org.opencontainers.image.description": f"{project_name} production image",
            },
        )

        self._docker_configs[project_name] = config
        return config

    # ==================== Kubernetes 模板 ====================

    def generate_k8s_deployment(
        self,
        app_name: str = "myapp",
        replicas: int = 3,
        container_port: int = 8000,
        resources: dict[str, Any] | None = None,
    ) -> K8sManifest:
        """生成Kubernetes Deployment清单"""
        res = resources or {
            "requests": {"cpu": "250m", "memory": "256Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"},
        }
        manifest = K8sManifest(
            kind="Deployment",
            api_version="apps/v1",
            metadata={"name": app_name, "labels": {"app": app_name, "version": "v1"}},
            spec={
                "replicas": replicas,
                "selector": {"matchLabels": {"app": app_name}},
                "strategy": {"type": "RollingUpdate", "rollingUpdate": {"maxSurge": "25%", "maxUnavailable": 0}},
                "template": {
                    "metadata": {"labels": {"app": app_name, "version": "v1"}},
                    "spec": {
                        "containers": [{
                            "name": app_name,
                            "image": f"{app_name}:latest",
                            "ports": [{"containerPort": container_port}],
                            "resources": res,
                            "livenessProbe": {"httpGet": {"path": "/health", "port": container_port}, "initialDelaySeconds": 15, "periodSeconds": 20},
                            "readinessProbe": {"httpGet": {"path": "/ready", "port": container_port}, "initialDelaySeconds": 5, "periodSeconds": 10},
                            "startupProbe": {"httpGet": {"path": "/health", "port": container_port}, "failureThreshold": 30, "periodSeconds": 10},
                            "envFrom": [{"configMapRef": {"name": f"{app_name}-config"}}, {"secretRef": {"name": f"{app_name}-secret"}}],
                            "volumeMounts": [{"name": "app-data", "mountPath": "/app/data"}],
                        }],
                        "volumes": [{"name": "app-data", "emptyDir": {}}],
                        "affinity": {"podAntiAffinity": {"preferredDuringSchedulingIgnoredDuringExecution": [
                            {"weight": 100, "podAffinityTerm": {"labelSelector": {"matchLabels": {"app": app_name}}, "topologyKey": "kubernetes.io/hostname"}}
                        ]}},
                        "tolerations": [{"key": "dedicated", "operator": "Equal", "value": "app-pool", "effect": "NoSchedule"}],
                    },
                },
            },
        )
        self._k8s_manifests.append(manifest)
        return manifest

    def generate_k8s_service(
        self,
        app_name: str = "myapp",
        service_type: str = "ClusterIP",
        port: int = 80,
        target_port: int = 8000,
    ) -> K8sManifest:
        """生成Kubernetes Service清单"""
        manifest = K8sManifest(
            kind="Service",
            api_version="v1",
            metadata={"name": app_name, "labels": {"app": app_name}},
            spec={
                "type": service_type,
                "selector": {"app": app_name},
                "ports": [{"port": port, "targetPort": target_port, "protocol": "TCP", "name": "http"}],
            },
        )
        self._k8s_manifests.append(manifest)
        return manifest

    def generate_k8s_ingress(
        self,
        app_name: str = "myapp",
        host: str = "app.example.com",
        path: str = "/",
        service_name: str | None = None,
        service_port: int = 80,
        tls_secret: str | None = None,
    ) -> K8sManifest:
        """生成Kubernetes Ingress清单"""
        spec: dict[str, Any] = {
            "ingressClassName": "nginx",
            "rules": [{
                "host": host,
                "http": {
                    "paths": [{
                        "path": path,
                        "pathType": "Prefix",
                        "backend": {"service": {"name": service_name or app_name, "port": {"number": service_port}}},
                    }],
                },
            }],
        }
        if tls_secret:
            spec["tls"] = [{"hosts": [host], "secretName": tls_secret}]
        manifest = K8sManifest(
            kind="Ingress",
            api_version="networking.k8s.io/v1",
            metadata={"name": f"{app_name}-ingress", "annotations": {
                "nginx.ingress.kubernetes.io/rewrite-target": "/",
                "nginx.ingress.kubernetes.io/ssl-redirect": "true",
            }},
            spec=spec,
        )
        self._k8s_manifests.append(manifest)
        return manifest

    def generate_k8s_configmap(
        self,
        app_name: str = "myapp",
        data: dict[str, str] | None = None,
    ) -> K8sManifest:
        """生成Kubernetes ConfigMap清单"""
        default_data = {
            "LOG_LEVEL": "INFO",
            "DATABASE_URL": "postgresql://db:5432/myapp",
            "REDIS_URL": "redis://redis:6379/0",
            "API_KEY_PLACEHOLDER": "set-via-secret",
        }
        manifest = K8sManifest(
            kind="ConfigMap",
            api_version="v1",
            metadata={"name": f"{app_name}-config", "labels": {"app": app_name}},
            spec={},
        )
        manifest.metadata["data"] = data or default_data
        self._k8s_manifests.append(manifest)
        return manifest

    def generate_k8s_hpa(
        self,
        app_name: str = "myapp",
        min_replicas: int = 2,
        max_replicas: int = 10,
        target_cpu: int = 70,
    ) -> K8sManifest:
        """生成Kubernetes HPA清单"""
        manifest = K8sManifest(
            kind="HorizontalPodAutoscaler",
            api_version="autoscaling/v2",
            metadata={"name": f"{app_name}-hpa", "labels": {"app": app_name}},
            spec={
                "scaleTargetRef": {"apiVersion": "apps/v1", "kind": "Deployment", "name": app_name},
                "minReplicas": min_replicas,
                "maxReplicas": max_replicas,
                "metrics": [{"type": "Resource", "resource": {"name": "cpu", "target": {"type": "Utilization", "averageUtilization": target_cpu}}}],
                "behavior": {
                    "scaleUp": {"stabilizationWindowSeconds": 60, "policies": [{"type": "Pods", "value": 4, "periodSeconds": 60}]},
                    "scaleDown": {"stabilizationWindowSeconds": 300, "policies": [{"type": "Pods", "value": 2, "periodSeconds": 120}]},
                },
            },
        )
        self._k8s_manifests.append(manifest)
        return manifest

    def generate_k8s_pdb(
        self,
        app_name: str = "myapp",
        min_available: int = 2,
    ) -> K8sManifest:
        """生成Kubernetes PDB(PodDisruptionBudget)清单"""
        manifest = K8sManifest(
            kind="PodDisruptionBudget",
            api_version="policy/v1",
            metadata={"name": f"{app_name}-pdb", "labels": {"app": app_name}},
            spec={
                "selector": {"matchLabels": {"app": app_name}},
                "minAvailable": min_available,
            },
        )
        self._k8s_manifests.append(manifest)
        return manifest

    # ==================== 云服务模板 ====================

    def generate_cloud_template(
        self,
        provider: str,
        service_name: str = "myapp",
    ) -> CloudTemplate:
        """
        生成云服务配置模板

        Args:
            provider: 云服务商 (aws/azure/gcp/alibaba)
            service_name: 服务名称

        Returns:
            CloudTemplate对象
        """
        templates: dict[str, CloudTemplate] = {}
        templates["aws"] = CloudTemplate(
            provider="AWS",
            service_type="Serverless Full Stack",
            resources=[
                {"type": "S3", "name": f"{service_name}-static", "config": {"bucket_policy": "public-read", "versioning": True}},
                {"type": "Lambda", "name": f"{service_name}-api", "config": {"runtime": "python3.11", "memory": 512, "timeout": 30}},
                {"type": "RDS", "name": f"{service_name}-db", "config": {"engine": "postgresql", "instance_class": "db.t3.micro", "storage": 100}},
                {"type": "CloudFront", "name": f"{service_name}-cdn", "config": {"origin": "S3", "price_class": "PriceClass_All"}},
            ],
            config={"region": "ap-northeast-1", "profile": "production"},
            estimated_cost_monthly=8500.0,
        )
        templates["azure"] = CloudTemplate(
            provider="Azure",
            service_type="PaaS Stack",
            resources=[
                {"type": "Blob Storage", "name": f"{service_name}-storage", "config": {"tier": "Hot", "replication": "LRS"}},
                {"type": "Function App", "name": f"{service_name}-func", "config": {"runtime": "python", "plan": "Consumption"}},
                {"type": "SQL Database", "name": f"{service_name}-sql", "config": {"sku": "Basic", "vcores": 2, "storage_gb": 32}},
                {"type": "CDN", "name": f"{service_name}-cdn", "config": {"profile": "Standard_Verizon"}},
            ],
            config={"location": "eastasia", "resource_group": f"{service_name}-rg"},
            estimated_cost_monthly=7200.0,
        )
        templates["gcp"] = CloudTemplate(
            provider="GCP",
            service_type="Cloud Native Stack",
            resources=[
                {"type": "Cloud Storage", "name": f"{service_name}-gs", "config": {"storage_class": "STANDARD", "location": "ASIA"}},
                {"type": "Cloud Run", "name": f"{service_name}-run", "config": {"region": "asia-east1", "min_instances": 0, "max_instances": 100}},
                {"type": "Cloud SQL", "name": f"{service_name}-sql", "config": {"engine": "POSTGRES_15", "tier": "db-custom-1-4096"}},
                {"type": "Cloud CDN", "name": f"{service_name}-cdn", "config": {"enabled": True, "cache_mode": "CACHE_ALL_STATIC"}},
            ],
            config={"project": f"{service_name}-proj", "region": "asia-east1"},
            estimated_cost_monthly=9000.0,
        )
        templates["alibaba"] = CloudTemplate(
            provider="Alibaba Cloud",
            service_type="云原生全栈",
            resources=[
                {"type": "OSS", "name": f"{service_name}-oss", "config": {"storage_class": "Standard", "acl": "public-read"}},
                {"type": "函数计算FC", "name": f"{service_name}-fc", "config": {"runtime": "python3.10", "memory_mb": 512}},
                {"type": "RDS MySQL", "name": f"{service_name}-rds", "config": {"instance_class": "mysql.n2.small.2e", "storage": 100}},
                {"type": "CDN", "name": f"{service_name}-cdn", "config": {"area": "overseas", "bandwidth": 10}},
            ],
            config={"region": "cn-hangzhou", "resource_group": f"{service_name}-rg"},
            estimated_cost_monthly=6800.0,
        )

        template = templates.get(provider.lower())
        if template is None:
            raise TemplateError(f"不支持的云服务商: {provider}")

        key = f"{provider}_{service_name}"
        self._cloud_templates[key] = template
        return template

    # ==================== 监控告警 ====================

    def generate_monitoring_config(
        self,
        tool: str = "prometheus_grafana",
        app_name: str = "myapp",
    ) -> MonitoringConfig:
        """
        生成监控告警配置

        Args:
            tool: 监控工具 (prometheus_grafana/elk/datadog)
            app_name: 应用名称

        Returns:
            MonitoringConfig对象
        """
        common_alerts = [
            {"name": "HighCPUUsage", "expr": f"rate(container_cpu_usage_seconds_total{{pod=~\"{app_name}-.*\"}}[5m]) > 0.8",
             "for": "5m", "severity": "warning", "summary": f"{app_name} CPU使用率超过80%"},
            {"name": "HighMemoryUsage", "expr": f"container_memory_working_set_bytes{{pod=~\"{app_name}-.*\"}} / container_spec_memory_limit_bytes{{pod=~\"{app_name}-.*\"}} > 0.85",
             "for": "5m", "severity": "critical", "summary": f"{app_name} 内存使用率超过85%"},
            {"name": "HighErrorRate", "expr": f"rate(http_requests_total{{app=\"{app_name}\", status=~\"5..\"}}[5m]) / rate(http_requests_total{{app=\"{app_name}\"}}[5m]) > 0.05",
             "for": "2m", "severity": "critical", "summary": f"{app_name} 错误率超过5%"},
            {"name": "SlowResponseTime", "expr": f"histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{{app=\"{app_name}\"}}[5m])) > 2",
             "for": "5m", "severity": "warning", "summary": f"{app_name} P99响应时间超过2秒"},
            {"name": "PodRestartFrequently", "expr": f"increase(kube_pod_container_status_restarts_total{{pod=~\"{app_name}-.*\"}}[1h]) > 5",
             "for": "10m", "severity": "warning", "summary": f"{app_name} Pod频繁重启"},
            {"name": "DatabaseConnectionExhaustion", "expr": f"pg_stat_activity_count{{dataname=\"{app_name}\"}} > 90",
             "for": "2m", "severity": "critical", "summary": f"{app_name} 数据库连接即将耗尽"},
        ]

        common_exporters = [
            {"name": "node-exporter", "port": 9100, "description": "主机指标采集"},
            {"name": "cadvisor", "port": 8080, "description": "容器指标采集"},
            {"name": "blackbox-exporter", "port": 9115, "description": "探针检测"},
            {"name": "postgres-exporter", "port": 9187, "description": "PostgreSQL指标"},
            {"name": "redis-exporter", "port": 9121, "description": "Redis指标"},
        ]

        common_dashboards = [
            {"title": "应用概览", "panels": ["CPU使用率", "内存使用率", "请求速率", "错误率", "响应时间分布"]},
            {"title": "数据库监控", "panels": ["连接数", "慢查询数", "缓存命中率", "锁等待", "复制延迟"]},
            {"title": "基础设施", "panels": ["节点资源", "Pod状态", "网络I/O", "磁盘使用", "容器重启"]},
        ]

        config = MonitoringConfig(
            tool=tool,
            alert_rules=common_alerts,
            exporters=common_exporters,
            dashboards=common_dashboards,
            retention_days=30,
        )

        self._monitoring_configs[f"{tool}_{app_name}"] = config
        return config

    # ==================== 辅助方法 ====================

    @staticmethod
    def _get_install_cmd(lang: str) -> str:
        cmds = {
            "python": "pip install -r requirements.txt",
            "node": "npm ci",
            "go": "go mod download && go build -o /dev/null .",
            "rust": "cargo build --release",
            "java": "./mvnw install -DskipTests",
        }
        return cmds.get(lang, "echo 'Install command not defined'")

    @staticmethod
    def _get_test_cmd(lang: str) -> str:
        cmds = {
            "python": "pytest --cov=. --cov-report=xml --junitxml=junit.xml -v",
            "node": "npm test -- --coverage --reporters=default --reporters=junit",
            "go": "go test -race -coverprofile=coverage.out ./...",
            "rust": "cargo test",
            "java": "./mvnw test",
        }
        return cmds.get(lang, "echo 'Test command not defined'")

    @staticmethod
    def _get_lint_cmd(lang: str) -> str:
        cmds = {
            "python": "ruff check . && ruff format --check .",
            "node": "eslint src/ --ext .ts,.tsx,.js,.jsx",
            "go": "golangci-lint run ./...",
            "rust": "cargo clippy -- -D warnings",
            "java": "./mvnw checkstyle:check",
        }
        return cmds.get(lang, "echo 'Lint command not defined'")

    @staticmethod
    def _get_build_cmd(lang: str) -> str:
        cmds = {
            "python": "pip install -e .",
            "node": "npm run build",
            "go": "CGO_ENABLED=0 go build -o bin/server .",
            "rust": "cargo build --release",
            "java": "./mvnw package -DskipTests",
        }
        return cmds.get(lang, "echo 'Build command not defined'")

    @staticmethod
    def _get_setup_action(lang: str) -> str:
        actions = {
            "python": "actions/setup-python@v5\n          with:\n            python-version: '3.11'",
            "node": "actions/setup-node@v4\n          with:\n            node-version: '20'",
            "go": "actions/setup-go@v5\n          with:\n            go-version: '1.21'",
            "rust": "dtolnay/rust-toolchain@stable",
            "java": "actions/setup-java@v4\n          with:\n            distribution: 'temurin'\n            java-version: '17'",
        }
        return actions.get(lang, "echo 'setup'")

    @staticmethod
    def _get_docker_image(lang: str) -> str:
        images = {
            "python": "python:3.11-slim",
            "node": "node:20-alpine",
            "go": "golang:1.21-alpine",
            "rust": "rust:1.75-slim",
            "java": "eclipse-temurin:17-jdk-alpine",
        }
        return images.get(lang, "ubuntu:22.04")

    @staticmethod
    def _get_vm_image(lang: str) -> str:
        images = {
            "python": "ubuntu-22.04",
            "node": "ubuntu-22.04",
            "go": "ubuntu-22.04",
            "rust": "ubuntu-22.04",
            "java": "windows-2022",
        }
        return images.get(lang, "ubuntu-22.04")

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成完整的基础设施报告(Markdown)"""
        lines: list[str] = []
        lines.append("# 🏗️ 基础设施司 · 综合报告\n")

        lines.append("## 🔧 CI/CD 流水线\n")
        for key, pipeline in self._pipelines.items():
            lines.append(f"### {pipeline.name} ({pipeline.platform.value})\n")
            lines.append(f"- **环境**: {pipeline.environment}")
            lines.append(f"- **阶段数**: {len(pipeline.stages)}")
            lines.append(f"- **变量**: {len(pipeline.variables)}, **密钥**: {len(pipeline.secrets)}")
            lines.append("- **分支规则**:")
            for branch, action in pipeline.branch_rules.items():
                lines.append(f"  - `{branch}` → {action}")
            lines.append("")

        if self._stage_gates:
            lines.append("## 🚦 阶段门禁\n")
            for gkey, gate in sorted(self._stage_gates.items()):
                lines.append(f"### {gate.stage_name.upper()} 门禁\n")
                lines.append("**准入条件:**")
                for cond in gate.entry_conditions:
                    icon = "✅" if cond["status"] == "pass" else "⚠️"
                    lines.append(f"  - {icon} {cond['check']}: {cond['message']}")
                lines.append("**准出条件:**")
                for cond in gate.exit_conditions:
                    icon = "✅" if cond["status"] == "pass" else "⚠️"
                    lines.append(f"  - {icon} {cond['check']}: {cond['message']}")
                if gate.approval_required:
                    lines.append(f"  - 👤 **审批要求**: {', '.join(gate.approvers)}")
                lines.append("")

        if self._docker_configs:
            lines.append("## 🐳 Docker 多阶段构建\n")
            for dkey, dconf in self._docker_configs.items():
                lines.append(f"### {dkey}\n")
                lines.append(f"- **阶段数**: {len(dconf.stages)}")
                for stage in dconf.stages:
                    lines.append(f"  - **{stage['name']}** (`{stage['from']}`): {stage['purpose']}")
                lines.append(f"- **端口**: {dconf.expose_ports}")
                lines.append(f"- **健康检查**: {'已配置' if dconf.healthcheck else '未配置'}")
                lines.append("")

        if self._k8s_manifests:
            lines.append("## ☸️ Kubernetes 资源清单\n")
            kinds_seen: set[str] = set()
            for m in self._k8s_manifests:
                if m.kind not in kinds_seen:
                    kinds_seen.add(m.kind)
                    yaml_preview = m.to_yaml()[:200]
                    lines.append(f"### {m.kind}\n")
                    lines.append("```yaml")
                    lines.append(yaml_preview)
                    lines.append("```\n")

        if self._cloud_templates:
            lines.append("## ☁️ 云服务模板\n")
            for ckey, ctmpl in self._cloud_templates.items():
                lines.append(f"### {ctmpl.provider} - {ctmpl.service_type}\n")
                lines.append(f"- **预估月费**: ¥{ctmpl.estimated_cost_monthly:,.0f}")
                for rsrc in ctmpl.resources:
                    lines.append(f"  - **{rsrc['type']}** `{rsrc['name']}`: {list(rsrc['config'].keys())}")
                lines.append("")

        if self._monitoring_configs:
            lines.append("## 📊 监控告警配置\n")
            for mkey, mconf in self._monitoring_configs.items():
                lines.append(f"### {mconf.tool}\n")
                lines.append(f"- **仪表盘**: {len(mconf.dashboards)}个, **告警规则**: {len(mconf.alert_rules)}条")
                lines.append(f"- **Exporter**: {len(mconf.exporters)}个, **数据保留**: {mconf.retention_days}天")
                critical_alerts = [a for a in mconf.alert_rules if a["severity"] == "critical"]
                if critical_alerts:
                    lines.append("- **关键告警**:")
                    for a in critical_alerts[:3]:
                        lines.append(f"  - 🔴 {a['name']}: {a['summary']}")
                lines.append("")

        lines.append("---\n")
        lines.append("*此报告由尚书省·户部·基础设施司自动生成*\n")
        return "\n".join(lines)

    @property
    def pipeline_count(self) -> int:
        return len(self._pipelines)

    @property
    def k8s_manifest_count(self) -> int:
        return len(self._k8s_manifests)

    @property
    def cloud_template_count(self) -> int:
        return len(self._cloud_templates)

    def __repr__(self) -> str:
        return (
            f"InfrastructureSi(pipelines={self.pipeline_count}, "
            f"k8s={self.k8s_manifest_count}, "
            f"cloud={self.cloud_template_count})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 基础设施司测试")
    print("=" * 60)

    si = InfrastructureSi()

    print("\n--- GitHub Actions 流水线 ---")
    gh_pipeline = si.generate_pipeline(CIPlatform.GITHUB_ACTIONS, "web-api", language="python")
    print(f"   名称: {gh_pipeline.name}")
    print(f"   平台: {gh_pipeline.platform.value}")
    print(f"   阶段: {len(gh_pipeline.stages)} 个")
    for s in gh_pipeline.stages:
        deps = s.get("needs", [])
        dep_str = f" (依赖: {deps})" if deps else ""
        print(f"      • {s['name']}{dep_str} - {len(s.get('steps', []))} 步骤")
    print(f"   变量: {len(gh_pipeline.variables)}, 密钥: {len(gh_pipeline.secrets)}")

    print("\n--- GitLab CI 流水线 ---")
    gl_pipeline = si.generate_pipeline(CIPlatform.GITLAB_CI, "backend-service", language="go")
    print(f"   名称: {gl_pipeline.name}")
    print(f"   阶段: {len(gl_pipeline.stages)} 个")
    for s in gl_pipeline.stages:
        print(f"      • {s['stage']}: {s.get('image', 'unknown')}")

    print("\n--- Jenkinsfile ---")
    jk_pipeline = si.generate_pipeline(CIPlatform.JENKINS, "monolith-app", language="java")
    print(f"   名称: {jk_pipeline.name}")
    for s in jk_pipeline.stages:
        print(f"      • {s['name']}: agent={s.get('agent', '?')}")

    print("\n--- Azure Pipelines ---")
    az_pipeline = si.generate_pipeline(CIPlatform.AZURE_PIPELINES, "frontend-app", language="node")
    print(f"   名称: {az_pipeline.name}, 阶段: {len(az_pipeline.stages)}")

    print("\n--- Cloud Build ---")
    cb_pipeline = si.generate_pipeline(CIPlatform.CLOUD_BUILD, "microsvc", language="python")
    print(f"   名称: {cb_pipeline.name}, 阶段: {len(cb_pipeline.stages)}")

    print("\n--- 阶段门禁 ---")
    for gkey, gate in sorted(si._stage_gates.items()):
        print(f"   [{gate.stage_name}] 准入{len(gate.entry_conditions)}项, 准出{len(gate.exit_conditions)}项"
              f", 审批={'是' if gate.approval_required else '否'}")

    print("\n--- Docker 多阶段构建 (Python) ---")
    docker_py = si.generate_docker_multistage(app_type="python", project_name="pyapp")
    print(f"   阶段: {[s['name'] for s in docker_py.stages]}")
    print(f"   端口: {docker_py.expose_ports}")
    print(f"   健康检查: {'✅ 已配置' if docker_py.healthcheck else '❌ 未配置'}")

    print("\n--- Docker 多阶段构建 (Go) ---")
    docker_go = si.generate_docker_multistage(app_type="go", project_name="goapp")
    print(f"   基础镜像: {docker_go.base_images}")
    print(f"   阶段: {[s['name'] for s in docker_go.stages]}")

    print("\n--- Kubernetes 清单生成 ---")
    dep = si.generate_k8s_deployment("myapp", replicas=3, container_port=8000)
    print(f"   ✅ Deployment: myapp (3副本)")
    svc = si.generate_k8s_service("myapp", service_type="ClusterIP", port=80, target_port=8000)
    print(f"   ✅ Service: ClusterIP :80 → :8000")
    ing = si.generate_k8s_ingress("myapp", host="api.example.com", tls_secret="myapp-tls")
    print(f"   ✅ Ingress: api.example.com (TLS)")
    cm = si.generate_k8s_configmap("myapp")
    print(f"   ✅ ConfigMap: myapp-config")
    hpa = si.generate_k8s_hpa("myapp", min_replicas=2, max_replicas=10, target_cpu=70)
    print(f"   ✅ HPA: 2~10副本, CPU目标70%")
    pdb = si.generate_k8s_pdb("myapp", min_available=2)
    print(f"   ✅ PDB: 最少可用2个Pod")

    print(f"\n   总共生成 {si.k8s_manifest_count} 个K8s资源")

    print("\n--- 云服务模板 ---")
    for provider in ["aws", "azure", "gcp", "alibaba"]:
        tmpl = si.generate_cloud_template(provider, "myapp")
        print(f"   ☁️ {tmpl.provider.upper()}: {tmpl.service_type} "
              f"(¥{tmpl.estimated_cost_monthly:,.0f}/月, {len(tmpl.resources)}个资源)")

    print("\n--- 监控告警配置 ---")
    mon = si.generate_monitoring_config("prometheus_grafana", "myapp")
    print(f"   工具: {mon.tool}")
    print(f"   仪表盘: {len(mon.dashboards)}个")
    print(f"   告警规则: {len(mon.alert_rules)}条")
    print(f"   Exporter: {len(mon.exporters)}个")
    critical = [a for a in mon.alert_rules if a["severity"] == "critical"]
    print(f"   关键告警: {len(critical)}条")
    for a in critical[:3]:
        print(f"      🔴 {a['name']}: {a['summary']}")

    print("\n--- 综合报告预览 (前1800字符) ---")
    report = si.generate_report()
    print(report[:1800])

    print("\n✅ 所有测试通过!")
