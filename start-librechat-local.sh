#!/bin/bash

# Start LibreChat with MCP UI Server locally

echo "🚀 Starting LibreChat with MCP UI Server..."

# Set working directory
cd librechat-source

# Ensure we have the config file
if [ ! -f "librechat.yaml" ]; then
    echo "❌ librechat.yaml not found in librechat-source/"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Created .env from .env.example - please configure it"
    fi
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start LibreChat
echo "🎯 Starting LibreChat on http://localhost:3080"
echo "📋 MCP UI Server will be available in the chat interface"
echo ""
echo "Available MCP UI Tools:"
echo "  - show_dashboard: Interactive system dashboard"
echo "  - show_form: User registration form"
echo "  - show_chart [type]: Interactive charts (bar/line/pie/doughnut/radar)"
echo ""
echo "Press Ctrl+C to stop"

# Start LibreChat with the config
npm run backend:dev