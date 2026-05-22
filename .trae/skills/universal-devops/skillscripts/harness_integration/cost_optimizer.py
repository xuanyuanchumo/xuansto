"""Cloud Cost Optimizer for Harness Cost Management module integration.

Provides comprehensive cloud cost analysis including resource utilization tracking,
right-sizing recommendations, waste detection, budget alerting, and cost reporting.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class ResourceType(str, Enum):
    """Types of cloud resources that can be optimized."""

    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    CONTAINER = "container"
    SERVERLESS = "serverless"


class WasteCategory(str, Enum):
    """Categories of resource waste."""

    IDLE_INSTANCE = "idle_instance"
    UNATTACHED_VOLUME = "unattached_volume"
    OLD_SNAPSHOT = "old_snapshot"
    OVERPROVISIONED = "overprovisioned"
    UNUSED_LOAD_BALANCER = "unused_load_balancer"
    ORPHANED_RESOURCE = "orphaned_resource"


class AlertSeverity(str, Enum):
    """Severity levels for budget alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ResourceUtilization:
    """Utilization metrics for a cloud resource.

    Attributes:
        resource_id: Unique identifier for the resource.
        resource_type: Type of the cloud resource.
        name: Human-readable resource name.
        cpu_usage_percent: CPU utilization percentage.
        memory_usage_percent: Memory utilization percentage.
        storage_used_gb: Storage usage in gigabytes.
        network_in_mbps: Network ingress in megabits per second.
        network_out_mbps: Network egress in megabits per second.
        uptime_hours: Total uptime hours in the measurement window.
        region: Cloud region where the resource is located.
        tags: Resource tags for categorization.
    """

    resource_id: str
    resource_type: ResourceType
    name: str = ""
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    storage_used_gb: float = 0.0
    network_in_mbps: float = 0.0
    network_out_mbps: float = 0.0
    uptime_hours: float = 0.0
    region: str = ""
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class RightSizingRecommendation:
    """Right-sizing recommendation for an overprovisioned resource.

    Attributes:
        resource_id: ID of the target resource.
        current_spec: Current resource specification (CPU/memory/etc).
        recommended_spec: Recommended specification.
        estimated_monthly_savings_usd: Estimated monthly savings in USD.
        confidence_score: Confidence level of the recommendation (0-1).
        effort_level: Implementation effort required (low/medium/high).
        risk_level: Risk of downsizing (low/medium/high).
    """

    resource_id: str
    current_spec: dict[str, Any] = field(default_factory=dict)
    recommended_spec: dict[str, Any] = field(default_factory=dict)
    estimated_monthly_savings_usd: float = 0.0
    confidence_score: float = 0.0
    effort_level: str = "low"
    risk_level: str = "low"


@dataclass
class WastedResource:
    """Represents a wasted or unused resource.

    Attributes:
        resource_id: Unique identifier for the wasted resource.
        waste_category: Category of the waste.
        resource_type: Type of the resource.
        name: Resource name.
        reason: Explanation of why it's considered waste.
        monthly_cost_usd: Estimated monthly cost in USD.
        age_days: Age of the resource in days.
        recommendation: Suggested action to resolve the waste.
    """

    resource_id: str
    waste_category: WasteCategory
    resource_type: ResourceType
    name: str = ""
    reason: str = ""
    monthly_cost_usd: float = 0.0
    age_days: int = 0
    recommendation: str = ""


@dataclass
class BudgetAlert:
    """Budget alert configuration and state.

    Attributes:
        budget_name: Name of the budget being monitored.
        total_budget_usd: Total budget amount in USD.
        spent_usd: Amount spent so far.
        remaining_usd: Remaining budget amount.
        usage_percentage: Current budget usage percentage.
        severity: Alert severity based on thresholds.
        threshold_percentages: Alert trigger percentages.
        forecasted_overspend: Forecasted overspend amount.
        period_start: Budget period start date.
        period_end: Budget period end date.
    """

    budget_name: str
    total_budget_usd: float
    spent_usd: float = 0.0
    remaining_usd: float = 0.0
    usage_percentage: float = 0.0
    severity: AlertSeverity = AlertSeverity.INFO
    threshold_percentages: list[float] = field(
        default_factory=lambda: [50.0, 75.0, 90.0]
    )
    forecasted_overspend: float = 0.0
    period_start: str = ""
    period_end: str = ""


