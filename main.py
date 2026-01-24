from app import app
import threading
import uvicorn
import os
import requests
from flask import request, Response
from urllib.parse import urlencode
from mcp_server import create_mcp_app


def run_mcp_server():
    """Run the MCP server on localhost (internal only)."""
    mcp_app = create_mcp_app()
    # Run on localhost so it's not publicly accessible
    uvicorn.run(mcp_app, host="127.0.0.1", port=8000, log_level="warning")


@app.route('/mcp', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/mcp/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def proxy_mcp(path=''):
    """
    Proxy MCP requests to the internal MCP server.

    This allows both Flask REST API and MCP Server to be accessible
    through Railway's single exposed port.

    MCP endpoints are available at /mcp/* and are proxied to
    the internal MCP server running on localhost:8000.
    """
    # Get the internal MCP server URL
    # Avoid double slash when path is empty
    path_suffix = f"/{path}" if path else ""
    mcp_url = f"http://127.0.0.1:8000/mcp{path_suffix}"

    # Forward the request to the MCP server
    if request.method == 'OPTIONS':
        # Handle CORS preflight
        response = Response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    elif request.method in ['GET', 'POST']:
        # Build URL with query string if present
        if request.args:
            query_string = urlencode(request.args)
            full_url = f"{mcp_url}?{query_string}"
        else:
            full_url = mcp_url

        # Filter headers to avoid protocol issues
        # Remove headers that could cause SSL/protocol upgrades
        filtered_headers = {}
        skip_headers = {'Host', 'X-Forwarded-Proto', 'X-Forwarded-Host',
                       'X-Forwarded-For', 'X-Forwarded-Port', 'Forwarded'}
        for key, value in request.headers:
            if key not in skip_headers:
                filtered_headers[key] = value

        # Forward GET/POST requests
        resp = requests.request(
            method=request.method,
            url=full_url,
            headers=filtered_headers,
            data=request.get_data(),
            timeout=30
        )

        # Create Flask response from MCP server response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response

    return Response("Method not allowed", 405)


if __name__ == "__main__":
    # Start MCP server in a background thread (internal only)
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()

    # Get port from Railway environment variable, or default to 5000 for local dev
    port = int(os.environ.get('PORT', 5000))

    # Run Flask app on Railway's PORT (publicly accessible)
    # Flask proxies /mcp/* requests to internal MCP server
    app.run(host="0.0.0.0", port=port)
