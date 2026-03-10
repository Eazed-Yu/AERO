from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EquipmentBase(BaseModel):
    building_id: str = Field(..., max_length=64)
    device_id: str = Field(..., max_length=128)
    device_name: str = Field(..., max_length=255)
    device_type: str = Field(..., max_length=64)
    rated_power_kw: float | None = None
    install_date: datetime | None = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentResponse(EquipmentBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EquipmentStatusBase(BaseModel):
    device_id: str = Field(..., max_length=128)
    timestamp: datetime
    status: str = Field(..., pattern="^(normal|abnormal|offline|maintenance)$")
    power_consumption_kw: float | None = None
    runtime_hours: float | None = None
    error_code: str | None = None
    notes: str | None = None


class EquipmentStatusCreate(EquipmentStatusBase):
    pass


class EquipmentStatusResponse(EquipmentStatusBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
