"""
MCP (Model Context Protocol) server for AERO.
Exposes query and statistics tools for AI agents.
"""

import logging

from app.config import settings

logger = logging.getLogger(__name__)

MCP_AVAILABLE = False
mcp = None

try:
    from fastmcp import FastMCP

    mcp = FastMCP("AERO Energy Management")
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


def get_mcp_status() -> dict:
    """Return MCP runtime status and tool list."""
    tools = []
    if MCP_AVAILABLE and mcp is not None:
        # Import tools module to ensure tools are registered
        import app.mcp.tools  # noqa: F401

        for tool in mcp._tool_manager.list_tools():
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
        "enabled": is_mcp_enabled(),
        "available": MCP_AVAILABLE,
        "tool_count": len(tools),
        "tools": tools,
        "endpoint": "/mcp" if is_mcp_enabled() else None,
    }


def mount_mcp(app) -> None:
    """Mount MCP streamable-HTTP sub-application onto the FastAPI app."""
    if not MCP_AVAILABLE or mcp is None:
        logger.info("MCP not available, skipping mount.")
        return

    # Ensure tools are registered
    import app.mcp.tools  # noqa: F401

    try:
        mcp_app = mcp.streamable_http_app()
        app.mount("/mcp", mcp_app)
        logger.info("MCP server mounted at /mcp")
    except Exception as e:
        logger.warning(f"Failed to mount MCP server: {e}")
