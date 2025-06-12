# MCP SSE Launcher

A Python-based management system for Model Context Protocol (MCP) servers that automatically wraps stdio-based servers with Supergateway to expose them as SSE endpoints, plus provides a web-based inspector for testing.

## Key Features

- **Auto-update** - keeps MCP servers up-to-date automatically
- **Background monitoring** - restarts crashed servers automatically  
- **Web inspector** - debug and test MCP servers via browser
- **SSE conversion** - wraps stdio servers for HTTP/SSE access
- **AI assistant integration** - works with Cursor, Claude Desktop, etc.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment (copy .env.example to .env and add API keys)
cp .env.example .env

# 3. Start all MCP servers (with auto-restart)
make run-servers

# 4. Start web inspector for debugging
make run-inspector

# 5. View inspector at http://localhost:5173
```

## Common Use Cases

### Debug a specific MCP server
```bash
# Start inspector connected to filesystem server
make run-inspector SERVER=filesystem
# Then visit http://localhost:5173 to test filesystem operations
```

### Add a new MCP server
```bash
# Add GitHub MCP server
python mcp_servers.py add \
  --name github \
  --cmd npx \
  --args "-y @modelcontextprotocol/server-github" \
  --env GITHUB_TOKEN=your_token_here \
  --port 8094
```

### Use with Cursor AI
Add to `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "filesystem": { "url": "http://localhost:8090/sse" },
    "github": { "url": "http://localhost:8094/sse" },
    "brave-search": { "url": "http://localhost:8096/sse" }
  }
}
```

### Restart a problematic server
```bash
# Kill conflicts and restart specific server
make restart-server SERVER=github
```

### Run without auto-restart (for development)
```bash
make run-servers KEEP_ALIVE=0
```

## What Happens Automatically

- **Updates**: npm packages and git repos are checked/updated before starting
- **Port conflicts**: conflicting processes are detected and can be killed
- **Process monitoring**: crashed servers restart up to 3 times
- **Logging**: each server logs to `/tmp/<server_name>.log`
- **Cleanup**: all processes are properly terminated on exit

## Available MCP Servers

The default config includes popular servers like:
- **filesystem** (8090) - local file access
- **github** (8094) - GitHub repository interaction  
- **brave-search** (8096) - web search
- **fetch** (8093) - HTTP requests
- **youtube** (8092) - YouTube search/info
- **memory** (8100) - persistent memory
- **puppeteer** (8101) - web automation

## Troubleshooting

```bash
# Check what's using ports
make check-all-ports

# Kill conflicting processes
make kill-conflicts

# Stop everything
make stop-servers && make stop-inspector

# View server logs
tail -f /tmp/filesystem.log
```

## Configuration

Servers are defined in `mcp_config.json`. Environment variables use `${VAR}` syntax and are loaded from `.env`.

Example server config:
```json
{
  "name": "github",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"], 
  "env": {"GITHUB_TOKEN": "${GITHUB_TOKEN}"},
  "port": 8094,
  "server_type": "stdio"
}
```