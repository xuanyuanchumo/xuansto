# 基础设施司 自主操作指南 (Autonomous Operation Guide)

## 概述

基础设施司（Infrastructure Si）是尚书省·户部下属四司之一，负责**CI/CD 流水线的自主演化与基础设施即代码（IaC）的全生命周期管理**。本司核心使命：将软件交付流水线从手动操作演进至智能化自治阶段，实现构建、测试、安全扫描、部署的全链路自动化。

### 定位

- **上级机构**：尚书省 · 户部（Hubu）
- **同级司署**：环境配置司、依赖管理司、资源优化司
- **核心能力域**：多平台 CI/CD、流水线成熟度评估、K8s 清单生成、监控栈配置、Pipeline as Code
- **自主等级**：L3（条件自主）— 可在预定义模板和规则框架内独立演化流水线

## 核心原则

1. **流水线即代码（PaC）**：所有 CI/CD 配置必须以代码形式版本化管理，禁止通过 UI 手动修改
2. **门禁驱动质量**：每个阶段必须设置明确的通过/失败标准，自动化决策替代人工判断
3. **渐进式成熟度**：遵循 L1→L2→L3→L4→L5 成熟度模型，每次升级需验证当前级别稳定
4. **可观测性内置**：流水线自身必须产出度量数据（耗时、成功率、失败原因分布）
5. **安全左移**：安全扫描尽可能前置到最早阶段，越早发现修复成本越低

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 流水线成熟度评估模型

本司采用 5 级成熟度模型评估当前 CI/CD 能力水平：

```
┌──────────────────────────────────────────────────────────────────┐
│                    CI/CD 成熟度模型 (Infrastructure Maturity)     │
├─────┬────────────────────────┬───────────────────────────────────┤
│ 级别 │ 名称                   │ 特征描述                          │
├─────┼────────────────────────┼───────────────────────────────────┤
│ L1  │ 手动 (Manual)          │ 手动构建、手动测试、手动部署        │
│     │                       │ 无自动化，完全依赖个人经验         │
├─────┼────────────────────────┼───────────────────────────────────┤
│ L2  │ 自动化 (Automated)     │ 基础 CI 自动化                    │
│     │                       │ 自动编译+单元测试，部署仍为手动     │
├─────┼────────────────────────┼───────────────────────────────────┤
│ L3  │ 优化 (Optimized)       │ CD 自动化 + 安全门禁              │
│     │                       │ 自动部署到 staging，安全扫描集成    │
├─────┼────────────────────────┼───────────────────────────────────┤
│ L4  │ 度量 (Measured)        │ 全流程可观测                      │
│     │                       │ DORA 指标采集，部署频率/MTTR 可量化│
├─────┼────────────────────────┼───────────────────────────────────┤
│ L5  │ 智能 (Intelligent)     │ 自主演化 + AIOps                  │
│     │                       │ AI 辅助决策，流水线自优化           │
└─────┴────────────────────────┴───────────────────────────────────┘
```

**成熟度评估检查清单**：

```python
@dataclass
class MaturityAssessment:
    current_level: int
    scores: dict[str, int]       # 各维度得分 0-100
    gaps: list[dict]             # 差距项
    next_level_requirements: list[str]
    recommended_actions: list[str]
    estimated_effort: str

MATURITY_CRITERIA = {
    "L1_L2": {
        "source_control": "代码托管在 Git 且有分支策略",
        "automated_build": "存在可重复执行的构建脚本",
        "unit_tests": "单元测试可在 CI 中自动运行",
        "artifact_management": "构建产物有版本化管理",
    },
    "L2_L3": {
        "automated_deploy_staging": "可自动部署到 staging 环境",
        "integration_tests": "集成测试自动化",
        "security_scanning": "基础 SAST/DAST 扫描",
        "environment_parity": "dev/staging/prod 环境一致性",
        "infrastructure_as_code": "基础设施配置已代码化",
    },
    "L3_L4": {
        "automated_deploy_prod": "生产环境支持一键部署（含审批）",
        "dora_metrics": "采集部署频率/变更前置时间/MTTR/变更失败率",
        "feature_flags": "支持 Feature Toggle 发布",
        "canary_deployment": "支持金丝雀/蓝绿部署",
        "rollback_automation": "一键回滚机制",
    },
    "L4_L5": {
        "ai_assisted_review": "AI 辅助 Code Review",
        "self_healing_pipeline": "流水线故障自愈能力",
        "predictive_scaling": "基于历史数据的预测性扩缩容",
        "chaos_engineering": "混沌工程常态化",
        "compliance_as_code": "合规策略即代码",
    }
}

def assess_pipeline_maturity(project_config: dict) -> MaturityAssessment:
    """
    对项目进行 CI/CD 成熟度评估
    返回当前等级、各维度得分、差距分析和改进建议
    """
    scores = {}
    gaps = []

    # 逐维度评分
    for dimension, criteria in MATURITY_CRITERIA.items():
        dim_score = 0
        total_criteria = len(criteria)
        met_criteria = 0

        for criterion_name, criterion_desc in criteria.items():
            is_met = check_criterion(project_config, criterion_name)
            if is_met:
                met_criteria += 1
            else:
                gaps.append({
                    "dimension": dimension,
                    "criterion": criterion_name,
                    "description": criterion_desc,
                    "priority": get_priority(dimension, criterion_name)
                })

        dim_score = int(met_criteria / total_criteria * 100) if total_criteria > 0 else 0
        scores[dimension] = dim_score

    # 确定当前等级
    avg_l1l2 = (scores.get("L1_L2", 0))
    avg_l2l3 = (scores.get("L2_L3", 0))
    avg_l3l4 = (scores.get("L3_L4", 0))
    avg_l4l5 = (scores.get("L4_L5", 0))

    if avg_l1l2 < 70:
        level = 1
    elif avg_l2l3 < 60:
        level = 2
    elif avg_l3l4 < 50:
        level = 3
    elif avg_l4l5 < 40:
        level = 4
    else:
        level = 5

    return MaturityAssessment(
        current_level=level,
        scores=scores,
        gaps=sorted(gaps, key=lambda g: g["priority"]),
        next_level_requirements=get_next_level_reqs(level),
        recommended_actions=prioritize_actions(gaps),
        estimated_effort=estimate_effort(level)
    )
```

