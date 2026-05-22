from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func
from .base import Base


class QualityAlertRecord(Base):
    __tablename__ = "quality_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(100), unique=True, index=True, nullable=False)
    rule_id = Column(String(100), index=True, nullable=False)
    metric_type = Column(String(50), index=True, nullable=False)
    severity = Column(String(20), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    current_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    source = Column(String(100), nullable=False)
    fingerprint = Column(String(255), index=True, nullable=False)
    acknowledged = Column(Boolean, default=False, index=True)
    resolved = Column(Boolean, default=False, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    notification_channels = Column(JSON, default=list)
    alert_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "rule_id": self.rule_id,
            "metric_type": self.metric_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "source": self.source,
            "fingerprint": self.fingerprint,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_by": self.acknowledged_by,
            "notification_channels": self.notification_channels,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
