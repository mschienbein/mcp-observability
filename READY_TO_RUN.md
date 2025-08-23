# 🚀 LibreChat + MCP UI Server - READY TO RUN!

## ✅ Configuration Complete

LibreChat is now properly configured to use the MCP UI server via stdio transport. The MCP UI tools will appear in the LibreChat interface.

## 📋 Key Configuration Points

### 1. **MCP Server Configuration** (`librechat.yaml`)
```yaml
mcpServers:
  mcp-ui-tools:
    command: uv
    args: [run, python, -m, mcp_local.ui_server.main]
    cwd: /Users/mooki/Code/mcp-observability
    startup: true      # CRITICAL: Auto-start on LibreChat launch
    chatMenu: true     # CRITICAL: Makes it appear in UI
    serverInstructions: |
      Interactive UI tools available...
```

### 2. **Environment Variables** (`.env`)
```bash
MCP_ENABLED=true         # Required for MCP to work
ENABLE_MCP=true          # Enables MCP in interface
OPENAI_API_KEY=user_provided  # User provides key
```

### 3. **Transport Method**
- Using **stdio** transport (LibreChat starts the server)
- No need to manually start the MCP server
- LibreChat manages the server lifecycle

## 🎯 Quick Start

### Step 1: Start LibreChat
```bash
cd /Users/mooki/Code/mcp-observability
./start-librechat-mcp.sh
```

This will:
- ✅ Check MongoDB is running
- ✅ Start LibreChat backend (which starts MCP server via stdio)
- ✅ Start LibreChat frontend
- ✅ Open http://localhost:3080

### Step 2: Configure in LibreChat UI
1. **Register/Login** to your account
2. **Go to Settings** (gear icon)
3. **Add your OpenAI API key**
4. **Select OpenAI** as provider
5. **Choose GPT-4 or GPT-3.5-turbo**

### Step 3: Enable MCP Tools
Look for the **MCP icon** in the chat interface:
- It should show "mcp-ui-tools" server
- Click to enable/select it
- The tools will be available to the AI

### Step 4: Test MCP UI Tools

Try these prompts:

#### 📝 Forms
```
"Show me a user registration form"
"Create an input form for user data"
```

#### 📊 Dashboard
```
"Display the system dashboard"
"Show me live metrics"
```

#### 📋 Data Tables
```
"Show me a data table with pagination"
"Display a list of users in a table"
```

#### 📈 Charts
```
"Create a bar chart"
"Show me a pie chart visualization"
"Display a line graph"
```

#### ⚙️ Settings
```
"Show me the settings panel"
"Display configuration options"
```

## 🔍 What You'll See

When the MCP tools work correctly:

1. **In Chat Input Area**: You'll see an MCP icon/indicator
2. **When Tool is Called**: The AI will show it's calling a tool like:
   ```
   Calling tool: get_user_form
   ```
3. **Artifact Appears**: An artifact card appears with:
   - **Preview Tab**: Interactive HTML UI
   - **Code Tab**: JSON resource data
4. **Interaction**: You can interact with forms, buttons, etc.

## ⚠️ Troubleshooting

### MCP Not Appearing in UI?
1. Check `.env` has `MCP_ENABLED=true`
2. Verify `librechat.yaml` has `chatMenu: true`
3. Restart LibreChat completely
4. Check browser console for errors

### MCP Tools Not Working?
1. Look for MCP icon in chat interface
2. Click to enable the mcp-ui-tools server
3. Check LibreChat backend logs for stdio errors
4. Verify the working directory is correct in yaml

### Server Connection Issues?
The stdio transport means:
- LibreChat starts the server automatically
- No need to run the MCP server separately
- Check LibreChat backend logs for server output

## 📝 Verification Checklist

- [ ] MongoDB is running
- [ ] LibreChat backend starts without errors
- [ ] LibreChat frontend loads at http://localhost:3080
- [ ] Can register/login to LibreChat
- [ ] Can add OpenAI API key
- [ ] MCP icon appears in chat interface
- [ ] Can select mcp-ui-tools server
- [ ] Tools respond when called
- [ ] Artifacts appear with UI resources

## 🎉 Success!

Once everything is running:
1. The MCP tools are available in the chat
2. Interactive UIs appear as artifacts
3. You can test all 7 UI tools
4. The integration is working!

## 📂 Key Files
```
librechat-source/
├── librechat.yaml      # MCP server configured here
├── .env                # MCP_ENABLED=true here
└── client/src/components/Artifacts/
    ├── MCPUIArtifact.tsx
    └── MCPUIRenderer.tsx

mcp_local/ui_server/
└── main.py            # The MCP server (started by LibreChat)
```

## 🚦 Start Now!
```bash
./start-librechat-mcp.sh
```

Then open http://localhost:3080 and start testing MCP UI tools! 🚀