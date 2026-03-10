from datetime import datetime, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnomalyEvent, EnergyRecord
from app.schemas.statistics import AggregationResult, AnomalyStatistics, COPResult
from app.utils.cop import calculate_cop, cop_rating


class StatisticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def aggregate_by_period(
        self,
        building_id: str,
        start_time: datetime,
        end_time: datetime,
        period: str = "day",
        metrics: list[str] | None = None,
    ) -> list[AggregationResult]:
        if not metrics:
            metrics = ["electricity_kwh"]

        # Use date_trunc for standard PostgreSQL
        period_map = {
            "hour": "hour",
            "day": "day",
            "week": "week",
            "month": "month",
        }
        pg_period = period_map.get(period, "day")

        results = []
        for metric in metrics:
            if not hasattr(EnergyRecord, metric):
                continue
            col = getattr(EnergyRecord, metric)

            stmt = (
                select(
                    func.date_trunc(pg_period, EnergyRecord.timestamp).label(
                        "period_start"
                    ),
                    func.avg(col).label("avg_val"),
                    func.min(col).label("min_val"),
                    func.max(col).label("max_val"),
                    func.sum(col).label("sum_val"),
                    func.count(col).label("cnt"),
                )
                .where(EnergyRecord.building_id == building_id)
                .where(EnergyRecord.timestamp >= start_time)
                .where(EnergyRecord.timestamp <= end_time)
                .where(col.isnot(None))
                .group_by(text("period_start"))
                .order_by(text("period_start"))
            )

            rows = await self.db.execute(stmt)
            for row in rows:
                results.append(
                    AggregationResult(
                        period_start=row.period_start,
                        metric_name=metric,
                        avg=round(row.avg_val, 2) if row.avg_val else None,
                        min=round(row.min_val, 2) if row.min_val else None,
                        max=round(row.max_val, 2) if row.max_val else None,
                        sum=round(row.sum_val, 2) if row.sum_val else None,
                        count=row.cnt or 0,
                    )
                )

        return results

    async def calculate_cop(
        self,
        building_id: str,
        start_time: datetime,
        end_time: datetime,
        period: str = "day",
    ) -> list[COPResult]:
        period_map = {"hour": "hour", "day": "day", "week": "week", "month": "month"}
        pg_period = period_map.get(period, "day")

        stmt = (
            select(
                func.date_trunc(pg_period, EnergyRecord.timestamp).label(
                    "period_start"
                ),
                func.avg(EnergyRecord.hvac_supply_temp).label("avg_supply"),
                func.avg(EnergyRecord.hvac_return_temp).label("avg_return"),
                func.avg(EnergyRecord.hvac_flow_rate).label("avg_flow"),
                func.sum(EnergyRecord.hvac_kwh).label("total_hvac"),
                func.count().label("cnt"),
            )
            .where(EnergyRecord.building_id == building_id)
            .where(EnergyRecord.timestamp >= start_time)
            .where(EnergyRecord.timestamp <= end_time)
            .where(EnergyRecord.hvac_kwh.isnot(None))
            .where(EnergyRecord.hvac_supply_temp.isnot(None))
            .where(EnergyRecord.hvac_return_temp.isnot(None))
            .group_by(text("period_start"))
            .order_by(text("period_start"))
        )

        rows = await self.db.execute(stmt)
        results = []

        for row in rows:
            hours = row.cnt  # Each record is 1 hour
            cop_val = calculate_cop(
                hvac_kwh=row.total_hvac,
                supply_temp=row.avg_supply,
                return_temp=row.avg_return,
                flow_rate_m3h=row.avg_flow,
                hours=hours,
            )

            # Cooling output
            if row.avg_flow and row.avg_supply is not None and row.avg_return is not None:
                delta_t = abs(row.avg_return - row.avg_supply)
                q_kw = row.avg_flow * 1.163 * delta_t
                cooling_kwh = round(q_kw * hours, 2)
            else:
                cooling_kwh = None

            results.append(
                COPResult(
                    period_start=row.period_start,
                    cop=round(cop_val, 2) if cop_val else None,
                    cooling_output_kwh=cooling_kwh,
                    energy_input_kwh=round(row.total_hvac, 2) if row.total_hvac else None,
                    avg_supply_temp=round(row.avg_supply, 1) if row.avg_supply else None,
                    avg_return_temp=round(row.avg_return, 1) if row.avg_return else None,
                    rating=cop_rating(cop_val),
                )
            )

        return results

    async def get_anomaly_statistics(
        self,
        building_id: str | None,
        start_time: datetime,
        end_time: datetime,
    ) -> AnomalyStatistics:
        base = select(AnomalyEvent).where(
            AnomalyEvent.timestamp >= start_time,
            AnomalyEvent.timestamp <= end_time,
        )
        if building_id:
            base = base.where(AnomalyEvent.building_id == building_id)

        result = await self.db.execute(base)
        events = list(result.scalars().all())

        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        unresolved = 0

        for e in events:
            by_type[e.anomaly_type] = by_type.get(e.anomaly_type, 0) + 1
            by_severity[e.severity] = by_severity.get(e.severity, 0) + 1
            if not e.resolved:
                unresolved += 1

        return AnomalyStatistics(
            total_count=len(events),
            by_type=by_type,
            by_severity=by_severity,
            unresolved_count=unresolved,
        )
