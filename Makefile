# MCP Inspector Standalone Server Makefile

.PHONY: run-inspector stop-inspector check-inspector-ports check-server-ports check-all-ports kill-conflicts kill-server-conflicts run-inspector-after-kill run-servers stop-servers kill-inspector-conflicts

# Default environment variables
CLIENT_PORT ?= 5173
SERVER_PORT ?= 8089
INSPECTOR_PORT ?= 8000
CONFIG_FILE ?= mcp_config.json

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
	@mkdir -p logs
	@if [ "$(FORCE)" = "1" ]; then \
		python mcp_inspector.py --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT) --force; \
	else \
		python mcp_inspector.py --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT); \
	fi

stop-inspector:
	@if [ -f .mcp-inspector.pid ]; then \
		echo "Stopping MCP Inspector server (PID: $$(cat .mcp-inspector.pid))..."; \
		kill $$(cat .mcp-inspector.pid) 2>/dev/null || echo "Process already stopped"; \
		rm .mcp-inspector.pid; \
	else \
		echo "No running MCP Inspector server found"; \
	fi

run-servers:
	@echo "Starting all MCP servers"
	@python mcp_servers.py run-all

stop-servers:
	@echo "Stopping all MCP servers..."
	@python mcp_servers.py stop 