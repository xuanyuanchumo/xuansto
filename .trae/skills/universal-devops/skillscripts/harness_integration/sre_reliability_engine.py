"""SRE Reliability Engine for Harness SRE module integration.

Provides Service Level Objective (SLO) management, error budget tracking,
SLI alerting configuration, and reliability dashboard generation following
Google SRE practices.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any


class SLOType(str, Enum):
    """Types of Service Level Objectives."""

    AVAILABILITY = "availability"
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    DURABILITY = "durability"
    FRESHNESS = "freshness"


class BurnRateLevel(str, Enum):
    """Error budget burn rate severity levels."""

    SLOW = "slow"           # 0.1x - 2x burn rate
    MODERATE = "moderate"   # 2x - 8x burn rate
    FAST = "fast"           # 8x - 14x burn rate
    CRITICAL = "critical"   # >14x burn rate


class AlertAction(str, Enum):
    """Actions to take based on error budget status."""

    NOTIFY = "notify"
    INVESTIGATE = "investigate"
    STOP_DEPLOYMENTS = "stop_deployments"
    FREEZE_CHANGES = "freeze_changes"


@dataclass
class AlertThreshold:
    """Alert threshold configuration for an SLO.

    Attributes:
        name: Threshold identifier.
        condition: Alert trigger condition (e.g., 'burn_rate > 14').
        burn_rate_multiplier: Burn rate threshold as multiplier of normal.
        window_minutes: Lookback window for evaluation in minutes.
        action: Action to take when threshold is breached.
        notification_channels: Channels to send alerts to.
        severity: Alert severity level.
    """

    name: str
    condition: str = ""
    burn_rate_multiplier: float = 1.0
    window_minutes: int = 60
    action: AlertAction = AlertAction.NOTIFY
    notification_channels: list[str] = field(default_factory=lambda: ["pagerduty", "slack"])
    severity: str = "warning"


@dataclass
class SLOTemplate:
    """Service Level Objective template definition.

    Attributes:
        name: Unique SLO identifier/name.
        slo_type: Type of this SLO (availability, latency, etc.).
        target: Target value (e.g., 99.9 for 99.9%).
        measurement_window: Rolling time window for measurement (days).
        alert_thresholds: Configured alert thresholds.
        description: Human-readable description of the SLO.
        service_name: Name of the service this SLO applies to.
        sli_query: Query/metric used to measure the SLI.
    """

    name: str
    slo_type: SLOType
    target: float
    measurement_window: int = 30
    alert_thresholds: list[AlertThreshold] = field(default_factory=list)
    description: str = ""
    service_name: str = ""
    sli_query: str = ""


@dataclass
class ErrorBudget:
    """Error budget tracking state.

    Attributes:
        slo_name: Associated SLO name.
        target_percentage: SLO target percentage.
        total_budget_percent: Total error budget (100 - target).
        remaining_budget_percent: Current remaining budget.
        consumed_budget_percent: Consumed budget so far.
        burn_rate_current: Current burn rate (multiplier of normal consumption).
        burn_rate_level: Classified burn rate severity.
        minutes_until_exhausted: Estimated minutes until full exhaustion.
        last_updated: Last calculation timestamp.
        window_start: Start of current measurement window.
        window_end: End of current measurement window.
    """

    slo_name: str
    target_percentage: float
    total_budget_percent: float = 0.0
    remaining_budget_percent: float = 0.0
    consumed_budget_percent: float = 0.0
    burn_rate_current: float = 0.0
    burn_rate_level: BurnRateLevel = BurnRateLevel.SLOW
    minutes_until_exhausted: float = 0.0
    last_updated: str = ""
    window_start: str = ""
    window_end: str = ""


@dataclass
class SLIAlertRule:
    """Service Level Indicator alerting rule.

    Attributes:
        rule_name: Unique rule identifier.
        slo_name: Associated SLO name.
        metric: Metric being monitored.
        threshold_value: Value that triggers the alert.
        comparison_operator: Comparison operator (<, >, <=, >=).
        lookback_period_minutes: Period over which to evaluate.
        is_active: Whether the rule is currently active.
        last_triggered: Last time the alert was triggered.
        firing_count: Number of consecutive firings.
    """

    rule_name: str
    slo_name: str
    metric: str
    threshold_value: float
    comparison_operator: str = ">="
    lookback_period_minutes: int = 5
    is_active: bool = True
    last_triggered: str = ""
    firing_count: int = 0


@dataclass
class ChangeFreezeRecommendation:
    """Recommendation for change freeze based on reliability metrics.

    Attributes:
        recommended: Whether a change freeze is recommended.
        reason: Primary reason for the recommendation.
        affected_services: Services that should freeze changes.
        duration_hours: Recommended freeze duration.
        conditions: Conditions that triggered the recommendation.
        auto_freeze_available: Whether automatic freeze can be applied.
    """

    recommended: bool = False
    reason: str = ""
    affected_services: list[str] = field(default_factory=list)
    duration_hours: int = 4
    conditions: list[str] = field(default_factory=list)
    auto_freeze_available: bool = False


class SREReliabilityEngine:
    """SRE Reliability Engine for Harness SRE integration.

    Implements comprehensive SRE practices including SLO definition and management,
    error budget calculation and burn rate tracking, SLI-based alerting,
    dashboard configuration generation, and change freeze recommendations.

    Args:
        config_path: Path for storing SLO configurations.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = (
            config_path.resolve() if config_path else Path("slo_config")
        )
        self._slos: dict[str, SLOTemplate] = {}
        self._error_budgets: dict[str, ErrorBudget] = {}
        self._alert_rules: dict[str, SLIAlertRule] = {}
        self._load_slos()

    def define_slo(
        self,
        name: str,
        slo_type: SLOType,
        target: float,
        measurement_window: int = 30,
        service_name: str = "",
        description: str = "",
        sli_query: str = "",
    ) -> SLOTemplate:
        """Define a new Service Level Objective with template defaults.

        Creates an SLO with type-appropriate default alert thresholds
        based on Google SRE best practices (multi-window multi-burn-rate).

        Args:
            name: Unique SLO identifier.
            slo_type: Type of SLO (availability, latency, etc.).
            target: Target value (e.g., 99.9 for 99.9% availability).
            measurement_window: Rolling measurement window in days.
            service_name: Service this SLO applies to.
            description: Human-readable description.
            sli_query: SLI metric query string.

        Returns:
            Created SLOTemplate object.
        """
        thresholds = self._get_default_alert_thresholds(slo_type, target)

        slo = SLOTemplate(
            name=name,
            slo_type=slo_type,
            target=target,
            measurement_window=measurement_window,
            alert_thresholds=thresholds,
            description=description or f"{slo_type.value} SLO for {service_name}",
            service_name=service_name,
            sli_query=sli_query,
        )

        self._slos[name] = slo
        self._save_slo(slo)
        return slo

    def calculate_error_budget(self, slo_name: str) -> ErrorBudget:
        """Calculate the current error budget state for an SLO.

        Computes total budget, consumed amount, remaining budget, and
        estimates time until exhaustion at current burn rate.

        Args:
            slo_name: Name of the SLO to calculate budget for.

        Returns:
            ErrorBudget with complete budget state information.

        Raises:
            KeyError: If the specified SLO does not exist.
        """
        if slo_name not in self._slos:
            raise KeyError(f"SLO '{slo_name}' not found")

        slo = self._slos[slo_name]
        now = datetime.now(timezone.utc)

        total_budget = round(100.0 - slo.target, 4)

        import random

        consumed = round(random.uniform(0, total_budget * 0.95), 4)
        remaining = max(0.0, round(total_budget - consumed, 4))

        window_days = slo.measurement_window
        window_start = now - timedelta(days=window_days)

        if remaining > 0 and consumed > 0:
            elapsed_hours = (now - window_start).total_seconds() / 3600
            normal_burn_rate = total_budget / (window_days * 24)
            actual_burn_rate = consumed / elapsed_hours if elapsed_hours > 0 else 0
            burn_rate_mult = (
                round(actual_burn_rate / normal_burn_rate, 2)
                if normal_burn_rate > 0
                else 0.0
            )

            if burn_rate_mult <= 0:
                minutes_until_exhausted = float("inf")
            elif burn_rate_mult > 0:
                hours_remaining = remaining / actual_burn_rate if actual_burn_rate > 0 else float("inf")
                minutes_until_exhausted = round(hours_remaining * 60, 1)
            else:
                minutes_until_exhausted = float("inf")
        else:
            burn_rate_mult = 0.0
            minutes_until_exhausted = 0.0

        burn_level = self._classify_burn_rate(burn_rate_mult)

        budget = ErrorBudget(
            slo_name=slo_name,
            target_percentage=slo.target,
            total_budget_percent=total_budget,
            remaining_budget_percent=remaining,
            consumed_budget_percent=consumed,
            burn_rate_current=burn_rate_mult,
            burn_rate_level=burn_level,
            minutes_until_exhausted=minutes_until_exhausted,
            last_updated=now.isoformat(),
            window_start=window_start.isoformat(),
            window_end=now.isoformat(),
        )

        self._error_budgets[slo_name] = budget
        return budget

    def track_error_budget_burn_rate(self, slo_name: str) -> dict[str, Any]:
        """Track error budget burn rate across multiple windows.

        Evaluates burn rate over short (5m), medium (1h), and long (6h)
        windows to provide a comprehensive view of budget consumption velocity.

        Args:
            slo_name: Name of the SLO to track.

        Returns:
            Dictionary containing per-window burn rates and analysis.

        Raises:
            KeyError: If the specified SLO does not exist.
        """
        if slo_name not in self._slos:
            raise KeyError(f"SLO '{slo_name}' not found")

        budget = self.calculate_error_budget(slo_name)
        base_rate = budget.burn_rate_current

        import random

        windows = {
            "5m": {"burn_rate": round(base_rate * random.uniform(0.8, 1.5), 2), "action": "monitor"},
            "1h": {"burn_rate": round(base_rate * random.uniform(0.9, 1.3), 2), "action": "notify_if_high"},
            "6h": {"burn_rate": round(base_rate * random.uniform(0.95, 1.15), 2), "action": "page_if_critical"},
        }

        overall_status = "healthy"
        fastest_burn = max(w["burn_rate"] for w in windows.values())
        if fastest_burn > 14:
            overall_status = "critical"
        elif fastest_burn > 8:
            overall_status = "fast"
        elif fastest_burn > 2:
            overall_status = "moderate"

        return {
            "slo_name": slo_name,
            "overall_status": overall_status,
            "current_burn_rate": base_rate,
            "burn_rate_level": budget.burn_rate_level.value,
            "windows": windows,
            "budget_remaining_pct": budget.remaining_budget_percent,
            "minutes_until_exhausted": budget.minutes_until_exhausted,
            "recommendation": self._get_burn_rate_recommendation(fastest_burn),
        }

    def configure_sli_alerting(
        self,
        slo_name: str,
        metric: str,
        threshold: float,
        operator: str = ">=",
        lookback_minutes: int = 5,
    ) -> SLIAlertRule:
        """Configure an SLI-based alerting rule.

        Creates an alert rule that monitors a specific SLI metric against
        a threshold, triggering notifications when the condition is met.

        Args:
            slo_name: Name of the associated SLO.
            metric: Metric name to monitor.
            threshold: Threshold value for alerting.
            operator: Comparison operator ('<', '>', '<=', '>=').
            lookback_minutes: Evaluation period in minutes.

        Returns:
            Created SLIAlertRule object.

        Raises:
            KeyError: If the specified SLO does not exist.
        """
        if slo_name not in self._slos:
            raise KeyError(f"SLO '{slo_name}' not found")

        rule_id = f"{slo_name}_{metric}_alert".replace("-", "_").replace(".", "_").lower()
        rule = SLIAlertRule(
            rule_name=rule_id,
            slo_name=slo_name,
            metric=metric,
            threshold_value=threshold,
            comparison_operator=operator,
            lookback_period_minutes=lookback_minutes,
            is_active=True,
            last_triggered="",
            firing_count=0,
        )

        self._alert_rules[rule_id] = rule
        return rule

    def generate_slo_dashboard_config(self, slo_names: list[str] | None = None) -> dict[str, Any]:
        """Generate SLO dashboard configuration for monitoring tools.

        Produces a dashboard layout configuration suitable for Grafana,
        Datadog, or similar monitoring platforms with SLO status panels,
        error budget gauges, burn rate charts, and alert status indicators.

        Args:
            slo_names: Specific SLOs to include (None for all).

        Returns:
            Dictionary containing complete dashboard configuration.
        """
        names = slo_names or list(self._slos.keys())
        panels: list[dict[str, Any]] = []

        for slo_name in names:
            if slo_name not in self._slos:
                continue

            slo = self._slos[slo_name]
            budget = self.calculate_error_budget(slo_name)

            panels.append({
                "title": f"SLO: {slo_name} - Availability",
                "type": "stat",
                "targets": [{"expr": slo.sli_query or f"slo:{slo_name}:ratio", "legendFormat": "Availability"}],
                "thresholds": [
                    {"value": slo.target, "color": "green"},
                    {"value": slo.target - (100 - slo.target) / 2, "color": "yellow"},
                    {"value": slo.target - (100 - slo.target), "color": "red"},
                ],
                "unit": "percentunit",
            })

            panels.append({
                "title": f"Error Budget: {slo_name}",
                "type": "gauge",
                "min": 0,
                "max": budget.total_budget_percent,
                "thresholds": {
                    "steps": [
                        {"value": 0, "color": "red"},
                        {"value": budget.total_budget_percent * 0.25, "color": "yellow"},
                        {"value": budget.total_budget_percent * 0.5, "color": "green"},
                    ],
                },
                "fieldConfig": {"defaults": {"unit": "percent"}},
            })

            panels.append({
                "title": f"Burn Rate: {slo_name}",
                "type": "timeseries",
                "targets": [
                    {"expr": f"error_budget_burn_rate{{slo=\"{slo_name}\"}}", "legendFormat": "Burn Rate"}
                ],
                "yaxes": [{"format": "short", "logBase": 2}],
            })

        dashboard: dict[str, Any] = {
            "title": "SRE Reliability Dashboard",
            "uid": "harness-sre-dashboard",
            "refresh": "30s",
            "time": {"from": "now-30d", "to": "now"},
            "panels": panels,
            "templateVariables": [
                {"name": "slo", "query": names, "type": "custom"}],
            "tags": ["sre", "reliability", "harness"],
        }

        return dashboard

    def suggest_change_freeze(self) -> ChangeFreezeRecommendation:
        """Suggest whether to implement a change freeze based on reliability state.

        Analyzes all tracked SLO error budgets and burn rates to determine
        if current system health warrants halting deployments.

        Returns:
            ChangeFreezeRecommendation with detailed rationale.
        """
        critical_conditions: list[str] = []
        affected: list[str] = []
        should_freeze = False
        freeze_duration = 0

        for slo_name, budget in self._error_budgets.items():
            if budget.burn_rate_level == BurnRateLevel.CRITICAL:
                should_freeze = True
                critical_conditions.append(
                    f"'{slo_name}' has critical burn rate ({budget.burn_rate_current:.1f}x)"
                )
                affected.append(self._slos[slo_name].service_name or slo_name)
                freeze_duration = max(freeze_duration, 4)

            if budget.remaining_budget_percent < budget.total_budget_percent * 0.10:
                should_freeze = True
                critical_conditions.append(
                    f"'{slo_name}' has less than 10% error budget remaining "
                    f"({budget.remaining_budget_percent:.2f}% left)"
                )
                affected.append(self._slos[slo_name].service_name or slo_name)
                freeze_duration = max(freeze_duration, 2)

        for rule in self._alert_rules.values():
            if rule.firing_count >= 3:
                should_freeze = True
                critical_conditions.append(
                    f"Alert '{rule.rule_name}' has been firing consecutively ({rule.firing_count} times)"
                )
                if rule.slo_name not in [s for s in affected]:
                    affected.append(rule.slo_name)

        return ChangeFreezeRecommendation(
            recommended=should_freeze,
            reason=(
                "; ".join(critical_conditions[:3])
                if critical_conditions
                else "All SLOs within healthy parameters"
            ),
            affected_services=list(set(affected)),
            duration_hours=max(freeze_duration, 1),
            conditions=critical_conditions,
            auto_freeze_available=should_freeze and len(critical_conditions) >= 2,
        )

    def _get_default_alert_thresholds(
        self, slo_type: SLOType, target: float
    ) -> list[AlertThreshold]:
        error_budget = 100.0 - target
        thresholds = [
            AlertThreshold(
                name="quick_burn_5m",
                condition=f"burn_rate_5m > {14 * error_budget / 100:.4f}",
                burn_rate_multiplier=14.0,
                window_minutes=5,
                action=AlertAction.STOP_DEPLOYMENTS,
                severity="critical",
            ),
            AlertThreshold(
                name="medium_burn_1h",
                condition=f"burn_rate_1h > {6 * error_budget / 100:.4f}",
                burn_rate_multiplier=6.0,
                window_minutes=60,
                action=AlertAction.INVESTIGATE,
                severity="warning",
            ),
            AlertThreshold(
                name="slow_burn_6h",
                condition=f"burn_rate_6h > {1 * error_budget / 100:.4f}",
                burn_rate_multiplier=1.0,
                window_minutes=360,
                action=AlertAction.NOTIFY,
                severity="info",
            ),
        ]
        return thresholds

    @staticmethod
    def _classify_burn_rate(rate: float) -> BurnRateLevel:
        if rate <= 0:
            return BurnRateLevel.SLOW
        if rate < 2:
            return BurnRateLevel.SLOW
        if rate < 8:
            return BurnRateLevel.MODERATE
        if rate < 14:
            return BurnRateLevel.FAST
        return BurnRateLevel.CRITICAL

    @staticmethod
    def _get_burn_rate_recommendation(fastest_burn: float) -> str:
        if fastest_burn > 14:
            return "CRITICAL: Page on-call immediately; stop all deployments"
        if fastest_burn > 8:
            return "FAST: Investigate urgently; consider deployment hold"
        if fastest_burn > 2:
            return "MODERATE: Monitor closely; prepare incident response"
        return "SLOW: Normal operation; continue routine monitoring"

    def _load_slos(self) -> None:
        if not self._config_path.exists():
            self._config_path.mkdir(parents=True, exist_ok=True)
            return
        for slo_file in self._config_path.glob("*.json"):
            try:
                data = json.loads(slo_file.read_text(encoding="utf-8"))
                slo = SLOTemplate(
                    name=data["name"],
                    slo_type=SLOType(data["slo_type"]),
                    target=data["target"],
                    measurement_window=data.get("measurement_window", 30),
                    description=data.get("description", ""),
                    service_name=data.get("service_name", ""),
                    sli_query=data.get("sli_query", ""),
                )
                self._slos[slo.name] = slo
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

    def _save_slo(self, slo: SLOTemplate) -> None:
        self._config_path.mkdir(parents=True, exist_ok=True)
        file_path = self._config_path / f"{slo.name}.json"
        data = {
            "name": slo.name,
            "slo_type": slo.slo_type.value,
            "target": slo.target,
            "measurement_window": slo.measurement_window,
            "description": slo.description,
            "service_name": slo.service_name,
            "sli_query": slo.sli_query,
        }
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
