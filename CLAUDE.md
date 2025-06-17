# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based management system for Model Context Protocol (MCP) servers that:
- Manages multiple MCP servers simultaneously 
- Automatically wraps stdio-based MCP servers with Supergateway to expose them as SSE endpoints
- Provides web-based MCP Inspector for testing and debugging
- Integrates with AI assistants like Cursor by exposing servers via HTTP/SSE endpoints

## Core Architecture

### Key Components
- **`mcp_servers.py`**: Main server management with MCPServer class, supports stdio/sse server types
- **`mcp_launcher.py`**: Multi-server orchestrator using multiprocessing for parallel execution
- **`keep_alive.py`**: Auto-restart functionality with exponential backoff (up to 3 retries)
- **`mcp_config.json`**: Server configuration with environment variable resolution (`${VAR}` syntax)

### Process Management Strategy
- Background processes tracked globally for cleanup
- Process groups use `start_new_session=True` for proper signal handling
- Graceful shutdown: SIGTERM → wait → SIGKILL pattern
- Individual server logs at `/tmp/<server_name>.log`

## Common Development Commands

Use `/usr/bin/make` in place of `make`.

### Inspector Management
- `/usr/bin/make run-inspector` - Start MCP Inspector web interface using npx

### Server Management
- `/usr/bin/make run-servers` - Start all servers with keep-alive (default)
- `/usr/bin/make run-servers KEEP_ALIVE=0` - Start without keep-alive
- `/usr/bin/make stop-servers` - Stop all running servers
- `/usr/bin/make list` - List configured servers

### Port Conflict Resolution
- `/usr/bin/make check-server-ports` - Check server port availability
- `/usr/bin/make kill-server-conflicts` - Kill processes using server ports
- `/usr/bin/make restart-server SERVER=<n>` - Restart specific server with port cleanup

## Configuration

Servers are defined in `mcp_config.json` with structure:
```json
{
  "servers": [
    {
      "name": "server-name",
      "command": "command",
      "args": ["arg1", "arg2"],
      "env": {},
      "port": 8090,
      "server_type": "stdio"  // or "sse"
    }
  ]
}
```

Environment variables loaded from `.env` file (gitignored) and support `${VAR}` resolution in config.

## Port Management

- Uses `lsof` on macOS for port conflict detection  
- Each MCP server gets dedicated port configured in `mcp_config.json`
- Automatic conflict cleanup before starting services
- MCP Inspector runs via npx and handles its own port management