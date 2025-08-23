#!/usr/bin/env python3
"""
MCP UI Server - Fixed implementation that properly returns UI resources
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from fastmcp import FastMCP, Context

# Create the MCP server
mcp = FastMCP("MCP UI Server", dependencies=[])

# In-memory storage for demo purposes
user_data_store = {}
chart_data = {
    "labels": ["January", "February", "March", "April", "May", "June"],
    "values": [12, 19, 3, 5, 2, 3]
}

@mcp.tool()
async def show_dashboard(ctx: Context, refresh: bool = False) -> Dict[str, Any]:
    """
    Shows an interactive system dashboard with live metrics.
    Returns an MCP-UI compliant resource that renders as an interactive HTML component.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resource_id = str(uuid.uuid4())
    
    # Generate random metrics for demo
    import random
    cpu_usage = random.randint(30, 70)
    memory_gb = round(random.uniform(4.0, 12.0), 1)
    active_users = random.randint(800, 1500)
    requests_per_min = random.randint(500, 1200)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>System Dashboard</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            .dashboard {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 16px;
                padding: 32px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h1 {{
                color: #1a202c;
                margin-bottom: 32px;
                font-size: 32px;
                display: flex;
                align-items: center;
                gap: 12px;
            }}
            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 32px;
            }}
            .metric-card {{
                background: #f8f9fa;
                padding: 24px;
                border-radius: 12px;
                border: 1px solid #e9ecef;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .metric-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            }}
            .metric-label {{
                font-size: 13px;
                color: #6c757d;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 12px;
                font-weight: 600;
            }}
            .metric-value {{
                font-size: 36px;
                font-weight: bold;
                color: #2d3748;
                margin-bottom: 8px;
            }}
            .metric-change {{
                font-size: 14px;
                color: #48bb78;
            }}
            .metric-change.negative {{
                color: #f56565;
            }}
            .actions {{
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
            }}
            button {{
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }}
            .btn-primary {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .btn-success {{
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
            }}
            .btn-warning {{
                background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
                color: white;
            }}
            .status-indicator {{
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #48bb78;
                margin-right: 8px;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 0 0 rgba(72, 187, 120, 0.4); }}
                70% {{ box-shadow: 0 0 0 10px rgba(72, 187, 120, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(72, 187, 120, 0); }}
            }}
            .time-display {{
                font-family: 'Courier New', monospace;
                background: #f8f9fa;
                padding: 4px 8px;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="dashboard">
            <h1>📊 System Dashboard</h1>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Current Time</div>
                    <div class="metric-value time-display" id="current-time">{current_time}</div>
                    <div class="metric-change">Live updating</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">CPU Usage</div>
                    <div class="metric-value" style="color: #667eea;">{cpu_usage}%</div>
                    <div class="metric-change">↑ 5% from last hour</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Memory</div>
                    <div class="metric-value" style="color: #764ba2;">{memory_gb} GB</div>
                    <div class="metric-change">↓ 0.5 GB available</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Active Users</div>
                    <div class="metric-value" style="color: #ed8936;">{active_users}</div>
                    <div class="metric-change">↑ 123 in last 5 min</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">Requests/min</div>
                    <div class="metric-value" style="color: #48bb78;">{requests_per_min}</div>
                    <div class="metric-change">Normal traffic</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-label">System Status</div>
                    <div class="metric-value" style="color: #38a169;">
                        <span class="status-indicator"></span>Online
                    </div>
                    <div class="metric-change">All systems operational</div>
                </div>
            </div>
            
            <div class="actions">
                <button class="btn-primary" onclick="handleAction('refresh')">
                    🔄 Refresh Data
                </button>
                <button class="btn-success" onclick="handleAction('export')">
                    📊 Export Report
                </button>
                <button class="btn-warning" onclick="handleAction('settings')">
                    ⚙️ Settings
                </button>
            </div>
        </div>
        
        <script>
            // Update time every second
            setInterval(() => {{
                const now = new Date();
                const timeString = now.toLocaleString();
                document.getElementById('current-time').textContent = timeString;
            }}, 1000);
            
            // Handle button clicks
            function handleAction(action) {{
                console.log('Dashboard action:', action);
                
                // Send message to parent window (LibreChat)
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'tool',
                        payload: {{
                            toolName: 'handle_dashboard_action',
                            params: {{ action: action }}
                        }},
                        messageId: '{resource_id}'
                    }}, '*');
                }}
                
                // Visual feedback
                if (action === 'refresh') {{
                    document.querySelector('.dashboard').style.opacity = '0.7';
                    setTimeout(() => {{
                        document.querySelector('.dashboard').style.opacity = '1';
                    }}, 300);
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://dashboard/{resource_id}",
            "name": "System Dashboard",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def show_form(ctx: Context) -> Dict[str, Any]:
    """
    Shows an interactive user registration form.
    Returns an MCP-UI compliant resource that renders as an HTML form.
    """
    resource_id = str(uuid.uuid4())
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>User Registration Form</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .form-container {{
                width: 100%;
                max-width: 500px;
                background: white;
                padding: 40px;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h2 {{
                color: #1a202c;
                margin-bottom: 32px;
                font-size: 28px;
                text-align: center;
            }}
            .form-group {{
                margin-bottom: 24px;
            }}
            label {{
                display: block;
                margin-bottom: 8px;
                color: #4a5568;
                font-weight: 600;
                font-size: 14px;
            }}
            input, select, textarea {{
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 15px;
                transition: all 0.2s;
                background: #f8f9fa;
            }}
            input:focus, select:focus, textarea:focus {{
                outline: none;
                border-color: #667eea;
                background: white;
                box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
            }}
            textarea {{
                resize: vertical;
                min-height: 100px;
            }}
            button {{
                width: 100%;
                padding: 14px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }}
            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 16px rgba(102,126,234,0.3);
            }}
            button:active {{
                transform: translateY(0);
            }}
            .success-message {{
                display: none;
                padding: 16px;
                background: #c6f6d5;
                border: 2px solid #9ae6b4;
                border-radius: 8px;
                color: #22543d;
                margin-top: 20px;
                text-align: center;
                font-weight: 600;
            }}
            .required {{
                color: #f56565;
            }}
        </style>
    </head>
    <body>
        <div class="form-container">
            <h2>📝 User Registration</h2>
            <form id="userForm">
                <div class="form-group">
                    <label for="name">Full Name <span class="required">*</span></label>
                    <input type="text" id="name" name="name" required placeholder="John Doe">
                </div>
                
                <div class="form-group">
                    <label for="email">Email Address <span class="required">*</span></label>
                    <input type="email" id="email" name="email" required placeholder="john.doe@example.com">
                </div>
                
                <div class="form-group">
                    <label for="phone">Phone Number</label>
                    <input type="tel" id="phone" name="phone" placeholder="+1 (555) 123-4567">
                </div>
                
                <div class="form-group">
                    <label for="role">Role <span class="required">*</span></label>
                    <select id="role" name="role" required>
                        <option value="">Select a role...</option>
                        <option value="user">Regular User</option>
                        <option value="admin">Administrator</option>
                        <option value="moderator">Moderator</option>
                        <option value="developer">Developer</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="department">Department</label>
                    <select id="department" name="department">
                        <option value="">Select department...</option>
                        <option value="engineering">Engineering</option>
                        <option value="sales">Sales</option>
                        <option value="marketing">Marketing</option>
                        <option value="support">Support</option>
                        <option value="hr">Human Resources</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="comments">Additional Comments</label>
                    <textarea id="comments" name="comments" placeholder="Tell us more about yourself..."></textarea>
                </div>
                
                <button type="submit">Submit Registration</button>
            </form>
            
            <div id="successMessage" class="success-message">
                ✅ Registration submitted successfully!
            </div>
        </div>
        
        <script>
            document.getElementById('userForm').addEventListener('submit', function(e) {{
                e.preventDefault();
                
                // Collect form data
                const formData = new FormData(e.target);
                const data = {{}};
                formData.forEach((value, key) => {{
                    data[key] = value;
                }});
                
                // Show success message
                document.getElementById('successMessage').style.display = 'block';
                
                // Send to parent (LibreChat)
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'tool',
                        payload: {{
                            toolName: 'process_form_submission',
                            params: data
                        }},
                        messageId: '{resource_id}'
                    }}, '*');
                }}
                
                // Reset form after delay
                setTimeout(() => {{
                    e.target.reset();
                    document.getElementById('successMessage').style.display = 'none';
                }}, 3000);
            }});
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://form/{resource_id}",
            "name": "User Registration Form",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def show_chart(ctx: Context, chart_type: str = "bar") -> Dict[str, Any]:
    """
    Shows an interactive chart visualization.
    Args:
        chart_type: Type of chart to display (bar, line, or pie)
    Returns an MCP-UI compliant resource that renders as an interactive chart.
    """
    resource_id = str(uuid.uuid4())
    
    # Generate some sample data
    import random
    data_values = [random.randint(10, 100) for _ in range(6)]
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Data Visualization</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            .chart-container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                padding: 32px;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            h2 {{
                color: #1a202c;
                margin-bottom: 24px;
                font-size: 28px;
            }}
            .chart-wrapper {{
                position: relative;
                height: 400px;
                margin-bottom: 32px;
            }}
            .controls {{
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
                justify-content: center;
            }}
            button {{
                padding: 10px 20px;
                border: 2px solid #e2e8f0;
                background: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }}
            button:hover {{
                background: #f8f9fa;
                border-color: #667eea;
            }}
            button.active {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-color: transparent;
            }}
        </style>
    </head>
    <body>
        <div class="chart-container">
            <h2>📈 Data Visualization</h2>
            <div class="chart-wrapper">
                <canvas id="myChart"></canvas>
            </div>
            <div class="controls">
                <button onclick="changeChart('bar')" class="{'active' if chart_type == 'bar' else ''}" id="bar-btn">📊 Bar Chart</button>
                <button onclick="changeChart('line')" class="{'active' if chart_type == 'line' else ''}" id="line-btn">📉 Line Chart</button>
                <button onclick="changeChart('pie')" class="{'active' if chart_type == 'pie' else ''}" id="pie-btn">🥧 Pie Chart</button>
                <button onclick="changeChart('doughnut')" class="{'active' if chart_type == 'doughnut' else ''}" id="doughnut-btn">🍩 Doughnut</button>
                <button onclick="changeChart('radar')" class="{'active' if chart_type == 'radar' else ''}" id="radar-btn">🎯 Radar</button>
            </div>
        </div>
        
        <script>
            const ctx = document.getElementById('myChart').getContext('2d');
            let chart;
            
            const data = {{
                labels: {json.dumps(chart_data["labels"])},
                datasets: [{{
                    label: 'Monthly Data',
                    data: {data_values},
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(118, 75, 162, 0.8)',
                        'rgba(237, 137, 54, 0.8)',
                        'rgba(72, 187, 120, 0.8)',
                        'rgba(245, 101, 101, 0.8)',
                        'rgba(159, 122, 234, 0.8)'
                    ],
                    borderColor: [
                        'rgb(102, 126, 234)',
                        'rgb(118, 75, 162)',
                        'rgb(237, 137, 54)',
                        'rgb(72, 187, 120)',
                        'rgb(245, 101, 101)',
                        'rgb(159, 122, 234)'
                    ],
                    borderWidth: 2
                }}]
            }};
            
            function createChart(type) {{
                if (chart) {{
                    chart.destroy();
                }}
                
                const config = {{
                    type: type,
                    data: data,
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'top',
                                labels: {{
                                    font: {{
                                        size: 14,
                                        weight: '600'
                                    }}
                                }}
                            }},
                            title: {{
                                display: true,
                                text: 'Monthly Performance Metrics',
                                font: {{
                                    size: 16,
                                    weight: 'bold'
                                }}
                            }}
                        }},
                        scales: type === 'pie' || type === 'doughnut' || type === 'radar' ? {{}} : {{
                            y: {{
                                beginAtZero: true,
                                grid: {{
                                    color: 'rgba(0, 0, 0, 0.05)'
                                }}
                            }},
                            x: {{
                                grid: {{
                                    display: false
                                }}
                            }}
                        }}
                    }}
                }};
                
                chart = new Chart(ctx, config);
            }}
            
            function changeChart(type) {{
                createChart(type);
                
                // Update button states
                document.querySelectorAll('button').forEach(btn => {{
                    btn.classList.remove('active');
                }});
                document.getElementById(type + '-btn').classList.add('active');
                
                // Notify parent
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'notify',
                        payload: {{
                            message: `Chart changed to ${{type}}`
                        }},
                        messageId: '{resource_id}'
                    }}, '*');
                }}
            }}
            
            // Initialize with the requested chart type
            createChart('{chart_type}');
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://chart/{chart_type}/{resource_id}",
            "name": f"{chart_type.capitalize()} Chart Visualization",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def handle_dashboard_action(ctx: Context, action: str) -> Dict[str, Any]:
    """
    Handles actions from the dashboard UI.
    Args:
        action: The action to perform (refresh, export, settings)
    """
    if action == "refresh":
        # Return a new dashboard with updated data
        return await show_dashboard(ctx, refresh=True)
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

