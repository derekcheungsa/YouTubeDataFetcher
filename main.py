"""
Main entry point for the YouTube Data Fetcher application.

This module starts the Flask REST API and MCP Server in a single process
for deployment on Railway (single-port architecture).
"""

from app import app
import os

if __name__ == "__main__":
    # Get port from Railway environment variable, or default to 5000 for local dev
    port = int(os.environ.get('PORT', 5000))

    # Run Flask app on Railway's PORT (publicly accessible)
    # The MCP proxy is now in app.py and starts on-demand
    app.run(host="0.0.0.0", port=port)
