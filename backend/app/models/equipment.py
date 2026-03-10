from datetime import datetime

from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, generate_uuid


class Equipment(TimestampMixin, Base):
    __tablename__ = "equipment"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    building_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    device_id: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False
    )
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)
    rated_power_kw: Mapped[float | None] = mapped_column(nullable=True)
    install_date: Mapped[datetime | None] = mapped_column(nullable=True)


class EquipmentStatus(Base):
    __tablename__ = "equipment_status"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    power_consumption_kw: Mapped[float | None] = mapped_column(nullable=True)
    runtime_hours: Mapped[float | None] = mapped_column(nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default="now()", nullable=False
    )

    __table_args__ = (
        Index("idx_equip_status_device_time", "device_id", "timestamp"),
    )