#### 1.2 多平台 CI/CD 配置检测

本司支持 5 大 CI/CD 平台的配置自主管理：

| 平台 | 配置文件 | 特点 | 适用场景 |
|------|---------|------|---------|
| **GitHub Actions** | `.github/workflows/*.yml` | 生态丰富，Marketplace 插件多 | 开源项目 / GitHub 托管 |
| **GitLab CI** | `.gitlab-ci.yml` | 内置 Docker/Cache/K8s 集成好 | 企业自建 GitLab |
| **Jenkins** | `Jenkinsfile` | 高度可定制，插件生态最大 | 复杂混合环境 |
| **Azure Pipelines** | `azure-pipelines.yml` | 与 Azure 服务深度集成 | Azure 云原生 |
| **Cloud Build** | `cloudbuild.yaml` | GCP 原生，Serverless 构建 | Google Cloud 项目 |

**平台检测脚本**：

```bash
#!/bin/bash
# detect_ci_platform.sh — 自动检测项目中使用的 CI/CD 平台
set -euo pipefail

detect_platforms() {
    local platforms=()

    if [[ -f ".github/workflows" ]] && ls .github/workflows/*.yml &>/dev/null; then
        platforms+=("GitHub Actions")
        echo "[DETECTED] GitHub Actions:"
        for wf in .github/workflows/*.yml; do
            echo "  - $(basename $wf)"
        done
    fi

    if [[ -f ".gitlab-ci.yml" ]]; then
        platforms+=("GitLab CI")
        echo "[DETECTED] GitLab CI: .gitlab-ci.yml"
    fi

    if find . -maxdepth 2 -name "Jenkinsfile" -o -name "Jenkinsfile.*" 2>/dev/null | head -1 | grep -q .; then
        platforms+=("Jenkins")
        echo "[DETECTED] Jenkins: $(find . -maxdepth 2 -name 'Jenkinsfile*')"
    fi

    if [[ -f "azure-pipelines.yml" ]]; then
        platforms+=("Azure Pipelines")
        echo "[DETECTED] Azure Pipelines: azure-pipelines.yml"
    fi

    if [[ -f "cloudbuild.yaml" || f "cloudbuild.json" ]]; then
        platforms+=("Google Cloud Build")
        echo "[DETECTED] Cloud Build: cloudbuild.yaml"
    fi

    if [[ ${#platforms[@]} -eq 0 ]]; then
        echo "[NOTICE] 未检测到任何 CI/CD 配置文件"
        echo "[SUGGEST] 推荐初始化 GitHub Actions 或 GitLab CI"
    else
        echo ""
        echo "========================================="
        echo "检测到 ${#platforms[@]} 个 CI/CD 平台配置"
    fi
}

detect_platforms
```

#### 1.3 K8s 资源清单现状扫描

```python
"""
K8s 清单扫描器 — 分析现有 Kubernetes 资源配置的完整性和最佳实践
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class K8sManifestAuditResult:
    file_path: str
    kind: str
    name: str
    namespace: str
    issues: list[dict] = field(default_factory=list)
    score: int = 100              # 最佳实践符合度 0-100
    recommendations: list[str] = field(default_factory=list)

REQUIRED_FIELDS_BY_KIND = {
    "Deployment": {
        "required": ["metadata.name", "spec.replicas", "spec.selector.matchLabels",
                     "spec.template.metadata.labels", "spec.template.spec.containers"],
        "recommended": [
            ("spec.strategy.type", "RollingUpdate"),
            ("spec.template.spec.terminationGracePeriodSeconds", 30),
            ("spec.template.spec.containers[0].resources.requests.cpu", True),
            ("spec.template.spec.containers[0].resources.limits.memory", True),
            ("spec.template.spec.containers[0].livenessProbe", True),
            ("spec.template.spec.containers[0].readinessProbe", True),
            ("spec.template.spec.securityContext.runAsNonRoot", True),
            ("spec.template.spec.securityContext.fsGroup", True),
        ]
    },
    "Service": {
        "required": ["metadata.name", "spec.selector", "spec.ports"],
        "recommended": [
            ("spec.type", "ClusterIP"),  # 默认应使用 ClusterIP
        ]
    },
    "ConfigMap": {
        "required": ["metadata.name", "data"],
        "recommended": []
    },
    "Secret": {
        "required": ["metadata.name"],
        "recommended": [
            ("type", "Opaque"),
        ]
    },
    "Ingress": {
        "required": ["metadata.name", "spec.rules"],
        "recommended": [
            ("spec.tls", True),  # 生产环境建议启用 TLS
            ("metadata.annotations.nginx.ingress.kubernetes.io/ssl-redirect", "true"),
        ]
    },
    "HPA": {
        "required": ["metadata.name", "spec.scaleTargetRef", "spec.minReplicas", "spec.maxReplicas"],
        "recommended": [
            ("spec.metrics", True),  # 应明确指定指标
        ]
    }
}

def audit_k8s_manifest(manifest_path: Path) -> list[K8sManifestAuditResult]:
    """审计单个或多个 K8s YAML 文件"""
    results = []
    
    with open(manifest_path) as f:
        docs = list(yaml.safe_load_all(f))

    for doc in docs:
        if not doc:
            continue
        
        kind = doc.get('kind', 'Unknown')
        name = doc.get('metadata', {}).get('name', 'unnamed')
        namespace = doc.get('metadata', {}).get('namespace', 'default')
        
        result = K8sManifestAuditResult(
            file_path=str(manifest_path),
            kind=kind,
            name=name,
            namespace=namespace
        )

        criteria = REQUIRED_FIELDS_BY_KIND.get(kind)
        if not criteria:
            result.recommendations.append(f"未知的 Kind '{kind}'，无法进行深度审计")
            results.append(result)
            continue

        # 检查必填字段
        for field in criteria['required']:
            if not _field_exists(doc, field):
                result.issues.append({
                    "severity": "CRITICAL",
                    "type": "missing_required",
                    "field": field,
                    "message": f"缺少必填字段: {field}"
                })
                result.score -= 15

        # 检查推荐字段
        for field, expected in criteria['recommended']:
            actual_value = _get_field(doc, field)
            if isinstance(expected, bool):
                if expected and actual_value is None:
                    result.issues.append({
                        "severity": "WARNING",
                        "type": "missing_recommended",
                        "field": field,
                        "message": f"推荐添加字段: {field}"
                    })
                    result.score -= 5
            elif actual_value != expected:
                result.issues.append({
                    "severity": "INFO",
                    "type": "best_practice",
                    "field": field,
                    "message": f"推荐值: {expected}, 当前值: {actual_value}"
                })
                result.score -= 2

        result.score = max(0, min(100, result.score))

        # 根据问题生成具体建议
        for issue in result.issues:
            if issue['severity'] == 'CRITICAL':
                result.recommendations.append(
                    f"[紧急] {issue['message']}"
                )

        results.append(result)

    return results
```

