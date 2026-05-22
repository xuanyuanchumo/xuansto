"""CD Deployment Manager for Harness CD module integration.

Provides deployment strategy management including canary, blue-green, and rolling
deployments with health checks, auto-rollback, and manifest generation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class DeploymentStrategy(str, Enum):
    """Deployment strategy types supported by the CD manager."""

    CANARY = "canary"
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"


class HealthCheckStatus(str, Enum):
    """Health check result status."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class RollbackReason(str, Enum):
    """Reasons triggering automatic rollback."""

    HEALTH_CHECK_FAILURE = "health_check_failure"
    ERROR_RATE_HIGH = "error_rate_high"
    LATENCY_HIGH = "latency_high"
    MANUAL_TRIGGER = "manual_trigger"
    CRASH_LOOP = "crash_loop"


@dataclass
class CanaryConfig:
    """Canary deployment configuration.

    Attributes:
        initial_percentage: Initial traffic percentage for canary (0-100).
        steps: List of percentage increments for gradual rollout.
        auto_promotion_threshold: Success metric threshold for auto-promotion.
        analysis_duration_seconds: Duration of each canary step analysis.
        metric_endpoints: Endpoints to monitor during canary.
        abort_on_failure: Whether to abort and rollback on failure.
    """

    initial_percentage: int = 5
    steps: list[int] = field(default_factory=lambda: [10, 25, 50, 100])
    auto_promotion_threshold: float = 99.0
    analysis_duration_seconds: int = 300
    metric_endpoints: list[str] = field(default_factory=lambda: ["/health", "/api/status"])
    abort_on_failure: bool = True


@dataclass
class BlueGreenConfig:
    """Blue-green deployment configuration.

    Attributes:
        active_environment: Currently active environment name ('blue' or 'green').
        standby_environment: Standby environment name.
        switch_traffic_mode: Traffic switching method ('dns', 'load_balancer', 'service_mesh').
        health_check_path: Endpoint path for health verification.
        warmup_duration_seconds: Duration to warm up the new environment.
        dns_ttl: TTL for DNS-based traffic switching (seconds).
    """

    active_environment: str = "blue"
    standby_environment: str = "green"
    switch_traffic_mode: str = "load_balancer"
    health_check_path: str = "/healthz"
    warmup_duration_seconds: int = 60
    dns_ttl: int = 30


@dataclass
class RollingConfig:
    """Rolling update deployment configuration.

    Attributes:
        batch_size: Percentage or count of pods to update per batch.
        batch_interval_seconds: Interval between batches in seconds.
        max_unavailable: Maximum unavailable pods during update.
        max_surge: Maximum surge pods allowed during update.
        grace_period_seconds: Grace period before terminating old pod.
        rollback_on_failure: Enable automatic rollback on batch failure.
    """

    batch_size: int = 25
    batch_interval_seconds: int = 30
    max_unavailable: str = "25%"
    max_surge: str = "25%"
    grace_period_seconds: int = 30
    rollback_on_failure: bool = True


@dataclass
class HealthCheckResult:
    """Result of a health check execution.

    Attributes:
        status: Overall health status.
        endpoint: Checked endpoint URL.
        response_time_ms: Response time in milliseconds.
        status_code: HTTP status code received.
        checks_passed: Number of individual checks passed.
        checks_total: Total number of checks performed.
        details: Additional details about the check.
        timestamp: ISO format timestamp of when check was performed.
    """

    status: HealthCheckStatus = HealthCheckStatus.UNKNOWN
    endpoint: str = ""
    response_time_ms: float = 0.0
    status_code: int = 0
    checks_passed: int = 0
    checks_total: int = 0
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class DeploymentPlan:
    """Generated deployment plan.

    Attributes:
        strategy: Selected deployment strategy.
        steps: Ordered list of deployment steps.
        estimated_duration_minutes: Estimated total duration.
        rollback_plan: Plan for rollback if needed.
        config: Strategy-specific configuration.
    """

    strategy: DeploymentStrategy
    steps: list[dict[str, Any]] = field(default_factory=list)
    estimated_duration_minutes: float = 0.0
    rollback_plan: dict[str, Any] = field(default_factory=dict)
    config: CanaryConfig | BlueGreenConfig | RollingConfig | None = None


