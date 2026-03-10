from pydantic import BaseModel, Field


class ExportRequest(BaseModel):
    building_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    metrics: list[str] | None = None
    format: str = Field("csv", pattern="^(csv|excel)$")
    data_type: str = Field(
        "energy",
        pattern="^(energy|chiller|ahu|boiler|vav|pump|cooling_tower|weather)$",
    )
    device_id: str | None = None


class QAQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    mode: str = Field("hybrid", pattern="^(local|global|hybrid|mix|naive)$")


class QAQueryResponse(BaseModel):
    answer: str
    mode_used: str
    processing_time_ms: int


class QAIngestRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source: str | None = None
