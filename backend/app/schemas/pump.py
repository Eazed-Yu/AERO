from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PumpRecordBase(BaseModel):
    device_id: str = Field(..., max_length=128)
    timestamp: datetime
    speed: float | None = Field(None, ge=0, le=100)
    power_kw: float | None = Field(None, ge=0)
    flow_rate: float | None = Field(None, ge=0)
    inlet_pressure: float | None = Field(None, ge=0)
    outlet_pressure: float | None = Field(None, ge=0)
    differential_pressure: float | None = Field(None, ge=0)
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class PumpRecordCreate(PumpRecordBase):
    pass


class PumpRecordUpdate(BaseModel):
    device_id: str | None = Field(None, max_length=128)
    timestamp: datetime | None = None
    speed: float | None = Field(None, ge=0, le=100)
    power_kw: float | None = Field(None, ge=0)
    flow_rate: float | None = Field(None, ge=0)
    inlet_pressure: float | None = Field(None, ge=0)
    outlet_pressure: float | None = Field(None, ge=0)
    differential_pressure: float | None = Field(None, ge=0)
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class PumpRecordResponse(PumpRecordBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
