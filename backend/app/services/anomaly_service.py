from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.detection.base import AbstractDetector, DetectionContext
from app.detection.threshold import ThresholdDetector
from app.models.anomaly import AnomalyEvent
from app.models.chiller import ChillerRecord
from app.models.ahu import AHURecord
from app.models.energy_meter import EnergyMeter
from app.models.vav import VAVRecord
from app.schemas.anomaly import AnomalyEventCreate, AnomalyEventUpdate


class AnomalyService:
    def __init__(
        self, db: AsyncSession, detector: AbstractDetector | None = None
    ):
        self.db = db
        self.detector = detector or ThresholdDetector()

    async def detect_anomalies(
        self,
        region_id: str,
        start_time: datetime,
        end_time: datetime,
        building_id: str | None = None,
    ) -> list[AnomalyEvent]:
        context = DetectionContext(building_id=building_id or region_id)

        # Gather data from multiple sources
        energy_stmt = (
            select(EnergyMeter)
            .where(EnergyMeter.region_id == region_id)
            .where(EnergyMeter.timestamp >= start_time)
            .where(EnergyMeter.timestamp <= end_time)
            .order_by(EnergyMeter.timestamp)
        )
        if building_id:
            energy_stmt = energy_stmt.where(EnergyMeter.building_id == building_id)
        energy_result = await self.db.execute(energy_stmt)
        energy_records = list(energy_result.scalars().all())

        chiller_stmt = (
            select(ChillerRecord)
            .where(ChillerRecord.timestamp >= start_time)
            .where(ChillerRecord.timestamp <= end_time)
            .order_by(ChillerRecord.timestamp)
        )
        chiller_result = await self.db.execute(chiller_stmt)
        chiller_records = list(chiller_result.scalars().all())

        ahu_stmt = (
            select(AHURecord)
            .where(AHURecord.timestamp >= start_time)
            .where(AHURecord.timestamp <= end_time)
            .order_by(AHURecord.timestamp)
        )
        ahu_result = await self.db.execute(ahu_stmt)
        ahu_records = list(ahu_result.scalars().all())

        vav_stmt = (
            select(VAVRecord)
            .where(VAVRecord.timestamp >= start_time)
            .where(VAVRecord.timestamp <= end_time)
            .order_by(VAVRecord.timestamp)
        )
        vav_result = await self.db.execute(vav_stmt)
        vav_records = list(vav_result.scalars().all())

        all_records = {
            "energy": energy_records,
            "chiller": chiller_records,
            "ahu": ahu_records,
            "vav": vav_records,
        }

        candidates = await self.detector.detect(all_records, context)

        events = []
        for c in candidates:
            event = AnomalyEvent(
                region_id=region_id,
                building_id=c.get("building_id", building_id),
                device_id=c.get("device_id"),
                timestamp=c["timestamp"],
                anomaly_type=c["anomaly_type"],
                severity=c["severity"],
                metric_name=c["metric_name"],
                metric_value=c["metric_value"],
                threshold_value=c.get("threshold_value"),
                description=c["description"],
                detection_method=c.get("detection_method", "threshold"),
                equipment_type=c.get("equipment_type"),
                fault_code=c.get("fault_code"),
                recommended_action=c.get("recommended_action"),
            )
            self.db.add(event)
            events.append(event)

        await self.db.flush()
        return events

    async def list_anomalies(
        self,
        region_id: str | None = None,
        building_id: str | None = None,
        severity: str | None = None,
        resolved: bool | None = None,
        equipment_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AnomalyEvent]:
        stmt = select(AnomalyEvent)
        if region_id:
            stmt = stmt.where(AnomalyEvent.region_id == region_id)
        if building_id:
            stmt = stmt.where(AnomalyEvent.building_id == building_id)
        if severity:
            stmt = stmt.where(AnomalyEvent.severity == severity)
        if resolved is not None:
            stmt = stmt.where(AnomalyEvent.resolved == resolved)
        if equipment_type:
            stmt = stmt.where(AnomalyEvent.equipment_type == equipment_type)
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

    async def get_anomaly(self, anomaly_id: str) -> AnomalyEvent | None:
        stmt = select(AnomalyEvent).where(AnomalyEvent.id == anomaly_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_anomaly(self, data: AnomalyEventCreate) -> AnomalyEvent:
        event = AnomalyEvent(**data.model_dump())
        self.db.add(event)
        await self.db.flush()
        return event

    async def update_anomaly(
        self, anomaly_id: str, data: AnomalyEventUpdate
    ) -> AnomalyEvent | None:
        event = await self.get_anomaly(anomaly_id)
        if not event:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(event, key, value)
        await self.db.flush()
        return event

    async def delete_anomaly(self, anomaly_id: str) -> bool:
        event = await self.get_anomaly(anomaly_id)
        if not event:
            return False
        await self.db.delete(event)
        await self.db.flush()
        return True
