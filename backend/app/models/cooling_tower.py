from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CoolingTowerRecord(Base):
    __tablename__ = "cooling_tower_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    fan_speed: Mapped[float | None] = mapped_column(nullable=True)
    fan_power_kw: Mapped[float | None] = mapped_column(nullable=True)
    cw_inlet_temp: Mapped[float | None] = mapped_column(nullable=True)
    cw_outlet_temp: Mapped[float | None] = mapped_column(nullable=True)
    wet_bulb_temp: Mapped[float | None] = mapped_column(nullable=True)
    approach: Mapped[float | None] = mapped_column(nullable=True)
    range: Mapped[float | None] = mapped_column(nullable=True)
    running_status: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )

    __table_args__ = (
        Index("idx_ct_device_time", "device_id", "timestamp"),
    )
