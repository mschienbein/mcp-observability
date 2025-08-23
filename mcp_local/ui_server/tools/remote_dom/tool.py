"""Remote DOM MCP Tool - Self-contained implementation."""

import uuid
from pathlib import Path
from typing import Dict, Any
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def remote_dom(
    ctx: Context,
    button_label: str = "Click me!"
) -> Dict[str, Any]:
    """
    Demonstrates Remote DOM pattern with custom web components and message passing.
    This shows how to create reusable UI components that communicate with MCP.
    
    Args:
        button_label: Label for the main button
    
    Returns:
        MCP UI resource response with remote DOM components
    """
    resource_id = str(uuid.uuid4())
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ button_label }}", button_label)
    html_content = html_content.replace("{{ resource_id }}", resource_id)
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://remote-dom/{resource_id}",
            "name": "Remote DOM Components",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "remote_dom",
    "description": "Remote DOM pattern with custom web components",
    "function": remote_dom
}