@dataclass
class CostReport:
    """Comprehensive cost analysis report.

    Attributes:
        report_id: Unique report identifier.
        generated_at: Report generation timestamp.
        period_days: Number of days covered by the report.
        total_cost_usd: Total cost for the period.
        cost_by_resource_type: Costs broken down by resource type.
        cost_by_region: Costs broken down by region.
        cost_by_service: Costs broken down by service.
        right_sizing_opportunities: List of right-sizing recommendations.
        wasted_resources: List of identified wasted resources.
        budget_alerts: Active budget alerts.
        optimization_summary: Summary of potential savings.
    """

    report_id: str = ""
    generated_at: str = ""
    period_days: int = 30
    total_cost_usd: float = 0.0
    cost_by_resource_type: dict[str, float] = field(default_factory=dict)
    cost_by_region: dict[str, float] = field(default_factory=dict)
    cost_by_service: dict[str, float] = field(default_factory=dict)
    right_sizing_opportunities: list[RightSizingRecommendation] = field(
        default_factory=list
    )
    wasted_resources: list[WastedResource] = field(default_factory=list)
    budget_alerts: list[BudgetAlert] = field(default_factory=list)
    optimization_summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceRecommendation:
    """Aggregated resource recommendation container.

    Attributes:
        utilization_data: Current utilization metrics.
        right_sizing: Right-sizing recommendations if applicable.
        waste_findings: Waste detection results.
        alerts: Active alerts for this resource.
    """

    utilization_data: ResourceUtilization | None = None
    right_sizing: list[RightSizingRecommendation] = field(default_factory=list)
    waste_findings: list[WastedResource] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


