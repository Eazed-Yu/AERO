from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VAVRecordBase(BaseModel):
    device_id: str = Field(..., max_length=128)
    timestamp: datetime
    zone_temp: float | None = None
    zone_temp_setpoint_clg: float | None = None
    zone_temp_setpoint_htg: float | None = None
    airflow: float | None = Field(None, ge=0)
    airflow_setpoint: float | None = Field(None, ge=0)
    damper_pos: float | None = Field(None, ge=0, le=100)
    discharge_air_temp: float | None = None
    reheat_valve_pos: float | None = Field(None, ge=0, le=100)
    zone_co2: float | None = Field(None, ge=0)
    occupancy_status: str | None = Field(
        None, pattern="^(occupied|unoccupied|standby)$"
    )
    operating_mode: str | None = Field(
        None, pattern="^(cooling|heating|deadband)$"
    )


class VAVRecordCreate(VAVRecordBase):
    pass


class VAVRecordUpdate(BaseModel):
    device_id: str | None = Field(None, max_length=128)
    timestamp: datetime | None = None
    zone_temp: float | None = None
    zone_temp_setpoint_clg: float | None = None
    zone_temp_setpoint_htg: float | None = None
    airflow: float | None = Field(None, ge=0)
    airflow_setpoint: float | None = Field(None, ge=0)
    damper_pos: float | None = Field(None, ge=0, le=100)
    discharge_air_temp: float | None = None
    reheat_valve_pos: float | None = Field(None, ge=0, le=100)
    zone_co2: float | None = Field(None, ge=0)
    occupancy_status: str | None = Field(
        None, pattern="^(occupied|unoccupied|standby)$"
    )
    operating_mode: str | None = Field(
        None, pattern="^(cooling|heating|deadband)$"
    )


class VAVRecordResponse(VAVRecordBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
