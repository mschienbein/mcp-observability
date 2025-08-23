#!/usr/bin/env python3
"""
Refactored MCP UI Server with modular tool structure.
Each tool is in its own folder with separate HTML templates.
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from mcp import Context, Tool
from mcp.server import Server

# Import tool implementations
from tools.simple_ui import show_simple_ui
from tools.form_builder import show_form_builder

# For tools not yet refactored, we'll import from the original file
# These will be gradually moved to the new structure
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# Initialize the MCP server
mcp = Server("mcp-ui-server")


# Register refactored tools
@mcp.tool()
async def simple_ui(ctx: Context, title: str = "Simple MCP UI", message: str = "Hello from MCP!") -> Dict[str, Any]:
    """Shows a simple interactive UI component with a counter."""
    return await show_simple_ui(ctx, title, message)


@mcp.tool()
async def form_builder(ctx: Context, fields: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Creates a dynamic form with specified fields."""
    return await show_form_builder(ctx, fields)


# Template for adding more refactored tools:
# @mcp.tool()
# async def tool_name(ctx: Context, **kwargs) -> Dict[str, Any]:
#     """Tool description."""
#     from tools.tool_folder import tool_function
#     return await tool_function(ctx, **kwargs)


# For now, keep a few original tools here as examples until fully refactored
@mcp.tool()
async def show_data_table(ctx: Context, data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Displays data in an interactive table format.
    This will be refactored into tools/data_table/ folder.
    """
    resource_id = str(uuid.uuid4())
    
    # Sample data if none provided
    if not data:
        data = [
            {"id": 1, "name": "Alice Johnson", "role": "Engineer", "department": "Engineering", "salary": 95000},
            {"id": 2, "name": "Bob Smith", "role": "Designer", "department": "Design", "salary": 85000},
            {"id": 3, "name": "Charlie Brown", "role": "Manager", "department": "Management", "salary": 105000},
            {"id": 4, "name": "Diana Prince", "role": "Developer", "department": "Engineering", "salary": 90000},
            {"id": 5, "name": "Eve Wilson", "role": "Analyst", "department": "Analytics", "salary": 80000}
        ]
    
    # Quick inline template for now (will be moved to tools/data_table/template.html)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: system-ui, -apple-system, sans-serif;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                margin: 0;
            }}
            .table-container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #e2e8f0;
            }}
            th {{
                background: #f7fafc;
                font-weight: 600;
                color: #2d3748;
                cursor: pointer;
                user-select: none;
            }}
            th:hover {{
                background: #edf2f7;
            }}
            tr:hover {{
                background: #f7fafc;
            }}
            .search-box {{
                margin-bottom: 20px;
            }}
            .search-box input {{
                width: 100%;
                padding: 10px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
        <div class="table-container">
            <h1>📊 Data Table</h1>
            
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search..." onkeyup="filterTable()">
            </div>
            
            <table id="dataTable">
                <thead>
                    <tr id="headerRow"></tr>
                </thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
        
        <script>
            const data = {json.dumps(data)};
            let sortColumn = null;
            let sortDirection = 'asc';
            
            function renderTable() {{
                const headerRow = document.getElementById('headerRow');
                const tableBody = document.getElementById('tableBody');
                
                // Clear existing content
                headerRow.innerHTML = '';
                tableBody.innerHTML = '';
                
                if (data.length === 0) return;
                
                // Create headers
                Object.keys(data[0]).forEach(key => {{
                    const th = document.createElement('th');
                    th.textContent = key.charAt(0).toUpperCase() + key.slice(1);
                    th.onclick = () => sortTable(key);
                    headerRow.appendChild(th);
                }});
                
                // Create rows
                data.forEach(row => {{
                    const tr = document.createElement('tr');
                    Object.values(row).forEach(value => {{
                        const td = document.createElement('td');
                        td.textContent = value;
                        tr.appendChild(td);
                    }});
                    tableBody.appendChild(tr);
                }});
            }}
            
            function sortTable(column) {{
                if (sortColumn === column) {{
                    sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
                }} else {{
                    sortColumn = column;
                    sortDirection = 'asc';
                }}
                
                data.sort((a, b) => {{
                    let aVal = a[column];
                    let bVal = b[column];
                    
                    if (typeof aVal === 'string') {{
                        aVal = aVal.toLowerCase();
                        bVal = bVal.toLowerCase();
                    }}
                    
                    if (sortDirection === 'asc') {{
                        return aVal > bVal ? 1 : -1;
                    }} else {{
                        return aVal < bVal ? 1 : -1;
                    }}
                }});
                
                renderTable();
            }}
            
            function filterTable() {{
                const input = document.getElementById('searchInput');
                const filter = input.value.toLowerCase();
                const rows = document.getElementById('tableBody').getElementsByTagName('tr');
                
                for (let i = 0; i < rows.length; i++) {{
                    const cells = rows[i].getElementsByTagName('td');
                    let match = false;
                    
                    for (let j = 0; j < cells.length; j++) {{
                        if (cells[j].textContent.toLowerCase().indexOf(filter) > -1) {{
                            match = true;
                            break;
                        }}
                    }}
                    
                    rows[i].style.display = match ? '' : 'none';
                }}
            }}
            
            // Initial render
            renderTable();
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://table/{resource_id}",
            "name": "Data Table",
            "mimeType": "text/html",
            "text": html_content
        }
    }


if __name__ == "__main__":
    # Run the MCP server
    print("Starting refactored MCP UI Server...")
    print("Tools are now organized in the tools/ folder")
    print("Each tool has its own folder with separate HTML templates")
    mcp.run()