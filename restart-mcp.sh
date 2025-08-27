#!/bin/bash

# Restart MCP Server Script
# This script stops and restarts the cursor-plans MCP server

echo "🔄 Restarting Cursor Plans MCP Server..."
echo

# Change to the cursor-plans directory
cd cursor-plans

# Check if there's a running MCP server process and kill it
echo "🛑 Stopping any running MCP server processes..."
pkill -f "cursor_plans_mcp" || echo "   No running MCP server found"

# Wait a moment for processes to stop
sleep 2

echo "🚀 Starting MCP server..."
echo "   (Press Ctrl+C to stop the server when needed)"
echo

# Start the MCP server
python3 -m cursor_plans_mcp.server

echo
echo "✅ MCP server stopped"