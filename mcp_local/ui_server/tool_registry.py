"""
Tool Registry - Automatically discovers and registers all MCP UI tools.
"""

import importlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Callable
from mcp.server import Server

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for MCP UI tools."""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.tool_functions: Dict[str, Callable] = {}
    
    def discover_tools(self, tools_dir: Path = None) -> List[str]:
        """
        Discover all tools in the tools directory.
        Each tool folder should contain a tool.py file with TOOL_DEFINITION.
        
        Returns:
            List of discovered tool names
        """
        if tools_dir is None:
            tools_dir = Path(__file__).parent / "tools"
        
        discovered = []
        
        # Iterate through all subdirectories in tools/
        for tool_dir in tools_dir.iterdir():
            if not tool_dir.is_dir():
                continue
            
            # Skip special directories
            if tool_dir.name.startswith("_") or tool_dir.name.startswith("."):
                continue
            
            tool_file = tool_dir / "tool.py"
            if not tool_file.exists():
                logger.debug(f"No tool.py found in {tool_dir.name}, skipping")
                continue
            
            try:
                # Import the tool module
                module_name = f"tools.{tool_dir.name}.tool"
                module = importlib.import_module(module_name)
                
                # Check for TOOL_DEFINITION
                if not hasattr(module, "TOOL_DEFINITION"):
                    logger.warning(f"No TOOL_DEFINITION found in {module_name}")
                    continue
                
                tool_def = module.TOOL_DEFINITION
                tool_name = tool_def.get("name", tool_dir.name)
                
                # Store the tool
                self.tools[tool_name] = tool_def
                self.tool_functions[tool_name] = tool_def["function"]
                discovered.append(tool_name)
                
                logger.info(f"Registered tool: {tool_name}")
                
            except Exception as e:
                logger.error(f"Failed to load tool from {tool_dir.name}: {e}")
        
        return discovered
    
    def register_with_mcp(self, mcp_server: Server) -> None:
        """
        Register all discovered tools with an MCP server.
        
        Args:
            mcp_server: The MCP server instance to register tools with
        """
        for tool_name, tool_def in self.tools.items():
            # Get the function and description
            func = tool_def["function"]
            description = tool_def.get("description", f"MCP UI tool: {tool_name}")
            
            # Register with MCP using the decorator
            mcp_server.tool(name=tool_name)(func)
            
            logger.info(f"Registered {tool_name} with MCP server")
    
    def get_tool(self, name: str) -> Dict[str, Any]:
        """Get a specific tool definition by name."""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    def get_tool_function(self, name: str) -> Callable:
        """Get a tool's function by name."""
        return self.tool_functions.get(name)


# Create a global registry instance
registry = ToolRegistry()


def initialize_tools(mcp_server: Server, tools_dir: Path = None) -> ToolRegistry:
    """
    Initialize and register all tools with the MCP server.
    
    Args:
        mcp_server: The MCP server instance
        tools_dir: Optional custom tools directory
    
    Returns:
        The tool registry with all discovered tools
    """
    # Discover all tools
    discovered = registry.discover_tools(tools_dir)
    logger.info(f"Discovered {len(discovered)} tools: {', '.join(discovered)}")
    
    # Register with MCP
    registry.register_with_mcp(mcp_server)
    
    return registry


# Export for convenience
__all__ = ["ToolRegistry", "registry", "initialize_tools"]