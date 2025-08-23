#!/usr/bin/env python3
"""
MCP UI Server - Main Entry Point
Clean, minimal entry point that uses the tool registry.
"""

import logging
from fastmcp import FastMCP
from mcp_local.ui_server.tool_registry import initialize_tools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the FastMCP server
mcp = FastMCP("mcp-ui-server")

# Initialize and register all tools from the tools directory
logger.info("Starting MCP UI Server...")
logger.info("Initializing tools from registry...")

# The tool registry will automatically discover and register all tools
tools = initialize_tools(mcp)

logger.info(f"MCP UI Server ready with {len(tools.list_tools())} tools: {', '.join(tools.list_tools())}")

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()