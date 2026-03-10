from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BuildingBase(BaseModel):
    building_id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    building_type: str = Field(..., max_length=64)
    area: float = Field(..., gt=0)
    address: str | None = None
    floors: int | None = None
    year_built: int | None = None


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(BaseModel):
    name: str | None = None
    building_type: str | None = None
    area: float | None = Field(None, gt=0)
    address: str | None = None
    floors: int | None = None
    year_built: int | None = None


class BuildingResponse(BuildingBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
