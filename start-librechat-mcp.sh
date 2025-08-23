#!/bin/bash

# LibreChat with MCP UI Server Startup Script
# This script starts all necessary services for testing MCP-UI integration

echo "🚀 Starting LibreChat with MCP UI Integration"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if MongoDB is running
check_mongodb() {
    if command_exists mongosh; then
        mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1
    elif command_exists mongo; then
        mongo --eval "db.adminCommand('ping')" >/dev/null 2>&1
    else
        return 1
    fi
}

# Step 1: Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

if ! command_exists uv; then
    echo -e "${RED}❌ uv is not installed${NC}"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites checked${NC}"

# Step 2: Check MongoDB
echo -e "${YELLOW}Checking MongoDB...${NC}"

if ! check_mongodb; then
    echo -e "${YELLOW}MongoDB is not running. Attempting to start...${NC}"
    
    # Try to start MongoDB
    if command_exists mongod; then
        mongod --fork --logpath /tmp/mongodb.log --dbpath /usr/local/var/mongodb >/dev/null 2>&1
        sleep 2
        
        if check_mongodb; then
            echo -e "${GREEN}✓ MongoDB started${NC}"
        else
            echo -e "${YELLOW}Could not start MongoDB locally. Trying Docker...${NC}"
            docker run -d -p 27017:27017 --name mongodb-librechat mongo >/dev/null 2>&1
            sleep 3
            
            if check_mongodb; then
                echo -e "${GREEN}✓ MongoDB started in Docker${NC}"
            else
                echo -e "${RED}❌ Could not start MongoDB. Please start it manually.${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${YELLOW}mongod not found. Trying Docker...${NC}"
        docker run -d -p 27017:27017 --name mongodb-librechat mongo >/dev/null 2>&1
        sleep 3
        
        if check_mongodb; then
            echo -e "${GREEN}✓ MongoDB started in Docker${NC}"
        else
            echo -e "${RED}❌ Could not start MongoDB. Please install MongoDB or Docker.${NC}"
            exit 1
        fi
    fi
else
    echo -e "${GREEN}✓ MongoDB is running${NC}"
fi

# Step 3: MCP UI Server is started by LibreChat via stdio
echo -e "${YELLOW}MCP UI Server Configuration${NC}"
echo "The MCP UI server will be started automatically by LibreChat"
echo "It's configured in librechat.yaml as 'mcp-ui-tools'"
echo -e "${GREEN}✓ MCP UI Server configured for stdio transport${NC}"

# Step 4: Install LibreChat dependencies if needed
cd /Users/mooki/Code/mcp-observability/librechat-source

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing LibreChat dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Step 5: Start LibreChat backend
echo -e "${YELLOW}Starting LibreChat backend...${NC}"

# Kill any existing backend
pkill -f "npm run backend" 2>/dev/null
pkill -f "node api/server" 2>/dev/null
sleep 1

# Start backend
npm run backend > /tmp/librechat-backend.log 2>&1 &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 5

if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ LibreChat backend started (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}❌ Failed to start LibreChat backend${NC}"
    echo "Check logs at: /tmp/librechat-backend.log"
    exit 1
fi

# Step 6: Start LibreChat frontend
echo -e "${YELLOW}Starting LibreChat frontend...${NC}"

# Start frontend
npm run frontend > /tmp/librechat-frontend.log 2>&1 &
FRONTEND_PID=$!

echo "Waiting for frontend to compile..."
sleep 10

if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ LibreChat frontend started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${RED}❌ Failed to start LibreChat frontend${NC}"
    echo "Check logs at: /tmp/librechat-frontend.log"
    exit 1
fi

# Step 7: Success message
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "📍 Access LibreChat at: http://localhost:3080"
echo ""
echo "📝 Next steps:"
echo "  1. Open http://localhost:3080 in your browser"
echo "  2. Register or login to your account"
echo "  3. Go to Settings and add your OpenAI API key"
echo "  4. Select GPT-4 or GPT-3.5 model"
echo "  5. Try MCP UI tools:"
echo "     - 'Show me a user registration form'"
echo "     - 'Display the dashboard'"
echo "     - 'Show me a data table'"
echo "     - 'Create a bar chart'"
echo ""
echo "📊 Service PIDs:"
echo "  - LibreChat Backend: $BACKEND_PID"
echo "  - LibreChat Frontend: $FRONTEND_PID"
echo "  - MCP UI Server: Started by LibreChat via stdio"
echo ""
echo "📁 Log files:"
echo "  - LibreChat Backend: /tmp/librechat-backend.log"
echo "  - LibreChat Frontend: /tmp/librechat-frontend.log"
echo "  - MCP UI Server: Check LibreChat logs for stdio output"
echo ""
echo "🛑 To stop all services, run:"
echo "  ./stop-librechat-mcp.sh"
echo ""

# Save PIDs to file for stop script
echo "$BACKEND_PID" > /tmp/librechat-backend.pid
echo "$FRONTEND_PID" > /tmp/librechat-frontend.pid

# Keep script running
echo "Press Ctrl+C to stop all services..."
trap 'echo "Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit' INT
wait