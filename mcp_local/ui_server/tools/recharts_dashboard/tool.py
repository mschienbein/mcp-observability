"""Recharts Dashboard MCP Tool - Self-contained implementation."""

import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def recharts_dashboard(
    ctx: Context,
    data: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Shows an interactive dashboard with multiple chart types using Recharts.
    
    Args:
        data: Optional data for charts (uses sample data if not provided)
    
    Returns:
        MCP UI resource response with Recharts dashboard
    """
    resource_id = str(uuid.uuid4())
    
    # Sample data if none provided
    if not data:
        data = [
            {"month": "Jan", "sales": 65, "revenue": 4500, "customers": 28},
            {"month": "Feb", "sales": 78, "revenue": 5200, "customers": 35},
            {"month": "Mar", "sales": 90, "revenue": 6100, "customers": 42},
            {"month": "Apr", "sales": 81, "revenue": 5800, "customers": 38},
            {"month": "May", "sales": 95, "revenue": 7200, "customers": 48},
            {"month": "Jun", "sales": 110, "revenue": 8500, "customers": 55}
        ]
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ chart_data }}", json.dumps(data))
    html_content = html_content.replace("{{ resource_id }}", resource_id)
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://recharts/{resource_id}",
            "name": "Recharts Dashboard",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "recharts_dashboard",
    "description": "Interactive dashboard with multiple chart types using Recharts",
    "function": recharts_dashboard
}