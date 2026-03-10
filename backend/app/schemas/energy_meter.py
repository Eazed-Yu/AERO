from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnergyMeterBase(BaseModel):
    building_id: str = Field(..., max_length=64)
    timestamp: datetime
    total_electricity_kwh: float | None = Field(None, ge=0)
    hvac_electricity_kwh: float | None = Field(None, ge=0)
    lighting_kwh: float | None = Field(None, ge=0)
    plug_load_kwh: float | None = Field(None, ge=0)
    peak_demand_kw: float | None = Field(None, ge=0)
    gas_m3: float | None = Field(None, ge=0)
    water_m3: float | None = Field(None, ge=0)
    cooling_kwh: float | None = Field(None, ge=0)
    heating_kwh: float | None = Field(None, ge=0)


class EnergyMeterCreate(EnergyMeterBase):
    pass


class EnergyMeterUpdate(BaseModel):
    building_id: str | None = Field(None, max_length=64)
    timestamp: datetime | None = None
    total_electricity_kwh: float | None = Field(None, ge=0)
    hvac_electricity_kwh: float | None = Field(None, ge=0)
    lighting_kwh: float | None = Field(None, ge=0)
    plug_load_kwh: float | None = Field(None, ge=0)
    peak_demand_kw: float | None = Field(None, ge=0)
    gas_m3: float | None = Field(None, ge=0)
    water_m3: float | None = Field(None, ge=0)
    cooling_kwh: float | None = Field(None, ge=0)
    heating_kwh: float | None = Field(None, ge=0)


class EnergyMeterResponse(EnergyMeterBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class EnergyImportRequest(BaseModel):
    records: list[EnergyMeterCreate]
    validate_data: bool = Field(True, alias="validate")
    on_conflict: str = Field("skip", pattern="^(skip|update|error)$")


class ImportResult(BaseModel):
    total: int
    inserted: int
    skipped: int
    errors: int
    error_details: list[str] = []
