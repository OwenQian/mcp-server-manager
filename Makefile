# MCP Inspector Standalone Server Makefile

.PHONY: run-inspector stop-inspector check-inspector-ports check-server-ports check-all-ports kill-conflicts kill-server-conflicts kill-inspector-conflicts run-servers stop-servers list restart-server restart-servers

# Default environment variables
CLIENT_PORT ?= 5173
SERVER_PORT ?= 8089
INSPECTOR_PORT ?= 8000
CONFIG_FILE ?= mcp_config.json
KEEP_ALIVE ?= 1

check-inspector-ports:
	@echo "Checking if required inspector ports are available..."
	@python mcp_inspector.py --check-ports-only --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT)

check-server-ports:
	@echo "Checking if required server ports are available..."
	@python check_server_ports.py --config $(CONFIG_FILE)

check-all-ports: check-inspector-ports check-server-ports
	@echo "All port checks completed."

kill-conflicts:
	@echo "Killing processes using conflicting inspector ports..."
	@python mcp_inspector.py --kill-conflicts --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT)

kill-server-conflicts:
	@echo "Killing processes using conflicting server ports..."
	@python check_server_ports.py --config $(CONFIG_FILE) --kill-conflicts

kill-inspector-conflicts:
	@echo "Killing processes using conflicting inspector ports..."
	@python mcp_inspector.py --kill-conflicts --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT)

run-inspector:
	@echo "Starting MCP Inspector server..."
	@python mcp_launcher.py inspector \
		--client-port $(CLIENT_PORT) \
		--server-port $(SERVER_PORT) \
		--inspector-port $(INSPECTOR_PORT) \
		$(if $(FORCE),--force,) \
		$(if $(filter 1,$(KEEP_ALIVE)),--keep-alive,)

run-servers:
	@echo "Starting all MCP servers..."
	@python mcp_launcher.py $(if $(filter 1,$(KEEP_ALIVE)),--keep-alive,)

stop-inspector:
	@if [ -f .mcp-inspector.pid ]; then \
		echo "Stopping MCP Inspector server (PID: $$(cat .mcp-inspector.pid))..."; \
		kill $$(cat .mcp-inspector.pid) 2>/dev/null || echo "Process already stopped"; \
		rm .mcp-inspector.pid; \
	else \
		echo "No running MCP Inspector server found"; \
	fi

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