### 阶段二：决策（Decide）

#### 2.1 流水线演化路径规划

```
当前状态 ──→ 目标状态 决策树

START
  │
  ├─ 当前成熟度？
  │   ├─ L1 → 目标 L2（自动化入门）
  │   │   ├── 项目语言是什么？
  │   │   │   ├── Python → 推荐 GitHub Actions + pytest
  │   │   │   ├── Node.js → 推荐 GitHub Actions + jest
  │   │   │   ├── Java → 推荐 GitLab CI + Maven
  │   │   │   └── Go → 推荐 GitHub Actions + go test
  │   │   └── 生成初始化 Pipeline 模板
  │   │
  │   ├─ L2 → 目标 L3（优化阶段）
  │   │   ├── 是否有 K8s 环境？
  │   │   │   ├── YES → 增加 deploy stage + kubectl apply
  │   │   │   └── NO → 建议 docker-compose 或 PaaS 部署
  │   │   ├── 安全要求？
  │   │   │   ├── HIGH → 集成 Trivy/Snyk/Checkov
  │   │   │   └── LOW → 基础 lint + 依赖扫描即可
  │   │   └── 生成 L3 升级方案
  │   │
  │   ├─ L3 → 目标 L4（度量阶段）
  │   │   ├── 集成 DORA 指标采集
  │   │   ├── 添加 Prometheus/Grafana 监控
  │   │   └── 实现金丝雀发布能力
  │   │
  │   └─ L4 → 目标 L5（智能阶段）
  │       ├── 引入 AI Code Review
  │       ├── 实现流水线自愈
  │       └── 混沌工程集成
  │
  └─ END
```

#### 2.2 四阶段门禁策略

本司采用 4 层门禁体系确保交付质量：

```
┌────────────────────────────────────────────────────────────────┐
│                    4阶段交付门禁 (Quality Gates)                 │
│                                                                │
│  Code Commit                                                  │
│      │                                                        │
│      ▼                                                        │
│  ┌─────────┐                                                 │
│  │  BUILD   │ ◄── 门禁1: 构建门禁                              │
│  │  Gate    │     ✓ 编译零错误                                  │
│  └────┬─────┘     ✓ 产物大小合理                               │
│       │           ✓ 无硬编码密钥                               │
│       ▼                                                    │
│  ┌─────────┐                                                 │
│  │  TEST    │ ◄── 门禁2: 测试门禁                              │
│  │  Gate    │     ✓ 单元测试覆盖率 ≥ 80%                       │
│  └────┬─────┘     ✓ 集成测试全通过                             │
│       │           ✓ E2E 关键路径全绿                           │
│       ▼                                                    │
│  ┌─────────┐                                                 │
│  │ SECURITY │ ◄── 门禁3: 安全门禁                              │
│  │  Gate    │     ✓ SAST 无 CRITICAL/HIGH                     │
│  └────┬─────┘     ✓ DAST 无已知漏洞                            │
│       │           ✓ 依赖漏洞 ≤ MEDIUM                          │
│       ▼                                                    │
│  ┌─────────┐                                                 │
│  │ DEPLOY   │ ◄── 门禁4: 部署门禁                              │
│  │  Gate    │     ✓ 基础设施漂移检测通过                        │
│  └────┬─────┘     ✓ Canary 健康检查通过                        │
│       │           ✓ 回滚预案就绪                               │
│       ▼                                                    │
│  Production ✅                                                │
└────────────────────────────────────────────────────────────────┘
```

**门禁详细规则**：

```yaml
# quality_gates.yaml — 门禁规则配置
quality_gates:
  build_gate:
    enabled: true
    rules:
      - id: "BG-001"
        name: "编译成功"
        check: "exit_code == 0"
        severity: blocking
      - id: "BG-002"
        name: "无硬编码密钥"
        check: "no_secrets_in_code()"
        severity: blocking
        tool: "gitleaks or trufflehog"
      - id: "BG-003"
        name: "产物大小限制"
        check: "artifact_size_mb < 500"
        severity: warning
        threshold: 500

  test_gate:
    enabled: true
    rules:
      - id: "TG-001"
        name: "单元测试通过率"
        check: "pass_rate >= 100%"
        severity: blocking
      - id: "TG-002"
        name: "单元测试覆盖率"
        check: "line_coverage >= 80%"
        severity: blocking
        tool: "jest --coverage / pytest-cov"
      - id: "TG-003"
        name: "集成测试通过率"
        check: "pass_rate >= 100%"
        severity: blocking
      - id: "TG-004"
        name: "E2E 测试关键路径"
        check: "critical_paths_all_green"
        severity: blocking

  security_gate:
    enabled: true
    rules:
      - id: "SG-001"
        name: "SAST 扫描"
        check: "no_critical_or_high_findings"
        severity: blocking
        tool: "SonarQube / Semgrep / CodeQL"
      - id: "SG-002"
        name: "依赖漏洞扫描"
        check: "max_severity <= MEDIUM"
        severity: blocking
        tool: "Snyk / Dependabot / Trivy"
      - id: "SG-003"
        name: "容器镜像扫描"
        check: "no_critical_vulnerabilities"
        severity: blocking
        tool: "Trivy / Grype"
      - id: "SG-004"
        name: "IaC 安全扫描"
        check: "no_critical_misconfigurations"
        severity: warning
        tool: "Checkov / tfsec"

  deploy_gate:
    enabled: true
    rules:
      - id: "DG-001"
        name: "基础设施一致性"
        check: "no_drift_detected"
        severity: blocking
        tool: "tfplan diff / driftctl"
      - id: "DG-002"
        name: "Canary 健康检查"
        check: "canary_error_rate < 1% AND latency_p99 < 500ms"
        severity: blocking
        observation_window: "5min"
      - id: "DG-003"
        name: "回滚预案就绪"
        check: "previous_version_rollback_tested"
        severity: blocking
      - id: "DG-004"
        name: "审批完成"
        check: "approval_count >= required_approvers"
        severity: blocking
        environments:
          production: { required_approvers: 2 }
          staging: { required_approvers: 1 }
          development: { required_approvers: 0 }
```

