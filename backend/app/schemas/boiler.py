from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BoilerRecordBase(BaseModel):
    device_id: str = Field(..., max_length=128)
    timestamp: datetime
    hw_supply_temp: float | None = None
    hw_return_temp: float | None = None
    hw_flow_rate: float | None = Field(None, ge=0)
    firing_rate: float | None = Field(None, ge=0, le=100)
    power_kw: float | None = Field(None, ge=0)
    fuel_consumption: float | None = Field(None, ge=0)
    heating_capacity_kw: float | None = Field(None, ge=0)
    efficiency: float | None = Field(None, ge=0, le=100)
    flue_gas_temp: float | None = None
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class BoilerRecordCreate(BoilerRecordBase):
    pass


class BoilerRecordUpdate(BaseModel):
    device_id: str | None = Field(None, max_length=128)
    timestamp: datetime | None = None
    hw_supply_temp: float | None = None
    hw_return_temp: float | None = None
    hw_flow_rate: float | None = Field(None, ge=0)
    firing_rate: float | None = Field(None, ge=0, le=100)
    power_kw: float | None = Field(None, ge=0)
    fuel_consumption: float | None = Field(None, ge=0)
    heating_capacity_kw: float | None = Field(None, ge=0)
    efficiency: float | None = Field(None, ge=0, le=100)
    flue_gas_temp: float | None = None
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class BoilerRecordResponse(BoilerRecordBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
