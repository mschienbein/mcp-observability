"""Real-time Data MCP Tool - Self-contained implementation."""

import uuid
from pathlib import Path
from typing import Dict, Any
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def realtime_data(ctx: Context) -> Dict[str, Any]:
    """
    Shows a real-time data visualization with WebSocket simulation.
    Demonstrates dynamic updates and live data streaming in MCP UI.
    
    Returns:
        MCP UI resource response with real-time data monitor
    """
    resource_id = str(uuid.uuid4())
    
    # No template variables needed for this tool
    html_content = HTML_TEMPLATE
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://realtime/{resource_id}",
            "name": "Real-time Data Monitor",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "realtime_data",
    "description": "Real-time data visualization with live updates",
    "function": realtime_data
}