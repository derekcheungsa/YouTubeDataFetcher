"""
FastMCP Server for YouTube Data Fetcher

This module provides an MCP (Model Context Protocol) server using FastMCP
with HTTP transport for n8n integration. Exposes YouTube data fetching tools
to AI agents through a streamable HTTP interface.
"""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse
import re
from app import get_unified_video_data, get_comments_for_video, is_valid_video_id

# Create FastMCP instance
mcp = FastMCP("YouTube Data Fetcher")


def extract_video_id(video_url_or_id: str) -> str:
    """
    Extract YouTube video ID from a URL or validate a bare video ID.

    Args:
        video_url_or_id: YouTube video URL or 11-character video ID

    Returns:
        str: Extracted or validated 11-character video ID

    Raises:
        ValueError: If video ID cannot be extracted or is invalid
    """
    # Check if it's already a valid video ID (11 chars, alphanumeric with - and _)
    if is_valid_video_id(video_url_or_id):
        return video_url_or_id

    # Try to extract from YouTube URL using regex
    # Pattern matches: youtube.com/watch?v=ID, youtu.be/ID, youtube.com/embed/ID, etc.
    pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(pattern, video_url_or_id)

    if match:
        video_id = match.group(1)
        if is_valid_video_id(video_id):
            return video_id

    raise ValueError(
        f"Could not extract valid video ID from: {video_url_or_id}. "
        "Provide a valid 11-character YouTube video ID or full YouTube URL."
    )


@mcp.custom_route("/health", methods=["GET"])
def health_check(request: Request) -> PlainTextResponse:
    """
    Health check endpoint for the MCP server.

    Returns:
        PlainTextResponse: "OK" if server is healthy
    """
    return PlainTextResponse("OK")


@mcp.tool()
def analyze_video(video_url_or_id: str) -> dict:
    """
    Fetch complete YouTube video data including transcript, metadata, statistics, and comments.

    Accepts video URL or ID. Returns full data bundle with graceful degradation if some data is unavailable.

    Args:
        video_url_or_id: YouTube video URL or 11-character video ID

    Returns:
        Dictionary containing:
        - success (bool): True if any data fetched successfully
        - video_id (str): The 11-character YouTube video ID
        - transcript (list or None): Video transcript with timestamps
        - metadata (dict or None): Video metadata (title, description, tags, etc.)
        - statistics (dict or None): Video statistics (views, likes, duration, etc.)
        - comments (list or None): Top comments from the video
        - partial_success (bool): True if some data failed to fetch
        - quota_cost (int): Total API quota cost (4)
        - errors (list): List of {field, error} for any failed fetches
    """
    # Extract and validate video ID
    try:
        video_id = extract_video_id(video_url_or_id)
    except ValueError as e:
        return {
            'success': False,
            'video_id': None,
            'transcript': None,
            'metadata': None,
            'statistics': None,
            'comments': None,
            'partial_success': False,
            'quota_cost': 0,
            'errors': [{'field': 'video_id', 'error': str(e)}]
        }

    # Initialize result structure
    result = {
        'success': True,
        'video_id': video_id,
        'transcript': None,
        'metadata': None,
        'statistics': None,
        'comments': None,
        'partial_success': False,
        'quota_cost': 4,  # transcript=0, metadata=1, stats=1, comments=2 (for threads)
        'errors': []
    }

    # Fetch transcript, metadata, statistics in parallel (via get_unified_video_data)
    try:
        unified_data = get_unified_video_data(video_id)

        # Extract data from unified response
        result['transcript'] = unified_data.get('transcript')
        result['metadata'] = unified_data.get('metadata')
        result['statistics'] = unified_data.get('statistics')

        # Merge errors from unified fetch
        if unified_data.get('errors'):
            result['errors'].extend(unified_data['errors'])
            result['partial_success'] = True

        # Update quota_cost base (3 for unified data)
        result['quota_cost'] = unified_data.get('quota_cost', 3)

    except Exception as e:
        result['errors'].append({'field': 'unified_data', 'error': str(e)})
        result['partial_success'] = True

    # Fetch comments separately (not in unified endpoint)
    try:
        comments = get_comments_for_video(video_id, max_results=100)
        result['comments'] = comments
        result['quota_cost'] += 1  # Add 1 for comments (threads endpoint)

    except Exception as e:
        # Comments failure shouldn't fail the entire request
        result['comments'] = None
        result['errors'].append({'field': 'comments', 'error': str(e)})
        result['partial_success'] = True

    # Check if all fetches failed
    has_any_data = any([
        result['transcript'] is not None,
        result['metadata'] is not None,
        result['statistics'] is not None,
        result['comments'] is not None
    ])

    if not has_any_data:
        result['success'] = False

    return result


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
