from datetime import datetime

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, generate_uuid


class AnomalyEvent(Base):
    __tablename__ = "anomaly_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    region_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    building_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    device_id: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    anomaly_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_value: Mapped[float] = mapped_column(nullable=False)
    threshold_value: Mapped[float | None] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolved: Mapped[bool] = mapped_column(default=False, nullable=False)
    detection_method: Mapped[str] = mapped_column(
        String(32), default="threshold", nullable=False
    )
    # New fields
    equipment_type: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    fault_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default="now()", nullable=False
    )

    __table_args__ = (
        Index("idx_anomaly_region_time", "region_id", "timestamp"),
        Index("idx_anomaly_severity", "severity", "resolved"),
    )