### 阶段三：执行（Execute）

#### 3.1 K8s 清单生成器

```python
"""
K8s 资源清单生成器 — 根据 AppSpec 自动生成完整的 K8s Deployment/Service/
ConfigMap/Secret/Ingress/HPA 清单
"""

from jinja2 import Template
from dataclasses import dataclass
from typing import Optional

@dataclass
class AppSpecification:
    app_name: str
    container_image: str
    replicas: int = 3
    container_port: int = 8080
    cpu_request: str = "100m"
    cpu_limit: str = "500m"
    memory_request: str = "128Mi"
    memory_limit: str = "512Mi"
    env_vars: dict = None
    secrets: list[str] = None
    config_mounts: list[dict] = None
    health_check_path: str = "/health"
    ingress_host: str = ""
    tls_secret: str = ""
    hpa_min: int = 2
    hpa_max: int = 10
    hpa_target_cpu: int = 70
    namespace: str = "default"
    service_type: str = "ClusterIP"

    def __post_init__(self):
        self.env_vars = self.env_vars or {}
        self.secrets = self.secrets or []
        self.config_mounts = self.config_mounts or []

K8S_DEPLOYMENT_TEMPLATE = Template("""\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ app_name }}
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
    version: v1
spec:
  replicas: {{ replicas }}
  selector:
    matchLabels:
      app: {{ app_name }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: {{ app_name }}
        version: v1
    spec:
      terminationGracePeriodSeconds: 30
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: {{ app_name }}
        image: {{ container_image }}
        ports:
        - containerPort: {{ container_port }}
          protocol: TCP
        resources:
          requests:
            cpu: "{{ cpu_request }}"
            memory: "{{ memory_request }}"
          limits:
            cpu: "{{ cpu_limit }}"
            memory: "{{ memory_limit }}"
        livenessProbe:
          httpGet:
            path: {{ health_check_path }}
            port: {{ container_port }}
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: {{ health_check_path }}
            port: {{ container_port }}
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        env:
{% for key, value in env_vars.items() %}
        - name: {{ key }}
          value: "{{ value }}"
{% endfor %}
{% for secret in secrets %}
        - name: {{ secret }}
          valueFrom:
            secretKeyRef:
              name: {{ app_name }}-secrets
              key: {{ secret }}
{% endfor %}
{% for mount in config_mounts %}
        volumeMounts:
        - name: {{ mount.name }}
          mountPath: {{ mount.mountPath }}
          readOnly: true
{% endfor %}
      volumes:
{% for mount in config_mounts %}
      - name: {{ mount.name }}
        configMap:
          name: {{ mount.configMapName }}
{% endfor %}
""")

K8S_SERVICE_TEMPLATE = Template("""\
---
apiVersion: v1
kind: Service
metadata:
  name: {{ app_name }}
  namespace: {{ namespace }}
  labels:
    app: {{ app_name }}
spec:
  type: {{ service_type }}
  selector:
    app: {{ app_name }}
  ports:
  - port: 80
    targetPort: {{ container_port }}
    protocol: TCP
""")

K8S_INGRESS_TEMPLATE = Template("""\
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ app_name }}
  namespace: {{ namespace }}
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
{% if tls_secret %}
spec:
  tls:
  - hosts:
    - {{ ingress_host }}
    secretName: {{ tls_secret }}
  rules:
  - host: {{ ingress_host }}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {{ app_name }}
            port:
              number: 80
{% endif %}
""")

K8S_HPA_TEMPLATE = Template("""\
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ app_name }}-hpa
  namespace: {{ namespace }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ app_name }}
  minReplicas: {{ hpa_min }}
  maxReplicas: {{ hpa_max }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ hpa_target_cpu }}
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
""")

def generate_k8s_manifests(spec: AppSpecification) -> str:
    """生成完整的 K8s 资源清单"""
    manifests = []
    manifests.append(K8S_DEPLOYMENT_TEMPLATE.render(
        app_name=spec.app_name,
        namespace=spec.namespace,
        container_image=spec.container_image,
        replicas=spec.replicas,
        container_port=spec.container_port,
        cpu_request=spec.cpu_request,
        cpu_limit=spec.cpu_limit,
        memory_request=spec.memory_request,
        memory_limit=spec.memory_limit,
        env_vars=spec.env_vars,
        secrets=spec.secrets,
        config_mounts=spec.config_mounts,
        health_check_path=spec.health_check_path
    ))
    manifests.append(K8S_SERVICE_TEMPLATE.render(
        app_name=spec.app_name,
        namespace=spec.namespace,
        service_type=spec.service_type,
        container_port=spec.container_port
    ))

    if spec.ingress_host:
        manifests.append(K8S_INGRESS_TEMPLATE.render(
            app_name=spec.app_name,
            namespace=spec.namespace,
            ingress_host=spec.ingress_host,
            tls_secret=spec.tls_secret
        ))

    manifests.append(K8S_HPA_TEMPLATE.render(
        app_name=spec.app_name,
        namespace=spec.namespace,
        hpa_min=spec.hpa_min,
        hpa_max=spec.hpa_max,
        hpa_target_cpu=spec.hpa_target_cpu
    ))

    return "\n".join(manifests)


# 使用示例
if __name__ == "__main__":
    app_spec = AppSpecification(
        app_name="order-service",
        container_image="registry.example.com/order-service:v1.2.3",
        replicas=3,
        container_port=8080,
        env_vars={"LOG_LEVEL": "INFO", "DB_HOST": "postgres-service"},
        secrets=["DB_PASSWORD", "API_KEY"],
        ingress_host="orders.example.com",
        tls_secret="orders-tls-secret",
        namespace="production"
    )

    yaml_output = generate_k8s_manifests(app_spec)
    print(yaml_output)
```

