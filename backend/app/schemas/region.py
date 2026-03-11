from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegionBase(BaseModel):
    region_id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    description: str | None = None
    address: str | None = Field(None, max_length=512)


class RegionCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    address: str | None = Field(None, max_length=512)


class RegionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    address: str | None = Field(None, max_length=512)


class RegionResponse(RegionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
