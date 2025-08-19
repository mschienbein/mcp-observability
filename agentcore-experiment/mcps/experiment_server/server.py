#!/usr/bin/env python3
"""
Clean MCP Server for AgentCore Runtime
Demonstrates modular architecture with separate tool implementations
"""

from fastmcp import FastMCP
import sys
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common import observability, ObservabilityLevel
from tools import (
    calculate_fibonacci,
    analyze_text,
    generate_random_data,
    weather_simulator,
    system_health_check
)

# Initialize MCP server for AgentCore compatibility
mcp = FastMCP(
    name="AgentCore Experiment Server"
)

# Register all tools with the MCP server
mcp.tool()(calculate_fibonacci)
mcp.tool()(analyze_text)
mcp.tool()(generate_random_data)
mcp.tool()(weather_simulator)
mcp.tool()(system_health_check)


def main():
    """Main entry point for the MCP server"""
    observability.log(
        ObservabilityLevel.INFO,
        "AgentCore Experiment MCP Server starting",
        {
            "host": "0.0.0.0",
            "port": 8000,
            "stateless_http": True,
            "tools": [
                "calculate_fibonacci",
                "analyze_text",
                "generate_random_data",
                "weather_simulator",
                "system_health_check"
            ],
            "architecture": "modular",
            "observability": "custom"
        }
    )
    
    # Run with streamable-http transport for AgentCore Runtime
    # Configuration moved to run() to avoid deprecation warnings
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
        stateless_http=True
    )


if __name__ == "__main__":
    main()