#### 3.2 Prometheus + Grafana 监控栈配置

```yaml
# monitoring-stack.yaml — Prometheus + Grafana 监控栈完整配置
# 由基础设施司自主生成和管理

apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s
      external_labels:
        cluster: 'production'
        environment: 'prod'

    rule_files:
      - "/etc/prometheus/rules/*.yml"

    alerting:
      alertmanagers:
        - static_configs:
            targets: ['alertmanager:9093']

    scrape_configs:
      # === 应用服务发现 ===
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
            action: keep
            regex: true
          - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
            action: replace
            target_label: __address__
            regex: (.+)
            replacement: ${1}:${2}

      # === K8s 组件 ===
      - job_name: 'kubelet'
        scheme: https
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
        kubernetes_sd_configs:
          - role: node
        relabel_configs:
          - action: labelmap
            regex: __meta_kubernetes_node_label_(.+)

      # === Node Exporter ===
      - job_name: 'node-exporter'
        kubernetes_sd_configs:
          - role: endpoints
        relabel_configs:
          - source_labels: [__meta_kubernetes_endpoints_name]
            action: keep
            regex: node-exporter

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-alert-rules
  namespace: monitoring
data:
  alerts.yml: |
    groups:
      - name: application_alerts
        rules:
          - alert: HighErrorRate
            expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
            for: 5m
            labels:
              severity: critical
            annotations:
              summary: "错误率超过 5%"
              description: "{{ $labels.instance }} 错误率: {{ $value | humanizePercentage }}"

          - alert: HighLatencyP99
            expr: histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "P99 延迟超过 1秒"
              description: "{{ $labels.instance }} P99延迟: {{ $value }}s"

          - alert: PodCrashLooping
            expr: kube_pod_container_status_restarts_total > 5
            for: 10m
            labels:
              severity: critical
            annotations:
              summary: "Pod 反复重启"
              description: "Pod {{ $labels.pod }} 在 10 分钟内重启超过 5 次"

          - alert: MemoryPressure
            expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.15
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "节点内存压力"
              description: "{{ $labels.instance }} 可用内存低于 15%"

          - alert: DiskSpaceLow
            expr: (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"}) < 0.15
            for: 10m
            labels:
              severity: warning
            annotations:
              summary: "磁盘空间不足"
              description: "{{ $labels.instance }} {{ $labels.mountpoint }} 使用率超过 85%"

      - name: pipeline_alerts
        rules:
          - alert: PipelineFailureRateHigh
            expr: increase(github_actions_workflow_runs{conclusion="failure"}[1h]) / increase(github_actions_workflow_runs[1h]) > 0.2
            for: 30m
            labels:
              severity: warning
            annotations:
              summary: "CI 流水线失败率过高"
              description: "过去1小时流水线失败率: {{ $value | humanizePercentage }}"

          - alert: DeployFrequencyDrop
            expr: changes(deploy_timestamp[24h]) < 1
            for: 48h
            labels:
              severity: info
            annotations:
              summary: "部署频率异常下降"
              description: "过去48小时无生产部署记录"
```

#### 3.3 多平台 CI/CD 流水线模板

##### GitHub Actions 完整模板

```yaml
# .github/workflows/ci-cd.yml — GitHub Actions 完整流水线
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ===== 阶段1: BUILD =====
  build:
    name: 🔨 Build & Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up language runtime
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Lint (flake8 + mypy)
        run: |
          flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
          mypy src/ --strict

      - name: Secret scanning (gitleaks)
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Build artifact
        run: python -m build

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  # ===== 阶段2: TEST =====
  test:
    name: 🧪 Test Suite
    runs-on: ubuntu-latest
    needs: build
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with:
          name: dist

      - name: Unit tests with coverage
        run: |
          pip install -e ".[test]"
          pytest tests/unit/ -v --cov=src/ --cov-report=xml --cov-fail-under=80
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379/0

      - name: Integration tests
        run: pytest tests/integration/ -v --junitxml=junit.xml

      - name: Upload coverage report
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  # ===== 阶段3: SECURITY =====
  security:
    name: 🔒 Security Scan
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      - name: Dependency audit (pip-audit)
        run: |
          pip install pip-audit
          pip-audit --format=json > dependency-audit.json

      - name: SAST (Semgrep)
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/security-audit
            p/secrets

  # ===== 阶段4: DEPLOY =====
  deploy-staging:
    name: 🚀 Deploy to Staging
    runs-on: ubuntu-latest
    needs: security
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG

      - name: Deploy to EKS (kubectl)
        run: |
          aws eks update-kubeconfig --name staging-cluster
          kubectl set image deployment/app app=$ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG -n staging
          kubectl rollout status deployment/app -n staging --timeout=300s

  deploy-production:
    name: 🏭 Deploy to Production
    runs-on: ubuntu-latest
    needs: security
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Approval gate
        run: echo "✅ Production deployment approved by workflow trigger"

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_TO_ASSUME }}
          aws-region: ap-northeast-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG

      - name: Deploy to production with canary
        run: |
          aws eks update-kubeconfig --name prod-cluster
          # 更新镜像
          kubectl set image deployment/app app=$ECR_REGISTRY/$IMAGE_NAME:$IMAGE_TAG -n production
          # 等待滚动更新完成
          kubectl rollout status deployment/app -n production --timeout=600s
          # 运行健康验证
          ./scripts/post-deploy-health-check.sh production

      - name: Notify deployment success
        if: success()
        run: |
          curl -X POST -H 'Content-type: application/json' \
            --data '{"text":"🚀 Production deploy successful: '"$GITHUB_SHA"'"}' \
            ${{ secrets.SLACK_WEBHOOK }}
```

### 阶段四：验证（Verify）

#### 4.1 流水线健康度验证矩阵

