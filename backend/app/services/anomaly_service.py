from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.detection.base import AbstractDetector, DetectionContext
from app.detection.threshold import ThresholdDetector
from app.models import AnomalyEvent, EnergyRecord
from app.schemas.anomaly import AnomalyEventResponse


class AnomalyService:
    def __init__(
        self, db: AsyncSession, detector: AbstractDetector | None = None
    ):
        self.db = db
        self.detector = detector or ThresholdDetector()

    async def detect_anomalies(
        self,
        building_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[AnomalyEvent]:
        # Fetch records
        stmt = (
            select(EnergyRecord)
            .where(EnergyRecord.building_id == building_id)
            .where(EnergyRecord.timestamp >= start_time)
            .where(EnergyRecord.timestamp <= end_time)
            .order_by(EnergyRecord.timestamp)
        )
        result = await self.db.execute(stmt)
        records = list(result.scalars().all())

        if not records:
            return []

        context = DetectionContext(building_id=building_id)
        candidates = await self.detector.detect(records, context)

        # Persist anomaly events
        events = []
        for c in candidates:
            event = AnomalyEvent(
                building_id=building_id,
                device_id=c.get("device_id"),
                timestamp=c["timestamp"],
                anomaly_type=c["anomaly_type"],
                severity=c["severity"],
                metric_name=c["metric_name"],
                metric_value=c["metric_value"],
                threshold_value=c.get("threshold_value"),
                description=c["description"],
                detection_method=c.get("detection_method", "threshold"),
            )
            self.db.add(event)
            events.append(event)

        await self.db.flush()
        return events

    async def list_anomalies(
        self,
        building_id: str | None = None,
        severity: str | None = None,
        resolved: bool | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AnomalyEvent]:
        stmt = select(AnomalyEvent)
        if building_id:
            stmt = stmt.where(AnomalyEvent.building_id == building_id)
        if severity:
            stmt = stmt.where(AnomalyEvent.severity == severity)
        if resolved is not None:
            stmt = stmt.where(AnomalyEvent.resolved == resolved)
        if start_time:
            stmt = stmt.where(AnomalyEvent.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(AnomalyEvent.timestamp <= end_time)
        stmt = stmt.order_by(AnomalyEvent.timestamp.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def resolve_anomaly(self, anomaly_id: str) -> bool:
        stmt = (
            update(AnomalyEvent)
            .where(AnomalyEvent.id == anomaly_id)
            .values(resolved=True)
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0
