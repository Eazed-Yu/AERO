from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CoolingTowerRecordBase(BaseModel):
    device_id: str = Field(..., max_length=128)
    timestamp: datetime
    fan_speed: float | None = Field(None, ge=0, le=100)
    fan_power_kw: float | None = Field(None, ge=0)
    cw_inlet_temp: float | None = None
    cw_outlet_temp: float | None = None
    wet_bulb_temp: float | None = None
    approach: float | None = None
    range: float | None = None
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class CoolingTowerRecordCreate(CoolingTowerRecordBase):
    pass


class CoolingTowerRecordUpdate(BaseModel):
    device_id: str | None = Field(None, max_length=128)
    timestamp: datetime | None = None
    fan_speed: float | None = Field(None, ge=0, le=100)
    fan_power_kw: float | None = Field(None, ge=0)
    cw_inlet_temp: float | None = None
    cw_outlet_temp: float | None = None
    wet_bulb_temp: float | None = None
    approach: float | None = None
    range: float | None = None
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class CoolingTowerRecordResponse(CoolingTowerRecordBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
