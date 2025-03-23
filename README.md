# MCP Server Manager

A Python script to manage Model Context Protocol (MCP) servers with Supergateway as SSE servers.

## Features

- Configure and manage multiple MCP servers
- Automatically wraps stdio servers with Supergateway to expose them as SSE servers
- Run multiple servers simultaneously with background mode
- Support for both stdio and SSE MCP servers
- Properly manage and clean up background processes


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
# Run all configured MCP servers (with keep-alive enabled by default)
make run-servers

# Run servers without keep-alive
make run-servers KEEP_ALIVE=0
```

The keep-alive functionality (enabled by default) provides automatic server recovery:
- Each server runs in its own monitored process
- If a server crashes, it will automatically restart up to 3 times
- The retry counter resets after 30 seconds of successful operation
- Servers are monitored independently - if one crashes, others continue running
- Clean shutdown of all servers when interrupted (Ctrl+C)

### 4. Configure Cursor to Use MCP Servers

Create or edit the Cursor MCP configuration file at `~/.cursor/mcp.json`:

See the [Using with Cursor](#using-with-cursor) section below for more details on available servers and usage examples.

### 5. Test Connectivity
In the MCP Inspector web interface:
1. Connect to an SSE endpoint (e.g., http://localhost:8090/sse)
2. Try using one of the available MCP services

Or open Cursor and ask a question that would use one of your configured MCP servers.

### 6. Stopping Servers
```bash
# Stop MCP Inspector
make stop-inspector

# Stop all other MCP servers
make stop-servers
```

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
# Check if all ports (inspector and server) are available
make check-all-ports

# Kill processes using conflicting inspector ports
make kill-conflicts

# Start the MCP Inspector server
make run-inspector

# Stop the MCP Inspector server
make stop-inspector

# Run all MCP servers
make run-servers

# Stop all running MCP servers
make stop-servers

# Force start even if ports are in use
FORCE=1 make run-inspector

# Use a custom configuration file
CONFIG_FILE=custom_config.json make check-server-ports
```

### Configuration Options

You can customize the MCP Inspector server by setting environment variables:

```bash
# Custom ports
CLIENT_PORT=5174 SERVER_PORT=8090 INSPECTOR_PORT=8001 make run-inspector

# Check specific ports
CLIENT_PORT=5174 SERVER_PORT=8090 INSPECTOR_PORT=8001 make check-inspector-ports

# Kill processes on specific ports
CLIENT_PORT=5174 SERVER_PORT=8090 INSPECTOR_PORT=8001 make kill-conflicts
```

### Port Conflict Detection

The MCP Inspector now automatically checks if required ports are available before starting. If a port is already in use, it will show the PIDs of the conflicting processes and fail. You can:

1. Fix the conflicts by stopping the conflicting processes manually
2. Use different ports with the `CLIENT_PORT`, `SERVER_PORT`, and `INSPECTOR_PORT` variables
3. Force start with the `--force` option or `FORCE=1` environment variable
4. Automatically kill conflicting processes with `make kill-conflicts` or `python mcp_inspector.py --kill-conflicts`

Server port checking is dynamic and reads from the `mcp_config.json` configuration file. This ensures all ports needed by your servers are properly checked without hardcoding. You can:

1. Run `make check-server-ports` to check all server ports defined in the config
2. Run `make kill-server-conflicts` to kill processes using server ports
3. Use a different config file with `CONFIG_FILE=custom_config.json make check-server-ports`

## Managing MCP Servers

### Adding a new MCP server configuration
The easiest way is to tell Cursor to do it for you. You can also use the CLI or edit `mcp_config.json` directly.

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

#### Run all servers:
```bash
# Run with keep-alive (default)
make run-servers

# Run without keep-alive
make run-servers KEEP_ALIVE=0
# or
python mcp_servers.py run-all
```

#### Run a single server:
```bash
python mcp_servers.py run <server_name>
```

#### Run multiple specific servers:
```bash
python mcp_servers.py run <server1_name> <server2_name> ... <serverN_name>
```

When running multiple servers:
- Each server runs in its own process
- By default (or with `KEEP_ALIVE=1`):
  - Each server is monitored independently
  - Automatic restart on crash (up to 3 attempts)
  - Retry counter resets after 30 seconds of stable operation
  - One server crashing doesn't affect others
- Server output is logged to `/tmp/<server_name>.log`

### Stopping servers

To stop all servers:
```bash
# Stop all servers (sends interrupt signal)
make stop-servers
```

The servers will shut down gracefully when stopped.

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

## Using with Cursor

MCP (Model Context Protocol) servers enhance AI assistants like those in Cursor by allowing them to access external tools and data sources. By running these servers locally, you gain more control and privacy.

### Cursor Configuration

1. Create or edit the Cursor MCP configuration file at `~/.cursor/mcp.json`
2. Add your MCP servers as shown in the example below:

```json
{
  "mcpServers": {
    "filesystem": {
      "url": "http://localhost:8090/sse"
    },
    "youtube": {
      "url": "http://localhost:8092/sse"
    }
  }
}
```

You can add any of your running MCP servers from the `mcp_config.json` file to this configuration. Each server runs on its own port as specified in the config.

### Available MCP Servers

Depending on your configuration, you may have access to servers like:

- `filesystem` (port 8090): Access to your local file system
- `youtube` (port 8092): Search and fetch YouTube videos
- `fetch` (port 8093): Make HTTP requests
- `github` (port 8094): Interact with GitHub repos
- `brave-search` (port 8096): Web search capabilities
- `google-maps` (port 8098): Mapping and location services
- And more...

### Testing MCP Servers in Cursor

Once you've configured Cursor to use your MCP servers:

1. Open Cursor
2. Start a new chat and ask a question that would use one of the configured MCP servers
3. Cursor should now be able to use these servers to access additional functionality

For example:
- With the filesystem server, ask "List files in my Downloads folder"
- With the brave-search server, ask "Search the web for the latest news about AI"