@dataclass
class DeploymentManifest:
    """Generated deployment manifest.

    Attributes:
        manifest_type: Type of manifest (kubernetes, terraform).
        content: Manifest content as string.
        file_path: Suggested file path for the manifest.
        resources: List of resource definitions.
    """

    manifest_type: str = "kubernetes"
    content: str = ""
    file_path: Path | None = None
    resources: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DeploymentConfig:
    """Configuration for the CD Deployment Manager.

    Attributes:
        project_root: Root directory of the project.
        app_name: Application name for deployment.
        namespace: Kubernetes namespace or deployment target.
        container_image: Container image reference.
        replicas: Number of desired replicas.
        resource_limits: CPU/memory resource limits.
        environment_variables: Environment variables for the deployment.
        strategy: Default deployment strategy.
        canary_config: Canary-specific configuration.
        blue_green_config: Blue-green specific configuration.
        rolling_config: Rolling-specific configuration.
    """

    project_root: Path
    app_name: str = "app"
    namespace: str = "default"
    container_image: str = ""
    replicas: int = 3
    resource_limits: dict[str, str] = field(
        default_factory=lambda: {"cpu": "500m", "memory": "512Mi"}
    )
    environment_variables: dict[str, str] = field(default_factory=dict)
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    canary_config: CanaryConfig = field(default_factory=CanaryConfig)
    blue_green_config: BlueGreenConfig = field(default_factory=BlueGreenConfig)
    rolling_config: RollingConfig = field(default_factory=RollingConfig)


