"""
Remembra MCP Server

Model Context Protocol server that exposes Remembra memory operations
as tools for AI assistants like Claude Code and Cursor.

Usage:
    # stdio transport (Claude Desktop, Claude Code)
    remembra-mcp

    # SSE transport (remote connections)
    REMEMBRA_MCP_TRANSPORT=sse remembra-mcp
"""

from remembra.mcp.server import main, mcp

__all__ = ["main", "mcp"]
