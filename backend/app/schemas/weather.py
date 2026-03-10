from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WeatherRecordBase(BaseModel):
    building_id: str = Field(..., max_length=64)
    timestamp: datetime
    dry_bulb_temp: float | None = None
    wet_bulb_temp: float | None = None
    relative_humidity: float | None = Field(None, ge=0, le=100)
    wind_speed: float | None = Field(None, ge=0)
    solar_radiation: float | None = Field(None, ge=0)
    atmospheric_pressure: float | None = None


class WeatherRecordCreate(WeatherRecordBase):
    pass


class WeatherRecordUpdate(BaseModel):
    building_id: str | None = Field(None, max_length=64)
    timestamp: datetime | None = None
    dry_bulb_temp: float | None = None
    wet_bulb_temp: float | None = None
    relative_humidity: float | None = Field(None, ge=0, le=100)
    wind_speed: float | None = Field(None, ge=0)
    solar_radiation: float | None = Field(None, ge=0)
    atmospheric_pressure: float | None = None


class WeatherRecordResponse(WeatherRecordBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
