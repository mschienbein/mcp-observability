"""Code Editor MCP Tool - Self-contained implementation."""

import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def code_editor(
    ctx: Context,
    initial_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Shows an interactive code editor with syntax highlighting.
    
    Args:
        initial_code: Initial code to display in the editor
    
    Returns:
        MCP UI resource response with code editor
    """
    resource_id = str(uuid.uuid4())
    
    # Default Python code if none provided
    if not initial_code:
        initial_code = '''# Welcome to the MCP Code Editor
def fibonacci(n):
    """Generate Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    
    return fib

# Example usage
result = fibonacci(10)
print(f"First 10 Fibonacci numbers: {result}")'''
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ initial_code }}", initial_code)
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://code-editor/{resource_id}",
            "name": "Code Editor",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "code_editor",
    "description": "Interactive code editor with syntax highlighting",
    "function": code_editor
}