| 验证维度 | 检查方法 | 通过标准 | 失败处理 |
|---------|---------|---------|---------|
| 构建成功率 | 近30天构建统计 | ≥ 95% | 分析失败根因并修复 |
| 平均构建时长 | 构建耗时中位数 | < 阈值（按项目定） | 优化缓存/并行化 |
| 测试覆盖率 | coverage 报告 | ≥ 80%（新增代码≥90%） | 补充测试用例 |
| 安全扫描结果 | SAST/DAST/SCA 报告 | 0 Critical/High | 修复后重新提交 |
| 部署成功率 | 近30次部署统计 | ≥ 98% | 检查部署脚本和环境 |
| MTTR（平均恢复时间）| 从失败到修复的时间 | < 1h（P0/P1） | 优化回滚和告警 |
| DORA 变更前置时间 | commit→deploy 时长 | < 1天（目标） | 减少人工审批环节 |
| 回滚成功率 | 回滚操作成功率 | 100% | 改进回滚脚本 |

#### 4.2 DORA 指标采集配置

```yaml
# dora-metrics-config.yaml — DORA 四大指标采集配置
dora_metrics:
  deployment_frequency:
    query: |
      count_increase(github_actions_workflow_runs{
        name="Deploy to Production",
        conclusion="success"
      }[30d])
    targets:
      elite: "每日多次"
      high: "每周一次到每月一次"
      medium: "每月到半年一次"
      low: "半年以上一次"

  lead_time_for_changes:
    query: |
      histogram_quantile(0.50,
        sum(rate(commit_to_deploy_duration_seconds_bucket[30d])) by (le)
      )
    targets:
      elite: "< 1小时"
      high: "< 1天"
      medium: "< 1周"
      low: "< 1月"

  change_failure_rate:
    query: |
      (
        count_increase(github_actions_workflow_runs{
          conclusion="failure",
          name="Deploy to Production"
        }[30d])
        /
        count_increase(github_actions_workflow_runs{
          name="Deploy to Production"
        }[30d])
      ) * 100
    targets:
      elite: "< 5%"
      high: "< 15%"
      medium: "< 25%
      low: "> 25%"

  mean_time_to_recovery:
    query: |
      histogram_quantile(0.50,
        sum rate(incident_resolve_duration_seconds_bucket[30d]) by (le)
      )
    targets:
      elite: "< 1小时"
      high: "< 1天"
      medium: "< 1周"
      low: "> 1周"
```

### 阶段五：记录（Record）

#### 5.1 流水线事件记录格式

```json
{
  "event_id": "INFR-20260406-001",
  "timestamp": "2026-04-06T16:00:00Z",
  "si_department": "infrastructure_si",
  "operation_type": "pipeline_evolution",
  "trigger_mode": "scheduled_maturity_assessment",
  "pipeline_details": {
    "platform": "GitHub Actions",
    "current_maturity_level": 3,
    "target_maturity_level": 4,
    "workflow_files": [".github/workflows/ci-cd.yml"]
  },
  "changes_applied": [
    {
      "change_type": "add_stage",
      "stage_name": "security_scan",
      "tools_added": ["Trivy", "Semgrep", "pip-audit"],
      "gate_rules": ["SG-001", "SG-002", "SG-003"]
    },
    {
      "change_type": "add_monitoring",
      "component": "prometheus_grafana_stack",
      "dashboards_created": ["application-overview", "pipeline-health", "infra-resources"]
    }
  ],
  "quality_gates_status": {
    "build_gate": "PASS",
    "test_gate": "PASS",
    "security_gate": "PASS",
    "deploy_gate": "APPROVAL_PENDING"
  },
  "dora_metrics_snapshot": {
    "deployment_frequency_per_day": 2.3,
    "lead_time_hours_median": 4.5,
    "change_failure_rate_pct": 3.2,
    "mttr_minutes_median": 28
  },
  "verification_status": "STAGING_VALIDATION_IN_PROGRESS",
  "rollback_available": true
}
```

## 典型自主场景

### 场景1：从 L2 到 L3 的流水线升级

**背景**：某 Python 项目目前只有基础的 GitHub Actions（build + unit test），需要升级到包含自动部署和安全扫描的 L3 级别。

**自主处理流程**：

1. **感知**：成熟度评估确认当前 L2（score: L1_L2=85%, L2_L3=35%）
2. **分析差距**：
   - ❌ 缺少 staging 自动部署
   - ❌ 缺少 SAST/DAST 安全扫描
   - ❌ 缺少 IaC 管理
   - ❌ 缺少环境一致性保障
3. **决策**：差距在可控范围内 → **批准执行 L3 升级**
4. **执行**：
   - 添加 `deploy-staging` job（kubectl apply 到 EKS staging）
   - 集成 Trivy（容器扫描）、Semgrep（SAST）、pip-audit（依赖扫描）
   - 生成初始 Helm Chart 作为 IaC 入口
   - 添加 4 层 Quality Gate 规则
5. **验证**：staging 部署成功，安全扫描 0 Critical
6. **记录**：升级事件日志 + DORA 基线快照

### 场景2：新微服务的 K8s 清单自动生成

**背景**：团队新建了 `payment-service` 微服务，需要快速生成完整的 K8s 部署清单。

**自主处理流程**：

1. **感知**：检测到新的 Dockerfile 和 `app.py`
2. **信息收集**：
   - 从 Dockerfile 提取基础镜像、暴露端口
   - 从 requirements.txt 判断技术栈
   - 从 README 提取环境变量需求
3. **生成清单**：
   - Deployment（3副本 + liveness/readiness probe + resource limits）
   - Service（ClusterIP :80→:8080）
   - ConfigMap（应用配置）
   - Secret（数据库密码等敏感值占位）
   - Ingress（payment.example.com + TLS）
   - HPA（2-10 副本，CPU 目标 70%）
4. **审计**：运行清单审计工具，score=92/100
5. **提交 PR**：自动创建 PR 包含生成的清单文件
6. **审查**：开发者审核后合并

### 场景3：Prometheus + Grafana 监控栈初始化

**背景**：新集群尚未配置监控，需要快速搭建完整的可观测性平台。

**自主处理流程**：

