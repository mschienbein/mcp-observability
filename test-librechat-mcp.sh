#!/bin/bash

echo "🧪 Testing LibreChat MCP Configuration"
echo "======================================="

# Check if MCP server can run
echo "1. Testing MCP server directly..."
/Users/mooki/Code/mcp-observability/.venv/bin/python -c "
import sys
sys.path.insert(0, '/Users/mooki/Code/mcp-observability')
from mcp_local.ui_server.mcp_ui_server_fixed import mcp
print('✅ MCP server module loaded successfully')
print(f'   Tools available: {list(mcp.tools.keys())}')
" || { echo "❌ Failed to load MCP server"; exit 1; }

# Check librechat.yaml
echo ""
echo "2. Checking librechat.yaml configuration..."
if grep -q "mcp-ui-server:" librechat-source/librechat.yaml; then
    echo "✅ MCP server configured in librechat.yaml"
    grep -A5 "mcp-ui-server:" librechat-source/librechat.yaml | sed 's/^/   /'
else
    echo "❌ MCP server not found in librechat.yaml"
    exit 1
fi

# Check .env file
echo ""
echo "3. Checking .env configuration..."
if [ -f librechat-source/.env ]; then
    if grep -q "MCP_ENABLED=true" librechat-source/.env; then
        echo "✅ MCP_ENABLED=true found in .env"
    else
        echo "⚠️  MCP_ENABLED not set to true. Adding it..."
        echo "MCP_ENABLED=true" >> librechat-source/.env
    fi
    
    if grep -q "DEBUG_MCP=true" librechat-source/.env; then
        echo "✅ DEBUG_MCP=true found in .env (verbose logging enabled)"
    else
        echo "   Adding DEBUG_MCP=true for troubleshooting..."
        echo "DEBUG_MCP=true" >> librechat-source/.env
    fi
else
    echo "❌ .env file not found"
    exit 1
fi

echo ""
echo "4. Starting LibreChat with MCP debugging..."
echo "==========================================="
echo "Watch for these in the logs:"
echo "  - 'Initializing MCP servers...'"
echo "  - 'MCP server 'mcp-ui-server' started'"
echo "  - Any MCP-related errors"
echo ""
echo "LibreChat will start at: http://localhost:3080"
echo "Press Ctrl+C to stop"
echo ""

cd librechat-source
npm run backend:dev 2>&1 | grep --line-buffered -E "MCP|mcp|Model Context Protocol|mcp-ui-server|Initializing"