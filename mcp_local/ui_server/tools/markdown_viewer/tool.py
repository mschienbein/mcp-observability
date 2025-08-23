"""Markdown Viewer MCP Tool - Self-contained implementation."""

import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastmcp import Context

# Load the HTML template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()


async def markdown_viewer(
    ctx: Context,
    content: Optional[str] = None
) -> Dict[str, Any]:
    """
    Displays rich Markdown content with syntax highlighting and interactive features.
    
    Args:
        content: Markdown content to display (uses default if not provided)
    
    Returns:
        MCP UI resource response with rendered markdown viewer
    """
    resource_id = str(uuid.uuid4())
    
    default_content = """# Welcome to MCP UI Markdown Viewer

## Features

This viewer supports **all** standard Markdown features:

- **Bold** and *italic* text
- ~~Strikethrough~~ text
- `Inline code` snippets
- [Links](https://mcpui.dev) to external resources

### Code Blocks with Syntax Highlighting

```python
# Python example
def greet(name: str) -> str:
    '''Returns a personalized greeting'''
    return f"Hello, {name}! Welcome to MCP UI!"

# Using the function
message = greet("Developer")
print(message)
```

```javascript
// JavaScript example
const calculateSum = (numbers) => {
  return numbers.reduce((acc, num) => acc + num, 0);
};

const result = calculateSum([1, 2, 3, 4, 5]);
console.log(`Sum: ${result}`);
```

### Tables

| Feature | Status | Description |
|---------|--------|-------------|
| Markdown Parsing | ✅ Complete | Full CommonMark support |
| Syntax Highlighting | ✅ Complete | Multiple language support |
| Interactive Elements | ✅ Complete | Buttons, forms, etc. |

### Task Lists

- [x] Basic Markdown rendering
- [x] Code syntax highlighting
- [x] Table support
- [ ] Mermaid diagram support
- [ ] LaTeX math rendering
"""
    
    markdown_content = content or default_content
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ markdown_content }}", markdown_content)
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://markdown/{resource_id}",
            "name": "Markdown Viewer",
            "mimeType": "text/html",
            "text": html_content
        }
    }


# Tool metadata for registration
TOOL_DEFINITION = {
    "name": "markdown_viewer",
    "description": "Displays rich Markdown content with syntax highlighting",
    "function": markdown_viewer
}