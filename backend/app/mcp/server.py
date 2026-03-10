"""
MCP (Model Context Protocol) server for AERO.
Exposes query and statistics tools for AI agents.
"""

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

MCP_AVAILABLE = False
mcp = None
_mount_error: str | None = None
_mcp_lifespan_context = None

try:
    from fastmcp import FastMCP

    mcp = FastMCP(
        name="AERO Energy Management",
        instructions=(
            "You are an assistant for building energy management. "
            "Prefer querying tools before making conclusions, and clearly explain "
            "time ranges, units, and anomaly evidence in Chinese."
        ),
        version="0.2.0",
        strict_input_validation=True,
    )
    MCP_AVAILABLE = True
except ImportError:
    logger.info("FastMCP not installed. MCP server features unavailable.")

# Runtime state
_mcp_enabled: bool = settings.ENABLE_MCP


def is_mcp_enabled() -> bool:
    return MCP_AVAILABLE and _mcp_enabled


def set_mcp_enabled(enabled: bool) -> bool:
    global _mcp_enabled
    _mcp_enabled = enabled
    return _mcp_enabled


def get_mcp_lifespan_context():
    """Return mounted FastMCP lifespan context callable if available."""
    return _mcp_lifespan_context


async def get_mcp_status() -> dict:
    """Return MCP runtime status and tool list."""
    tools = []
    if MCP_AVAILABLE and mcp is not None:
        # Import tools module to ensure tools are registered
        from app.mcp import tools as _tools  # noqa: F401

        for tool in await mcp.list_tools():
            params = []
            schema = tool.parameters
            if schema and "properties" in schema:
                for name, prop in schema["properties"].items():
                    params.append({
                        "name": name,
                        "type": prop.get("type", "string"),
                        "description": prop.get("description", ""),
                        "required": name in schema.get("required", []),
                    })
            tools.append({
                "name": tool.name,
                "description": tool.description or "",
                "parameters": params,
            })

    return {
        "name": "aero-energy-mcp",
        "enabled": is_mcp_enabled(),
        "available": MCP_AVAILABLE,
        "tool_count": len(tools),
        "tools": tools,
        "endpoint": "/mcp/" if is_mcp_enabled() else None,
        "transport": "streamable-http",
        "mount_error": _mount_error,
    }


def mount_mcp(fastapi_app) -> None:
    """Mount MCP streamable-HTTP sub-application onto the FastAPI app."""
    global _mount_error, _mcp_lifespan_context

    if not MCP_AVAILABLE or mcp is None:
        logger.info("MCP not available, skipping mount.")
        return

    # Ensure tools are registered
    from app.mcp import tools as _tools  # noqa: F401

    try:
        # FastMCP 2.x uses `http_app`, where `transport="streamable-http"`
        # is the modern protocol expected by MCP clients.
        mcp_app: Any = mcp.http_app(
            path="/",
            transport="streamable-http",
            stateless_http=True,
        )
        fastapi_app.mount("/mcp", mcp_app)
        _mcp_lifespan_context = getattr(mcp_app.router, "lifespan_context", None)
        _mount_error = None
        logger.info("MCP server mounted at /mcp")
    except Exception as e:
        _mount_error = str(e)
        _mcp_lifespan_context = None
        logger.exception("Failed to mount MCP server")
