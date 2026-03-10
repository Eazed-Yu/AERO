from datetime import datetime

from pydantic import BaseModel, Field


class EnergyQueryParams(BaseModel):
    building_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    metrics: list[str] | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)
    sort_by: str = "timestamp"
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class HVACDataQueryParams(BaseModel):
    device_id: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    running_status: str | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)
    sort_by: str = "timestamp"
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    items: list = []
    total: int = 0
    page: int = 1
    page_size: int = 50
    pages: int = 0


class BatchDeleteRequest(BaseModel):
    ids: list[str | int] = Field(..., min_length=1)


class BatchOperationResult(BaseModel):
    total: int
    success: int
    skipped: int
    failed: int
    failed_items: list[str] = []
