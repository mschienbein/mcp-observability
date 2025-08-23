"""Utility functions for MCP UI tools."""

import json
from pathlib import Path
from typing import Any, Dict, Optional


def load_template(template_name: str, tool_folder: Path) -> str:
    """Load an HTML template from a tool folder."""
    template_path = tool_folder / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text()


def render_template(template: str, **kwargs) -> str:
    """
    Simple template rendering with placeholder replacement.
    Supports both {{ variable }} and {variable} syntax.
    """
    rendered = template
    
    for key, value in kwargs.items():
        # Handle different value types
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value)
        elif value is None:
            value_str = ""
        else:
            value_str = str(value)
        
        # Replace both {{ key }} and {key} patterns
        rendered = rendered.replace(f"{{{{ {key} }}}}", value_str)
        rendered = rendered.replace(f"{{{key}}}", value_str)
    
    return rendered


def create_ui_resource(
    uri_prefix: str,
    resource_id: str,
    name: str,
    html_content: str,
    mime_type: str = "text/html"
) -> Dict[str, Any]:
    """Create a standard MCP UI resource response."""
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://{uri_prefix}/{resource_id}",
            "name": name,
            "mimeType": mime_type,
            "text": html_content
        }
    }


def escape_js_string(s: str) -> str:
    """Escape a string for safe inclusion in JavaScript."""
    if not s:
        return ""
    
    # Escape backslashes first, then quotes and newlines
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("'", "\\'")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("\t", "\\t")
    
    # Escape backticks for template literals
    s = s.replace("`", "\\`")
    
    return s


def sanitize_html(html: str) -> str:
    """Basic HTML sanitization to prevent XSS."""
    # Remove script tags
    import re
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove event handlers
    html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
    html = re.sub(r'\s*on\w+\s*=\s*[^\s>]+', '', html, flags=re.IGNORECASE)
    
    return html