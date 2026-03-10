from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnergyRecordBase(BaseModel):
    building_id: str = Field(..., max_length=64)
    timestamp: datetime
    electricity_kwh: float | None = Field(None, ge=0)
    water_m3: float | None = Field(None, ge=0)
    gas_m3: float | None = Field(None, ge=0)
    hvac_kwh: float | None = Field(None, ge=0)
    hvac_supply_temp: float | None = None
    hvac_return_temp: float | None = None
    hvac_flow_rate: float | None = Field(None, ge=0)
    outdoor_temp: float | None = None
    outdoor_humidity: float | None = None
    occupancy_density: float | None = Field(None, ge=0)


class EnergyRecordCreate(EnergyRecordBase):
    pass


class EnergyRecordResponse(EnergyRecordBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnergyImportRequest(BaseModel):
    records: list[EnergyRecordCreate]
    validate_data: bool = Field(True, alias="validate")
    on_conflict: str = Field("skip", pattern="^(skip|update|error)$")


class ImportResult(BaseModel):
    total: int
    inserted: int
    skipped: int
    errors: int
    error_details: list[str] = []
