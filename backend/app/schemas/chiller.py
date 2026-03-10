from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChillerRecordBase(BaseModel):
    device_id: str = Field(..., max_length=128)
    timestamp: datetime
    chw_supply_temp: float | None = None
    chw_return_temp: float | None = None
    chw_flow_rate: float | None = Field(None, ge=0)
    cw_supply_temp: float | None = None
    cw_return_temp: float | None = None
    cw_flow_rate: float | None = Field(None, ge=0)
    power_kw: float | None = Field(None, ge=0)
    cooling_capacity_kw: float | None = Field(None, ge=0)
    load_ratio: float | None = Field(None, ge=0, le=150)
    cop: float | None = Field(None, ge=0)
    evaporator_approach: float | None = None
    condenser_approach: float | None = None
    compressor_rla_pct: float | None = Field(None, ge=0, le=150)
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class ChillerRecordCreate(ChillerRecordBase):
    pass


class ChillerRecordUpdate(BaseModel):
    device_id: str | None = Field(None, max_length=128)
    timestamp: datetime | None = None
    chw_supply_temp: float | None = None
    chw_return_temp: float | None = None
    chw_flow_rate: float | None = Field(None, ge=0)
    cw_supply_temp: float | None = None
    cw_return_temp: float | None = None
    cw_flow_rate: float | None = Field(None, ge=0)
    power_kw: float | None = Field(None, ge=0)
    cooling_capacity_kw: float | None = Field(None, ge=0)
    load_ratio: float | None = Field(None, ge=0, le=150)
    cop: float | None = Field(None, ge=0)
    evaporator_approach: float | None = None
    condenser_approach: float | None = None
    compressor_rla_pct: float | None = Field(None, ge=0, le=150)
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class ChillerRecordResponse(ChillerRecordBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
