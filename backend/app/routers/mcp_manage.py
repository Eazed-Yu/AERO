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
    return get_mcp_status()


@router.post("/toggle")
async def mcp_toggle(body: ToggleRequest):
    """Enable or disable the MCP server at runtime."""
    new_state = set_mcp_enabled(body.enabled)
    return {"enabled": new_state}
