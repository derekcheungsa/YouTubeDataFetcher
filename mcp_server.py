"""
FastMCP Server for YouTube Data Fetcher

This module provides an MCP (Model Context Protocol) server using FastMCP
with HTTP transport for n8n integration. Exposes YouTube data fetching tools
to AI agents through a streamable HTTP interface.
"""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

# Create FastMCP instance
mcp = FastMCP("YouTube Data Fetcher")


@mcp.custom_route("/health", methods=["GET"])
def health_check(request: Request) -> PlainTextResponse:
    """
    Health check endpoint for the MCP server.

    Returns:
        PlainTextResponse: "OK" if server is healthy
    """
    return PlainTextResponse("OK")


@mcp.tool()
def analyze_video_placeholder(video_url_or_id: str) -> str:
    """
    Placeholder tool for video analysis.

    This tool will be implemented in the next plan (04-02) to provide
    comprehensive video data analysis including transcript, metadata,
    statistics, and comments.

    Args:
        video_url_or_id: YouTube video URL or 11-character video ID

    Returns:
        Placeholder message indicating tool is not yet implemented
    """
    return "Tool not yet implemented - will be available in plan 04-02"


def create_mcp_app():
    """
    Create and return the ASGI application for the MCP server.

    This function returns the ASGI app that can be mounted in production
    deployments or run directly with an ASGI server like uvicorn.

    Returns:
        ASGI application: The FastMCP HTTP application
    """
    return mcp.http_app()


if __name__ == "__main__":
    # Run the MCP server with HTTP transport
    mcp.run(transport="http", host="0.0.0.0", port=8000)
