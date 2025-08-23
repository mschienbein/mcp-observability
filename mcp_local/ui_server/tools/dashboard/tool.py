"""Dashboard MCP Tool - Self-contained implementation."""

import uuid
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def dashboard(ctx: Context, refresh: bool = False) -> Dict[str, Any]:
    """
    Shows an interactive system dashboard with live metrics.
    
    Args:
        refresh: Whether this is a refresh request
    
    Returns:
        MCP UI resource response with system dashboard
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resource_id = str(uuid.uuid4())
    
    # Generate random metrics for demo
    cpu_usage = random.randint(30, 70)
    memory_gb = round(random.uniform(4.0, 12.0), 1)
    active_users = random.randint(800, 1500)
    requests_per_min = random.randint(500, 1200)
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ current_time }}", current_time)
    html_content = html_content.replace("{{ cpu_usage }}", str(cpu_usage))
    html_content = html_content.replace("{{ memory_gb }}", str(memory_gb))
    html_content = html_content.replace("{{ active_users }}", str(active_users))
    html_content = html_content.replace("{{ requests_per_min }}", str(requests_per_min))
    html_content = html_content.replace("{{ resource_id }}", resource_id)
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://dashboard/{resource_id}",
            "name": "System Dashboard",
            "mimeType": "text/html",
            "text": html_content
        }
    }


async def dashboard_action(ctx: Context, action: str) -> Dict[str, Any]:
    """
    Handles actions from the dashboard UI.
    
    Args:
        action: The action to perform (refresh, export, settings)
    
    Returns:
        Response based on the action
    """
    if action == "refresh":
        # Return a new dashboard with updated data
        return await dashboard(ctx, refresh=True)
    elif action == "export":
        return {
            "type": "text",
            "text": "📊 Export Report Generated!\n\nReport Summary:\n- Time Period: Last 24 hours\n- Total Requests: 1,234,567\n- Average Response Time: 45ms\n- Uptime: 99.98%\n- Error Rate: 0.02%\n\nThe full report has been generated and would normally be downloaded as a CSV/PDF file."
        }
    elif action == "settings":
        return {
            "type": "text",
            "text": "⚙️ Settings Panel\n\nAvailable settings:\n- Dashboard refresh interval: 5 seconds\n- Metric units: Standard\n- Theme: Light\n- Notifications: Enabled\n- Data retention: 30 days\n\nUse the settings tool to modify these values."
        }
    else:
        return {
            "type": "text",
            "text": f"Unknown action: {action}"
        }


# Tool metadata for registration - main dashboard tool
TOOL_DEFINITION = {
    "name": "dashboard",
    "description": "Interactive system dashboard with live metrics",
    "function": dashboard
}

# Additional tool for handling dashboard actions
DASHBOARD_ACTION_TOOL = {
    "name": "dashboard_action",
    "description": "Handles actions from the dashboard UI",
    "function": dashboard_action
}