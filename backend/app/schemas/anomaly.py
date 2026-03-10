from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AnomalyEventBase(BaseModel):
    building_id: str = Field(..., max_length=64)
    device_id: str | None = None
    timestamp: datetime
    anomaly_type: str = Field(..., max_length=64)
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    metric_name: str = Field(..., max_length=64)
    metric_value: float
    threshold_value: float | None = None
    description: str
    detection_method: str = "threshold"


class AnomalyEventCreate(AnomalyEventBase):
    pass


class AnomalyEventResponse(AnomalyEventBase):
    id: str
    resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnomalyDetectRequest(BaseModel):
    building_id: str
    start_time: datetime
    end_time: datetime