class CDDeploymentManager:
    """CD Deployment Manager for Harness CD integration.

    Manages deployment strategies including canary releases, blue-green deployments,
    and rolling updates with comprehensive health checking, automatic rollback,
    and multi-format manifest generation.

    Args:
        config: Deployment configuration object.
    """

    def __init__(self, config: DeploymentConfig) -> None:
        self._config = config
        self._project_root = config.project_root.resolve()

    def plan_canary_deployment(self) -> DeploymentPlan:
        """Plan a canary deployment with progressive traffic shifting.

        Creates a detailed canary deployment plan with incremental traffic
        percentage increases, metric monitoring at each step, and automatic
        promotion or abort logic based on configured thresholds.

        Returns:
            DeploymentPlan containing the complete canary rollout strategy.
        """
        cfg = self._config.canary_config
        steps: list[dict[str, Any]] = []

        current_pct = cfg.initial_percentage
        all_percentages = sorted(set([cfg.initial_percentage] + cfg.steps))

        for idx, target_pct in enumerate(all_percentages):
            step: dict[str, Any] = {
                "step_number": idx + 1,
                "traffic_percentage": target_pct,
                "duration_seconds": cfg.analysis_duration_seconds,
                "metric_endpoints": cfg.metric_endpoints,
                "auto_promote": target_pct == 100,
            }
            if idx > 0:
                step["traffic_increase"] = target_pct - all_percentages[idx - 1]
            steps.append(step)

        total_duration = len(steps) * cfg.analysis_duration_seconds

        rollback_steps = [
            {
                "step": f"reduce_traffic_to_{pct}%",
                "action": "route_traffic",
                "target_percentage": pct,
            }
            for pct in reversed([cfg.initial_percentage] + cfg.steps[:-1])
        ]
        rollback_steps.append({"step": "full_rollback", "action": "restore_previous_version"})

        return DeploymentPlan(
            strategy=DeploymentStrategy.CANARY,
            steps=steps,
            estimated_duration_minutes=total_duration / 60,
            rollback_plan={
                "trigger_conditions": {
                    "error_rate_threshold": 1.0 - (cfg.auto_promotion_threshold / 100),
                    "abort_on_failure": cfg.abort_on_failure,
                },
                "steps": rollback_steps,
            },
            config=cfg,
        )

    def plan_blue_green_deployment(self) -> DeploymentPlan:
        """Plan a blue-green deployment with traffic switching.

        Creates a deployment plan that deploys to the standby environment,
        performs health checks and warmup, then switches traffic using the
        configured method (DNS, load balancer, or service mesh).

        Returns:
            DeploymentPlan containing the complete blue-green strategy.
        """
        cfg = self._config.blue_green_config
        new_active = cfg.standby_environment
        new_standby = cfg.active_environment

        steps: list[dict[str, Any]] = [
            {
                "step_number": 1,
                "name": "deploy_to_standby",
                "description": f"Deploy new version to {new_active} environment",
                "actions": ["pull_image", "create_pods", "wait_for_ready"],
            },
            {
                "step_number": 2,
                "name": "health_verification",
                "description": f"Run health checks against {new_active}",
                "endpoint": cfg.health_check_path,
                "retries": 3,
            },
            {
                "step_number": 3,
                "name": "warmup_phase",
                "description": f"Allow warmup of {new_active} environment",
                "duration_seconds": cfg.warmup_duration_seconds,
            },
            {
                "step_number": 4,
                "name": "switch_traffic",
                "description": f"Switch traffic from {cfg.active_environment} to {new_active}",
                "method": cfg.switch_traffic_mode,
                "dns_ttl": cfg.dns_ttl if cfg.switch_traffic_mode == "dns" else None,
            },
            {
                "step_number": 5,
                "name": "verify_post_switch",
                "description": "Verify application health after traffic switch",
                "endpoint": cfg.health_check_path,
            },
            {
                "step_number": 6,
                "name": "cleanup_standby",
                "description": f"Optionally clean up {new_standby} environment",
                "optional": True,
            },
        ]

        return DeploymentPlan(
            strategy=DeploymentStrategy.BLUE_GREEN,
            steps=steps,
            estimated_duration_minutes=(
                cfg.warmup_duration_seconds + 120
            ) / 60,
            rollback_plan={
                "trigger_conditions": {"health_check_failure": True},
                "steps": [
                    {"action": "switch_traffic_back", "target": cfg.active_environment},
                    {"action": "scale_down_new", "target": new_active},
                ],
            },
            config=cfg,
        )

    def plan_rolling_deployment(self) -> DeploymentPlan:
        """Plan a rolling update deployment with batched pod replacement.

        Creates a rolling update plan that gradually replaces pods in batches,
        respecting max_unavailable and max_surge constraints, with graceful
        termination and optional automatic rollback on failure.

        Returns:
            DeploymentPlan containing the complete rolling update strategy.
        """
        cfg = self._config.rolling_config
        total_replicas = self._config.replicas
        batch_size = cfg.batch_size

        if isinstance(batch_size, int) and batch_size <= 100:
            pods_per_batch = max(1, round(total_replicas * batch_size / 100))
        else:
            pods_per_batch = max(1, total_replicas // 4)

        num_batches = (total_replicas + pods_per_batch - 1) // pods_per_batch
        steps: list[dict[str, Any]] = []

        for batch_num in range(1, num_batches + 1):
            start_idx = (batch_num - 1) * pods_per_batch
            end_idx = min(batch_num * pods_per_batch, total_replicas)
            pods_in_batch = end_idx - start_idx

            step: dict[str, Any] = {
                "step_number": batch_num,
                "pods_to_update": pods_in_batch,
                "pod_range": f"{start_idx + 1}-{end_idx}/{total_replicas}",
                "max_unavailable": cfg.max_unavailable,
                "max_surge": cfg.max_surge,
                "grace_period_seconds": cfg.grace_period_seconds,
                "wait_between_pods": cfg.batch_interval_seconds,
            }
            steps.append(step)

        total_duration = num_batches * (
            cfg.batch_interval_seconds * pods_per_batch + cfg.grace_period_seconds
        )

        rollback_plan: dict[str, Any] = {
            "trigger_conditions": {
                "batch_failure": cfg.rollback_on_failure,
            },
            "steps": [{"action": "undo_rolling_update", "target": "restore_previous_replica_set"}],
        }

        return DeploymentPlan(
            strategy=DeploymentStrategy.ROLLING,
            steps=steps,
            estimated_duration_minutes=total_duration / 60,
            rollback_plan=rollback_plan,
            config=cfg,
        )

    def execute_health_check(
        self,
        endpoint: str = "",
        timeout_seconds: int = 10,
        retries: int = 3,
    ) -> HealthCheckResult:
        """Execute a health check against the deployed application.

        Performs HTTP health check with configurable timeout and retry logic.
        Checks response status code, response time, and basic connectivity.

        Args:
            endpoint: Health check endpoint URL (uses config default if empty).
            timeout_seconds: Timeout for each attempt in seconds.
            retries: Number of retry attempts on failure.

        Returns:
            HealthCheckResult with detailed check outcome information.
        """
        from datetime import datetime, timezone

        target = endpoint or f"http://localhost:8080{self._config.blue_green_config.health_check_path}"
        passed = 0
        total_checks = 3
        details: dict[str, Any] = {}
        status_code = 0
        response_time = 0.0

        for attempt in range(retries):
            try:
                import urllib.request
                import time

                start = time.monotonic()
                req = urllib.request.Request(target, method="GET")
                req.add_header("User-Agent", "Harness-CD-HealthChecker/1.0")
                with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                    status_code = resp.status
                    response_time = (time.monotonic() - start) * 1000
                    body = resp.read().decode("utf-8", errors="replace")
                    if 200 <= status_code < 300:
                        passed += 1
                        details[f"attempt_{attempt + 1}"] = {
                            "status": "success",
                            "status_code": status_code,
                            "response_time_ms": round(response_time, 2),
                        }
                    else:
                        details[f"attempt_{attempt + 1}"] = {
                            "status": "http_error",
                            "status_code": status_code,
                        }
            except Exception as exc:
                details[f"attempt_{attempt + 1}"] = {
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }

        overall_status = HealthCheckStatus.HEALTHY if passed >= (total_checks + 1) // 2 else HealthCheckStatus.UNHEALTHY
        if 0 < passed < (total_checks + 1) // 2:
            overall_status = HealthCheckStatus.DEGRADED

        return HealthCheckResult(
            status=overall_status,
            endpoint=target,
            response_time_ms=round(response_time, 2),
            status_code=status_code,
            checks_passed=passed,
            checks_total=retries,
            details=details,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def trigger_auto_rollback(
        self,
        reason: RollbackReason = RollbackReason.MANUAL_TRIGGER,
        additional_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Trigger an automatic rollback of the current deployment.

        Initiates rollback procedure based on the specified reason, executing
        the appropriate rollback plan for the current deployment strategy.

        Args:
            reason: Reason for triggering the rollback.
            additional_context: Optional additional context for audit logging.

        Returns:
            Dictionary describing the rollback action taken.
        """
        from datetime import datetime, timezone

        context = additional_context or {}

        match self._config.strategy:
            case DeploymentStrategy.CANARY:
                action = "reduce_canary_traffic_to_zero_and_restore_stable"
                plan = self.plan_canary_deployment().rollback_plan
            case DeploymentStrategy.BLUE_GREEN:
                action = "switch_traffic_back_to_previous_environment"
                plan = self.plan_blue_green_deployment().rollback_plan
            case DeploymentStrategy.ROLLING:
                action = "undo_rolling_update_restore_previous_replicaset"
                plan = self.plan_rolling_deployment().rollback_plan
            case _:
                action = "generic_rollback"
                plan = {}

        rollback_record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "application": self._config.app_name,
            "namespace": self._config.namespace,
            "reason": reason.value,
            "action_taken": action,
            "rollback_plan": plan,
            "context": context,
        }

        return rollback_record

    def generate_deployment_manifest(
        self, manifest_type: str = "kubernetes"
    ) -> DeploymentManifest:
        """Generate deployment manifest for the target platform.

        Produces either a Kubernetes YAML manifest or Terraform configuration
        based on the current deployment configuration and selected strategy.

        Args:
            manifest_type: Target manifest format ('kubernetes' or 'terraform').

        Returns:
            DeploymentManifest with generated content and metadata.
        """
        match manifest_type:
            case "kubernetes":
                content = self._generate_k8s_manifest()
                file_name = f"{self._config.app_name}-deployment.yaml"
            case "terraform":
                content = self._generate_terraform_manifest()
                file_name = f"{self._config.app_name}-deployment.tf"
            case _:
                raise ValueError(f"Unsupported manifest type: {manifest_type}")

        file_path = self._project_root / "deploy" / file_name

        resources = self._extract_resources(content)

        return DeploymentManifest(
            manifest_type=manifest_type,
            content=content,
            file_path=file_path,
            resources=resources,
        )

    def _generate_k8s_manifest(self) -> str:
        cfg = self._config
        labels = {
            "app": cfg.app_name,
            "managed-by": "harness-cd",
            "strategy": cfg.strategy.value,
        }

        deployment_spec: dict[str, Any] = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": cfg.app_name,
                "namespace": cfg.namespace,
                "labels": labels,
            },
            "spec": {
                "replicas": cfg.replicas,
                "selector": {"matchLabels": {"app": cfg.app_name}},
                "template": {
                    "metadata": {"labels": labels},
                    "spec": {
                        "containers": [
                            {
                                "name": cfg.app_name,
                                "image": cfg.container_image or f"{cfg.app_name}:latest",
                                "resources": {
                                    "limits": cfg.resource_limits,
                                    "requests": {
                                        k: str(int(v.rstrip("mMiGi")) // 2) + v[-1:]
                                        if v[:-1].isdigit()
                                        else v
                                        for k, v in cfg.resource_limits.items()
                                    },
                                },
                                "env": [
                                    {"name": k, "value": v}
                                    for k, v in cfg.environment_variables.items()
                                ],
                                "ports": [{"containerPort": 8080}],
                                "livenessProbe": {
                                    "httpGet": {"path": "/healthz", "port": 8080},
                                    "initialDelaySeconds": 15,
                                    "periodSeconds": 10,
                                },
                                "readinessProbe": {
                                    "httpGet": {"path": "/ready", "port": 8080},
                                    "initialDelaySeconds": 5,
                                    "periodSeconds": 5,
                                },
                            }
                        ]
                    },
                },
            },
        }

        match cfg.strategy:
            case DeploymentStrategy.CANARY:
                deployment_spec["spec"]["strategy"] = {
                    "type": "RollingUpdate",
                    "rollingUpdate": cfg.canary_config.__dict__,
                }
            case DeploymentStrategy.BLUE_GREEN:
                deployment_spec["metadata"]["labels"]["environment"] = cfg.blue_green_config.active_environment
            case DeploymentStrategy.ROLLING:
                rcfg = cfg.rolling_config
                deployment_spec["spec"]["strategy"] = {
                    "type": "RollingUpdate",
                    "rollingUpdate": {
                        "maxUnavailable": rcfg.max_unavailable,
                        "maxSurge": rcfg.max_surge,
                    },
                }

        service_spec: dict[str, Any] = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": f"{cfg.app_name}-service",
                "namespace": cfg.namespace,
                "labels": labels,
            },
            "spec": {
                "selector": {"app": cfg.app_name},
                "ports": [
                    {
                        "protocol": "TCP",
                        "port": 80,
                        "targetPort": 8080,
                    }
                ],
                "type": "ClusterIP",
            },
        }

        import yaml

        try:
            deployment_yaml = yaml.dump(deployment_spec, default_flow_style=False, sort_keys=False)
            service_yaml = yaml.dump(service_spec, default_flow_style=False, sort_keys=False)
            return f"---\n{deployment_yaml}---\n{service_yaml}"
        except ImportError:
            return json.dumps([deployment_spec, service_spec], indent=2)

    def _generate_terraform_manifest(self) -> str:
        cfg = self._config
        tf_lines: list[str] = [
            'resource "kubernetes_deployment" "' + cfg.app_name + '" {',
            f'  metadata {{',
            f'    name      = "{cfg.app_name}"',
            f'    namespace = "{cfg.namespace}"',
            f'    labels = {{',
            f'      app         = "{cfg.app_name}"',
            '      managed-by  = "harness-cd"',
            f'      strategy    = "{cfg.strategy.value}"',
            f'    }}',
            f'  }}',
            f'',
            f'  spec {{',
            f'    replicas = {cfg.replicas}',
            f'',
            f'    selector {{',
            f'      match_labels = {{',
            f'        app = "{cfg.app_name}"',
            f'      }}',
            f'    }}',
            f'',
            f'    template {{',
            f'      metadata {{',
            f'        labels = {{',
            f'          app         = "{cfg.app_name}"',
            '          managed-by  = "harness-cd"',
            f'        }}',
            f'      }}',
            f'',
            f'      spec {{',
            f'        container {{',
            f'          name  = "{cfg.app_name}"',
            f'          image = "{cfg.container_image or cfg.app_name + ":latest"}"',
            f'',
            f'          port {{',
            f'            container_port = 8080',
            f'          }}',
            f'',
            f'          resources {{',
            f'            limits = {{',
        ]

        for key, val in cfg.resource_limits.items():
            tf_lines.append(f'              {key} = "{val}"')
        tf_lines.extend([
            f'            }}',
            f'          }}',
            f'',
            f'          liveness_probe {{',
            f'            http_get {{',
            f'              path = "/healthz"',
            f'              port = 8080',
            f'            }}',
            f'          }}',
            f'        }}',
            f'      }}',
            f'    }}',
            f'  }}',
            f'}}',
            f'',
        ])

        return "\n".join(tf_lines)

    def _extract_resources(self, content: str) -> list[dict[str, Any]]:
        try:
            import yaml
            resources: list[dict[str, Any]] = []
            for doc in yaml.safe_load_all(content):
                if doc and isinstance(doc, dict):
                    resources.append({
                        "kind": doc.get("kind", "Unknown"),
                        "name": doc.get("metadata", {}).get("name", "unnamed"),
                        "namespace": doc.get("metadata", {}).get("namespace", ""),
                    })
            return resources
        except Exception:
            return []
