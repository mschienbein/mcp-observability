"""Interactive Chart MCP Tool - Self-contained implementation."""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from mcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def interactive_chart(
    ctx: Context,
    title: str = "Interactive Chart Visualization",
    chart_type: str = "line",
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates an interactive chart visualization using Chart.js.
    
    Args:
        title: Chart title
        chart_type: Initial chart type (line, bar, pie, doughnut, radar, polarArea)
        data: Chart data in Chart.js format
    
    Returns:
        MCP UI resource response with interactive chart
    """
    resource_id = str(uuid.uuid4())
    
    # Default data if none provided
    if not data:
        data = {
            "labels": ["January", "February", "March", "April", "May", "June"],
            "datasets": [
                {
                    "label": "Sales",
                    "data": [65, 78, 90, 81, 56, 95],
                    "backgroundColor": [
                        "rgba(102, 126, 234, 0.8)",
                        "rgba(72, 187, 120, 0.8)",
                        "rgba(251, 191, 36, 0.8)",
                        "rgba(239, 68, 68, 0.8)",
                        "rgba(139, 92, 246, 0.8)",
                        "rgba(59, 130, 246, 0.8)"
                    ],
                    "borderColor": [
                        "rgba(102, 126, 234, 1)",
                        "rgba(72, 187, 120, 1)",
                        "rgba(251, 191, 36, 1)",
                        "rgba(239, 68, 68, 1)",
                        "rgba(139, 92, 246, 1)",
                        "rgba(59, 130, 246, 1)"
                    ],
                    "borderWidth": 2
                }
            ]
        }
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ chart_title }}", title)
    html_content = html_content.replace("{{ initial_chart_type }}", chart_type)
    html_content = html_content.replace("{{ chart_data }}", json.dumps(data))
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://chart/{resource_id}",
            "name": "Interactive Chart",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "interactive_chart",
    "description": "Creates an interactive chart visualization",
    "function": interactive_chart
}