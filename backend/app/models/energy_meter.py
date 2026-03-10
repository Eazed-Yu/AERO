from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class EnergyMeter(Base):
    __tablename__ = "energy_meters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    building_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    # Electricity
    total_electricity_kwh: Mapped[float | None] = mapped_column(nullable=True)
    hvac_electricity_kwh: Mapped[float | None] = mapped_column(nullable=True)
    lighting_kwh: Mapped[float | None] = mapped_column(nullable=True)
    plug_load_kwh: Mapped[float | None] = mapped_column(nullable=True)
    peak_demand_kw: Mapped[float | None] = mapped_column(nullable=True)
    # Other energy
    gas_m3: Mapped[float | None] = mapped_column(nullable=True)
    water_m3: Mapped[float | None] = mapped_column(nullable=True)
    # Building-level cooling/heating
    cooling_kwh: Mapped[float | None] = mapped_column(nullable=True)
    heating_kwh: Mapped[float | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("idx_energy_meter_building_time", "building_id", "timestamp"),
    )
