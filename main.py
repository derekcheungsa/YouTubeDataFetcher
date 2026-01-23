from app import app
import threading
import uvicorn
from mcp_server import create_mcp_app


def run_mcp_server():
    """Run the MCP server in a separate thread."""
    mcp_app = create_mcp_app()
    uvicorn.run(mcp_app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    # Start MCP server in a background thread
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()

    # Run Flask app in the main thread
    app.run(host="0.0.0.0", port=5000)
