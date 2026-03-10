from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PumpRecord(Base):
    __tablename__ = "pump_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    speed: Mapped[float | None] = mapped_column(nullable=True)
    power_kw: Mapped[float | None] = mapped_column(nullable=True)
    flow_rate: Mapped[float | None] = mapped_column(nullable=True)
    inlet_pressure: Mapped[float | None] = mapped_column(nullable=True)
    outlet_pressure: Mapped[float | None] = mapped_column(nullable=True)
    differential_pressure: Mapped[float | None] = mapped_column(nullable=True)
    running_status: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )

    __table_args__ = (
        Index("idx_pump_device_time", "device_id", "timestamp"),
    )
