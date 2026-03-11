from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    region_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    dry_bulb_temp: Mapped[float | None] = mapped_column(nullable=True)
    wet_bulb_temp: Mapped[float | None] = mapped_column(nullable=True)
    relative_humidity: Mapped[float | None] = mapped_column(nullable=True)
    wind_speed: Mapped[float | None] = mapped_column(nullable=True)
    solar_radiation: Mapped[float | None] = mapped_column(nullable=True)
    atmospheric_pressure: Mapped[float | None] = mapped_column(nullable=True)

    __table_args__ = (
        Index("idx_weather_region_time", "region_id", "timestamp"),
    )
