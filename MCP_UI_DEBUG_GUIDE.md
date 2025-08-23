# MCP-UI Debug Guide

## 🔍 Current Issue
The UI components are "rendering nothing" - the assistant describes the components but they don't appear as interactive elements.

## 📋 Debug Setup Complete

### 1. Debug Server Running
- **File**: `/Users/mooki/Code/mcp-observability/mcp_local/ui_server/mcp_ui_server_debug.py`
- **Logs**: `/tmp/mcp_ui_debug.log`
- **Features**:
  - Comprehensive logging at every step
  - Debug info embedded in HTML
  - Console logging in browser
  - Log viewer tool (`check_debug_logs`)

### 2. Log Monitoring Active
Monitor tool calls in real-time:
```bash
tail -f /tmp/mcp_ui_debug.log | grep -E "(show_dashboard|show_form|show_chart|📤|🎯)"
```

### 3. Backend Logs
```bash
tail -f /tmp/librechat_backend.log | grep -E "(MCP|mcp-ui|Tool|tool)"
```

## 🧪 Testing Steps

### Step 1: Open LibreChat
Navigate to http://localhost:3090

### Step 2: Test Dashboard
Type in chat:
```
Show me the interactive dashboard
```

### Step 3: Check Browser Console
Open DevTools (F12) and look for:
- `🎯 Dashboard UI loaded - Resource ID: xxx`
- `✅ Dashboard UI fully loaded and ready`
- Any error messages

### Step 4: Check Server Logs
```bash
# Check if tool was called
grep "🎯 show_dashboard called" /tmp/mcp_ui_debug.log

# Check response format
grep "📤 Tool 'show_dashboard' response" /tmp/mcp_ui_debug.log

# View full response
grep -A 10 "Full response JSON" /tmp/mcp_ui_debug.log
```

### Step 5: Check Debug Logs from Chat
Type in chat:
```
Check the debug logs
```
This will call the `check_debug_logs` tool and show recent server activity.

## 🔎 What to Look For

### ✅ Correct Flow:
1. Tool gets called (see `🎯 show_dashboard called` in logs)
2. Response has correct structure:
   ```json
   {
     "type": "resource",
     "resource": {
       "uri": "ui://dashboard/xxx",
       "mimeType": "text/html",
       "text": "<html>...</html>"
     }
   }
   ```
3. LibreChat detects `ui://` URI
4. UIResourceRenderer component renders the HTML
5. HTML appears as interactive component

### ❌ Possible Issues:

#### Issue 1: Tool Not Being Called
- **Symptom**: No `🎯` logs in `/tmp/mcp_ui_debug.log`
- **Check**: Is the assistant actually calling the tool or just describing it?
- **Fix**: Update system prompt to ensure tool is called

#### Issue 2: Wrong Response Format
- **Symptom**: Tool called but response structure wrong
- **Check**: Look for `📤 Tool` logs to see actual response
- **Fix**: Ensure response matches UIResource format exactly

#### Issue 3: LibreChat Not Detecting UIResource
- **Symptom**: Response correct but renders as text
- **Check**: Browser console for detection logs
- **Fix**: Check if MCPUIDetector.tsx is working

#### Issue 4: UIResourceRenderer Not Rendering
- **Symptom**: Resource detected but nothing appears
- **Check**: Browser console for iframe errors
- **Fix**: Check Content Security Policy, iframe permissions

## 📊 Current Status

### ✅ Completed:
1. Debug server with comprehensive logging
2. Correct UIResource JSON format
3. Tools properly decorated with @mcp.tool()
4. HTML includes debug info and console logging
5. Server connected to LibreChat (confirmed in logs)

### 🔄 Monitoring:
- Server logs: `/tmp/mcp_ui_debug.log`
- Backend logs: `/tmp/librechat_backend.log`
- Real-time monitoring active (bash_45)

### 📝 Next Steps:
1. **Test in browser** - Try asking for dashboard/form/chart
2. **Check browser console** - Look for debug messages
3. **Review server logs** - Confirm tool calls and responses
4. **Check LibreChat code** - Verify UIResourceRenderer integration

## 🛠️ Quick Commands

```bash
# View last tool call
grep -E "🎯.*called" /tmp/mcp_ui_debug.log | tail -1

# View last response
grep "📤 Tool" /tmp/mcp_ui_debug.log | tail -1

# Check if HTML is being generated
grep "HTML content generated" /tmp/mcp_ui_debug.log | tail -5

# Monitor in real-time
tail -f /tmp/mcp_ui_debug.log

# Clear logs and restart
echo "" > /tmp/mcp_ui_debug.log
# Then restart backend
```

## 🎯 Key Insight
The issue is likely in one of these areas:
1. **Assistant behavior** - Not calling tools, just describing them
2. **Response format** - Not matching expected UIResource structure
3. **Frontend detection** - Not recognizing ui:// resources
4. **Rendering** - UIResourceRenderer not working properly

Use the debug logs to identify which step is failing!