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
    climate_zone: str | None = Field(None, max_length=32)
    cooling_area: float | None = Field(None, ge=0)
    design_cooling_load: float | None = Field(None, ge=0)
    design_heating_load: float | None = Field(None, ge=0)


class BuildingCreate(BuildingBase):
    pass


class BuildingUpdate(BaseModel):
    name: str | None = None
    building_type: str | None = None
    area: float | None = Field(None, gt=0)
    address: str | None = None
    floors: int | None = None
    year_built: int | None = None
    climate_zone: str | None = Field(None, max_length=32)
    cooling_area: float | None = Field(None, ge=0)
    design_cooling_load: float | None = Field(None, ge=0)
    design_heating_load: float | None = Field(None, ge=0)


class BuildingResponse(BuildingBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BuildingBatchUpdateItem(BuildingUpdate):
    building_id: str = Field(..., max_length=64)
