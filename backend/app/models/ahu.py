from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AHURecord(Base):
    __tablename__ = "ahu_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    # Core 4 temperatures
    supply_air_temp: Mapped[float | None] = mapped_column(nullable=True)
    return_air_temp: Mapped[float | None] = mapped_column(nullable=True)
    mixed_air_temp: Mapped[float | None] = mapped_column(nullable=True)
    outdoor_air_temp: Mapped[float | None] = mapped_column(nullable=True)
    # Humidity
    supply_air_humidity: Mapped[float | None] = mapped_column(nullable=True)
    return_air_humidity: Mapped[float | None] = mapped_column(nullable=True)
    # Fan
    supply_fan_speed: Mapped[float | None] = mapped_column(nullable=True)
    supply_fan_power_kw: Mapped[float | None] = mapped_column(nullable=True)
    supply_air_flow: Mapped[float | None] = mapped_column(nullable=True)
    return_fan_speed: Mapped[float | None] = mapped_column(nullable=True)
    # Valves & dampers
    chw_valve_pos: Mapped[float | None] = mapped_column(nullable=True)
    hw_valve_pos: Mapped[float | None] = mapped_column(nullable=True)
    oa_damper_pos: Mapped[float | None] = mapped_column(nullable=True)
    ra_damper_pos: Mapped[float | None] = mapped_column(nullable=True)
    # Pressure
    duct_static_pressure: Mapped[float | None] = mapped_column(nullable=True)
    filter_dp: Mapped[float | None] = mapped_column(nullable=True)
    # Mode & setpoints
    operating_mode: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )
    sat_setpoint: Mapped[float | None] = mapped_column(nullable=True)
    dsp_setpoint: Mapped[float | None] = mapped_column(nullable=True)
    running_status: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )

    __table_args__ = (
        Index("idx_ahu_device_time", "device_id", "timestamp"),
    )
