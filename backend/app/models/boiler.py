from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BoilerRecord(Base):
    __tablename__ = "boiler_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    hw_supply_temp: Mapped[float | None] = mapped_column(nullable=True)
    hw_return_temp: Mapped[float | None] = mapped_column(nullable=True)
    hw_flow_rate: Mapped[float | None] = mapped_column(nullable=True)
    firing_rate: Mapped[float | None] = mapped_column(nullable=True)
    power_kw: Mapped[float | None] = mapped_column(nullable=True)
    fuel_consumption: Mapped[float | None] = mapped_column(nullable=True)
    heating_capacity_kw: Mapped[float | None] = mapped_column(nullable=True)
    efficiency: Mapped[float | None] = mapped_column(nullable=True)
    flue_gas_temp: Mapped[float | None] = mapped_column(nullable=True)
    running_status: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )

    __table_args__ = (
        Index("idx_boiler_device_time", "device_id", "timestamp"),
    )
