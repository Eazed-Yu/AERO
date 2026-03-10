from datetime import datetime

from pydantic import BaseModel, Field


class AggregationRequest(BaseModel):
    building_id: str
    start_time: datetime
    end_time: datetime
    period: str = Field("day", pattern="^(hour|day|week|month)$")
    metrics: list[str] = Field(
        default=["electricity_kwh"],
        description="Metrics to aggregate",
    )


class AggregationResult(BaseModel):
    period_start: datetime
    period_end: datetime | None = None
    metric_name: str
    avg: float | None = None
    min: float | None = None
    max: float | None = None
    sum: float | None = None
    count: int = 0


class COPResult(BaseModel):
    period_start: datetime
    cop: float | None = None
    cooling_output_kwh: float | None = None
    energy_input_kwh: float | None = None
    avg_supply_temp: float | None = None
    avg_return_temp: float | None = None
    rating: str = "N/A"


class AnomalyStatistics(BaseModel):
    total_count: int = 0
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    unresolved_count: int = 0
