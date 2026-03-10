"""MCP management API: status inspection and runtime toggle."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.mcp.server import get_mcp_client_config, get_mcp_status, set_mcp_enabled

router = APIRouter()


class ToggleRequest(BaseModel):
    enabled: bool


@router.get("/status")
async def mcp_status(request: Request):
    """Return MCP runtime status, tool list, and endpoint info."""
    return await get_mcp_status(_request_origin(request))


@router.post("/toggle")
async def mcp_toggle(body: ToggleRequest):
    """Enable or disable the MCP server at runtime."""
    new_state = set_mcp_enabled(body.enabled)
    return {"enabled": new_state}


@router.get("/config")
async def mcp_config(request: Request):
    """Return MCP client configuration snippets for installation pages."""
    return await get_mcp_client_config(_request_origin(request))


def _request_origin(request: Request) -> str:
    """Build client-visible origin, preferring reverse-proxy headers."""
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}"
    return str(request.base_url).rstrip("/")
