from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class VAVRecord(Base):
    __tablename__ = "vav_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    zone_temp: Mapped[float | None] = mapped_column(nullable=True)
    zone_temp_setpoint_clg: Mapped[float | None] = mapped_column(nullable=True)
    zone_temp_setpoint_htg: Mapped[float | None] = mapped_column(nullable=True)
    airflow: Mapped[float | None] = mapped_column(nullable=True)
    airflow_setpoint: Mapped[float | None] = mapped_column(nullable=True)
    damper_pos: Mapped[float | None] = mapped_column(nullable=True)
    discharge_air_temp: Mapped[float | None] = mapped_column(nullable=True)
    reheat_valve_pos: Mapped[float | None] = mapped_column(nullable=True)
    zone_co2: Mapped[float | None] = mapped_column(nullable=True)
    occupancy_status: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )
    operating_mode: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )

    __table_args__ = (
        Index("idx_vav_device_time", "device_id", "timestamp"),
    )
