# Claude Code MCP Configuration

This directory contains MCP (Model Context Protocol) server configurations for Claude Code.

## Available MCP Servers

### Custom Project Servers

1. **mcp-tools** / **mcp-tools-local**
   - Tools server with math and utility functions
   - Port: 3002
   - Features: add_numbers, multiply_numbers, get_timestamp, echo_message

2. **mcp-feedback** / **mcp-feedback-local**
   - Feedback collection server
   - Port: 3003
   - Features: submit_feedback, get_feedback_summary

### Standard MCP Servers

3. **filesystem**
   - File system access to the project directory
   - Path: `/Users/mooki/Code/mcp-observability`

4. **github**
   - GitHub repository interaction
   - Requires: `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable

5. **memory**
   - Persistent memory storage across conversations

### Cloud MCP Servers

6. **aws-knowledge-mcp-server**
   - AWS Knowledge Base MCP server
   - Type: SSE (Server-Sent Events)
   - URL: https://knowledge-mcp.global.api.aws

7. **context7**
   - Context7 MCP service
   - Type: SSE (Server-Sent Events)
   - URL: https://mcp.context7.com/sse

8. **github-copilot**
   - GitHub Copilot MCP integration
   - Type: HTTP
   - URL: https://api.githubcopilot.com/mcp/
   - Requires: `GITHUB_COPILOT_TOKEN` environment variable

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the project root with:

```bash
# Required for custom MCP servers
LANGFUSE_PUBLIC_KEY=pk-lf-xxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxx
LANGFUSE_HOST=http://your-langfuse-host

# Optional for GitHub MCP
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxx

# For GitHub Copilot MCP
GITHUB_COPILOT_TOKEN=ghp_xxxx
```

### 2. Install Dependencies

```bash
# Python dependencies for custom servers
uv venv
uv pip install -e .

# Node dependencies for standard servers (installed automatically)
# These will be fetched via npx when servers start
```

### 3. Enable in Claude Code

The servers should be automatically detected when you open this project in Claude Code.

If not, you can manually enable them:

1. Run `/mcp` in Claude Code
2. The servers defined in `.mcp.json` should appear
3. Select the servers you want to enable

### 4. Test the Servers

```bash
# Test custom servers locally
uv run python -m mcp.tools_server.main
uv run python -m mcp.feedback_server.main

# Or use the test clients
uv run test-mcp-tools
uv run test-mcp-feedback
```

## Configuration Files

- `.mcp.json` - Main MCP server configuration (project root)
- `.claude/mcp.json` - Alternative configuration location
- `.claude/settings.json` - Claude Code settings for MCP

## Troubleshooting

### Servers Not Appearing

1. Check that `.mcp.json` exists in the project root
2. Verify environment variables are set
3. Run `/doctor` in Claude Code to diagnose issues
4. Check that `uv` is installed and available in PATH

### Connection Errors

1. Ensure Python dependencies are installed: `uv pip install -e .`
2. Check that ports 3002 and 3003 are not in use
3. Verify Langfuse credentials if using observability features

### Environment Variables Not Loading

1. Make sure `.env` file exists in project root
2. Variables should use format: `${VAR_NAME}` in config
3. Restart Claude Code after changing environment variables

## Development

To add a new MCP server:

1. Create the server implementation in `mcp/your_server/`
2. Add configuration to `.mcp.json`:
   ```json
   {
     "your-server": {
       "command": "uv",
       "args": ["run", "python", "-m", "mcp.your_server.main"],
       "type": "stdio"
     }
   }
   ```
3. Enable in `.claude/settings.json`:
   ```json
   {
     "enabledMcpjsonServers": ["your-server", ...]
   }
   ```

## Security Notes

- Never commit `.env` files with real credentials
- Use environment variables for sensitive data
- The `filesystem` server has access to the entire project directory
- Review server permissions before enabling them