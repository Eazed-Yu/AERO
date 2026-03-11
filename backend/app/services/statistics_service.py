from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ahu import AHURecord
from app.models.anomaly import AnomalyEvent
from app.models.building import Building
from app.models.chiller import ChillerRecord
from app.models.cooling_tower import CoolingTowerRecord
from app.models.energy_meter import EnergyMeter
from app.models.pump import PumpRecord
from app.schemas.statistics import (
    AggregationResult,
    AnomalyStatistics,
    COPResult,
    EUIResult,
    PlantEfficiencyResult,
)
from app.utils.cop import cop_rating


class StatisticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def aggregate_by_period(
        self,
        start_time: datetime,
        end_time: datetime,
        region_id: str | None = None,
        building_id: str | None = None,
        period: str = "day",
        metrics: list[str] | None = None,
    ) -> list[AggregationResult]:
        if not metrics:
            metrics = ["total_electricity_kwh"]

        period_map = {"hour": "hour", "day": "day", "week": "week", "month": "month"}
        pg_period = period_map.get(period, "day")

        results = []
        for metric in metrics:
            if not hasattr(EnergyMeter, metric):
                continue
            col = getattr(EnergyMeter, metric)

            stmt = (
                select(
                    func.date_trunc(pg_period, EnergyMeter.timestamp).label("period_start"),
                    func.avg(col).label("avg_val"),
                    func.min(col).label("min_val"),
                    func.max(col).label("max_val"),
                    func.sum(col).label("sum_val"),
                    func.count(col).label("cnt"),
                )
                .where(EnergyMeter.timestamp >= start_time)
                .where(EnergyMeter.timestamp <= end_time)
                .where(col.isnot(None))
            )

            if region_id:
                stmt = stmt.where(EnergyMeter.region_id == region_id)
            if building_id:
                stmt = stmt.where(EnergyMeter.building_id == building_id)

            stmt = stmt.group_by(text("period_start")).order_by(text("period_start"))

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
        start_time: datetime,
        end_time: datetime,
        device_id: str | None = None,
        region_id: str | None = None,
        building_id: str | None = None,
        period: str = "day",
    ) -> list[COPResult]:
        period_map = {"hour": "hour", "day": "day", "week": "week", "month": "month"}
        pg_period = period_map.get(period, "day")

        stmt = select(
            func.date_trunc(pg_period, ChillerRecord.timestamp).label("period_start"),
            ChillerRecord.device_id,
            func.avg(ChillerRecord.chw_supply_temp).label("avg_chw_st"),
            func.avg(ChillerRecord.chw_return_temp).label("avg_chw_rt"),
            func.avg(ChillerRecord.cw_supply_temp).label("avg_cw_st"),
            func.avg(ChillerRecord.cw_return_temp).label("avg_cw_rt"),
            func.avg(ChillerRecord.load_ratio).label("avg_load"),
            func.sum(ChillerRecord.cooling_capacity_kw).label("total_cooling"),
            func.sum(ChillerRecord.power_kw).label("total_power"),
            func.count().label("cnt"),
        ).where(
            ChillerRecord.timestamp >= start_time,
            ChillerRecord.timestamp <= end_time,
            ChillerRecord.running_status == "running",
        )

        if device_id:
            stmt = stmt.where(ChillerRecord.device_id == device_id)

        stmt = stmt.group_by(text("period_start"), ChillerRecord.device_id)
        stmt = stmt.order_by(text("period_start"))

        rows = await self.db.execute(stmt)
        results = []
        for row in rows:
            cop_val = None
            if row.total_power and row.total_power > 0 and row.total_cooling:
                cop_val = round(row.total_cooling / row.total_power, 2)

            results.append(
                COPResult(
                    period_start=row.period_start,
                    device_id=row.device_id,
                    cop=cop_val,
                    cooling_capacity_kwh=round(row.total_cooling, 2) if row.total_cooling else None,
                    power_kwh=round(row.total_power, 2) if row.total_power else None,
                    chw_supply_temp_avg=round(row.avg_chw_st, 1) if row.avg_chw_st else None,
                    chw_return_temp_avg=round(row.avg_chw_rt, 1) if row.avg_chw_rt else None,
                    cw_supply_temp_avg=round(row.avg_cw_st, 1) if row.avg_cw_st else None,
                    cw_return_temp_avg=round(row.avg_cw_rt, 1) if row.avg_cw_rt else None,
                    load_ratio_avg=round(row.avg_load, 1) if row.avg_load else None,
                    rating=cop_rating(cop_val),
                )
            )
        return results

    async def calculate_eui(
        self,
        building_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> EUIResult | None:
        # Get building info
        bld_stmt = select(Building).where(Building.building_id == building_id)
        bld_result = await self.db.execute(bld_stmt)
        building = bld_result.scalar_one_or_none()
        if not building:
            return None

        # Sum energy
        stmt = select(
            func.sum(EnergyMeter.total_electricity_kwh).label("total_elec"),
            func.sum(EnergyMeter.hvac_electricity_kwh).label("total_hvac"),
        ).where(
            EnergyMeter.building_id == building_id,
            EnergyMeter.timestamp >= start_time,
            EnergyMeter.timestamp <= end_time,
        )
        row = (await self.db.execute(stmt)).one()
        total_elec = row.total_elec or 0

        eui = round(total_elec / building.area, 2) if building.area > 0 else 0
        hvac_eui = None
        if row.total_hvac and building.area > 0:
            hvac_eui = round(row.total_hvac / building.area, 2)

        return EUIResult(
            building_id=building_id,
            building_name=building.name,
            period_start=start_time,
            period_end=end_time,
            total_electricity_kwh=round(total_elec, 2),
            area=building.area,
            eui=eui,
            hvac_eui=hvac_eui,
        )

    async def plant_efficiency(
        self,
        start_time: datetime,
        end_time: datetime,
        period: str = "day",
    ) -> list[PlantEfficiencyResult]:
        pg_period = {"hour": "hour", "day": "day", "week": "week", "month": "month"}.get(period, "day")

        # Chiller power and cooling
        ch_stmt = select(
            func.date_trunc(pg_period, ChillerRecord.timestamp).label("p"),
            func.sum(ChillerRecord.cooling_capacity_kw).label("cooling"),
            func.sum(ChillerRecord.power_kw).label("ch_power"),
        ).where(
            ChillerRecord.timestamp >= start_time,
            ChillerRecord.timestamp <= end_time,
            ChillerRecord.running_status == "running",
        ).group_by(text("p"))

        # Pump power
        pump_stmt = select(
            func.date_trunc(pg_period, PumpRecord.timestamp).label("p"),
            func.sum(PumpRecord.power_kw).label("pump_power"),
        ).where(
            PumpRecord.timestamp >= start_time,
            PumpRecord.timestamp <= end_time,
        ).group_by(text("p"))

        # Tower power
        ct_stmt = select(
            func.date_trunc(pg_period, CoolingTowerRecord.timestamp).label("p"),
            func.sum(CoolingTowerRecord.fan_power_kw).label("ct_power"),
        ).where(
            CoolingTowerRecord.timestamp >= start_time,
            CoolingTowerRecord.timestamp <= end_time,
        ).group_by(text("p"))

        ch_rows = {r.p: r for r in (await self.db.execute(ch_stmt)).all()}
        pump_rows = {r.p: r for r in (await self.db.execute(pump_stmt)).all()}
        ct_rows = {r.p: r for r in (await self.db.execute(ct_stmt)).all()}

        all_periods = sorted(set(ch_rows) | set(pump_rows) | set(ct_rows))
        results = []
        for p in all_periods:
            ch = ch_rows.get(p)
            pm = pump_rows.get(p)
            ct = ct_rows.get(p)

            cooling = ch.cooling if ch and ch.cooling else 0
            ch_pw = ch.ch_power if ch and ch.ch_power else 0
            pm_pw = pm.pump_power if pm and pm.pump_power else 0
            ct_pw = ct.ct_power if ct and ct.ct_power else 0
            total_pw = ch_pw + pm_pw + ct_pw
            sys_cop = round(cooling / total_pw, 2) if total_pw > 0 else None

            results.append(PlantEfficiencyResult(
                period_start=p,
                total_cooling_kwh=round(cooling, 2) if cooling else None,
                chiller_power_kwh=round(ch_pw, 2) if ch_pw else None,
                pump_power_kwh=round(pm_pw, 2) if pm_pw else None,
                tower_power_kwh=round(ct_pw, 2) if ct_pw else None,
                total_power_kwh=round(total_pw, 2) if total_pw else None,
                system_cop=sys_cop,
            ))
        return results

    async def get_anomaly_statistics(
        self,
        start_time: datetime,
        end_time: datetime,
        region_id: str | None = None,
        building_id: str | None = None,
    ) -> AnomalyStatistics:
        base = select(AnomalyEvent).where(
            AnomalyEvent.timestamp >= start_time,
            AnomalyEvent.timestamp <= end_time,
        )
        if region_id:
            base = base.where(AnomalyEvent.region_id == region_id)
        if building_id:
            base = base.where(AnomalyEvent.building_id == building_id)

        result = await self.db.execute(base)
        events = list(result.scalars().all())

        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_eq_type: dict[str, int] = {}
        unresolved = 0

        for e in events:
            by_type[e.anomaly_type] = by_type.get(e.anomaly_type, 0) + 1
            by_severity[e.severity] = by_severity.get(e.severity, 0) + 1
            if e.equipment_type:
                by_eq_type[e.equipment_type] = by_eq_type.get(e.equipment_type, 0) + 1
            if not e.resolved:
                unresolved += 1

        return AnomalyStatistics(
            total_count=len(events),
            by_type=by_type,
            by_severity=by_severity,
            by_equipment_type=by_eq_type,
            unresolved_count=unresolved,
        )
