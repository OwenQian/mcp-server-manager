# MCP Inspector Standalone Server Makefile

.PHONY: run-inspector check-server-ports run-servers stop-servers list restart-server restart-servers

# Default environment variables
CONFIG_FILE ?= mcp_config.json
KEEP_ALIVE ?= 1

check-server-ports:
	@echo "Checking if required server ports are available..."
	@python check_server_ports.py --config $(CONFIG_FILE)

run-inspector:
	@echo "Starting MCP Inspector..."
	@npx @modelcontextprotocol/inspector

run-servers:
	@echo "Starting all MCP servers..."
	@python mcp_launcher.py $(if $(filter 1,$(KEEP_ALIVE)),--keep-alive,)


stop-servers:
	@echo "Stopping all MCP servers..."
	@python mcp_servers.py stop 

list:
	@echo "Listing all servers"
	@python mcp_servers.py list

restart-server:
	@if [ -z "$(SERVER)" ]; then \
		echo "Error: SERVER parameter required. Usage: make restart-server SERVER=<server_name>"; \
		exit 1; \
	fi
	@echo "Restarting server: $(SERVER)"
	@python check_server_port.py --server $(SERVER) --config $(CONFIG_FILE) --kill-conflicts
	@python mcp_servers.py run $(SERVER)

restart-servers:
	@echo "Killing processes using conflicting ports and restarting all servers..."
	@python check_server_ports.py --config $(CONFIG_FILE) --kill-conflicts
	@python mcp_servers.py stop
	@python mcp_launcher.py
