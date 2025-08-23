"""Data Table MCP Tool - Self-contained implementation."""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def data_table(
    ctx: Context,
    title: str = "Data Table",
    data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Displays data in an interactive, sortable, searchable table format.
    
    Args:
        title: Table title
        data: List of dictionaries representing table rows
    
    Returns:
        MCP UI resource response with interactive data table
    """
    resource_id = str(uuid.uuid4())
    
    # Sample data if none provided
    if not data:
        data = [
            {"id": 1, "name": "Alice Johnson", "role": "Engineer", "department": "Engineering", "salary": 95000},
            {"id": 2, "name": "Bob Smith", "role": "Designer", "department": "Design", "salary": 85000},
            {"id": 3, "name": "Charlie Brown", "role": "Manager", "department": "Management", "salary": 105000},
            {"id": 4, "name": "Diana Prince", "role": "Developer", "department": "Engineering", "salary": 90000},
            {"id": 5, "name": "Eve Wilson", "role": "Analyst", "department": "Analytics", "salary": 80000},
            {"id": 6, "name": "Frank Miller", "role": "DevOps", "department": "Engineering", "salary": 92000},
            {"id": 7, "name": "Grace Lee", "role": "Product Manager", "department": "Product", "salary": 110000},
            {"id": 8, "name": "Henry Ford", "role": "QA Engineer", "department": "Quality", "salary": 75000},
            {"id": 9, "name": "Iris West", "role": "UX Designer", "department": "Design", "salary": 88000},
            {"id": 10, "name": "Jack Ryan", "role": "Security Engineer", "department": "Security", "salary": 98000}
        ]
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ title }}", title)
    html_content = html_content.replace("{{ table_data }}", json.dumps(data))
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://table/{resource_id}",
            "name": "Data Table",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "data_table",
    "description": "Displays data in an interactive table format",
    "function": data_table
}