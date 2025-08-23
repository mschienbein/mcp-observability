"""Simple UI MCP Tool - Self-contained implementation."""

import uuid
from pathlib import Path
from typing import Dict, Any
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def simple_ui(ctx: Context, title: str = "Simple MCP UI", message: str = "Hello from MCP!") -> Dict[str, Any]:
    """
    Shows a simple interactive UI component with a counter.
    This demonstrates basic UI capabilities in MCP tools.
    
    Args:
        title: The title to display in the UI
        message: The message to show in the UI
    
    Returns:
        MCP UI resource response
    """
    resource_id = str(uuid.uuid4())
    
    # Replace placeholders in template
    html_content = HTML_TEMPLATE.replace("{{ title }}", title).replace("{{ message }}", message)
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://simple/{resource_id}",
            "name": "Simple UI Component",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "simple_ui",
    "description": "Shows a simple interactive UI component with a counter",
    "function": simple_ui
}