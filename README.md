# MCP Server Manager

A Python script to manage Model Context Protocol (MCP) servers with Supergateway as SSE servers.

## Features

- Configure and manage multiple MCP servers
- Set custom commands, arguments, and environment variables for each server
- Run individual, multiple, or all configured servers
- Support for both stdio and SSE MCP servers
- Automatically wraps stdio servers with Supergateway to expose them as SSE servers
- Run multiple servers simultaneously with background mode
- Properly manage and clean up background processes

## Installation

### Prerequisites

- Python 3.6+
- Supergateway must be installed and available in your PATH

## Usage

Make the script executable:
```bash
chmod +x mcp_servers.py
```

### Adding a new MCP server configuration

```bash
python mcp_servers.py add --name <server_name> --cmd <command> [--args arg1 arg2 ...] [--env KEY1=VALUE1 KEY2=VALUE2 ...] [--port <port>] [--type stdio|sse]
```

The `--type` parameter specifies whether the server is a stdio-based MCP server (needs supergateway) or an SSE-based server (can be run directly):
- `stdio` (default): The server will be wrapped with supergateway to convert it to an SSE server
- `sse`: The server already supports SSE and will be run directly without supergateway

Example for stdio server:
```bash
python mcp_servers.py add --name github-api --cmd python --args github_mcp_server.py --port 8080 --env API_KEY=abc123 --type stdio
```

Example for SSE server:
```bash
python mcp_servers.py add --name perplexity-api --cmd python --args perplexity_mcp_server.py --type sse
```

### Listing configured servers

```bash
python mcp_servers.py list
```

### Running servers

#### Run a single server:
```bash
python mcp_servers.py run <server_name>
```

#### Run multiple specific servers:
```bash
python mcp_servers.py run <server1_name> <server2_name> ... <serverN_name>
```

When running multiple servers, all except the last one will be launched in the background by default.
Each background server's output is logged to `/tmp/<server_name>.log`.

For example:
```bash
python mcp_servers.py run filesystem mcp-inspector
```

The script will:
1. Start the `filesystem` server in the background
2. Wait 5 seconds for it to initialize
3. Start the `mcp-inspector` server in the foreground
4. When you exit the foreground server, all background processes will be automatically terminated

#### Run without background mode:
```bash
python mcp_servers.py run <server1_name> <server2_name> ... --no-background
```

This will run each server in sequence (each one blocking until it's terminated).

#### Run without Supergateway:
```bash
python mcp_servers.py run <server_name> --no-supergateway
```

### Running all configured servers

```bash
python mcp_servers.py run-all
```

By default, all servers except the last one will be run in the background.
Use `--no-background` if you want to run them sequentially:

```bash
python mcp_servers.py run-all --no-background
```

### Stopping background servers

To stop all background servers (if the main script terminates unexpectedly):

```bash
python mcp_servers.py stop
```

### Removing a server configuration

```bash
python mcp_servers.py remove <server_name>
```

### Using a different configuration file

All commands support the `--config` flag to specify a custom configuration file path:

```bash
python mcp_servers.py <command> --config custom_config.json
```

## Configuration Format

The script stores server configurations in a JSON file (default: `mcp_config.json`):

```json
{
  "servers": [
    {
      "name": "github-api",
      "command": "python",
      "args": ["github_mcp_server.py"],
      "env_vars": {
        "API_KEY": "abc123"
      },
      "port": 8080,
      "server_type": "stdio"
    },
    {
      "name": "perplexity-api",
      "command": "python",
      "args": ["perplexity_mcp_server.py"],
      "env_vars": {},
      "port": null,
      "server_type": "sse"
    }
  ]
}
``` 