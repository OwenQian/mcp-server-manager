# MCP Inspector Standalone Server Makefile

.PHONY: run-inspector stop-inspector help check-ports kill-conflicts force-kill-conflicts

# Default environment variables
CLIENT_PORT ?= 5173
SERVER_PORT ?= 8089
INSPECTOR_PORT ?= 8000

help:
	@echo "MCP Inspector Server Commands:"
	@echo "  make run-inspector        - Start the MCP inspector server"
	@echo "  make stop-inspector       - Stop the running MCP inspector server"
	@echo "  make check-ports          - Check if required ports are available"
	@echo "  make kill-conflicts       - Kill processes using conflicting ports"
	@echo "  make force-kill-conflicts - Force kill processes using conflicting ports (SIGKILL)"
	@echo ""
	@echo "Configuration options (can be set via environment variables):"
	@echo "  CLIENT_PORT=5173      - Port for the inspector client (default: 5173)"
	@echo "  SERVER_PORT=8089      - Port for the inspector server (default: 8089)"
	@echo "  INSPECTOR_PORT=8000   - Port for the SSE connection (default: 8000)"
	@echo ""
	@echo "Additional options:"
	@echo "  FORCE=1              - Force start even if ports are in use"

check-ports:
	@echo "Checking if required ports are available..."
	@./mcp_inspector.py --check-ports-only --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT)

kill-conflicts:
	@echo "Killing processes using conflicting ports..."
	@./mcp_inspector.py --kill-conflicts --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT)

force-kill-conflicts:
	@echo "Force killing processes using conflicting ports..."
	@./mcp_inspector.py --kill-conflicts --force-kill --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT)

run-inspector-after-kill: kill-conflicts
	@echo "Starting MCP Inspector server after killing conflicts..."
	@$(MAKE) run-inspector

run-inspector:
	@echo "Starting MCP Inspector server..."
	@mkdir -p logs
	@if [ "$(FORCE)" = "1" ]; then \
		./mcp_inspector.py --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT) --force; \
	else \
		./mcp_inspector.py --client-port $(CLIENT_PORT) --server-port $(SERVER_PORT) --inspector-port $(INSPECTOR_PORT); \
	fi

stop-inspector:
	@if [ -f .mcp-inspector.pid ]; then \
		echo "Stopping MCP Inspector server (PID: $$(cat .mcp-inspector.pid))..."; \
		kill $$(cat .mcp-inspector.pid) 2>/dev/null || echo "Process already stopped"; \
		rm .mcp-inspector.pid; \
	else \
		echo "No running MCP Inspector server found"; \
	fi 