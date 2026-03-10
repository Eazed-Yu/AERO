"""
MCP tool definitions wrapping query and statistics services.
These tools are exposed via the MCP protocol for AI agent consumption.
"""

from datetime import datetime
from typing import Literal
import base64
import csv
import io

from app.mcp.server import MCP_AVAILABLE, is_mcp_enabled

if MCP_AVAILABLE:
    from app.database import async_session
    from app.mcp.server import mcp
    from app.services.anomaly_service import AnomalyService
    from app.services.energy_service import EnergyService
    from app.services.statistics_service import StatisticsService
    from openpyxl import Workbook

    ALLOWED_PERIODS = {"hour", "day", "week", "month"}
    ALLOWED_METRICS = {
        "electricity_kwh", "water_m3", "gas_m3", "hvac_kwh",
        "hvac_supply_temp", "hvac_return_temp", "hvac_flow_rate",
        "outdoor_temp", "outdoor_humidity", "occupancy_density",
    }

    def _validate_period(period: str) -> str | None:
        if period not in ALLOWED_PERIODS:
            return f"Invalid period: {period}. Allowed: {sorted(ALLOWED_PERIODS)}"
        return None

    def _validate_metrics(metrics: list[str] | None) -> str | None:
        if not metrics:
            return None
        invalid = [m for m in metrics if m not in ALLOWED_METRICS]
        if invalid:
            return f"Invalid metrics: {invalid}. Allowed: {sorted(ALLOWED_METRICS)}"
        return None

    def _runtime_disabled_response() -> dict:
        return {"error": "MCP server is disabled at runtime."}

    def _parse_timerange(start_time: str, end_time: str) -> tuple[datetime, datetime] | tuple[None, None]:
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            if start_dt > end_dt:
                return None, None
            return start_dt, end_dt
        except ValueError:
            return None, None

    @mcp.tool()
    async def health_check() -> dict:
        """Return MCP health for client-side connectivity checks."""
        return {
            "ok": is_mcp_enabled(),
            "service": "aero-energy-mcp",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    @mcp.tool()
    async def get_capabilities() -> dict:
        """Return supported metrics, periods, and core analysis capabilities."""
        return {
            "supported_metrics": sorted(ALLOWED_METRICS),
            "supported_periods": sorted(ALLOWED_PERIODS),
            "analysis": [
                "time_aggregation",
                "cop_calculation",
                "anomaly_detection",
                "report_export",
            ],
        }

    @mcp.tool()
    async def export_energy_report(
        building_id: str,
        start_time: str,
        end_time: str,
        format: Literal["csv", "excel"] = "csv",
    ) -> dict:
        """Export energy report and return file content in base64.

        Args:
            building_id: Unique building identifier.
            start_time: ISO-8601 start datetime.
            end_time: ISO-8601 end datetime.
            format: Report format, "csv" or "excel".
        """
        if not is_mcp_enabled():
            return _runtime_disabled_response()

        start_dt, end_dt = _parse_timerange(start_time, end_time)
        if not start_dt or not end_dt:
            return {"error": "Invalid datetime range. Use ISO-8601 and ensure start_time <= end_time."}

        async with async_session() as session:
            svc = EnergyService(session)
            records = await svc.get_records(
                building_id=building_id,
                start_time=start_dt,
                end_time=end_dt,
            )

        columns = [
            "building_id",
            "timestamp",
            "electricity_kwh",
            "water_m3",
            "gas_m3",
            "hvac_kwh",
            "hvac_supply_temp",
            "hvac_return_temp",
            "outdoor_temp",
            "outdoor_humidity",
        ]
        rows = []
        for r in records:
            rows.append(
                {
                    "building_id": r.building_id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "electricity_kwh": r.electricity_kwh,
                    "water_m3": r.water_m3,
                    "gas_m3": r.gas_m3,
                    "hvac_kwh": r.hvac_kwh,
                    "hvac_supply_temp": r.hvac_supply_temp,
                    "hvac_return_temp": r.hvac_return_temp,
                    "outdoor_temp": r.outdoor_temp,
                    "outdoor_humidity": r.outdoor_humidity,
                }
            )

        date_suffix = f"{start_dt.date()}_{end_dt.date()}"
        if format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            content_bytes = output.getvalue().encode("utf-8")
            file_name = f"energy_{building_id}_{date_suffix}.csv"
            mime_type = "text/csv"
        else:
            wb = Workbook()
            ws = wb.active
            ws.title = "energy_report"
            for col_idx, col_name in enumerate(columns, 1):
                ws.cell(row=1, column=col_idx, value=col_name)
            for row_idx, row_data in enumerate(rows, 2):
                for col_idx, col_name in enumerate(columns, 1):
                    ws.cell(row=row_idx, column=col_idx, value=row_data.get(col_name))
            stream = io.BytesIO()
            wb.save(stream)
            content_bytes = stream.getvalue()
            file_name = f"energy_{building_id}_{date_suffix}.xlsx"
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        return {
            "building_id": building_id,
            "format": format,
            "filename": file_name,
            "mime_type": mime_type,
            "record_count": len(rows),
            "content_base64": base64.b64encode(content_bytes).decode("ascii"),
        }

    @mcp.tool()
    async def query_energy_data(
        building_id: str,
        start_time: str,
        end_time: str,
        metrics: list[str] | None = None,
    ) -> dict:
        """Query energy consumption data for a building within a time range.

        Args:
            building_id: Unique building identifier.
            start_time: ISO-8601 start datetime, e.g. "2024-01-01T00:00:00".
            end_time: ISO-8601 end datetime.
            metrics: Optional list of metric names to include. Defaults to all.
        """
        if not is_mcp_enabled():
            return _runtime_disabled_response()

        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except ValueError as e:
            return {"error": f"Invalid datetime format: {e}"}

        metrics_error = _validate_metrics(metrics)
        if metrics_error:
            return {"error": metrics_error}

        all_metrics = [
            "electricity_kwh", "water_m3", "gas_m3", "hvac_kwh",
            "hvac_supply_temp", "hvac_return_temp", "hvac_flow_rate",
            "outdoor_temp", "outdoor_humidity", "occupancy_density",
        ]
        selected = metrics if metrics else all_metrics

        async with async_session() as session:
            svc = EnergyService(session)
            records = await svc.get_records(
                building_id=building_id,
                start_time=start_dt,
                end_time=end_dt,
            )
            return {
                "building_id": building_id,
                "start_time": start_time,
                "end_time": end_time,
                "count": len(records),
                "records": [
                    {
                        "timestamp": r.timestamp.isoformat(),
                        **{
                            m: getattr(r, m, None)
                            for m in selected
                            if hasattr(r, m)
                        },
                    }
                    for r in records
                ],
            }

    @mcp.tool()
    async def calculate_cop(
        building_id: str,
        start_time: str,
        end_time: str,
        period: Literal["hour", "day", "week", "month"] = "day",
    ) -> dict:
        """Calculate COP (Coefficient of Performance) for HVAC system.

        Args:
            building_id: Unique building identifier.
            start_time: ISO-8601 start datetime.
            end_time: ISO-8601 end datetime.
            period: Aggregation period - "hour", "day", "week", or "month".
        """
        if not is_mcp_enabled():
            return _runtime_disabled_response()

        start_dt, end_dt = _parse_timerange(start_time, end_time)
        if not start_dt or not end_dt:
            return {"error": "Invalid datetime range. Use ISO-8601 and ensure start_time <= end_time."}

        async with async_session() as session:
            svc = StatisticsService(session)
            results = await svc.calculate_cop(
                building_id=building_id,
                start_time=start_dt,
                end_time=end_dt,
                period=period,
            )
            return {
                "building_id": building_id,
                "period": period,
                "count": len(results),
                "results": [
                    {
                        "period_start": r.period_start.isoformat(),
                        "cop": r.cop,
                        "cooling_output_kwh": r.cooling_output_kwh,
                        "energy_input_kwh": r.energy_input_kwh,
                        "avg_supply_temp": r.avg_supply_temp,
                        "avg_return_temp": r.avg_return_temp,
                        "rating": r.rating,
                    }
                    for r in results
                ],
            }

    @mcp.tool()
    async def detect_anomalies(
        building_id: str,
        start_time: str,
        end_time: str,
    ) -> dict:
        """Run anomaly detection on energy data.

        Args:
            building_id: Unique building identifier.
            start_time: ISO-8601 start datetime.
            end_time: ISO-8601 end datetime.
        """
        if not is_mcp_enabled():
            return _runtime_disabled_response()

        start_dt, end_dt = _parse_timerange(start_time, end_time)
        if not start_dt or not end_dt:
            return {"error": "Invalid datetime range. Use ISO-8601 and ensure start_time <= end_time."}

        async with async_session() as session:
            svc = AnomalyService(session)
            events = await svc.detect_anomalies(
                building_id=building_id,
                start_time=start_dt,
                end_time=end_dt,
            )
            await session.commit()
            return {
                "building_id": building_id,
                "count": len(events),
                "anomalies": [
                    {
                        "id": e.id,
                        "timestamp": e.timestamp.isoformat(),
                        "anomaly_type": e.anomaly_type,
                        "severity": e.severity,
                        "metric_name": e.metric_name,
                        "metric_value": e.metric_value,
                        "threshold_value": e.threshold_value,
                        "description": e.description,
                    }
                    for e in events
                ],
            }

    @mcp.tool()
    async def get_building_statistics(
        building_id: str,
        period: Literal["hour", "day", "week", "month"] = "month",
    ) -> dict:
        """Get aggregated energy statistics for a building over the last year.

        Args:
            building_id: Unique building identifier.
            period: Aggregation period - "hour", "day", "week", or "month".
        """
        from datetime import timedelta

        if not is_mcp_enabled():
            return _runtime_disabled_response()

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=365)

        async with async_session() as session:
            svc = StatisticsService(session)
            results = await svc.aggregate_by_period(
                building_id=building_id,
                start_time=start_dt,
                end_time=end_dt,
                period=period,
                metrics=["electricity_kwh", "water_m3", "gas_m3", "hvac_kwh"],
            )
            return {
                "building_id": building_id,
                "period": period,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "count": len(results),
                "statistics": [
                    {
                        "period_start": r.period_start.isoformat(),
                        "metric_name": r.metric_name,
                        "avg": r.avg,
                        "min": r.min,
                        "max": r.max,
                        "sum": r.sum,
                        "count": r.count,
                    }
                    for r in results
                ],
            }
