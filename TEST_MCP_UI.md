# Testing MCP-UI Integration in LibreChat

## ✅ Setup Complete

### Servers Running:
- **Frontend**: http://localhost:3090
- **Backend**: http://localhost:3080
- **MCP-UI Compliant Server**: Loaded with 5 tools

### Available MCP-UI Tools:
1. `show_dashboard` - Interactive system dashboard
2. `show_form` - User information form
3. `show_chart` - Interactive charts (bar/line/pie)
4. `handle_dashboard_action` - Process dashboard interactions
5. `process_form_submission` - Handle form submissions

## 🧪 Test Instructions

### 1. Open LibreChat
Navigate to http://localhost:3090 in your browser

### 2. Test Dashboard
Type in chat:
```
Show me an interactive dashboard
```

Expected: The assistant will call `show_dashboard` and return a UIResource that renders as an interactive dashboard with:
- Real-time clock
- Metric cards
- Action buttons (Refresh, Export, Settings)

### 3. Test Form
Type in chat:
```
Show me a user form
```

Expected: Interactive form with:
- Name field
- Email field
- Role dropdown
- Comments textarea
- Submit button

### 4. Test Charts
Type in chat:
```
Show me a bar chart
```

Expected: Interactive chart using Chart.js with buttons to switch between bar/line/pie views

### 5. Test Interactions
- Click buttons in the dashboard
- Submit the form
- Switch chart types

These should trigger `postMessage` events that call back to MCP tools.

## 🔍 Debugging

### Check Console Logs
Open browser DevTools (F12) and look for:
- `✅ MCP UI Resource detected!` - Resource detected in tool output
- `MCP UI Action:` - User interactions captured
- `ToolCallInfo - Storing MCP UI resource:` - Resource being stored

### Check Network
MCP communication happens via the backend, so check:
- WebSocket connections to backend
- Tool calls in the network tab

## 📝 Current Implementation Status

### ✅ Completed:
1. **Python MCP Server**: Returns proper UIResource JSON format
2. **LibreChat Integration**: Has UIResourceRenderer component
3. **Configuration**: MCP server configured in librechat.yaml
4. **UI Detection**: Components detect and render ui:// resources
5. **Interaction Handling**: postMessage events captured

### 🔄 How It Works:

1. **User asks** for dashboard/form/chart
2. **LLM calls** MCP tool (e.g., `show_dashboard`)
3. **Python server** returns UIResource:
   ```json
   {
     "type": "resource",
     "resource": {
       "uri": "ui://dashboard/abc-123",
       "mimeType": "text/html",
       "text": "<html>...</html>"
     }
   }
   ```
4. **LibreChat detects** resource type and renders with UIResourceRenderer
5. **User interacts** → postMessage → onUIAction handler
6. **Handler** can call other MCP tools for updates

## 🎯 Key Points

- **No TypeScript server needed** - Python returns JSON directly
- **Protocol-based** - Any language can implement by returning correct JSON
- **Interactive** - Full HTML/JS capabilities in sandboxed iframes
- **Bidirectional** - UI can trigger tool calls via postMessage

## 🚀 Next Steps

If the UI resources appear as code blocks instead of interactive components:
1. Check that `@mcp-ui/client` is installed
2. Verify UIResourceRenderer is imported in ToolCallInfo.tsx
3. Check console for detection logs
4. Ensure the MCP server is returning correct JSON structure

The integration is complete and should be working!