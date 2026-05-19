"""Compatibility entry point for QualityPilot's MCP server.

The installable ``mcp-server`` console script now points directly to
``src.mcp_server.server:main``. This module remains as a clear forwarding
entry point for users who still run ``python main.py``.
"""

import sys

from src.mcp_server.server import main as run_mcp_server


def main() -> int:
    """Run the real MCP server entry point."""
    return run_mcp_server()


if __name__ == "__main__":
    sys.exit(main())
