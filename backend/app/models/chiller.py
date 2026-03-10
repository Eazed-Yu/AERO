from datetime import datetime

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ChillerRecord(Base):
    __tablename__ = "chiller_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, index=True)
    # Chilled water side
    chw_supply_temp: Mapped[float | None] = mapped_column(nullable=True)
    chw_return_temp: Mapped[float | None] = mapped_column(nullable=True)
    chw_flow_rate: Mapped[float | None] = mapped_column(nullable=True)
    # Condenser water side
    cw_supply_temp: Mapped[float | None] = mapped_column(nullable=True)
    cw_return_temp: Mapped[float | None] = mapped_column(nullable=True)
    cw_flow_rate: Mapped[float | None] = mapped_column(nullable=True)
    # Operating parameters
    power_kw: Mapped[float | None] = mapped_column(nullable=True)
    cooling_capacity_kw: Mapped[float | None] = mapped_column(nullable=True)
    load_ratio: Mapped[float | None] = mapped_column(nullable=True)
    cop: Mapped[float | None] = mapped_column(nullable=True)
    # Advanced
    evaporator_approach: Mapped[float | None] = mapped_column(nullable=True)
    condenser_approach: Mapped[float | None] = mapped_column(nullable=True)
    compressor_rla_pct: Mapped[float | None] = mapped_column(nullable=True)
    running_status: Mapped[str | None] = mapped_column(
        String(16), nullable=True
    )

    __table_args__ = (
        Index("idx_chiller_device_time", "device_id", "timestamp"),
    )
