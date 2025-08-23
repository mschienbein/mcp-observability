"""Base64 Image MCP Tool - Self-contained implementation."""

import base64
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def base64_image(ctx: Context, text: str = "MCP UI") -> Dict[str, Any]:
    """
    Generates and displays a dynamic Base64-encoded SVG image.
    
    Args:
        text: Text to display in the generated image
    
    Returns:
        MCP UI resource response with base64-encoded SVG image
    """
    resource_id = str(uuid.uuid4())
    
    # Create an SVG image
    svg_content = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
        <defs>
            <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
            </linearGradient>
            <filter id="shadow">
                <feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.3"/>
            </filter>
        </defs>
        
        <!-- Background -->
        <rect width="600" height="400" fill="url(#bg)"/>
        
        <!-- Decorative circles -->
        <circle cx="100" cy="100" r="60" fill="white" opacity="0.1"/>
        <circle cx="500" cy="300" r="80" fill="white" opacity="0.1"/>
        <circle cx="300" cy="350" r="40" fill="white" opacity="0.1"/>
        
        <!-- Main content card -->
        <rect x="100" y="100" width="400" height="200" rx="20" fill="white" filter="url(#shadow)"/>
        
        <!-- Text -->
        <text x="300" y="180" font-family="system-ui, -apple-system, sans-serif" font-size="36" font-weight="bold" text-anchor="middle" fill="#333">
            {text}
        </text>
        <text x="300" y="220" font-family="system-ui, -apple-system, sans-serif" font-size="18" text-anchor="middle" fill="#666">
            Generated at {datetime.now().strftime('%H:%M:%S')}
        </text>
    </svg>
    """
    
    # Encode to base64
    svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ svg_base64 }}", svg_base64)
    html_content = html_content.replace("{{ base64_length }}", str(len(svg_base64)))
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://base64image/{resource_id}",
            "name": "Base64 SVG Image",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "base64_image",
    "description": "Generates and displays a dynamic Base64-encoded SVG image",
    "function": base64_image
}