#!/bin/bash

# LibreChat with MCP UI Server Stop Script
# This script stops all services started by start-librechat-mcp.sh

echo "🛑 Stopping LibreChat with MCP UI Services"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to stop a service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping $service_name (PID: $PID)...${NC}"
            kill $PID 2>/dev/null
            sleep 1
            
            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID 2>/dev/null
            fi
            
            echo -e "${GREEN}✓ $service_name stopped${NC}"
        else
            echo -e "${YELLOW}$service_name was not running (PID: $PID)${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${YELLOW}No PID file found for $service_name${NC}"
    fi
}

# Stop services using PID files
stop_service "LibreChat Backend" "/tmp/librechat-backend.pid"
stop_service "LibreChat Frontend" "/tmp/librechat-frontend.pid"

# MCP UI Server is managed by LibreChat via stdio, so it stops when backend stops
echo -e "${YELLOW}MCP UI Server will stop with LibreChat backend${NC}"

# Also try to stop by process name as backup
echo -e "${YELLOW}Cleaning up any remaining processes...${NC}"

# Stop MCP UI Server
pkill -f "mcp_local.ui_server.main" 2>/dev/null

# Stop LibreChat backend
pkill -f "api/server/index.js" 2>/dev/null

# Stop LibreChat frontend
pkill -f "vite" 2>/dev/null

# Stop MongoDB Docker container if we started it
docker stop mongodb-librechat 2>/dev/null && docker rm mongodb-librechat 2>/dev/null

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✓ All services stopped${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# Clean up log files (optional)
read -p "Do you want to clean up log files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f /tmp/mcp-ui-server.log
    rm -f /tmp/librechat-backend.log
    rm -f /tmp/librechat-frontend.log
    echo -e "${GREEN}✓ Log files cleaned${NC}"
fi