# MCP Server Manager

A Python script to manage Model Context Protocol (MCP) servers with Supergateway as SSE servers.

## QuickStart

### 1. Set Up Environment
```bash
# Clone the repository and cd
cd mcp-server-manager

# Set up your environment file with API keys
cp .env.example .env
# Edit .env and add your API keys

# Install required packages
pip install -r requirements.txt
```

### 2. Run the MCP Inspector
```bash
# Start the MCP Inspector server
make run-inspector

# In a web browser, navigate to:
# http://localhost:5173
```

### 3. Run All MCP Servers
```bash
# In another terminal, run all configured MCP servers
python mcp_servers.py run-all --parallel
```

### 4. Test Connectivity
In the MCP Inspector web interface:
1. Connect to an SSE endpoint (e.g., http://localhost:8090/sse)
2. Try using one of the available MCP services

### 5. Stopping Servers
```bash
# Stop MCP Inspector
make stop-inspector

# Ctrl+C in the terminal running the servers or
# Stop all other MCP servers
python mcp_servers.py stop
```

## Features

- Configure and manage multiple MCP servers
- Set custom commands, arguments, and environment variables for each server
- Run individual, multiple, or all configured servers
- Support for both stdio and SSE MCP servers
- Automatically wraps stdio servers with Supergateway to expose them as SSE servers
- Run multiple servers simultaneously with background mode
- Properly manage and clean up background processes
- Support for environment variables in the configuration

## Installation

### Prerequisites

- Python 3.6+
- Supergateway must be installed and available in your PATH
- python-dotenv package (`pip install python-dotenv`)
- psutil package (`pip install psutil`)

### Environment Setup

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
# Then edit .env to add your actual API keys
```

Make sure to add `.env` to your `.gitignore` to avoid committing sensitive keys.

## MCP Inspector Server

The MCP Inspector server is now managed separately using a dedicated script and a Makefile.

### Running the MCP Inspector Server with Make

```bash
# Check if the required ports are available
make check-ports

# Kill processes using conflicting ports (uses SIGTERM)
make kill-conflicts

# Force kill processes using conflicting ports (uses SIGKILL)
make force-kill-conflicts 

# Kill conflicts and then start the inspector
make run-inspector-after-kill

# Start the MCP Inspector server
make run-inspector

# Stop the MCP Inspector server
make stop-inspector

# Show available commands and configuration options
make help

# Force start even if ports are in use
FORCE=1 make run-inspector
```

### Configuration Options

You can customize the MCP Inspector server by setting environment variables:

```bash
# Custom ports
CLIENT_PORT=5174 SERVER_PORT=8090 INSPECTOR_PORT=8001 make run-inspector

# Check specific ports
CLIENT_PORT=5174 SERVER_PORT=8090 INSPECTOR_PORT=8001 make check-ports

# Kill processes on specific ports
CLIENT_PORT=5174 SERVER_PORT=8090 INSPECTOR_PORT=8001 make kill-conflicts
```

### Running the MCP Inspector Server Directly

You can also run the MCP Inspector server directly using the dedicated Python script:

```bash
# Run in background mode (default)
./mcp_inspector.py

# Run in foreground mode
./mcp_inspector.py --foreground

# Customize ports
./mcp_inspector.py --client-port 5174 --server-port 8090 --inspector-port 8001

# Set additional environment variables
./mcp_inspector.py --env KEY1=value1 KEY2=value2

# Force start even if ports are in use
./mcp_inspector.py --force

# Only check if ports are available (won't start the server)
./mcp_inspector.py --check-ports-only

# Kill processes using conflicting ports
./mcp_inspector.py --kill-conflicts

# Kill processes with SIGKILL if SIGTERM doesn't work
./mcp_inspector.py --kill-conflicts --force-kill
```

### Port Conflict Detection

The MCP Inspector now automatically checks if required ports are available before starting. If a port is already in use, it will show the PIDs of the conflicting processes and fail. You can:

1. Fix the conflicts by stopping the conflicting processes manually
2. Use different ports with the `CLIENT_PORT`, `SERVER_PORT`, and `INSPECTOR_PORT` variables
3. Force start with the `--force` option or `FORCE=1` environment variable
4. Automatically kill conflicting processes with `make kill-conflicts` or `./mcp_inspector.py --kill-conflicts`

### Exit Codes

The port checking and conflict killing tools use the following exit codes:

- `make check-ports`: Exits with code 0 if all ports are available, 1 if there are conflicts
- `make kill-conflicts`: Exits with code 0 if all conflicts were successfully killed, 1 if there were issues
- `./mcp_inspector.py --check-ports-only`: Returns 0 if all ports are available, 1 if there are conflicts
- `./mcp_inspector.py --kill-conflicts`: Returns 0 if all conflicts were successfully killed, 1 if there were issues

These exit codes can be useful in shell scripts for conditional logic.

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

To reference an environment variable in the configuration:
```bash
python mcp_servers.py add --name github-api --cmd python --args github_mcp_server.py --env API_KEY=${GITHUB_API_KEY} --type stdio
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
2. Check if it started successfully
3. Start the `mcp-inspector` server in the foreground
4. When you exit the foreground server, all background processes will be automatically terminated

#### Run with parallel mode:
```bash
python mcp_servers.py run <server1_name> <server2_name> ... --parallel
```

This will start all servers in parallel (all in background) and keep the main process running to handle signals. Press Ctrl+C to stop all servers.

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

Use `--parallel` to start all servers in parallel:

```bash
python mcp_servers.py run-all --parallel
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
      "env": {
        "API_KEY": "${GITHUB_API_KEY}"
      },
      "port": 8080,
      "server_type": "stdio"
    },
    {
      "name": "perplexity-api",
      "command": "python",
      "args": ["perplexity_mcp_server.py"],
      "env": {},
      "port": null,
      "server_type": "sse"
    }
  ]
}
```

Environment variables in `env` can be referenced using `${VARIABLE_NAME}` syntax. These will be automatically resolved from the `.env` file when running the servers. 