1. **感知**：集群中无 monitoring namespace 和 Prometheus Deployment
2. **决策**：监控是生产必备设施 → **批准自动安装**
3. **执行**：
   - 创建 monitoring namespace + RBAC
   - 部署 Prometheus（StatefulSet + PVC 持久化存储）
   - 部署 AlertManager（告警路由 + Slack/邮件通知）
   - 部署 Grafana（持久化 + 预置仪表盘）
   - 配置 NodeExporter + cAdvisor + kube-state-metrics
   - 导入预定义告警规则（CPU/Memory/Disk/Latency/ErrorRate）
   - 导入预置 Grafana 仪表盘（集群概览、Pod 详情、流量拓扑）
4. **验证**：
   - Prometheus `/targets` 所有 target UP
   - Grafana 可访问且仪表盘有数据
   - AlertManager 告警通道测试消息送达
5. **记录**：监控栈安装报告 + 默认凭证轮换提醒

### 场景4：流水线性能优化

**背景**：CI 流水平均耗时 25 分钟，团队希望压缩到 15 分钟以内。

**自主处理流程**：

1. **感知**：分析近 100 次 pipeline 运行数据
2. **瓶颈定位**：
   - `pip install` 占 8min（无缓存）→ 启用 actions/cache
   - 串行执行 test job → 拆分为 unit/integration/e2e 并行
   - Docker build 每次 from-scratch → 启用 layer caching
   - security scan 在最后串行 → 移至并行阶段
3. **决策**：所有优化均为低风险改动 → **批准执行**
4. **执行**：
   - 添加 pip cache action（预计节省 6min）
   - 将 test 拆分为 3 个并行 job（预计节省 5min）
   - 启用 Docker BuildKit cache（预计节省 3min）
   - security scan 并行化（预计节省 2min）
5. **验证**：优化后平均耗时降至 13.5min（↓46%）
6. **记录**：优化前后对比报告 + 节省的 CI minutes 费用估算

## 决策框架

### 流水线变更权限矩阵

| 变更类型 | 自主执行 | 需审批 | 禁止 |
|---------|---------|--------|------|
| 新增非破坏性 step | ✅ | - | - |
| 修改超时/重试参数 | ✅ | - | - |
| 添加新的 lint/test 规则 | ✅ | - | - |
| 修改部署目标环境 | - | ✅ | - |
| 修改安全门禁阈值 | - | ✅ | - |
| 修改生产部署流程 | - | ✅ | - |
| 删除现有门禁 | - | ✅ | - |
| 修改 secrets 权限 | - | - | ❌ |
| 修改 runner 类型（self-hosted ↔ cloud）| - | ✅ | - |

### 成熟度升级审批要求

| 目标级别 | 所需审批 | 前置条件 |
|---------|---------|---------|
| L1 → L2 | 无需审批 | 有 Git 仓库 |
| L2 → L3 | Tech Lead 审批 | L2 稳定运行 ≥ 2 周 |
| L3 → L4 | 团队负责人 + DevOps 负责人 | L3 稳定运行 ≥ 1 月 |
| L4 → L5 | 架构委员会审批 | L4 稳定运行 ≥ 3 月 + 安全评审 |

## 安全与治理

### 流水线安全基线

- **Runner 安全**：使用 ephemeral runner，禁用持久化存储
- **Secret 管理**：所有敏感值通过 GitHub Secrets/AWS Parameter Store 注入，禁止明文写入 YAML
- **权限最小化**：workflow token 使用最小所需权限（`permissions` 字段显式声明）
- **Pin 版本**：所有 Actions/第三方工具必须 pin 到 SHA 或精确版本号
- **供应链安全**：启用 Dependabot + GHAS（GitHub Advanced Security）

### 合规审计追踪

- 所有流水线变更必须关联 Issue/PR
- 每次生产部署保留完整审计线索（who/what/when/why）
- Security Gate 的扫描原始报告保留 ≥ 90 天
- 符合 SOC2 Type II 控制要求

## 协作关系

### 向上汇报（户部）

| 报送内容 | 频率 | 格式 |
|---------|------|------|
| 流水线健康日报 | 每日 | 成功率 + 失败列表 |
| DORA 指标周报 | 每周 | 四大指标趋势图 |
| 成熟度评估季报 | 每季度 | 等级变化 + 改进路线图 |
| 安全态势月报 | 每月 | 漏洞趋势 + 修复进展 |

### 平级协作

| 协作对象 | 协作内容 | 接口协议 |
|---------|---------|---------|
| **环境配置司** | 流水线中的环境注入与配置同步 | ConfigMap 模板 + 环境变量 schema |
| **依赖管理司** | 流水线中的依赖安装与安全扫描步骤 | lock 文件 + audit 结果 |
| **资源优化司** | 流水线中的性能基准测试与资源影响评估 | benchmark 结果 + cost report |

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| **DevOps Automator** | Agency Engineering | CI/CD 流水线执行 | 作为户部司流水线的核心执行引擎，负责实际运行构建、测试、部署等 Pipeline 步骤，并将执行结果反馈给户部司进行成熟度评估 |
| **SRE** | Agency Reliability | 可靠性保障与事件响应 | 为户部司的 CI/CD 流水线添加 SLO 保障层，负责流水线自身的可靠性（构建成功率、部署MTTR）以及生产环境的事件响应 |
| **Incident Response Commander** | Agency Incident | 事件指挥与恢复领导 | 当流水线故障或部署引发生产事故时接管指挥权，协调各方进行快速恢复，并为户部司提供事后改进输入 |

### Agent 协作工作流

1. **Pipeline 定义与演化**: 户部司基于成熟度评估生成/演化 Pipeline 定义（YAML） → DevOps Automator 在目标 CI 平台（GitHub Actions/GitLab CI/Jenkins）上创建或更新 Pipeline 配置
2. **4 层门禁执行**: 户部司定义 Build/Test/Security/Deploy 四层 Quality Gate 规则 → DevOps Automator 在每个 Gate 点严格执行 → 任一门禁失败则阻断并向户部司上报失败详情
3. **流水线可观测接入**: SRE 为 Pipeline 配置 DORA 指标采集（部署频率、前置时间、变更失败率、MTTR）→ 数据汇入户部司的成熟度评估系统 → 驱动 L1→L5 的渐进式升级
4. **部署事件响应**: 生产部署触发后 → SRE 监控 Golden Signal（延迟、错误率、吞吐量、饱和度）→ 若检测到异常立即通知 Incident Response Commander → IRC 启动应急流程（通报→诊断→修复→恢复→复盘）
5. **混沌工程验证**: 户部司在 L4→L5 升级路径中引入混沌实验 → SRE 设计实验场景（Pod 杀死、网络延迟、磁盘满）→ DevOps Automator 在 Staging 环境执行 → IRC 评估系统韧性 → 结果反馈户部司调整 Pipeline 策略
6. **持续改进闭环**: IRC 主持事后复盘（Post-mortem）→ 产出改进 Action Item → 户部司将 Action Item 转化为 Pipeline 演化需求（如增加新的 Gate Rule、优化超时配置）→ DevOps Automator 落地实施

