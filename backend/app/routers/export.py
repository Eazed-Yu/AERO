from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EnergyRecord
from app.services.export_service import ExportService

router = APIRouter()

ALLOWED_METRICS = [
    "electricity_kwh",
    "water_m3",
    "gas_m3",
    "hvac_kwh",
    "hvac_supply_temp",
    "hvac_return_temp",
    "hvac_flow_rate",
    "outdoor_temp",
    "outdoor_humidity",
    "occupancy_density",
]


def _parse_metrics(metrics: str | None) -> list[str]:
    if not metrics:
        return ALLOWED_METRICS.copy()
    requested = [m.strip() for m in metrics.split(",") if m.strip()]
    valid = [m for m in requested if m in ALLOWED_METRICS]
    return valid if valid else ALLOWED_METRICS.copy()


def _to_float_list(records: list[dict], key: str) -> list[float]:
    values: list[float] = []
    for row in records:
        value = row.get(key)
        if value is not None:
            values.append(float(value))
    return values


def _build_summary_rows(records: list[dict], metrics: list[str]) -> list[dict]:
    summary_rows = [
        {"metric": "record_count", "count": len(records), "sum": "", "avg": "", "min": "", "max": ""}
    ]
    for metric in metrics:
        values = _to_float_list(records, metric)
        if not values:
            summary_rows.append(
                {"metric": metric, "count": 0, "sum": "", "avg": "", "min": "", "max": ""}
            )
            continue
        total = sum(values)
        summary_rows.append(
            {
                "metric": metric,
                "count": len(values),
                "sum": round(total, 4),
                "avg": round(total / len(values), 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
            }
        )
    return summary_rows


def _build_building_summary(records: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for row in records:
        bid = row.get("building_id") or "UNKNOWN"
        if bid not in grouped:
            grouped[bid] = {
                "building_id": bid,
                "record_count": 0,
                "electricity_kwh_sum": 0.0,
                "water_m3_sum": 0.0,
                "gas_m3_sum": 0.0,
                "hvac_kwh_sum": 0.0,
            }
        g = grouped[bid]
        g["record_count"] += 1
        g["electricity_kwh_sum"] += float(row.get("electricity_kwh") or 0)
        g["water_m3_sum"] += float(row.get("water_m3") or 0)
        g["gas_m3_sum"] += float(row.get("gas_m3") or 0)
        g["hvac_kwh_sum"] += float(row.get("hvac_kwh") or 0)

    rows = list(grouped.values())
    for row in rows:
        for key in ["electricity_kwh_sum", "water_m3_sum", "gas_m3_sum", "hvac_kwh_sum"]:
            row[key] = round(float(row[key]), 4)
    return sorted(rows, key=lambda x: x["building_id"])


async def _query_export_rows(
    db: AsyncSession,
    building_id: str | None,
    start_time: datetime | None,
    end_time: datetime | None,
    electricity_min: float | None,
    electricity_max: float | None,
    hvac_min: float | None,
    hvac_max: float | None,
    outdoor_temp_min: float | None,
    outdoor_temp_max: float | None,
) -> list[EnergyRecord]:
    stmt = select(EnergyRecord)
    if building_id:
        stmt = stmt.where(EnergyRecord.building_id == building_id)
    if start_time:
        stmt = stmt.where(EnergyRecord.timestamp >= start_time)
    if end_time:
        stmt = stmt.where(EnergyRecord.timestamp <= end_time)
    if electricity_min is not None:
        stmt = stmt.where(EnergyRecord.electricity_kwh >= electricity_min)
    if electricity_max is not None:
        stmt = stmt.where(EnergyRecord.electricity_kwh <= electricity_max)
    if hvac_min is not None:
        stmt = stmt.where(EnergyRecord.hvac_kwh >= hvac_min)
    if hvac_max is not None:
        stmt = stmt.where(EnergyRecord.hvac_kwh <= hvac_max)
    if outdoor_temp_min is not None:
        stmt = stmt.where(EnergyRecord.outdoor_temp >= outdoor_temp_min)
    if outdoor_temp_max is not None:
        stmt = stmt.where(EnergyRecord.outdoor_temp <= outdoor_temp_max)

    stmt = stmt.order_by(EnergyRecord.timestamp)
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _serialize_rows(records: list[EnergyRecord], columns: list[str]) -> list[dict]:
    data = [{k: getattr(r, k, None) for k in columns} for r in records]
    for row in data:
        if row.get("timestamp"):
            row["timestamp"] = row["timestamp"].isoformat()
    return data


@router.post("/csv")
async def export_csv(
    building_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    metrics: str | None = Query(None, description="Comma-separated metrics"),
    electricity_min: float | None = None,
    electricity_max: float | None = None,
    hvac_min: float | None = None,
    hvac_max: float | None = None,
    outdoor_temp_min: float | None = None,
    outdoor_temp_max: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    records = await _query_export_rows(
        db=db,
        building_id=building_id,
        start_time=start_time,
        end_time=end_time,
        electricity_min=electricity_min,
        electricity_max=electricity_max,
        hvac_min=hvac_min,
        hvac_max=hvac_max,
        outdoor_temp_min=outdoor_temp_min,
        outdoor_temp_max=outdoor_temp_max,
    )

    selected_metrics = _parse_metrics(metrics)
    columns = ["building_id", "timestamp", *selected_metrics]
    data = _serialize_rows(records, columns)

    export_svc = ExportService()
    return await export_svc.export_csv(
        data=data,
        columns=columns,
        filename="energy_filtered_export.csv",
    )


@router.post("/excel")
async def export_excel(
    building_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    metrics: str | None = Query(None, description="Comma-separated metrics"),
    electricity_min: float | None = None,
    electricity_max: float | None = None,
    hvac_min: float | None = None,
    hvac_max: float | None = None,
    outdoor_temp_min: float | None = None,
    outdoor_temp_max: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    records = await _query_export_rows(
        db=db,
        building_id=building_id,
        start_time=start_time,
        end_time=end_time,
        electricity_min=electricity_min,
        electricity_max=electricity_max,
        hvac_min=hvac_min,
        hvac_max=hvac_max,
        outdoor_temp_min=outdoor_temp_min,
        outdoor_temp_max=outdoor_temp_max,
    )

    selected_metrics = _parse_metrics(metrics)
    columns = ["building_id", "timestamp", *selected_metrics]
    data = _serialize_rows(records, columns)

    summary_columns = ["metric", "count", "sum", "avg", "min", "max"]
    summary_rows = _build_summary_rows(data, selected_metrics)
    building_columns = [
        "building_id",
        "record_count",
        "electricity_kwh_sum",
        "water_m3_sum",
        "gas_m3_sum",
        "hvac_kwh_sum",
    ]
    building_rows = _build_building_summary(data)

    export_svc = ExportService()
    return await export_svc.export_excel(
        data=data,
        columns=columns,
        sheet_name="能耗数据",
        filename="energy_filtered_with_stats.xlsx",
        summary_rows=summary_rows,
        summary_columns=summary_columns,
        building_rows=building_rows,
        building_columns=building_columns,
    )