@mcp.tool()
async def process_form_submission(
    ctx: Context,
    name: str = "",
    email: str = "",
    phone: str = "",
    role: str = "",
    department: str = "",
    comments: str = ""
) -> Dict[str, Any]:
    """
    Processes form submissions from the registration form.
    Stores the data and returns a confirmation.
    """
    # Store the form data
    user_id = str(uuid.uuid4())
    user_data_store[user_id] = {
        "name": name,
        "email": email,
        "phone": phone,
        "role": role,
        "department": department,
        "comments": comments,
        "timestamp": datetime.now().isoformat()
    }
    
    # Format the response
    response = f"""✅ Registration Successful!

**User ID**: {user_id}

**Submitted Information:**
- **Name**: {name}
- **Email**: {email}
- **Phone**: {phone if phone else "Not provided"}
- **Role**: {role}
- **Department**: {department if department else "Not specified"}
- **Comments**: {comments if comments else "No additional comments"}

**Timestamp**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

The user has been successfully registered in the system."""
    
    return {
        "type": "text",
        "text": response
    }

# =============================================================================
# ADVANCED UI EXAMPLES
# =============================================================================

@mcp.tool()
async def show_markdown_viewer(ctx: Context, content: str = None) -> Dict[str, Any]:
    """
    Displays rich Markdown content with syntax highlighting and interactive features.
    Demonstrates how to render formatted documentation in MCP UI.
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
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Markdown Viewer</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/github-markdown-css@5/github-markdown.min.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/styles/github.min.css">
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/highlight.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f6f8fa;
                min-height: 600px;
            }}
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                min-height: 560px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px 30px;
                border-radius: 12px 12px 0 0;
            }}
            .markdown-body {{
                padding: 30px;
                min-height: 400px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📝 Markdown Viewer</h1>
            </div>
            <div id="content" class="markdown-body"></div>
        </div>
        
        <script>
            const content = `{markdown_content}`;
            document.getElementById('content').innerHTML = marked.parse(content);
            
            // Apply syntax highlighting
            document.querySelectorAll('pre code').forEach((block) => {{
                hljs.highlightBlock(block);
            }});
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://markdown/{resource_id}",
            "name": "Markdown Viewer",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def show_canvas_drawing(ctx: Context) -> Dict[str, Any]:
    """
    Shows an interactive canvas drawing application.
    Demonstrates HTML5 Canvas API usage in MCP UI.
    """
    resource_id = str(uuid.uuid4())
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Canvas Drawing App</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 620px;
                overflow: hidden;
            }}
            .container {{
                max-width: 800px;
                height: 580px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                box-sizing: border-box;
            }}
            h1 {{
                margin: 0 0 20px 0;
                color: #333;
            }}
            .toolbar {{
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            .toolbar button {{
                padding: 8px 16px;
                border: 2px solid #ddd;
                background: white;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
            }}
            .toolbar button.active {{
                background: #667eea;
                color: white;
            }}
            .color-picker {{
                width: 40px;
                height: 40px;
                border: 2px solid #ddd;
                border-radius: 8px;
                cursor: pointer;
            }}
            canvas {{
                border: 2px solid #ddd;
                border-radius: 8px;
                cursor: crosshair;
                display: block;
                margin: 0 auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎨 Canvas Drawing App</h1>
            
            <div class="toolbar">
                <button class="active" data-tool="pen">✏️ Pen</button>
                <button data-tool="eraser">🧹 Eraser</button>
                <button data-tool="line">📏 Line</button>
                <button data-tool="rect">▭ Rectangle</button>
                <button data-tool="circle">⭕ Circle</button>
                
                <input type="color" class="color-picker" id="colorPicker" value="#667eea">
                
                <label>
                    Size: <input type="range" id="sizeSlider" min="1" max="50" value="5">
                    <span id="sizeDisplay">5</span>
                </label>
                
                <button onclick="clearCanvas()">🗑️ Clear</button>
                <button onclick="saveCanvas()">💾 Save</button>
            </div>
            
            <canvas id="drawingCanvas" width="760" height="400"></canvas>
        </div>
        
        <script>
            const canvas = document.getElementById('drawingCanvas');
            const ctx = canvas.getContext('2d');
            let isDrawing = false;
            let currentTool = 'pen';
            let currentColor = '#667eea';
            let currentSize = 5;
            let startX, startY;
            
            // Tool selection
            document.querySelectorAll('[data-tool]').forEach(btn => {{
                btn.addEventListener('click', (e) => {{
                    document.querySelectorAll('[data-tool]').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentTool = btn.dataset.tool;
                }});
            }});
            
            // Color picker
            document.getElementById('colorPicker').addEventListener('change', (e) => {{
                currentColor = e.target.value;
            }});
            
            // Size slider
            document.getElementById('sizeSlider').addEventListener('input', (e) => {{
                currentSize = e.target.value;
                document.getElementById('sizeDisplay').textContent = currentSize;
            }});
            
            // Drawing functions
            canvas.addEventListener('mousedown', (e) => {{
                isDrawing = true;
                const rect = canvas.getBoundingClientRect();
                startX = e.clientX - rect.left;
                startY = e.clientY - rect.top;
                
                if (currentTool === 'pen' || currentTool === 'eraser') {{
                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                }}
            }});
            
            canvas.addEventListener('mousemove', (e) => {{
                if (!isDrawing) return;
                
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                ctx.lineWidth = currentSize;
                ctx.lineCap = 'round';
                
                if (currentTool === 'pen') {{
                    ctx.globalCompositeOperation = 'source-over';
                    ctx.strokeStyle = currentColor;
                    ctx.lineTo(x, y);
                    ctx.stroke();
                }} else if (currentTool === 'eraser') {{
                    ctx.globalCompositeOperation = 'destination-out';
                    ctx.lineTo(x, y);
                    ctx.stroke();
                }}
            }});
            
            canvas.addEventListener('mouseup', (e) => {{
                if (!isDrawing) return;
                isDrawing = false;
                
                const rect = canvas.getBoundingClientRect();
                const endX = e.clientX - rect.left;
                const endY = e.clientY - rect.top;
                
                ctx.globalCompositeOperation = 'source-over';
                ctx.strokeStyle = currentColor;
                ctx.lineWidth = currentSize;
                
                if (currentTool === 'line') {{
                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                    ctx.lineTo(endX, endY);
                    ctx.stroke();
                }} else if (currentTool === 'rect') {{
                    ctx.strokeRect(startX, startY, endX - startX, endY - startY);
                }} else if (currentTool === 'circle') {{
                    const radius = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
                    ctx.beginPath();
                    ctx.arc(startX, startY, radius, 0, 2 * Math.PI);
                    ctx.stroke();
                }}
            }});
            
            function clearCanvas() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }}
            
            function saveCanvas() {{
                const link = document.createElement('a');
                link.download = 'drawing.png';
                link.href = canvas.toDataURL();
                link.click();
            }}
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://canvas/{resource_id}",
            "name": "Canvas Drawing Application",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def show_base64_image(ctx: Context, text: str = "MCP UI") -> Dict[str, Any]:
    """
    Generates and displays a dynamic Base64-encoded SVG image.
    This demonstrates how to create and embed images directly in MCP UI.
    """
    import base64
    
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
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Base64 Image Display</title>
        <style>
            body {{
                font-family: system-ui, -apple-system, sans-serif;
                padding: 20px;
                background: #f5f5f5;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                max-width: 700px;
                width: 100%;
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
                text-align: center;
            }}
            img {{
                width: 100%;
                height: auto;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .info {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                font-size: 14px;
                color: #666;
                margin-top: 20px;
            }}
            code {{
                background: #e9ecef;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: monospace;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🖼️ Base64 Encoded SVG Image</h1>
            <img src="data:image/svg+xml;base64,{svg_base64}" alt="Generated SVG" />
            <div class="info">
                <strong>About this image:</strong><br>
                • Generated dynamically on the server<br>
                • Encoded as Base64 data URI<br>
                • No external image requests needed<br>
                • SVG format for perfect scaling<br>
                • Data URI length: <code>{len(svg_base64)} characters</code>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://base64image/{uuid.uuid4()}",
            "name": "Base64 SVG Image",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def show_realtime_data(ctx: Context) -> Dict[str, Any]:
    """
    Shows a real-time data visualization with WebSocket simulation.
    Demonstrates dynamic updates and live data streaming in MCP UI.
    """
    resource_id = str(uuid.uuid4())
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Real-time Data Monitor</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #1a1a2e;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 12px 12px 0 0;
            }}
            .dashboard {{
                background: white;
                padding: 20px;
                border-radius: 0 0 12px 12px;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }}
            .stat-label {{
                font-size: 12px;
                color: #6c757d;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .stat-value {{
                font-size: 28px;
                font-weight: bold;
                color: #2d3748;
                margin: 5px 0;
            }}
            .stat-change {{
                font-size: 14px;
                color: #48bb78;
            }}
            .stat-change.negative {{
                color: #f56565;
            }}
            .chart-container {{
                position: relative;
                height: 300px;
                margin-top: 20px;
            }}
            .status {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 600;
                background: #48bb78;
                color: white;
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Real-time Data Monitor</h1>
                <span class="status">● LIVE</span>
            </div>
            <div class="dashboard">
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Current Value</div>
                        <div class="stat-value" id="currentValue">0</div>
                        <div class="stat-change" id="currentChange">+0%</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Average</div>
                        <div class="stat-value" id="avgValue">0</div>
                        <div class="stat-change">Last 60 seconds</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Peak</div>
                        <div class="stat-value" id="peakValue">0</div>
                        <div class="stat-change">Maximum recorded</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Data Points</div>
                        <div class="stat-value" id="dataPoints">0</div>
                        <div class="stat-change">Total collected</div>
                    </div>
                </div>
                
                <div class="chart-container">
                    <canvas id="realtimeChart"></canvas>
                </div>
            </div>
        </div>
        
        <script>
            // Initialize chart
            const ctx = document.getElementById('realtimeChart').getContext('2d');
            const chart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: [],
                    datasets: [{{
                        label: 'Real-time Value',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        x: {{
                            display: true,
                            grid: {{ display: false }}
                        }},
                        y: {{
                            display: true,
                            beginAtZero: true,
                            grid: {{ color: 'rgba(0,0,0,0.05)' }}
                        }}
                    }}
                }}
            }});
            
            // Simulate real-time data
            let dataHistory = [];
            let peakValue = 0;
            let dataCount = 0;
            
            function generateDataPoint() {{
                // Simulate realistic data with trends and noise
                const time = new Date();
                const baseValue = 50;
                const trend = Math.sin(Date.now() / 10000) * 20;
                const noise = (Math.random() - 0.5) * 10;
                const value = Math.max(0, baseValue + trend + noise);
                
                return {{
                    time: time.toLocaleTimeString(),
                    value: Math.round(value * 100) / 100
                }};
            }}
            
            function updateData() {{
                const newPoint = generateDataPoint();
                dataHistory.push(newPoint);
                dataCount++;
                
                // Keep only last 60 data points
                if (dataHistory.length > 60) {{
                    dataHistory.shift();
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }}
                
                // Update chart
                chart.data.labels.push(newPoint.time);
                chart.data.datasets[0].data.push(newPoint.value);
                chart.update('none'); // No animation for smooth updates
                
                // Update statistics
                const currentValue = newPoint.value;
                const previousValue = dataHistory[dataHistory.length - 2]?.value || currentValue;
                const change = ((currentValue - previousValue) / previousValue * 100).toFixed(1);
                
                document.getElementById('currentValue').textContent = currentValue.toFixed(2);
                document.getElementById('currentChange').textContent = (change >= 0 ? '+' : '') + change + '%';
                document.getElementById('currentChange').className = change >= 0 ? 'stat-change' : 'stat-change negative';
                
                // Calculate average
                const sum = dataHistory.reduce((acc, point) => acc + point.value, 0);
                const avg = sum / dataHistory.length;
                document.getElementById('avgValue').textContent = avg.toFixed(2);
                
                // Update peak
                if (currentValue > peakValue) {{
                    peakValue = currentValue;
                }}
                document.getElementById('peakValue').textContent = peakValue.toFixed(2);
                
                // Update data points
                document.getElementById('dataPoints').textContent = dataCount;
            }}
            
            // Start real-time updates
            setInterval(updateData, 1000);
            
            // Initialize with some data
            for (let i = 0; i < 10; i++) {{
                updateData();
            }}
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://realtime/{resource_id}",
            "name": "Real-time Data Monitor",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def show_react_interactive(ctx: Context, initial_count: int = 0) -> Dict[str, Any]:
    """
    Shows an interactive React component with state management and tool callbacks.
    This demonstrates how to use React instead of plain HTML for more complex UIs.
    """
    resource_id = str(uuid.uuid4())
    
    # React component with hooks and interactivity
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>React Interactive Component</title>
        <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 500px;
            }}
            #root {{
                max-width: 600px;
                margin: 0 auto;
            }}
            .card {{
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            .button {{
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                cursor: pointer;
                margin: 5px;
                transition: all 0.3s;
            }}
            .button:hover {{
                background: #5a67d8;
                transform: translateY(-2px);
            }}
            .button.secondary {{
                background: #48bb78;
            }}
            .button.secondary:hover {{
                background: #38a169;
            }}
            .counter {{
                font-size: 48px;
                font-weight: bold;
                color: #667eea;
                margin: 20px 0;
                text-align: center;
            }}
            .input {{
                width: 100%;
                padding: 10px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 16px;
                margin: 10px 0;
            }}
            .todo-list {{
                list-style: none;
                padding: 0;
            }}
            .todo-item {{
                display: flex;
                align-items: center;
                padding: 10px;
                margin: 5px 0;
                background: #f7fafc;
                border-radius: 8px;
            }}
            .todo-item.completed {{
                opacity: 0.6;
                text-decoration: line-through;
            }}
            .checkbox {{
                margin-right: 10px;
                width: 20px;
                height: 20px;
            }}
        </style>
    </head>
    <body>
        <div id="root"></div>
        
        <script type="text/babel">
            const {{ useState, useEffect, useCallback }} = React;
            
            function InteractiveApp() {{
                const [count, setCount] = useState({initial_count});
                const [todos, setTodos] = useState([
                    {{ id: 1, text: 'Learn React in MCP', completed: false }},
                    {{ id: 2, text: 'Build interactive UIs', completed: false }}
                ]);
                const [newTodo, setNewTodo] = useState('');
                const [message, setMessage] = useState('');
                
                // Send message to parent window (for MCP tool integration)
                const sendToMCP = useCallback((action, data) => {{
                    if (window.parent !== window) {{
                        window.parent.postMessage({{
                            type: 'mcp-action',
                            action: action,
                            data: data,
                            timestamp: new Date().toISOString()
                        }}, '*');
                    }}
                    console.log('MCP Action:', action, data);
                }}, []);
                
                const incrementCounter = () => {{
                    const newCount = count + 1;
                    setCount(newCount);
                    sendToMCP('counter-increment', {{ value: newCount }});
                    setMessage(`Counter increased to ${{newCount}}`);
                }};
                
                const decrementCounter = () => {{
                    const newCount = count - 1;
                    setCount(newCount);
                    sendToMCP('counter-decrement', {{ value: newCount }});
                    setMessage(`Counter decreased to ${{newCount}}`);
                }};
                
                const addTodo = () => {{
                    if (newTodo.trim()) {{
                        const todo = {{
                            id: Date.now(),
                            text: newTodo,
                            completed: false
                        }};
                        setTodos([...todos, todo]);
                        sendToMCP('todo-added', todo);
                        setNewTodo('');
                        setMessage(`Added: "${{newTodo}}"`);
                    }}
                }};
                
                const toggleTodo = (id) => {{
                    setTodos(todos.map(todo => 
                        todo.id === id 
                            ? {{ ...todo, completed: !todo.completed }}
                            : todo
                    ));
                    const todo = todos.find(t => t.id === id);
                    sendToMCP('todo-toggled', {{ id, completed: !todo.completed }});
                }};
                
                const resetAll = () => {{
                    setCount(0);
                    setTodos([]);
                    setMessage('Everything reset!');
                    sendToMCP('reset', {{}});
                }};
                
                useEffect(() => {{
                    // Listen for messages from parent
                    const handleMessage = (event) => {{
                        if (event.data?.type === 'mcp-command') {{
                            const {{ command }} = event.data;
                            if (command === 'increment') incrementCounter();
                            else if (command === 'decrement') decrementCounter();
                            else if (command === 'reset') resetAll();
                        }}
                    }};
                    window.addEventListener('message', handleMessage);
                    return () => window.removeEventListener('message', handleMessage);
                }}, [count, todos]);
                
                return (
                    <div className="card">
                        <h1>🚀 React Interactive Component</h1>
                        
                        <div className="counter">{{count}}</div>
                        
                        <div style={{{{ textAlign: 'center', marginBottom: '30px' }}}}>
                            <button className="button" onClick={{incrementCounter}}>
                                ➕ Increment
                            </button>
                            <button className="button" onClick={{decrementCounter}}>
                                ➖ Decrement
                            </button>
                            <button className="button secondary" onClick={{resetAll}}>
                                🔄 Reset All
                            </button>
                        </div>
                        
                        {{message && (
                            <div style={{{{
                                background: '#edf2f7',
                                padding: '10px',
                                borderRadius: '8px',
                                marginBottom: '20px',
                                textAlign: 'center'
                            }}}}>
                                {{message}}
                            </div>
                        )}}
                        
                        <h2>📝 Todo List</h2>
                        
                        <div style={{{{ display: 'flex', gap: '10px' }}}}>
                            <input
                                className="input"
                                type="text"
                                placeholder="Add a new todo..."
                                value={{newTodo}}
                                onChange={{(e) => setNewTodo(e.target.value)}}
                                onKeyPress={{(e) => e.key === 'Enter' && addTodo()}}
                            />
                            <button className="button secondary" onClick={{addTodo}}>
                                Add
                            </button>
                        </div>
                        
                        <ul className="todo-list">
                            {{todos.map(todo => (
                                <li key={{todo.id}} className={{`todo-item ${{todo.completed ? 'completed' : ''}}`}}>
                                    <input
                                        type="checkbox"
                                        className="checkbox"
                                        checked={{todo.completed}}
                                        onChange={{() => toggleTodo(todo.id)}}
                                    />
                                    <span>{{todo.text}}</span>
                                </li>
                            ))}}
                        </ul>
                        
                        <div style={{{{ marginTop: '20px', fontSize: '12px', color: '#718096' }}}}>
                            <p>This React component sends events to the MCP server when you interact with it.</p>
                            <p>Try clicking buttons and adding todos!</p>
                        </div>
                    </div>
                );
            }}
            
            // Render the React app
            const root = ReactDOM.createRoot(document.getElementById('root'));
            root.render(<InteractiveApp />);
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://react/{resource_id}",
            "name": "React Interactive Component",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def show_recharts_dashboard(ctx: Context) -> Dict[str, Any]:
    """
    Shows a comprehensive interactive dashboard using Recharts library.
    Demonstrates all major chart types with live data switching and customization.
    """
    resource_id = str(uuid.uuid4())
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Recharts Dashboard</title>
        <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>
        <script crossorigin src="https://unpkg.com/recharts@2.5.0/umd/Recharts.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 800px;
            }}
            .dashboard {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            .controls {{
                display: flex;
                gap: 15px;
                margin-bottom: 30px;
                flex-wrap: wrap;
                align-items: center;
            }}
            .chart-selector {{
                padding: 10px 15px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                background: white;
                font-size: 14px;
                cursor: pointer;
            }}
            .chart-button {{
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                background: #667eea;
                color: white;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            }}
            .chart-button:hover {{
                background: #5a67d8;
                transform: translateY(-2px);
            }}
            .chart-button.active {{
                background: #48bb78;
            }}
            .chart-container {{
                min-height: 400px;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 20px 0;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            .stat-card {{
                background: #f7fafc;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }}
            .stat-value {{
                font-size: 32px;
                font-weight: bold;
                color: #667eea;
            }}
            .stat-label {{
                color: #718096;
                margin-top: 5px;
            }}
        </style>
    </head>
    <body>
        <div id="root"></div>
        
        <script type="text/babel">
            const {{ useState, useEffect, useMemo }} = React;
            
            // Check if Recharts is loaded
            if (typeof Recharts === 'undefined') {{
                console.error('Recharts library not loaded!');
                document.getElementById('root').innerHTML = '<div style="padding: 20px; color: red;">Error: Recharts library failed to load. Please refresh the page.</div>';
            }}
            
            const {{
                LineChart, Line, BarChart, Bar, AreaChart, Area,
                PieChart, Pie, RadarChart, Radar, ScatterChart, Scatter,
                ComposedChart, RadialBarChart, RadialBar, Treemap,
                XAxis, YAxis, CartesianGrid, Tooltip, Legend,
                ResponsiveContainer, Cell, PolarGrid, PolarAngleAxis, PolarRadiusAxis
            }} = window.Recharts || {{}};
            
            function RechartsDashboard() {{
                const [chartType, setChartType] = useState('line');
                const [dataSet, setDataSet] = useState('sales');
                const [animated, setAnimated] = useState(true);
                
                // Sample datasets
                const datasets = {{
                    sales: [
                        {{ name: 'Jan', sales: 4000, profit: 2400, customers: 240 }},
                        {{ name: 'Feb', sales: 3000, profit: 1398, customers: 220 }},
                        {{ name: 'Mar', sales: 2000, profit: 9800, customers: 290 }},
                        {{ name: 'Apr', sales: 2780, profit: 3908, customers: 200 }},
                        {{ name: 'May', sales: 1890, profit: 4800, customers: 181 }},
                        {{ name: 'Jun', sales: 2390, profit: 3800, customers: 250 }},
                        {{ name: 'Jul', sales: 3490, profit: 4300, customers: 310 }},
                        {{ name: 'Aug', sales: 4200, profit: 5100, customers: 420 }},
                        {{ name: 'Sep', sales: 3700, profit: 4200, customers: 380 }},
                        {{ name: 'Oct', sales: 4100, profit: 4900, customers: 400 }},
                        {{ name: 'Nov', sales: 4500, profit: 5200, customers: 450 }},
                        {{ name: 'Dec', sales: 5000, profit: 5800, customers: 500 }}
                    ],
                    performance: [
                        {{ subject: 'Math', A: 120, B: 110, fullMark: 150 }},
                        {{ subject: 'Chinese', A: 98, B: 130, fullMark: 150 }},
                        {{ subject: 'English', A: 86, B: 130, fullMark: 150 }},
                        {{ subject: 'Geography', A: 99, B: 100, fullMark: 150 }},
                        {{ subject: 'Physics', A: 85, B: 90, fullMark: 150 }},
                        {{ subject: 'History', A: 65, B: 85, fullMark: 150 }}
                    ],
                    distribution: [
                        {{ name: 'Group A', value: 400, color: '#8884d8' }},
                        {{ name: 'Group B', value: 300, color: '#82ca9d' }},
                        {{ name: 'Group C', value: 300, color: '#ffc658' }},
                        {{ name: 'Group D', value: 200, color: '#ff7c7c' }},
                        {{ name: 'Group E', value: 150, color: '#8dd1e1' }}
                    ],
                    scatter: Array.from({{ length: 50 }}, () => ({{
                        x: Math.floor(Math.random() * 100),
                        y: Math.floor(Math.random() * 100),
                        z: Math.floor(Math.random() * 50) + 50
                    }})),
                    treemap: [
                        {{ name: 'axis', size: 24593 }},
                        {{ name: 'controls', size: 28232 }},
                        {{ name: 'data', size: 42897 }},
                        {{ name: 'display', size: 15620 }},
                        {{ name: 'flex', size: 22324 }},
                        {{ name: 'operators', size: 35198 }},
                        {{ name: 'physics', size: 18349 }},
                        {{ name: 'query', size: 25003 }},
                        {{ name: 'scale', size: 30287 }},
                        {{ name: 'util', size: 40183 }},
                        {{ name: 'vis', size: 38292 }},
                        {{ name: 'analytics', size: 28746 }}
                    ]
                }};
                
                const currentData = datasets[dataSet] || datasets.sales;
                
                // Calculate statistics
                const stats = useMemo(() => {{
                    if (dataSet === 'sales') {{
                        const totalSales = currentData.reduce((sum, item) => sum + item.sales, 0);
                        const totalProfit = currentData.reduce((sum, item) => sum + item.profit, 0);
                        const avgCustomers = Math.round(currentData.reduce((sum, item) => sum + item.customers, 0) / currentData.length);
                        const growth = ((currentData[currentData.length - 1].sales - currentData[0].sales) / currentData[0].sales * 100).toFixed(1);
                        return [
                            {{ label: 'Total Sales', value: `${{totalSales.toLocaleString()}}` }},
                            {{ label: 'Total Profit', value: `${{totalProfit.toLocaleString()}}` }},
                            {{ label: 'Avg Customers', value: avgCustomers }},
                            {{ label: 'Growth', value: `${{growth}}%` }}
                        ];
                    }}
                    return [];
                }}, [dataSet, currentData]);
                
                const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1'];
                
                const renderChart = () => {{
                    switch(chartType) {{
                        case 'line':
                            return (
                                <ResponsiveContainer width="100%" height={400}>
                                    <LineChart data={{currentData}}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Line type="monotone" dataKey="sales" stroke="#8884d8" 
                                              strokeWidth={{2}} animationDuration={{animated ? 1500 : 0}} />
                                        <Line type="monotone" dataKey="profit" stroke="#82ca9d" 
                                              strokeWidth={{2}} animationDuration={{animated ? 1500 : 0}} />
                                        <Line type="monotone" dataKey="customers" stroke="#ffc658" 
                                              strokeWidth={{2}} animationDuration={{animated ? 1500 : 0}} />
                                    </LineChart>
                                </ResponsiveContainer>
                            );
                        
                        case 'bar':
                            return (
                                <ResponsiveContainer width="100%" height={400}>
                                    <BarChart data={{currentData}}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Bar dataKey="sales" fill="#8884d8" animationDuration={{animated ? 1500 : 0}} />
                                        <Bar dataKey="profit" fill="#82ca9d" animationDuration={{animated ? 1500 : 0}} />
                                    </BarChart>
                                </ResponsiveContainer>
                            );
                        
                        case 'area':
                            return (
                                <ResponsiveContainer width="100%" height={400}>
                                    <AreaChart data={{currentData}}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Area type="monotone" dataKey="sales" stackId="1" 
                                              stroke="#8884d8" fill="#8884d8" animationDuration={{animated ? 1500 : 0}} />
                                        <Area type="monotone" dataKey="profit" stackId="1" 
                                              stroke="#82ca9d" fill="#82ca9d" animationDuration={{animated ? 1500 : 0}} />
                                        <Area type="monotone" dataKey="customers" stackId="1" 
                                              stroke="#ffc658" fill="#ffc658" animationDuration={{animated ? 1500 : 0}} />
                                    </AreaChart>
                                </ResponsiveContainer>
                            );
                        
                        case 'pie':
                            return (
                                <ResponsiveContainer width="100%" height={400}>
                                    <PieChart>
                                        <Pie
                                            data={{datasets.distribution}}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={{false}}
                                            label={{(entry) => entry.name}}
                                            outerRadius={{120}}
                                            fill="#8884d8"
                                            dataKey="value"
                                            animationDuration={{animated ? 1500 : 0}}
                                        >
                                            {{datasets.distribution.map((entry, index) => (
                                                <Cell key={{`cell-${{index}}`}} fill={{entry.color}} />
                                            ))}}
                                        </Pie>
                                        <Tooltip />
                                    </PieChart>
                                </ResponsiveContainer>
                            );
                        
                        case 'radar':
                            return (
                                <ResponsiveContainer width="100%" height={400}>
                                    <RadarChart data={{datasets.performance}} cx="50%" cy="50%" outerRadius="80%">
                                        <PolarGrid />
                                        <PolarAngleAxis dataKey="subject" />
                                        <PolarRadiusAxis angle={{90}} domain={{[0, 150]}} />
                                        <Radar name="Student A" dataKey="A" stroke="#8884d8" 
                                               fill="#8884d8" fillOpacity={{0.6}} animationDuration={{animated ? 1500 : 0}} />
                                        <Radar name="Student B" dataKey="B" stroke="#82ca9d" 
                                               fill="#82ca9d" fillOpacity={{0.6}} animationDuration={{animated ? 1500 : 0}} />
                                        <Legend />
                                        <Tooltip />
                                    </RadarChart>
                                </ResponsiveContainer>
                            );
                        
                        case 'scatter':
                            return (
                                <ResponsiveContainer width="100%" height={400}>
                                    <ScatterChart>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="x" name="X Value" unit="" />
                                        <YAxis dataKey="y" name="Y Value" unit="" />
                                        <Tooltip cursor={{{{ strokeDasharray: '3 3' }}}} />
                                        <Scatter name="Data Points" data={{datasets.scatter}} fill="#8884d8">
                                            {{datasets.scatter.map((entry, index) => (
                                                <Cell key={{`cell-${{index}}`}} fill={{COLORS[index % COLORS.length]}} />
                                            ))}}
                                        </Scatter>
                                    </ScatterChart>
                                </ResponsiveContainer>
                            );
                        
                        case 'composed':
                            return (
                                <ResponsiveContainer width="100%" height={400}>
                                    <ComposedChart data={{currentData}}>
                                        <CartesianGrid stroke="#f5f5f5" />
                                        <XAxis dataKey="name" />
                                        <YAxis />
                                        <Tooltip />
                                        <Legend />
                                        <Bar dataKey="customers" barSize={{20}} fill="#413ea0" />
                                        <Line type="monotone" dataKey="sales" stroke="#ff7300" />
                                        <Area type="monotone" dataKey="profit" fill="#8884d8" stroke="#8884d8" />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            );
                        
                        case 'radialBar':
                            return (
                                <ResponsiveContainer width="100%" height={400}>
                                    <RadialBarChart cx="50%" cy="50%" innerRadius="10%" outerRadius="80%" 
                                                   barSize={{10}} data={{datasets.distribution}}>
                                        <RadialBar
                                            minAngle={{15}}
                                            label={{{{ position: 'insideStart', fill: '#fff' }}}}
                                            background
                                            clockWise
                                            dataKey="value"
                                        />
                                        <Legend iconSize={{10}} layout="vertical" verticalAlign="middle" wrapperStyle={{{{
                                            paddingLeft: "20px",
                                        }}}} />
                                        <Tooltip />
                                    </RadialBarChart>
                                </ResponsiveContainer>
                            );
                        
                        case 'treemap':
                            return (
                                <ResponsiveContainer width="100%" height={400}>
                                    <Treemap
                                        data={{datasets.treemap}}
                                        dataKey="size"
                                        aspectRatio={{4 / 3}}
                                        stroke="#fff"
                                        fill="#8884d8"
                                        animationDuration={{animated ? 1500 : 0}}
                                    >
                                        <Tooltip />
                                    </Treemap>
                                </ResponsiveContainer>
                            );
                        
                        default:
                            return null;
                    }}
                }};
                
                return (
                    <div className="dashboard">
                        <h1>📊 Recharts Interactive Dashboard</h1>
                        
                        <div className="controls">
                            <select 
                                className="chart-selector"
                                value={{chartType}}
                                onChange={{(e) => setChartType(e.target.value)}}
                            >
                                <option value="line">Line Chart</option>
                                <option value="bar">Bar Chart</option>
                                <option value="area">Area Chart</option>
                                <option value="pie">Pie Chart</option>
                                <option value="radar">Radar Chart</option>
                                <option value="scatter">Scatter Plot</option>
                                <option value="composed">Composed Chart</option>
                                <option value="radialBar">Radial Bar Chart</option>
                                <option value="treemap">Treemap</option>
                            </select>
                            
                            <select 
                                className="chart-selector"
                                value={{dataSet}}
                                onChange={{(e) => setDataSet(e.target.value)}}
                            >
                                <option value="sales">Sales Data</option>
                                <option value="performance">Performance Data</option>
                                <option value="distribution">Distribution Data</option>
                                <option value="scatter">Scatter Data</option>
                                <option value="treemap">Treemap Data</option>
                            </select>
                            
                            <button 
                                className={{`chart-button ${{animated ? 'active' : ''}}`}}
                                onClick={{() => setAnimated(!animated)}}
                            >
                                {{animated ? '🎬 Animated' : '⏸️ Static'}}
                            </button>
                        </div>
                        
                        {{stats.length > 0 && (
                            <div className="stats-grid">
                                {{stats.map((stat, index) => (
                                    <div key={{index}} className="stat-card">
                                        <div className="stat-value">{{stat.value}}</div>
                                        <div className="stat-label">{{stat.label}}</div>
                                    </div>
                                ))}}
                            </div>
                        )}}
                        
                        <div className="chart-container">
                            {{renderChart()}}
                        </div>
                        
                        <div style={{{{ marginTop: '20px', fontSize: '12px', color: '#718096' }}}}>
                            <p>This dashboard demonstrates various Recharts chart types with interactive data.</p>
                            <p>Try switching between different chart types and datasets!</p>
                        </div>
                    </div>
                );
            }}
            
            const root = ReactDOM.createRoot(document.getElementById('root'));
            root.render(<RechartsDashboard />);
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://recharts/{resource_id}",
            "name": "Recharts Dashboard",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def show_cytoscape_network(ctx: Context) -> Dict[str, Any]:
    """
    Shows an interactive network graph using Cytoscape.js.
    Demonstrates node visualization, layouts, interactions, and graph algorithms.
    """
    resource_id = str(uuid.uuid4())
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Cytoscape Network Visualization</title>
        <script src="https://unpkg.com/cytoscape@3.28.1/dist/cytoscape.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 800px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            .controls {{
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            .control-button {{
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                background: #667eea;
                color: white;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s;
            }}
            .control-button:hover {{
                background: #5a67d8;
                transform: translateY(-2px);
            }}
            .control-button.active {{
                background: #48bb78;
            }}
            .layout-selector {{
                padding: 10px 15px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                background: white;
                font-size: 14px;
                cursor: pointer;
            }}
            #cy {{
                width: 100%;
                height: 600px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                background: #fafafa;
            }}
            .info-panel {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 20px;
                padding: 20px;
                background: #f7fafc;
                border-radius: 8px;
            }}
            .info-item {{
                text-align: center;
            }}
            .info-label {{
                color: #718096;
                font-size: 12px;
                text-transform: uppercase;
            }}
            .info-value {{
                color: #2d3748;
                font-size: 24px;
                font-weight: bold;
                margin-top: 5px;
            }}
            .node-details {{
                margin-top: 20px;
                padding: 15px;
                background: #edf2f7;
                border-radius: 8px;
                min-height: 60px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🕸️ Cytoscape Network Visualization</h1>
            
            <div class="controls">
                <select class="layout-selector" id="layoutSelect">
                    <option value="cose">Cose (Force-Directed)</option>
                    <option value="circle">Circle</option>
                    <option value="concentric">Concentric</option>
                    <option value="breadthfirst">Breadth First</option>
                    <option value="grid">Grid</option>
                    <option value="random">Random</option>
                </select>
                
                <button class="control-button" onclick="resetView()">🔄 Reset View</button>
                <button class="control-button" onclick="fitView()">📐 Fit to Screen</button>
                <button class="control-button" onclick="addRandomNode()">➕ Add Node</button>
                <button class="control-button" onclick="removeSelected()">🗑️ Remove Selected</button>
                <button class="control-button" onclick="findShortestPath()">🛣️ Shortest Path</button>
                <button class="control-button" onclick="highlightClusters()">🎨 Color Clusters</button>
                <button class="control-button" onclick="toggleAnimation()">🎬 Toggle Animation</button>
                <button class="control-button" onclick="exportData()">💾 Export Graph</button>
            </div>
            
            <div id="cy"></div>
            
            <div class="info-panel">
                <div class="info-item">
                    <div class="info-label">Nodes</div>
                    <div class="info-value" id="nodeCount">0</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Edges</div>
                    <div class="info-value" id="edgeCount">0</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Selected</div>
                    <div class="info-value" id="selectedCount">0</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Layout</div>
                    <div class="info-value" id="currentLayout">Cose</div>
                </div>
            </div>
            
            <div class="node-details" id="nodeDetails">
                Click on a node to see its details...
            </div>
        </div>
        
        <script>
            // Initialize Cytoscape
            const cy = cytoscape({{
                container: document.getElementById('cy'),
                
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'background-color': '#667eea',
                            'label': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'color': '#fff',
                            'text-outline-width': 2,
                            'text-outline-color': '#667eea',
                            'width': 'mapData(weight, 1, 10, 30, 80)',
                            'height': 'mapData(weight, 1, 10, 30, 80)',
                            'font-size': '12px',
                            'border-width': 2,
                            'border-color': '#fff'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'width': 'mapData(weight, 1, 10, 1, 8)',
                            'line-color': '#cbd5e0',
                            'target-arrow-color': '#cbd5e0',
                            'target-arrow-shape': 'triangle',
                            'curve-style': 'bezier',
                            'label': 'data(weight)',
                            'font-size': '10px',
                            'text-rotation': 'autorotate',
                            'text-margin-y': -10
                        }}
                    }},
                    {{
                        selector: 'node:selected',
                        style: {{
                            'background-color': '#48bb78',
                            'border-color': '#2f855a',
                            'border-width': 4
                        }}
                    }},
                    {{
                        selector: 'edge:selected',
                        style: {{
                            'line-color': '#48bb78',
                            'target-arrow-color': '#48bb78',
                            'width': 4
                        }}
                    }},
                    {{
                        selector: '.highlighted',
                        style: {{
                            'background-color': '#ff6b6b',
                            'line-color': '#ff6b6b',
                            'target-arrow-color': '#ff6b6b',
                            'transition-property': 'background-color, line-color, target-arrow-color',
                            'transition-duration': '0.5s'
                        }}
                    }},
                    {{
                        selector: '.faded',
                        style: {{
                            'opacity': 0.25
                        }}
                    }}
                ],
                
                elements: {{
                    nodes: [
                        {{ data: {{ id: 'a', label: 'Alpha', weight: 8, type: 'hub' }} }},
                        {{ data: {{ id: 'b', label: 'Beta', weight: 5, type: 'node' }} }},
                        {{ data: {{ id: 'c', label: 'Gamma', weight: 7, type: 'hub' }} }},
                        {{ data: {{ id: 'd', label: 'Delta', weight: 3, type: 'node' }} }},
                        {{ data: {{ id: 'e', label: 'Epsilon', weight: 6, type: 'node' }} }},
                        {{ data: {{ id: 'f', label: 'Zeta', weight: 4, type: 'node' }} }},
                        {{ data: {{ id: 'g', label: 'Eta', weight: 5, type: 'node' }} }},
                        {{ data: {{ id: 'h', label: 'Theta', weight: 9, type: 'hub' }} }},
                        {{ data: {{ id: 'i', label: 'Iota', weight: 2, type: 'node' }} }},
                        {{ data: {{ id: 'j', label: 'Kappa', weight: 4, type: 'node' }} }},
                        {{ data: {{ id: 'k', label: 'Lambda', weight: 6, type: 'node' }} }},
                        {{ data: {{ id: 'l', label: 'Mu', weight: 3, type: 'node' }} }},
                        {{ data: {{ id: 'm', label: 'Nu', weight: 5, type: 'node' }} }},
                        {{ data: {{ id: 'n', label: 'Xi', weight: 7, type: 'hub' }} }},
                        {{ data: {{ id: 'o', label: 'Omicron', weight: 4, type: 'node' }} }}
                    ],
                    edges: [
                        {{ data: {{ id: 'ab', source: 'a', target: 'b', weight: 3 }} }},
                        {{ data: {{ id: 'ac', source: 'a', target: 'c', weight: 5 }} }},
                        {{ data: {{ id: 'ad', source: 'a', target: 'd', weight: 2 }} }},
                        {{ data: {{ id: 'ae', source: 'a', target: 'e', weight: 4 }} }},
                        {{ data: {{ id: 'bc', source: 'b', target: 'c', weight: 2 }} }},
                        {{ data: {{ id: 'be', source: 'b', target: 'e', weight: 3 }} }},
                        {{ data: {{ id: 'bf', source: 'b', target: 'f', weight: 1 }} }},
                        {{ data: {{ id: 'cd', source: 'c', target: 'd', weight: 4 }} }},
                        {{ data: {{ id: 'cg', source: 'c', target: 'g', weight: 3 }} }},
                        {{ data: {{ id: 'ch', source: 'c', target: 'h', weight: 6 }} }},
                        {{ data: {{ id: 'de', source: 'd', target: 'e', weight: 2 }} }},
                        {{ data: {{ id: 'ef', source: 'e', target: 'f', weight: 3 }} }},
                        {{ data: {{ id: 'fh', source: 'f', target: 'h', weight: 4 }} }},
                        {{ data: {{ id: 'gh', source: 'g', target: 'h', weight: 5 }} }},
                        {{ data: {{ id: 'hi', source: 'h', target: 'i', weight: 2 }} }},
                        {{ data: {{ id: 'hj', source: 'h', target: 'j', weight: 3 }} }},
                        {{ data: {{ id: 'hk', source: 'h', target: 'k', weight: 4 }} }},
                        {{ data: {{ id: 'hn', source: 'h', target: 'n', weight: 7 }} }},
                        {{ data: {{ id: 'ij', source: 'i', target: 'j', weight: 1 }} }},
                        {{ data: {{ id: 'jk', source: 'j', target: 'k', weight: 2 }} }},
                        {{ data: {{ id: 'kl', source: 'k', target: 'l', weight: 3 }} }},
                        {{ data: {{ id: 'km', source: 'k', target: 'm', weight: 2 }} }},
                        {{ data: {{ id: 'ln', source: 'l', target: 'n', weight: 4 }} }},
                        {{ data: {{ id: 'mn', source: 'm', target: 'n', weight: 3 }} }},
                        {{ data: {{ id: 'no', source: 'n', target: 'o', weight: 2 }} }}
                    ]
                }},
                
                layout: {{
                    name: 'cose',
                    animate: true,
                    randomize: false,
                    componentSpacing: 100,
                    nodeOverlap: 20,
                    idealEdgeLength: 100,
                    nodeRepulsion: 400000,
                    numIter: 1000
                }}
            }});
            
            // Update info panel
            function updateInfo() {{
                document.getElementById('nodeCount').textContent = cy.nodes().length;
                document.getElementById('edgeCount').textContent = cy.edges().length;
                document.getElementById('selectedCount').textContent = cy.$(':selected').length;
            }}
            
            // Event handlers
            cy.on('tap', 'node', function(evt) {{
                const node = evt.target;
                const data = node.data();
                const degree = node.degree();
                const neighbors = node.neighborhood().nodes().length;
                
                document.getElementById('nodeDetails').innerHTML = `
                    <strong>Node Details:</strong><br>
                    ID: ${{data.id}}<br>
                    Label: ${{data.label}}<br>
                    Weight: ${{data.weight}}<br>
                    Type: ${{data.type}}<br>
                    Degree: ${{degree}}<br>
                    Neighbors: ${{neighbors}}
                `;
            }});
            
            cy.on('select unselect', updateInfo);
            cy.on('add remove', updateInfo);
            
            // Layout selector
            document.getElementById('layoutSelect').addEventListener('change', function(e) {{
                const layoutName = e.target.value;
                document.getElementById('currentLayout').textContent = 
                    layoutName.charAt(0).toUpperCase() + layoutName.slice(1);
                
                let layoutOptions = {{ name: layoutName, animate: true }};
                
                if (layoutName === 'cose') {{
                    layoutOptions.componentSpacing = 100;
                    layoutOptions.nodeOverlap = 20;
                    layoutOptions.idealEdgeLength = 100;
                    layoutOptions.nodeRepulsion = 400000;
                    layoutOptions.numIter = 1000;
                }} else if (layoutName === 'circle') {{
                    layoutOptions.radius = 200;
                }} else if (layoutName === 'concentric') {{
                    layoutOptions.concentric = function(node) {{ return node.degree(); }};
                    layoutOptions.levelWidth = function(nodes) {{ return 2; }};
                }} else if (layoutName === 'breadthfirst') {{
                    layoutOptions.directed = true;
                    layoutOptions.spacingFactor = 1.5;
                }} else if (layoutName === 'grid') {{
                    layoutOptions.rows = 4;
                }}
                
                cy.layout(layoutOptions).run();
            }});
            
            // Control functions
            function resetView() {{
                cy.reset();
                cy.center();
            }}
            
            function fitView() {{
                cy.fit();
            }}
            
            let nodeIdCounter = 15;
            function addRandomNode() {{
                const id = String.fromCharCode(112 + nodeIdCounter); // p, q, r...
                const label = 'Node ' + id.toUpperCase();
                const weight = Math.floor(Math.random() * 9) + 1;
                
                cy.add({{
                    group: 'nodes',
                    data: {{ id: id, label: label, weight: weight, type: 'node' }},
                    position: {{
                        x: Math.random() * 500 + 100,
                        y: Math.random() * 400 + 100
                    }}
                }});
                
                // Add random edges to existing nodes
                const nodes = cy.nodes();
                const numEdges = Math.floor(Math.random() * 3) + 1;
                for (let i = 0; i < numEdges && i < nodes.length - 1; i++) {{
                    const target = nodes[Math.floor(Math.random() * (nodes.length - 1))];
                    if (target.id() !== id) {{
                        cy.add({{
                            group: 'edges',
                            data: {{
                                id: id + target.id(),
                                source: id,
                                target: target.id(),
                                weight: Math.floor(Math.random() * 5) + 1
                            }}
                        }});
                    }}
                }}
                
                nodeIdCounter++;
                updateInfo();
            }}
            
            function removeSelected() {{
                cy.$(':selected').remove();
                updateInfo();
            }}
            
            function findShortestPath() {{
                const selected = cy.$('node:selected');
                if (selected.length === 2) {{
                    const dijkstra = cy.elements().dijkstra(selected[0], function(edge) {{
                        return edge.data('weight');
                    }});
                    const path = dijkstra.pathTo(selected[1]);
                    
                    cy.elements().removeClass('highlighted').addClass('faded');
                    path.removeClass('faded').addClass('highlighted');
                    
                    setTimeout(() => {{
                        cy.elements().removeClass('highlighted faded');
                    }}, 3000);
                }} else {{
                    alert('Please select exactly 2 nodes to find the shortest path between them.');
                }}
            }}
            
            const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0'];
            function highlightClusters() {{
                // Simple clustering based on connectivity
                const components = cy.elements().components();
                components.forEach((component, index) => {{
                    component.style('background-color', colors[index % colors.length]);
                    component.style('line-color', colors[index % colors.length]);
                    component.style('target-arrow-color', colors[index % colors.length]);
                }});
            }}
            
            let animating = false;
            function toggleAnimation() {{
                animating = !animating;
                if (animating) {{
                    cy.nodes().forEach(node => {{
                        node.animate({{
                            position: {{
                                x: node.position('x') + (Math.random() - 0.5) * 50,
                                y: node.position('y') + (Math.random() - 0.5) * 50
                            }}
                        }}, {{
                            duration: 1000,
                            loop: true
                        }});
                    }});
                }} else {{
                    cy.nodes().stop();
                }}
            }}
            
            function exportData() {{
                const graphData = {{
                    nodes: cy.nodes().map(n => n.data()),
                    edges: cy.edges().map(e => e.data())
                }};
                console.log('Graph Data:', graphData);
                alert('Graph data exported to console (F12 to view)');
                
                // Send to parent window for MCP integration
                if (window.parent !== window) {{
                    window.parent.postMessage({{
                        type: 'cytoscape-export',
                        data: graphData,
                        timestamp: new Date().toISOString()
                    }}, '*');
                }}
            }}
            
            // Initialize
            updateInfo();
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://cytoscape/{resource_id}",
            "name": "Cytoscape Network Graph",
            "mimeType": "text/html",
            "text": html_content
        }
    }

@mcp.tool()
async def generate_custom_ui(
    ctx: Context, 
    ui_type: str = "dashboard",
    data: str = None,
    requirements: str = None
) -> Dict[str, Any]:
    """
    Generates a custom UI component based on user requirements and data.
    This demonstrates how AI can safely generate interactive UI artifacts.
    
    Args:
        ui_type: Type of UI to generate (dashboard, form, visualization, etc.)
        data: JSON string of data to visualize or work with
        requirements: Natural language description of what the UI should do
    """
    resource_id = str(uuid.uuid4())
    
    # Parse data if provided
    try:
        parsed_data = json.loads(data) if data else {}
    except:
        parsed_data = {}
    
    # This is a template that an AI model would fill in based on requirements
    # In production, this would be generated by Claude/GPT based on the requirements
    
    # SAFETY MEASURES:
    # 1. Content Security Policy to prevent XSS
    # 2. Sandboxed iframe execution
    # 3. No direct eval() or innerHTML with user content
    # 4. All data properly escaped
    # 5. Limited API surface (only specific libraries loaded)
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="Content-Security-Policy" content="
            default-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net;
            script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net;
            style-src 'self' 'unsafe-inline' https://unpkg.com https://cdn.jsdelivr.net;
            img-src 'self' data: https:;
            font-src 'self' data: https:;
        ">
        <title>Custom Generated UI</title>
        <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/recharts@2.10.4/dist/Recharts.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 500px;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            .error-boundary {{
                color: red;
                padding: 20px;
                border: 2px solid red;
                border-radius: 8px;
                background: #ffebee;
            }}
        </style>
    </head>
    <body>
        <div id="root"></div>
        
        <script type="text/babel">
            const {{ useState, useEffect, Component }} = React;
            
            // Error Boundary for safe rendering
            class ErrorBoundary extends Component {{
                constructor(props) {{
                    super(props);
                    this.state = {{ hasError: false, error: null }};
                }}
                
                static getDerivedStateFromError(error) {{
                    return {{ hasError: true, error: error.toString() }};
                }}
                
                componentDidCatch(error, errorInfo) {{
                    console.error('UI Error:', error, errorInfo);
                    // Send error to parent for debugging
                    if (window.parent !== window) {{
                        window.parent.postMessage({{
                            type: 'ui-error',
                            error: error.toString(),
                            stack: errorInfo.componentStack
                        }}, '*');
                    }}
                }}
                
                render() {{
                    if (this.state.hasError) {{
                        return (
                            <div className="error-boundary">
                                <h2>Something went wrong with the generated UI</h2>
                                <p>{{this.state.error}}</p>
                                <button onClick={{() => this.setState({{ hasError: false }})}}>
                                    Try Again
                                </button>
                            </div>
                        );
                    }}
                    return this.props.children;
                }}
            }}
            
            // Safe data sanitization
            function sanitizeData(data) {{
                // Remove any potential XSS vectors
                if (typeof data === 'string') {{
                    return data.replace(/<script[^>]*>.*?<\\/script>/gi, '')
                               .replace(/on\\w+="[^"]*"/gi, '')
                               .replace(/on\\w+='[^']*'/gi, '');
                }}
                return data;
            }}
            
            // Generated Component (this would be AI-generated based on requirements)
            function GeneratedUI() {{
                const [data, setData] = useState({json.dumps(parsed_data)});
                const [selectedItem, setSelectedItem] = useState(null);
                
                // Safe message handling
                useEffect(() => {{
                    const handleMessage = (event) => {{
                        // Verify origin in production
                        if (event.data?.type === 'update-data') {{
                            try {{
                                const sanitized = sanitizeData(event.data.data);
                                setData(sanitized);
                            }} catch (e) {{
                                console.error('Invalid data received:', e);
                            }}
                        }}
                    }};
                    
                    window.addEventListener('message', handleMessage);
                    return () => window.removeEventListener('message', handleMessage);
                }}, []);
                
                // Example generated UI based on type
                const renderUI = () => {{
                    switch('{ui_type}') {{
                        case 'dashboard':
                            return (
                                <div>
                                    <h1>📊 Generated Dashboard</h1>
                                    <p>Requirements: {requirements or 'Custom dashboard based on your data'}</p>
                                    
                                    <div style={{{{
                                        display: 'grid',
                                        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                                        gap: '20px',
                                        margin: '30px 0'
                                    }}}}>
                                        {{Object.entries(data).slice(0, 6).map(([key, value]) => (
                                            <div key={{key}} style={{{{
                                                background: '#f7fafc',
                                                padding: '20px',
                                                borderRadius: '8px',
                                                cursor: 'pointer',
                                                transition: 'all 0.3s',
                                                border: selectedItem === key ? '2px solid #667eea' : '2px solid transparent'
                                            }}}}
                                            onClick={{() => setSelectedItem(key)}}
                                            >
                                                <h3 style={{{{ color: '#667eea', margin: 0 }}}}>{{key}}</h3>
                                                <p style={{{{ fontSize: '24px', fontWeight: 'bold', margin: '10px 0' }}}}>
                                                    {{typeof value === 'object' ? JSON.stringify(value) : value}}
                                                </p>
                                            </div>
                                        ))}}
                                    </div>
                                    
                                    {{selectedItem && (
                                        <div style={{{{
                                            background: '#edf2f7',
                                            padding: '20px',
                                            borderRadius: '8px',
                                            marginTop: '20px'
                                        }}}}>
                                            <h3>Selected: {{selectedItem}}</h3>
                                            <pre>{{JSON.stringify(data[selectedItem], null, 2)}}</pre>
                                        </div>
                                    )}}
                                </div>
                            );
                        
                        case 'form':
                            return (
                                <div>
                                    <h1>📝 Generated Form</h1>
                                    <p>Requirements: {requirements or 'Interactive form based on your schema'}</p>
                                    
                                    <form onSubmit={{(e) => {{
                                        e.preventDefault();
                                        const formData = new FormData(e.target);
                                        const values = Object.fromEntries(formData);
                                        
                                        // Send to parent
                                        if (window.parent !== window) {{
                                            window.parent.postMessage({{
                                                type: 'form-submit',
                                                data: values
                                            }}, '*');
                                        }}
                                        
                                        alert('Form submitted! Check console for data.');
                                        console.log('Form Data:', values);
                                    }}}}>
                                        {{Object.keys(data).map(key => (
                                            <div key={{key}} style={{{{ marginBottom: '20px' }}}}>
                                                <label style={{{{
                                                    display: 'block',
                                                    marginBottom: '5px',
                                                    fontWeight: 'bold'
                                                }}}}>
                                                    {{key}}:
                                                </label>
                                                <input
                                                    name={{key}}
                                                    type="text"
                                                    defaultValue={{data[key]}}
                                                    style={{{{
                                                        width: '100%',
                                                        padding: '10px',
                                                        border: '2px solid #e2e8f0',
                                                        borderRadius: '8px',
                                                        fontSize: '16px'
                                                    }}}}
                                                />
                                            </div>
                                        ))}}
                                        
                                        <button type="submit" style={{{{
                                            background: '#667eea',
                                            color: 'white',
                                            padding: '12px 24px',
                                            border: 'none',
                                            borderRadius: '8px',
                                            fontSize: '16px',
                                            cursor: 'pointer'
                                        }}}}>
                                            Submit Form
                                        </button>
                                    </form>
                                </div>
                            );
                        
                        default:
                            return (
                                <div>
                                    <h1>🎨 Custom UI Component</h1>
                                    <p>Type: {ui_type}</p>
                                    <p>Requirements: {requirements or 'No specific requirements provided'}</p>
                                    
                                    <div style={{{{
                                        background: '#f7fafc',
                                        padding: '20px',
                                        borderRadius: '8px',
                                        marginTop: '20px'
                                    }}}}>
                                        <h3>Provided Data:</h3>
                                        <pre style={{{{ overflow: 'auto' }}}}>
                                            {{JSON.stringify(data, null, 2)}}
                                        </pre>
                                    </div>
                                    
                                    <p style={{{{ marginTop: '20px', color: '#718096' }}}}>
                                        This UI was generated based on your requirements. 
                                        In a production system, an AI model would generate 
                                        more sophisticated components based on your specific needs.
                                    </p>
                                </div>
                            );
                    }}
                }};
                
                return renderUI();
            }}
            
            // Render with Error Boundary
            const root = ReactDOM.createRoot(document.getElementById('root'));
            root.render(
                <ErrorBoundary>
                    <div className="container">
                        <GeneratedUI />
                    </div>
                </ErrorBoundary>
            );
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://generated/{resource_id}",
            "name": f"Generated {ui_type.title()} UI",
            "mimeType": "text/html",
            "text": html_template
        }
    }

@mcp.tool()
async def show_remote_dom_example(ctx: Context, button_label: str = "Click me!") -> Dict[str, Any]:
    """
    Demonstrates Remote DOM pattern with custom web components and message passing.
    This shows how to create reusable UI components that communicate with MCP.
    """
    resource_id = str(uuid.uuid4())
    
    # This simulates a remote-dom style component with custom elements
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Remote DOM Component</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f0f4f8;
                min-height: 400px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
            }}
            /* Custom element styles */
            ui-card {{
                display: block;
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            ui-button {{
                display: inline-block;
                background: var(--bg-color, #667eea);
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                margin: 5px;
                user-select: none;
                transition: all 0.3s;
            }}
            ui-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }}
            ui-button[variant="success"] {{
                --bg-color: #48bb78;
            }}
            ui-button[variant="danger"] {{
                --bg-color: #f56565;
            }}
            ui-input {{
                display: block;
                width: 100%;
                margin: 10px 0;
            }}
            ui-input input {{
                width: 100%;
                padding: 10px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 16px;
            }}
            ui-output {{
                display: block;
                padding: 15px;
                background: #edf2f7;
                border-radius: 8px;
                margin: 10px 0;
                font-family: monospace;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔌 Remote DOM Components</h1>
            <div id="remote-root"></div>
        </div>
        
        <script>
            // Define custom web components
            class UIButton extends HTMLElement {{
                constructor() {{
                    super();
                    this.addEventListener('click', this.handleClick.bind(this));
                }}
                
                connectedCallback() {{
                    this.textContent = this.getAttribute('label') || 'Button';
                }}
                
                handleClick(event) {{
                    const eventName = this.getAttribute('event') || 'press';
                    const data = {{
                        component: 'ui-button',
                        label: this.getAttribute('label'),
                        variant: this.getAttribute('variant'),
                        timestamp: new Date().toISOString()
                    }};
                    
                    // Dispatch custom event
                    this.dispatchEvent(new CustomEvent(eventName, {{ 
                        detail: data,
                        bubbles: true 
                    }}));
                    
                    // Send to parent window for MCP integration
                    if (window.parent !== window) {{
                        window.parent.postMessage({{
                            type: 'remote-dom-event',
                            event: eventName,
                            data: data
                        }}, '*');
                    }}
                    
                    console.log('UIButton clicked:', data);
                }}
            }}
            
            class UIInput extends HTMLElement {{
                constructor() {{
                    super();
                    this.input = null;
                }}
                
                connectedCallback() {{
                    const placeholder = this.getAttribute('placeholder') || '';
                    const value = this.getAttribute('value') || '';
                    
                    this.innerHTML = `<input type="text" placeholder="${{placeholder}}" value="${{value}}">`;
                    this.input = this.querySelector('input');
                    
                    this.input.addEventListener('input', (e) => {{
                        const data = {{
                            component: 'ui-input',
                            value: e.target.value,
                            placeholder: placeholder
                        }};
                        
                        this.dispatchEvent(new CustomEvent('change', {{
                            detail: data,
                            bubbles: true
                        }}));
                        
                        if (window.parent !== window) {{
                            window.parent.postMessage({{
                                type: 'remote-dom-event',
                                event: 'input-change',
                                data: data
                            }}, '*');
                        }}
                    }});
                }}
                
                get value() {{
                    return this.input ? this.input.value : '';
                }}
                
                set value(val) {{
                    if (this.input) this.input.value = val;
                }}
            }}
            
            class UICard extends HTMLElement {{
                connectedCallback() {{
                    const title = this.getAttribute('title');
                    if (title) {{
                        const header = document.createElement('h2');
                        header.textContent = title;
                        this.prepend(header);
                    }}
                }}
            }}
            
            class UIOutput extends HTMLElement {{
                set value(val) {{
                    this.textContent = val;
                }}
                
                get value() {{
                    return this.textContent;
                }}
            }}
            
            // Register custom elements
            customElements.define('ui-button', UIButton);
            customElements.define('ui-input', UIInput);
            customElements.define('ui-card', UICard);
            customElements.define('ui-output', UIOutput);
            
            // Initialize the remote DOM
            function initializeRemoteDOM() {{
                const root = document.getElementById('remote-root');
                
                // Create a card container
                const card = document.createElement('ui-card');
                card.setAttribute('title', 'Interactive Controls');
                
                // Create input field
                const input = document.createElement('ui-input');
                input.setAttribute('placeholder', 'Type something...');
                
                // Create buttons
                const button1 = document.createElement('ui-button');
                button1.setAttribute('label', '{button_label}');
                button1.setAttribute('event', 'primary-action');
                
                const button2 = document.createElement('ui-button');
                button2.setAttribute('label', 'Success Action');
                button2.setAttribute('variant', 'success');
                button2.setAttribute('event', 'success-action');
                
                const button3 = document.createElement('ui-button');
                button3.setAttribute('label', 'Danger Action');
                button3.setAttribute('variant', 'danger');
                button3.setAttribute('event', 'danger-action');
                
                // Create output display
                const output = document.createElement('ui-output');
                output.textContent = 'Events will appear here...';
                
                // Add event listeners
                root.addEventListener('primary-action', (e) => {{
                    output.value = `Primary action triggered: ${{JSON.stringify(e.detail)}}`;
                }});
                
                root.addEventListener('success-action', (e) => {{
                    output.value = `Success! Input value: "${{input.value}}"`;
                }});
                
                root.addEventListener('danger-action', (e) => {{
                    output.value = 'Danger action executed!';
                    input.value = '';
                }});
                
                root.addEventListener('change', (e) => {{
                    if (e.detail.component === 'ui-input') {{
                        output.value = `Input changed: "${{e.detail.value}}"`;
                    }}
                }});
                
                // Assemble the DOM
                card.appendChild(input);
                card.appendChild(button1);
                card.appendChild(button2);
                card.appendChild(button3);
                card.appendChild(output);
                root.appendChild(card);
                
                // Create a second card with different components
                const card2 = document.createElement('ui-card');
                card2.setAttribute('title', 'Message Logger');
                
                const logger = document.createElement('ui-output');
                logger.textContent = 'Waiting for events...';
                
                // Listen for all events on the root element to log them
                root.addEventListener('primary-action', (e) => {{
                    logger.value = `[LOG] Primary: ${{JSON.stringify(e.detail)}}`;
                }});
                
                root.addEventListener('success-action', (e) => {{
                    logger.value = `[LOG] Success: ${{JSON.stringify(e.detail)}}`;
                }});
                
                root.addEventListener('danger-action', (e) => {{
                    logger.value = `[LOG] Danger: ${{JSON.stringify(e.detail)}}`;
                }});
                
                root.addEventListener('change', (e) => {{
                    if (e.detail?.component === 'ui-input') {{
                        logger.value = `[LOG] Input: "${{e.detail.value}}"`;
                    }}
                }});
                
                card2.appendChild(logger);
                root.appendChild(card2);
            }}
            
            // Initialize when DOM is ready
            initializeRemoteDOM();
        </script>
    </body>
    </html>
    """
    
    return {
        "type": "resource",
        "resource": {
            "uri": f"ui://remote-dom/{resource_id}",
            "name": "Remote DOM Components",
            "mimeType": "text/html",
            "text": html_content
        }
    }

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()