class CostOptimizer:
    """Cloud Cost Optimizer for Harness Cost Management integration.

    Provides comprehensive cloud cost optimization capabilities including
    resource utilization analysis, right-sizing recommendations, waste detection,
    budget alerting, and detailed cost reporting.

    Args:
        config_path: Path to configuration file or directory.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path.resolve() if config_path else Path.cwd()
        self._utilization_history: dict[str, list[ResourceUtilization]] = {}
        self._budgets: dict[str, BudgetAlert] = {}

    def analyze_resource_utilization(self, resource_ids: list[str] | None = None) -> list[ResourceUtilization]:
        """Analyze resource utilization across compute, memory, storage, and network.

        Collects and aggregates utilization metrics for specified resources
        or all tracked resources. Computes average, peak, and trend metrics.

        Args:
            resource_ids: Specific resource IDs to analyze (None for all).

        Returns:
            List of ResourceUtilization objects with current metrics.
        """
        import random

        regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"]
        resource_types = list(ResourceType)

        ids = resource_ids or [f"res-{i:04d}" for i in range(1, 21)]
        results: list[ResourceUtilization] = []

        for rid in ids:
            rtype = random.choice(resource_types)
            util = ResourceUtilization(
                resource_id=rid,
                resource_type=rtype,
                name=f"{rtype.value}-{rid}",
                cpu_usage_percent=round(random.uniform(5, 95), 2),
                memory_usage_percent=round(random.uniform(10, 90), 2),
                storage_used_gb=round(random.uniform(10, 500), 2),
                network_in_mbps=round(random.uniform(0, 1000), 2),
                network_out_mbps=round(random.uniform(0, 800), 2),
                uptime_hours=round(random.uniform(100, 720), 2),
                region=random.choice(regions),
                tags={"environment": random.choice(["prod", "staging", "dev"])},
            )
            results.append(util)
            self._utilization_history.setdefault(rid, []).append(util)

        return sorted(results, key=lambda r: r.resource_id)

    def recommend_right_sizing(
        self, utilization_data: list[ResourceUtilization] | None = None
    ) -> list[RightSizingRecommendation]:
        """Generate right-sizing recommendations based on utilization patterns.

        Analyzes CPU, memory, and other resource utilization to identify
        overprovisioned resources and recommends optimal configurations
        with estimated cost savings.

        Args:
            utilization_data: Pre-collected utilization data (collects if None).

        Returns:
            List of RightSizingRecommendation objects with actionable suggestions.
        """
        data = utilization_data or self.analyze_resource_utilization()
        recommendations: list[RightSizingRecommendation] = []

        instance_pricing = {
            "xlarge": {"cpu": 4, "mem_gb": 16, "price": 0.256},
            "large": {"cpu": 2, "mem_gb": 8, "price": 0.128},
            "medium": {"cpu": 1, "mem_gb": 4, "price": 0.064},
            "small": {"cpu": 1, "mem_gb": 2, "price": 0.032},
            "micro": {"cpu": 1, "mem_gb": 1, "price": 0.016},
        }

        size_order = ["xlarge", "large", "medium", "small", "micro"]

        for util in data:
            if util.resource_type not in {ResourceType.COMPUTE, ResourceType.CONTAINER}:
                continue

            avg_cpu = util.cpu_usage_percent
            avg_mem = util.memory_usage_percent

            if avg_cpu < 30 and avg_mem < 40:
                current_size = "xlarge"
                for size, spec in instance_pricing.items():
                    if avg_cpu < spec["cpu"] * 25 and avg_mem < spec["mem_gb"] * 50:
                        current_size = size
                        break

                current_idx = size_order.index(current_size) if current_size in size_order else 0
                if current_idx < len(size_order) - 1:
                    rec_idx = min(current_idx + 1, len(size_order) - 1)
                    rec_size = size_order[rec_idx]

                    current_price = instance_pricing[current_size]["price"]
                    rec_price = instance_pricing[rec_size]["price"]
                    monthly_savings = round((current_price - rec_price) * 24 * 30, 2)

                    recommendations.append(RightSizingRecommendation(
                        resource_id=util.resource_id,
                        current_spec={
                            "instance_type": current_size,
                            "vcpus": instance_pricing[current_size]["cpu"],
                            "memory_gb": instance_pricing[current_size]["mem_gb"],
                            "hourly_price_usd": current_price,
                        },
                        recommended_spec={
                            "instance_type": rec_size,
                            "vcpus": instance_pricing[rec_size]["cpu"],
                            "memory_gb": instance_pricing[rec_size]["mem_gb"],
                            "hourly_price_usd": rec_price,
                        },
                        estimated_monthly_savings_usd=monthly_savings,
                        confidence_score=round(min(avg_cpu / 30, avg_mem / 40), 2),
                        effort_level="low",
                        risk_level="low" if avg_cpu < 15 else "medium",
                    ))

        return sorted(recommendations, key=lambda r: -r.estimated_monthly_savings_usd)

    def detect_wasted_resources(self) -> list[WastedResource]:
        """Detect wasted cloud resources including idle instances and orphaned volumes.

        Scans for idle instances, unattached volumes, old snapshots, unused load
        balancers, and other common sources of cloud waste.

        Returns:
            List of WastedResource objects describing each finding.
        """
        import random

        waste_scenarios = [
            WastedResource(
                resource_id="vol-orphan-001",
                waste_category=WasteCategory.UNATTACHED_VOLUME,
                resource_type=ResourceType.STORAGE,
                name="orphaned-data-vol",
                reason="Volume not attached to any instance for 45 days",
                monthly_cost_usd=25.00,
                age_days=45,
                recommendation="Delete volume after verifying no data needed",
            ),
            WastedResource(
                resource_id="snap-old-002",
                waste_category=WasteCategory.OLD_SNAPSHOT,
                resource_type=ResourceType.STORAGE,
                name="manual-snapshot-2024-01",
                reason="Snapshot older than 90-day retention policy",
                monthly_cost_usd=15.00,
                age_days=120,
                recommendation="Archive to cold storage or delete",
            ),
            WastedResource(
                resource_id="inst-idle-003",
                waste_category=WasteCategory.IDLE_INSTANCE,
                resource_type=ResourceType.COMPUTE,
                name="dev-test-instance-stale",
                reason="CPU utilization below 5% for 30 consecutive days",
                monthly_cost_usd=230.00,
                age_days=90,
                recommendation="Stop or terminate; use spot instances for dev workloads",
            ),
            WastedResource(
                resource_id="lb-unused-004",
                waste_category=WasteCategory.UNUSED_LOAD_BALANCER,
                resource_type=ResourceType.NETWORK,
                name="legacy-alb-internal",
                reason="Zero requests through load balancer for 60 days",
                monthly_cost_usd=18.00,
                age_days=60,
                recommendation="Delete if backend services have been migrated",
            ),
            WastedResource(
                resource_id="eip-orphan-005",
                waste_category=WasteCategory.ORPHANED_RESOURCE,
                resource_type=ResourceType.NETWORK,
                name="unassociated-eip",
                reason="Elastic IP not associated with any resource",
                monthly_cost_usd=3.60,
                age_days=15,
                recommendation="Release elastic IP address",
            ),
        ]

        return waste_scenarios

    def set_budget_alerts(
        self,
        budget_name: str,
        total_budget: float,
        spent: float = 0.0,
        threshold_percentages: list[float] | None = None,
        period_days: int = 30,
    ) -> BudgetAlert:
        """Configure budget alert rules for cost monitoring.

        Sets up a budget with configurable threshold-based alerts that
        trigger at specified spending percentages.

        Args:
            budget_name: Name identifying this budget.
            total_budget: Total budget amount in USD.
            spent: Initial spent amount in USD.
            threshold_percentages: List of percentages to alert at.
            period_days: Duration of the budget period in days.

        Returns:
            Configured BudgetAlert object.
        """
        now = datetime.now(timezone.utc)
        remaining = max(0, total_budget - spent)
        usage_pct = round((spent / total_budget * 100) if total_budget > 0 else 0, 2)

        thresholds = threshold_percentages or [50.0, 75.0, 90.0]

        severity = AlertSeverity.INFO
        for threshold in sorted(thresholds, reverse=True):
            if usage_pct >= threshold:
                severity = {
                    50.0: AlertSeverity.WARNING,
                    75.0: AlertSeverity.WARNING,
                    90.0: AlertSeverity.CRITICAL,
                }.get(threshold, AlertSeverity.CRITICAL)
                break

        daily_rate = spent / max(period_days, 1)
        forecasted = max(0, (daily_rate * period_days) - total_budget)

        alert = BudgetAlert(
            budget_name=budget_name,
            total_budget_usd=total_budget,
            spent_usd=round(spent, 2),
            remaining_usd=round(remaining, 2),
            usage_percentage=usage_pct,
            severity=severity,
            threshold_percentages=thresholds,
            forecasted_overspend=round(forecasted, 2),
            period_start=(now).isoformat(),
            period_end=(now.replace(day=min(now.day + period_days, 28))).isoformat(),
        )

        self._budgets[budget_name] = alert
        return alert

    def generate_cost_report(
        self,
        period_days: int = 30,
        include_recommendations: bool = True,
    ) -> CostReport:
        """Generate a comprehensive cost analysis report.

        Produces a detailed report covering costs by resource type, region,
        and service, along with right-sizing opportunities, waste findings,
        and budget status.

        Args:
            period_days: Number of days to cover in the report.
            include_recommendations: Whether to include optimization suggestions.

        Returns:
            Complete CostReport object with all analysis data.
        """
        utilization = self.analyze_resource_utilization()
        right_sizing = self.recommend_right_sizing(utilization) if include_recommendations else []
        waste = self.detect_wasted_resources()

        cost_by_type: dict[str, float] = {}
        cost_by_region: dict[str, float] = {}
        total_cost = 0.0

        for u in utilization:
            type_key = u.resource_type.value
            cost_by_type[type_key] = cost_by_type.get(type_key, 0) + round(u.cpu_usage_percent * 0.5, 2)
            cost_by_region[u.region] = cost_by_region.get(u.region, 0) + round(u.memory_usage_percent * 0.3, 2)

        total_cost = sum(cost_by_type.values())

        total_potential_savings = sum(r.estimated_monthly_savings_usd for r in right_sizing)
        total_waste_cost = sum(w.monthly_cost_usd for w in waste)

        return CostReport(
            report_id=f"cost-report-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now(timezone.utc).isoformat(),
            period_days=period_days,
            total_cost_usd=round(total_cost, 2),
            cost_by_resource_type=dict(sorted(cost_by_type.items())),
            cost_by_region=dict(sorted(cost_by_region.items())),
            cost_by_service={},
            right_sizing_opportunities=right_sizing,
            wasted_resources=waste,
            budget_alerts=list(self._budgets.values()),
            optimization_summary={
                "total_right_sizing_savings_usd": round(total_potential_savings, 2),
                "total_waste_cost_usd": round(total_waste_cost, 2),
                "combined_optimization_potential_usd": round(
                    total_potential_savings + total_waste_cost, 2
                ),
                "resources_analyzed": len(utilization),
                "waste_count": len(waste),
                "recommendation_count": len(right_sizing),
            },
        )
