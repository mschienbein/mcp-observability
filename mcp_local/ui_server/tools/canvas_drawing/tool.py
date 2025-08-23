"""Canvas Drawing MCP Tool - Self-contained implementation."""

import uuid
from pathlib import Path
from typing import Dict, Any
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def canvas_drawing(ctx: Context) -> Dict[str, Any]:
    """
    Shows an interactive canvas drawing application.
    Demonstrates HTML5 Canvas API usage in MCP UI.
    
    Returns:
        MCP UI resource response with interactive drawing canvas
    """
    resource_id = str(uuid.uuid4())
    
    # No template variables needed for this tool
    html_content = HTML_TEMPLATE
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://canvas/{resource_id}",
            "name": "Canvas Drawing Application",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "canvas_drawing",
    "description": "Interactive canvas drawing application with multiple tools",
    "function": canvas_drawing
}