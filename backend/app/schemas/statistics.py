from datetime import datetime

from pydantic import BaseModel, Field


class AggregationRequest(BaseModel):
    building_id: str
    start_time: datetime
    end_time: datetime
    period: str = Field("day", pattern="^(hour|day|week|month)$")
    metrics: list[str] = Field(
        default=["total_electricity_kwh"],
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


class COPRequest(BaseModel):
    building_id: str | None = None
    device_id: str | None = None
    start_time: datetime
    end_time: datetime
    period: str = Field("day", pattern="^(hour|day|week|month)$")


class COPResult(BaseModel):
    period_start: datetime
    device_id: str | None = None
    cop: float | None = None
    cooling_capacity_kwh: float | None = None
    power_kwh: float | None = None
    chw_supply_temp_avg: float | None = None
    chw_return_temp_avg: float | None = None
    cw_supply_temp_avg: float | None = None
    cw_return_temp_avg: float | None = None
    load_ratio_avg: float | None = None
    rating: str = "N/A"


class EUIResult(BaseModel):
    building_id: str
    building_name: str
    period_start: datetime
    period_end: datetime
    total_electricity_kwh: float
    area: float
    eui: float  # kWh/m²
    hvac_eui: float | None = None


class PlantEfficiencyResult(BaseModel):
    period_start: datetime
    total_cooling_kwh: float | None = None
    chiller_power_kwh: float | None = None
    pump_power_kwh: float | None = None
    tower_power_kwh: float | None = None
    total_power_kwh: float | None = None
    system_cop: float | None = None


class AnomalyStatistics(BaseModel):
    total_count: int = 0
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_equipment_type: dict[str, int] = {}
    unresolved_count: int = 0