### 典型协作场景

- **场景一 - L2→L3 全自动升级**: 户部司评估某项目当前 L2（score: 65%）→ 生成 L3 升级方案（添加 deploy stage + Trivy 安全扫描 + K8s 部署 step）→ DevOps Automator 在 GitHub Actions 中创建完整的 4-stage Pipeline → SRE 配置 Prometheus 采集部署指标 → 首次 staging 部署成功 → 户部司确认升级至 L3
- **场景二 - 部署事故快速恢复**: 生产部署后 P99 延迟突增 800ms，错误率飙升至 5% → SRE 30 秒内检测到异常 → IRC 接管指挥：①立即触发回滚（DevOps Automator 执行 rollback pipeline，MTTR=3min）②并行诊断根因（新版本引入了 N+1 查询）③修复并重新部署 → 全程 18 分钟恢复 → IRC 输出 Post-mortem → 户部司据此在 Pipeline 中增加了 DB 慢查询检测 Gate
- **场景三 - 混沌工程常态化**: 户部司推动项目进入 L4→L5 过渡期 → SRE 设计混沌实验矩阵（每周一个场景：网络分区、CPU 风暴、内存泄漏、DNS 故障、证书过期）→ DevOps Automator 通过 Harness Chaos 执行实验 → IRC 评估每次实验的系统表现 → 3 个月后项目 Chaos 工程覆盖率达 85% → 户部司批准进入 L5 候选

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **Harness CI/CD (Pipeline)**: **核心对接模块** — 户部司的流水线成熟度模型和 4 层门禁体系直接基于 Harness Pipeline 能力构建，充分利用其多阶段工作流、Approval Gate、Custom Step 和 Matrix Strategy 等特性
- **Harness SRE (Incident Management & Service Guard)**: 将户部司的异常恢复策略框架与 Harness 的 Incident Management、Runbook、Service Guard（虚拟哨兵）深度整合，实现从检测→响应→恢复→学习的完整闭环

### 实践指南

1. **Pipeline 模板库建设**: 将户部司的 L1-L5 各级别 Pipeline 定义封装为 Harness Pipeline Template（或 GitSync管理的 YAML 模板），新项目可通过 `harness create project --template=L3-python` 一键初始化对应成熟度的完整流水线
2. **Incident Response 自动化**: 将户部司的级联失败恢复策略（隔离→稳定→评估→修复→渐进恢复→复盘）编码为 Harness Runbook —— 当 Service Guard 检测到部署回归时自动触发对应 Runbook，IRC 可在 Harness 统一的 Incident 界面中指挥整个恢复过程

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改CI/CD流水线配置、K8s清单、监控配置时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/ci-cd.yml",
      agent_id="基础设施司",
      lock_type=LockType.EXCLUSIVE,
      priority=9,
      timeout=180.0
  )
  ```
- **读锁**：读取流水线状态、构建日志、部署历史时申请读锁（高频查询场景）
- **释放锁**：流水线变更和部署操作完成后立即释放锁，避免阻塞其他司的状态查询

#### 终端会话池使用
- 从MARC终端会话池获取会话执行CI/CD命令、kubectl操作、构建脚本
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（完整CI/CD流水线可能耗时较长）

#### 并发安全注意事项
- 流水线配置文件是多司共享的核心资产，写入时必须独占锁保护
- K8s清单变更需原子性操作，避免出现部分应用导致集群状态不一致
- 死锁预防：按固定顺序申请锁（先锁Pipeline配置→再锁K8s清单→最后锁监控配置）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 流水线生成提示词、K8s清单生成提示词、门禁规则定义提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许基础设施操作（CI/CD、IaC、部署），禁止修改业务逻辑代码 | 全自动 |
| **规则校验层** | 输出格式：YAML Pipeline配置、K8s YAML清单、JSON DORA指标 | 全自动 |
| **兜底恢复层** | 部署失败时自动回滚至上一版本或切换到蓝绿部署的另一环境 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于Pipeline设计、K8s清单编写、监控配置）
   - 示例：直接编辑YAML流水线文件、手动调整K8s Deployment配置、编写Prometheus告警规则
   - 优势：精确控制基础设施细节、可逐步验证配置正确性、可随时回滚变更

2. 🥈 **规划脚本操作**（适用于批量环境初始化、周期性健康检查）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查CI/CD资源配额和运行时间配额
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的流水线演化
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限紧急生产部署回滚、容器重启等极少数场景）
   - ⚠️ 必须预演影响范围（基础设施变更影响全局服务可用性）
   - ⚠️ 生产环境操作需逐条确认并获得关键方Ack
   - 推荐使用PS7适配器转换kubectl/docker命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- 文件操作：使用原生PowerShell Cmdlet处理YAML/JSON配置（ConvertFrom-Yaml/Yaml配置）
- K8s操作：kubectl命令在PS7中原生可用（用于部署、滚动更新、扩缩容）
- Docker操作：docker命令用于镜像构建、容器管理和网络配置
- Git操作：git命令用于IaC配置版本管理
- 编码：确保所有输出 UTF-8 无 BOM（Pipeline日志和审计记录）

### 与其他司的协作接口

- 上游依赖：环境配置司（获取环境配置注入）、依赖管理司（获取依赖安装步骤）
- 下游输出：协同调度司（推送部署状态和依赖拓扑）、兵部测试司（提供测试环境）
- 数据交换格式：YAML / JSON / Markdown（统一UTF-8无BOM）
