from datetime import date, datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, generate_uuid


class Equipment(TimestampMixin, Base):
    __tablename__ = "equipment"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    region_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    building_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    device_id: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False
    )
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    device_type: Mapped[str] = mapped_column(String(64), nullable=False)
    # New fields
    system_type: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )
    rated_power_kw: Mapped[float | None] = mapped_column(nullable=True)
    rated_capacity: Mapped[float | None] = mapped_column(nullable=True)
    rated_cop: Mapped[float | None] = mapped_column(nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    install_date: Mapped[date | None] = mapped_column(nullable=True)
    status: Mapped[str | None] = mapped_column(
        String(32), default="active", nullable=True
    )

    __table_args__ = (
        Index("idx_equipment_region", "region_id"),
        Index("idx_equipment_building", "building_id"),
        Index("idx_equipment_type", "device_type"),
    )
