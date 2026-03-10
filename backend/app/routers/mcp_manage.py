"""MCP management API: status inspection and runtime toggle."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.mcp.server import get_mcp_status, is_mcp_enabled, set_mcp_enabled

router = APIRouter()


class ToggleRequest(BaseModel):
    enabled: bool


@router.get("/status")
async def mcp_status():
    """Return MCP runtime status, tool list, and endpoint info."""
    return await get_mcp_status()


@router.post("/toggle")
async def mcp_toggle(body: ToggleRequest):
    """Enable or disable the MCP server at runtime."""
    new_state = set_mcp_enabled(body.enabled)
    return {"enabled": new_state}


@router.get("/config")
async def mcp_config():
    """Return standard MCP client configuration in Claude Desktop format."""
    from app.config import settings

    return {
        "mcpServers": {
            "aero-energy": {
                "command": "npx",
                "args": ["-y", "mcp-remote", f"http://localhost:{settings.APP_PORT}/mcp/"],
                "env": {},
                "disabled": False,
                "autoApprove": [
                    "health_check",
                    "get_capabilities",
                    "query_energy_data",
                    "export_energy_report",
                    "calculate_cop",
                    "detect_anomalies",
                    "get_building_statistics"
                ]
            }
        },
        "cherryStudio": {
            "mcpServers": {
                "aero-energy": {
                    "type": "streamableHttp",
                    "url": f"http://localhost:{settings.APP_PORT}/mcp/"
                }
            }
        }
    }
