"""Cytoscape Network MCP Tool - Self-contained implementation."""

import uuid
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def cytoscape_network(
    ctx: Context,
    nodes: Optional[List[Dict]] = None,
    edges: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Shows an interactive network/graph visualization using Cytoscape.js.
    
    Args:
        nodes: Optional list of node definitions
        edges: Optional list of edge definitions
    
    Returns:
        MCP UI resource response with Cytoscape network visualization
    """
    resource_id = str(uuid.uuid4())
    
    # Sample network data if none provided
    if not nodes:
        nodes = [
            {"id": "1", "label": "Node 1", "group": "core"},
            {"id": "2", "label": "Node 2", "group": "core"},
            {"id": "3", "label": "Node 3", "group": "secondary"},
            {"id": "4", "label": "Node 4", "group": "secondary"},
            {"id": "5", "label": "Node 5", "group": "tertiary"},
            {"id": "6", "label": "Node 6", "group": "tertiary"}
        ]
    
    if not edges:
        edges = [
            {"source": "1", "target": "2", "label": "connects"},
            {"source": "1", "target": "3", "label": "links"},
            {"source": "2", "target": "4", "label": "relates"},
            {"source": "3", "target": "5", "label": "depends"},
            {"source": "4", "target": "6", "label": "uses"},
            {"source": "5", "target": "6", "label": "requires"}
        ]
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ nodes_data }}", json.dumps(nodes))
    html_content = html_content.replace("{{ edges_data }}", json.dumps(edges))
    html_content = html_content.replace("{{ resource_id }}", resource_id)
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://cytoscape/{resource_id}",
            "name": "Cytoscape Network Visualization",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "cytoscape_network",
    "description": "Interactive network/graph visualization using Cytoscape.js",
    "function": cytoscape_network
}