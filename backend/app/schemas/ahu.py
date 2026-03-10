from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AHURecordBase(BaseModel):
    device_id: str = Field(..., max_length=128)
    timestamp: datetime
    supply_air_temp: float | None = None
    return_air_temp: float | None = None
    mixed_air_temp: float | None = None
    outdoor_air_temp: float | None = None
    supply_air_humidity: float | None = Field(None, ge=0, le=100)
    return_air_humidity: float | None = Field(None, ge=0, le=100)
    supply_fan_speed: float | None = Field(None, ge=0, le=100)
    supply_fan_power_kw: float | None = Field(None, ge=0)
    supply_air_flow: float | None = Field(None, ge=0)
    return_fan_speed: float | None = Field(None, ge=0, le=100)
    chw_valve_pos: float | None = Field(None, ge=0, le=100)
    hw_valve_pos: float | None = Field(None, ge=0, le=100)
    oa_damper_pos: float | None = Field(None, ge=0, le=100)
    ra_damper_pos: float | None = Field(None, ge=0, le=100)
    duct_static_pressure: float | None = Field(None, ge=0)
    filter_dp: float | None = Field(None, ge=0)
    operating_mode: str | None = Field(
        None, pattern="^(cooling|heating|ventilation|off)$"
    )
    sat_setpoint: float | None = None
    dsp_setpoint: float | None = Field(None, ge=0)
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class AHURecordCreate(AHURecordBase):
    pass


class AHURecordUpdate(BaseModel):
    device_id: str | None = Field(None, max_length=128)
    timestamp: datetime | None = None
    supply_air_temp: float | None = None
    return_air_temp: float | None = None
    mixed_air_temp: float | None = None
    outdoor_air_temp: float | None = None
    supply_air_humidity: float | None = Field(None, ge=0, le=100)
    return_air_humidity: float | None = Field(None, ge=0, le=100)
    supply_fan_speed: float | None = Field(None, ge=0, le=100)
    supply_fan_power_kw: float | None = Field(None, ge=0)
    supply_air_flow: float | None = Field(None, ge=0)
    return_fan_speed: float | None = Field(None, ge=0, le=100)
    chw_valve_pos: float | None = Field(None, ge=0, le=100)
    hw_valve_pos: float | None = Field(None, ge=0, le=100)
    oa_damper_pos: float | None = Field(None, ge=0, le=100)
    ra_damper_pos: float | None = Field(None, ge=0, le=100)
    duct_static_pressure: float | None = Field(None, ge=0)
    filter_dp: float | None = Field(None, ge=0)
    operating_mode: str | None = Field(
        None, pattern="^(cooling|heating|ventilation|off)$"
    )
    sat_setpoint: float | None = None
    dsp_setpoint: float | None = Field(None, ge=0)
    running_status: str | None = Field(
        None, pattern="^(running|standby|fault)$"
    )


class AHURecordResponse(AHURecordBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
