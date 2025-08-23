"""React Interactive MCP Tool - Self-contained implementation."""

import uuid
from pathlib import Path
from typing import Dict, Any
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def react_interactive(
    ctx: Context,
    initial_count: int = 0
) -> Dict[str, Any]:
    """
    Shows an interactive React component with state management.
    
    Args:
        initial_count: Initial counter value
    
    Returns:
        MCP UI resource response with React interactive component
    """
    resource_id = str(uuid.uuid4())
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ initial_count }}", str(initial_count))
    html_content = html_content.replace("{{ resource_id }}", resource_id)
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://react/{resource_id}",
            "name": "React Interactive Component",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "react_interactive",
    "description": "Interactive React component with state management",
    "function": react_interactive
}