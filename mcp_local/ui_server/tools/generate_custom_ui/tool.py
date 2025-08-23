"""Generate Custom UI MCP Tool - Self-contained implementation."""

import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def generate_custom_ui(
    ctx: Context,
    prompt: str = "Create a beautiful dashboard",
    style: str = "modern",
    include_interactions: bool = True
) -> Dict[str, Any]:
    """
    Generates a custom UI component based on natural language description.
    This simulates an AI-generated UI (in production, would call an LLM).
    
    Args:
        prompt: Natural language description of desired UI
        style: Visual style preference (modern, minimal, corporate, playful)
        include_interactions: Whether to include interactive elements
    
    Returns:
        MCP UI resource response with generated custom UI
    """
    resource_id = str(uuid.uuid4())
    
    # In a real implementation, this would call an LLM to generate the UI
    # For now, we'll use a template that demonstrates the concept
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ prompt }}", prompt)
    html_content = html_content.replace("{{ style }}", style)
    html_content = html_content.replace("{{ resource_id }}", resource_id)
    html_content = html_content.replace("{{ include_interactions }}", str(include_interactions).lower())
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://custom/{resource_id}",
            "name": "AI-Generated Custom UI",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "generate_custom_ui",
    "description": "Generates custom UI components based on natural language descriptions",
    "function": generate_custom_ui
}