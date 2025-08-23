# MCP UI Server Tools

This directory contains modular MCP UI tools, each organized in its own folder with separate HTML templates. Tools are automatically discovered and registered by the tool registry.

## Structure

```
ui_server/
├── main.py                     # Clean entry point
├── tool_registry.py            # Automatic tool discovery and registration
└── tools/
    ├── simple_ui/              # Simple UI component
    │   ├── tool.py            # Tool implementation with TOOL_DEFINITION
    │   └── template.html      # HTML template
    ├── form_builder/          # Dynamic form builder
    │   ├── tool.py
    │   └── template.html
    ├── data_table/            # Data table
    │   ├── tool.py
    │   └── template.html
    └── ... (other tools)
```

## Creating a New Tool

1. Create a new folder in `tools/` with your tool name
2. Create `tool.py` with the tool implementation and TOOL_DEFINITION
3. Create `template.html` with the HTML/CSS/JS
4. The tool will be automatically discovered and registered!

### Example Tool Structure

```python
# tools/my_tool/tool.py
import uuid
from pathlib import Path
from typing import Dict, Any
from mcp import Context

# Load template
TEMPLATE_PATH = Path(__file__).parent / "template.html"
HTML_TEMPLATE = TEMPLATE_PATH.read_text()

async def my_tool(ctx: Context, param1: str = "default", param2: int = 42) -> Dict[str, Any]:
    """Tool description."""
    resource_id = str(uuid.uuid4())
    
    # Replace template variables
    html_content = HTML_TEMPLATE.replace("{{ param1 }}", param1)
    html_content = html_content.replace("{{ param2 }}", str(param2))
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://my_tool/{resource_id}",
            "name": "My Tool",
            "mimeType": "text/html",
            "text": html_content
        }
    }

# REQUIRED: Tool definition for auto-registration
TOOL_DEFINITION = {
    "name": "my_tool",
    "description": "Description of what my tool does",
    "function": my_tool
}
```

### Template Variables

Templates use `{{ variable }}` syntax for placeholders that get replaced:

```html
<!-- template.html -->
<h1>{{ title }}</h1>
<p>{{ message }}</p>
<script>
    const data = {{ json_data }};
</script>
```

## How It Works

1. **Auto-Discovery**: The `tool_registry.py` scans the `tools/` directory
2. **Tool Loading**: Each `tool.py` file with a `TOOL_DEFINITION` is loaded
3. **Registration**: Tools are automatically registered with the MCP server
4. **No Manual Imports**: Just create the tool folder and files - that's it!

## Benefits of This Structure

1. **Separation of Concerns** - HTML/CSS/JS separated from Python logic
2. **Maintainability** - Each tool is self-contained
3. **Reusability** - Common utilities shared across tools
4. **Testability** - Tools can be tested independently
5. **Collaboration** - Multiple developers can work on different tools
6. **Version Control** - Better diff tracking for templates

## Migration Status

- [x] simple_ui - Fully refactored with auto-registration
- [x] form_builder - Fully refactored with auto-registration
- [x] interactive_chart - Fully refactored with auto-registration
- [x] data_table - Fully refactored with auto-registration
- [x] file_viewer - Fully refactored with auto-registration
- [x] markdown_viewer - Fully refactored with auto-registration
- [x] canvas_drawing - Fully refactored with auto-registration
- [x] base64_image - Fully refactored with auto-registration
- [x] realtime_data - Fully refactored with auto-registration
- [x] code_editor - Fully refactored with auto-registration
- [x] react_interactive - Fully refactored with auto-registration
- [x] recharts_dashboard - Fully refactored with auto-registration
- [x] cytoscape_network - Fully refactored with auto-registration
- [x] generate_custom_ui - Fully refactored with auto-registration

## Usage

The main entry point is incredibly simple:

```python
# main.py
from mcp.server import Server
from tool_registry import initialize_tools

# Create MCP server
mcp = Server("mcp-ui-server")

# Auto-discover and register all tools
tools = initialize_tools(mcp)

# Run the server
mcp.run()
```

That's it! All tools in the `tools/` directory are automatically discovered and registered.