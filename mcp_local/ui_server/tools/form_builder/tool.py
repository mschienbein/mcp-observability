"""Form Builder MCP Tool - Self-contained implementation."""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from mcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def form_builder(
    ctx: Context, 
    fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Creates a dynamic form with specified fields.
    
    Args:
        fields: List of field definitions, each containing:
            - name: Field identifier
            - label: Display label
            - type: Input type (text, email, number, select, checkbox, textarea)
            - placeholder: Placeholder text (optional)
            - required: Whether field is required (optional)
            - options: List of options for select fields (optional)
    
    Returns:
        MCP UI resource response with interactive form
    """
    resource_id = str(uuid.uuid4())
    
    # Default fields if none provided
    if not fields:
        fields = [
            {
                "name": "name",
                "label": "Full Name",
                "type": "text",
                "placeholder": "Enter your full name",
                "required": True
            },
            {
                "name": "email",
                "label": "Email Address",
                "type": "email",
                "placeholder": "your@email.com",
                "required": True
            },
            {
                "name": "age",
                "label": "Age",
                "type": "number",
                "placeholder": "Your age"
            },
            {
                "name": "country",
                "label": "Country",
                "type": "select",
                "options": ["United States", "Canada", "United Kingdom", "Australia", "Other"],
                "required": True
            },
            {
                "name": "subscribe",
                "label": "Subscribe to newsletter",
                "type": "checkbox"
            },
            {
                "name": "comments",
                "label": "Comments",
                "type": "textarea",
                "placeholder": "Any additional comments?"
            }
        ]
    
    # Replace template variable with JSON data
    html_content = HTML_TEMPLATE.replace("{{ fields_json }}", json.dumps(fields))
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://form/{resource_id}",
            "name": "Dynamic Form Builder",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "form_builder",
    "description": "Creates a dynamic form with specified fields",
    "function": form_builder
}