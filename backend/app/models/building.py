from datetime import datetime

from sqlalchemy import CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, generate_uuid


class Building(TimestampMixin, Base):
    __tablename__ = "buildings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    building_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    region_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    building_type: Mapped[str] = mapped_column(String(64), nullable=False)
    area: Mapped[float] = mapped_column(nullable=False)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    floors: Mapped[int | None] = mapped_column(nullable=True)
    year_built: Mapped[int | None] = mapped_column(nullable=True)
    # HVAC design fields
    climate_zone: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    cooling_area: Mapped[float | None] = mapped_column(nullable=True)
    design_cooling_load: Mapped[float | None] = mapped_column(nullable=True)
    design_heating_load: Mapped[float | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint("area > 0", name="ck_building_area_positive"),
        Index("idx_building_region", "region_id"),
        Index("idx_building_type", "building_type"),
    )
