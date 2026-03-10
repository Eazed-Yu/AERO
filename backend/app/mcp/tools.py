"""
MCP tool definitions wrapping query and statistics services.
These tools are exposed via the MCP protocol for AI agent consumption.
"""

from datetime import datetime

from app.mcp.server import MCP_AVAILABLE

if MCP_AVAILABLE:
    from app.database import async_session
    from app.mcp.server import mcp
    from app.services.anomaly_service import AnomalyService
    from app.services.energy_service import EnergyService
    from app.services.statistics_service import StatisticsService

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
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except ValueError as e:
            return {"error": f"Invalid datetime format: {e}"}

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
        period: str = "day",
    ) -> dict:
        """Calculate COP (Coefficient of Performance) for HVAC system.

        Args:
            building_id: Unique building identifier.
            start_time: ISO-8601 start datetime.
            end_time: ISO-8601 end datetime.
            period: Aggregation period — "hour", "day", "week", or "month".
        """
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except ValueError as e:
            return {"error": f"Invalid datetime format: {e}"}

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
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
        except ValueError as e:
            return {"error": f"Invalid datetime format: {e}"}

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
        period: str = "month",
    ) -> dict:
        """Get aggregated energy statistics for a building over the last year.

        Args:
            building_id: Unique building identifier.
            period: Aggregation period — "hour", "day", "week", or "month".
        """
        from datetime import timedelta

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
