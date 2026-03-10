"""
MCP (Model Context Protocol) server for AERO.
Exposes query and statistics tools for AI agents.
"""

import logging

logger = logging.getLogger(__name__)

try:
    from fastmcp import FastMCP

    mcp = FastMCP("AERO Energy Management")
    MCP_AVAILABLE = True
except ImportError:
    mcp = None
    MCP_AVAILABLE = False
    logger.info("FastMCP not installed. MCP server features unavailable.")
