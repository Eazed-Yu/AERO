from datetime import datetime

from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class EnergyRecord(Base):
    __tablename__ = "energy_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    building_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)

    # Energy metrics
    electricity_kwh: Mapped[float | None] = mapped_column(nullable=True)
    water_m3: Mapped[float | None] = mapped_column(nullable=True)
    gas_m3: Mapped[float | None] = mapped_column(nullable=True)
    hvac_kwh: Mapped[float | None] = mapped_column(nullable=True)

    # HVAC details
    hvac_supply_temp: Mapped[float | None] = mapped_column(nullable=True)
    hvac_return_temp: Mapped[float | None] = mapped_column(nullable=True)
    hvac_flow_rate: Mapped[float | None] = mapped_column(nullable=True)

    # Environment
    outdoor_temp: Mapped[float | None] = mapped_column(nullable=True)
    outdoor_humidity: Mapped[float | None] = mapped_column(nullable=True)
    occupancy_density: Mapped[float | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default="now()", nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "electricity_kwh IS NULL OR electricity_kwh >= 0",
            name="ck_energy_electricity_positive",
        ),
        CheckConstraint(
            "water_m3 IS NULL OR water_m3 >= 0",
            name="ck_energy_water_positive",
        ),
        CheckConstraint(
            "hvac_kwh IS NULL OR hvac_kwh >= 0",
            name="ck_energy_hvac_positive",
        ),
        CheckConstraint(
            "hvac_flow_rate IS NULL OR hvac_flow_rate >= 0",
            name="ck_energy_flow_positive",
        ),
        Index("idx_energy_building_time", "building_id", "timestamp"),
    )
