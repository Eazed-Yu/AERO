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


def _normalize_public_base(origin: str | None = None) -> str:
    """Resolve the externally reachable base URL for MCP clients."""
    configured = (settings.MCP_PUBLIC_BASE_URL or "").strip()
    if configured:
        return configured.rstrip("/")
    if origin:
        return origin.rstrip("/")
    return f"http://localhost:{settings.APP_PORT}"


def get_mcp_mount_path() -> str:
    """Return normalized mount path (always starts with '/')."""
    path = (settings.MCP_BASE_PATH or "/mcp").strip()
    if not path:
        return "/mcp"
    return path if path.startswith("/") else f"/{path}"


def get_mcp_endpoint(origin: str | None = None) -> str:
    """Return full MCP streamable-http endpoint URL."""
    return f"{_normalize_public_base(origin)}{get_mcp_mount_path()}/"


def is_mcp_enabled() -> bool:
    return MCP_AVAILABLE and _mcp_enabled


def set_mcp_enabled(enabled: bool) -> bool:
    global _mcp_enabled
    _mcp_enabled = enabled
    return _mcp_enabled


def get_mcp_lifespan_context():
    """Return mounted FastMCP lifespan context callable if available."""
    return _mcp_lifespan_context


async def get_mcp_status(origin: str | None = None) -> dict:
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
        "name": settings.MCP_SERVER_NAME,
        "enabled": is_mcp_enabled(),
        "available": MCP_AVAILABLE,
        "tool_count": len(tools),
        "tools": tools,
        "mount_path": get_mcp_mount_path(),
        "endpoint": get_mcp_endpoint(origin),
        "transport": "streamable-http",
        "mount_error": _mount_error,
    }


async def get_mcp_client_config(origin: str | None = None) -> dict:
    """Return MCP client config snippets for common MCP clients."""
    endpoint = get_mcp_endpoint(origin)
    tools = []
    if MCP_AVAILABLE and mcp is not None:
        from app.mcp import tools as _tools  # noqa: F401

        tools = [tool.name for tool in await mcp.list_tools()]

    return {
        "server_name": settings.MCP_SERVER_NAME,
        "endpoint": endpoint,
        "transport": "streamable-http",
        "claudeDesktop": {
            "mcpServers": {
                settings.MCP_SERVER_NAME: {
                    "command": "npx",
                    "args": ["-y", "mcp-remote", endpoint],
                    "env": {},
                    "disabled": False,
                    "autoApprove": tools,
                }
            }
        },
        "cherryStudio": {
            "mcpServers": {
                settings.MCP_SERVER_NAME: {
                    "type": "streamableHttp",
                    "url": endpoint,
                }
            }
        },
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
        fastapi_app.mount(get_mcp_mount_path(), mcp_app)
        _mcp_lifespan_context = getattr(mcp_app.router, "lifespan_context", None)
        _mount_error = None
        logger.info("MCP server mounted at %s", get_mcp_mount_path())
    except Exception as e:
        _mount_error = str(e)
        _mcp_lifespan_context = None
        logger.exception("Failed to mount MCP server")
