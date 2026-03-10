"""
MCP tool definitions wrapping query and statistics services.
These tools are exposed via the MCP protocol for AI agent consumption.
"""

from app.mcp.server import MCP_AVAILABLE

if MCP_AVAILABLE:
    from app.mcp.server import mcp

    @mcp.tool()
    async def query_energy_data(
        building_id: str,
        start_time: str,
        end_time: str,
        metrics: list[str] | None = None,
    ) -> dict:
        """Query energy consumption data for a building within a time range."""
        # Will be connected to EnergyService in production
        return {
            "status": "not_implemented",
            "message": "MCP tool integration pending service wiring",
        }

    @mcp.tool()
    async def calculate_cop(
        building_id: str,
        start_time: str,
        end_time: str,
        period: str = "day",
    ) -> dict:
        """Calculate COP (Coefficient of Performance) for HVAC system."""
        return {
            "status": "not_implemented",
            "message": "MCP tool integration pending service wiring",
        }

    @mcp.tool()
    async def detect_anomalies(
        building_id: str,
        start_time: str,
        end_time: str,
    ) -> dict:
        """Run anomaly detection on energy data."""
        return {
            "status": "not_implemented",
            "message": "MCP tool integration pending service wiring",
        }

    @mcp.tool()
    async def get_building_statistics(
        building_id: str,
        period: str = "month",
    ) -> dict:
        """Get aggregated statistics for a building."""
        return {
            "status": "not_implemented",
            "message": "MCP tool integration pending service wiring",
        }
