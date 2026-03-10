from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EquipmentBase(BaseModel):
    building_id: str = Field(..., max_length=64)
    device_id: str = Field(..., max_length=128)
    device_name: str = Field(..., max_length=255)
    device_type: str = Field(
        ...,
        pattern="^(chiller|ahu|boiler|vav|chw_pump|cw_pump|hw_pump|cooling_tower)$",
    )
    system_type: str | None = Field(
        None,
        pattern="^(cooling_plant|air_system|heating_plant|terminal)$",
    )
    model: str | None = Field(None, max_length=128)
    manufacturer: str | None = Field(None, max_length=128)
    rated_power_kw: float | None = Field(None, ge=0)
    rated_capacity: float | None = Field(None, ge=0)
    rated_cop: float | None = Field(None, ge=0)
    location: str | None = Field(None, max_length=255)
    install_date: date | None = None
    status: str | None = Field(
        "active", pattern="^(active|inactive|maintenance)$"
    )


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    building_id: str | None = Field(None, max_length=64)
    device_name: str | None = Field(None, max_length=255)
    device_type: str | None = Field(
        None,
        pattern="^(chiller|ahu|boiler|vav|chw_pump|cw_pump|hw_pump|cooling_tower)$",
    )
    system_type: str | None = Field(
        None,
        pattern="^(cooling_plant|air_system|heating_plant|terminal)$",
    )
    model: str | None = Field(None, max_length=128)
    manufacturer: str | None = Field(None, max_length=128)
    rated_power_kw: float | None = Field(None, ge=0)
    rated_capacity: float | None = Field(None, ge=0)
    rated_cop: float | None = Field(None, ge=0)
    location: str | None = Field(None, max_length=255)
    install_date: date | None = None
    status: str | None = Field(
        None, pattern="^(active|inactive|maintenance)$"
    )


class EquipmentResponse(EquipmentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EquipmentBatchUpdateItem(EquipmentUpdate):
    device_id: str = Field(..., max_length=128)
