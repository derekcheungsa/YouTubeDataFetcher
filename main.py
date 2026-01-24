from app import app
import threading
import uvicorn
import os
import requests
import atexit
from flask import request, Response, jsonify
from urllib.parse import urlencode
from mcp_server import create_mcp_app


# Global state for MCP server
_mcp_server_thread = None
_mcp_server_started = False
_mcp_startup_lock = threading.Lock()


def run_mcp_server():
    """Run the MCP server on localhost (internal only)."""
    try:
        mcp_app = create_mcp_app()
        uvicorn.run(
            mcp_app,
            host="127.0.0.1",
            port=8000,
            log_level="error",  # Minimal logging
            access_log=False,
            timeout_keep_alive=30
        )
    except Exception as e:
        print(f"MCP server error: {e}", flush=True)


def ensure_mcp_server_running():
    """Ensure MCP server is running (called on first request)."""
    global _mcp_server_thread, _mcp_server_started

    with _mcp_startup_lock:
        if not _mcp_server_started:
            print("Starting MCP server on-demand...", flush=True)
            _mcp_server_thread = threading.Thread(target=run_mcp_server, daemon=True)
            _mcp_server_thread.start()
            _mcp_server_started = True

            # Give it a moment to start
            import time
            time.sleep(1)


@app.route('/mcp', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/mcp/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def proxy_mcp(path=''):
    """
    Proxy MCP requests to the internal MCP server.

    MCP endpoints are available at /mcp/* and are proxied to
    the internal MCP server running on localhost:8000.
    """
    # Ensure MCP server is running before proxying
    ensure_mcp_server_running()

    # Get the internal MCP server URL
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
        filtered_headers = {}
        skip_headers = {'Host', 'X-Forwarded-Proto', 'X-Forwarded-Host',
                       'X-Forwarded-For', 'X-Forwarded-Port', 'Forwarded'}
        for key, value in request.headers:
            if key not in skip_headers:
                filtered_headers[key] = value

        try:
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

        except requests.exceptions.ConnectionError as e:
            app.logger.error(f"MCP server connection error: {e}")
            return jsonify({"error": "MCP server not available", "detail": str(e)}), 502
        except requests.exceptions.Timeout as e:
            app.logger.error(f"MCP server timeout: {e}")
            return jsonify({"error": "MCP server timeout", "detail": str(e)}), 504
        except Exception as e:
            app.logger.error(f"MCP proxy error: {e}")
            return jsonify({"error": "MCP proxy error", "detail": str(e)}), 500

    return Response("Method not allowed", 405)


if __name__ == "__main__":
    # Get port from Railway environment variable, or default to 5000 for local dev
    port = int(os.environ.get('PORT', 5000))

    # Run Flask app on Railway's PORT (publicly accessible)
    app.run(host="0.0.0.0", port=port)
