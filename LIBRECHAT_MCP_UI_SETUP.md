# LibreChat MCP UI Server Setup Guide

## Overview
This guide will help you configure LibreChat to use our local MCP UI server and enable OpenAI models for testing the MCP-UI integration.

## Configuration Steps

### 1. LibreChat Configuration File
We'll create a `librechat.yaml` configuration file that:
- Enables OpenAI models with user-provided API keys
- Configures our MCP UI server
- Sets up proper endpoints and model access

### 2. MCP UI Server Configuration
The MCP UI server will be configured as a local stdio server with the following tools:
- `get_user_form` - Interactive user registration form
- `get_dashboard` - System dashboard with metrics
- `get_settings_panel` - Settings configuration UI
- `get_data_table` - Paginated data table
- `get_chart_visualization` - Interactive charts
- `save_user_data` - Form data handler
- `update_settings` - Settings update handler

### 3. OpenAI Configuration
- Models: GPT-4, GPT-3.5-turbo
- Authentication: User-provided API key
- No proxy required for direct OpenAI access

## File Structure

```
librechat-source/
├── librechat.yaml          # Main configuration file
├── .env                    # Environment variables
└── client/
    └── src/
        └── components/
            └── Artifacts/  # MCP-UI integration components
```

## Running the Setup

### Step 1: Start the MCP UI Server
```bash
# In one terminal
cd /Users/mooki/Code/mcp-observability
uv run python -m mcp_local.ui_server.main
```

### Step 2: Start LibreChat Backend
```bash
# In another terminal
cd librechat-source
npm run backend:dev
```

### Step 3: Start LibreChat Frontend
```bash
# In another terminal
cd librechat-source
npm run frontend:dev
```

### Step 4: Access LibreChat
Open browser to: http://localhost:3090

### Step 5: Configure OpenAI
1. Go to Settings
2. Add your OpenAI API key
3. Select GPT-4 or GPT-3.5-turbo model

### Step 6: Test MCP UI Tools
In the chat, try:
- "Show me a user registration form"
- "Display the dashboard"
- "Show me a data table with pagination"
- "Create a bar chart"

## Expected Results

When you use MCP UI tools, you should see:
1. The tool being called in the assistant's response
2. An artifact appearing with the UI resource
3. Interactive HTML content in the Preview tab
4. JSON representation in the Code tab

## Troubleshooting

### MCP Server Not Connecting
- Ensure the MCP UI server is running
- Check that the stdio transport is configured correctly
- Verify the command path in librechat.yaml

### UI Resources Not Rendering
- Check browser console for errors
- Ensure @mcp-ui/client is installed
- Verify artifact type is set to 'mcp_ui'

### OpenAI Models Not Working
- Verify API key is correct
- Check network connectivity
- Ensure models are enabled in config

## Environment Variables

Required in `.env`:
```bash
# OpenAI (user will provide key in UI)
ALLOW_USER_API_KEYS=true

# MCP
MCP_ENABLED=true

# Server
HOST=localhost
PORT=3090

# Client
VITE_PORT=3091
```

## Security Notes

- OpenAI API keys are stored per-user
- MCP UI server runs locally only
- UI resources are sandboxed in iframes
- No external data is sent without user action

## Next Steps

Once everything is running:
1. Test each MCP UI tool
2. Verify interactions work correctly
3. Check that artifacts persist in conversation
4. Test with different OpenAI models
5. Try complex interactions with forms and charts