#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import time
import signal
import atexit
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Keep track of background processes for cleanup
background_processes = []


def cleanup_background_processes():
    """Terminate any background processes on exit"""
    for proc in background_processes:
        try:
            if proc.poll() is None:  # Check if process is still running
                proc.terminate()     # First try terminating gracefully
                print(f"Terminated background process {proc.pid}")
        except (ProcessLookupError, OSError) as e:
            print(f"Error terminating process: {e}")
    
    # Wait a moment for processes to terminate
    time.sleep(1)
    
    # Force kill any remaining processes
    for proc in background_processes:
        try:
            if proc.poll() is None:  # Still running after terminate
                proc.kill()          # Force kill
                print(f"Force killed background process {proc.pid}")
        except (ProcessLookupError, OSError):
            pass


# Register cleanup function
atexit.register(cleanup_background_processes)


class MCPServer:
    def __init__(
        self,
        name: str,
        command: str,
        args: List[str] = None,
        env: Dict[str, str] = None,
        port: Optional[int] = None,
        server_type: str = "stdio"  # New parameter for server type (stdio or sse)
    ):
        self.name = name
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.port = port
        self.server_type = server_type  # Store the server type

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "port": self.port,
            "server_type": self.server_type  # Include server_type in the serialized data
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MCPServer":
        return cls(
            name=data["name"],
            command=data["command"],
            args=data.get("args", []),
            env=data.get("env", {}),
            port=data.get("port"),
            server_type=data.get("server_type", "stdio")  # Default to stdio for backward compatibility
        )


def load_config(config_file: str) -> List[MCPServer]:
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            return [MCPServer.from_dict(server_data) for server_data in config_data["servers"]]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)


def save_config(config_file: str, servers: List[MCPServer]):
    config_data = {"servers": [server.to_dict() for server in servers]}
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)


def run_server(server: MCPServer, use_supergateway: bool = True, run_in_background: bool = False):
    env = os.environ.copy()
    
    # Process environment variables to expand any ${VAR} references
    processed_env_vars = {}
    for key, value in server.env.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            # Extract variable name from ${VAR}
            env_var_name = value[2:-1]
            # Get actual value from environment
            env_var_value = os.environ.get(env_var_name, "")
            processed_env_vars[key] = env_var_value
            print(f"Using environment variable for {key}")
        else:
            processed_env_vars[key] = value
    
    # Update environment with processed variables
    env.update(processed_env_vars)
    
    base_cmd = [server.command] + server.args
    
    # Only use supergateway if requested AND server is a stdio type
    if use_supergateway and server.server_type == "stdio":
        # Construct the command to be wrapped by supergateway
        cmd_str = f"{server.command} {' '.join(server.args)}"
        
        # Construct the supergateway command
        cmd = ["npx", "-y", "supergateway", "--stdio", cmd_str]
        if server.port:
            # Insert port argument before the stdio argument
            cmd = ["npx", "-y", "supergateway", "--port", str(server.port), "--stdio", cmd_str]
    else:
        # Run the command directly without supergateway
        cmd = base_cmd
    
    print(f"Starting {server.name}...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        if run_in_background:
            # Create log file
            log_file_path = f"/tmp/{server.name}.log"
            log_file = open(log_file_path, "w")
            
            # Run process in background
            # Use start_new_session=True instead of preexec_fn for macOS compatibility
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
            )
            
            # Track this process for cleanup
            background_processes.append(process)
            
            print(f"Server {server.name} launched in background with PID {process.pid}")
            print(f"Logs are written to {log_file_path}")
            
            # Check if process exited immediately (indicating a failure)
            # Give a short grace period for immediate crashes
            time.sleep(0.5)
            if process.poll() is not None:
                print(f"ERROR: Server {server.name} exited immediately with code {process.returncode}")
                print(f"Check logs at {log_file_path}")
                return False
            
            print(f"Server {server.name} is running")
            
            # If it's a stdio server with supergateway, print the connection URL
            if use_supergateway and server.server_type == "stdio":
                port = server.port if server.port else 8000
                print(f"Connect to SSE endpoint: http://localhost:{port}/sse")
                print(f"POST messages to: http://localhost:{port}/message")
        else:
            subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running server {server.name}: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\nStopping {server.name}...")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Configure and run MCP servers with supergateway")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Add server command
    add_parser = subparsers.add_parser("add", help="Add a new MCP server configuration")
    add_parser.add_argument("--name", required=True, help="Name of the server")
    add_parser.add_argument("--cmd", required=True, help="Command to run")
    add_parser.add_argument("--args", nargs="*", default=[], help="Command arguments")
    add_parser.add_argument("--env", nargs="*", default=[], help="Environment variables in KEY=VALUE format")
    add_parser.add_argument("--port", type=int, help="Port for supergateway to listen on")
    add_parser.add_argument("--config", default="mcp_config.json", help="Configuration file")
    add_parser.add_argument("--type", choices=["stdio", "sse"], default="stdio", 
                           help="Server type: stdio (needs supergateway) or sse (direct SSE server)")
    
    # List servers command
    list_parser = subparsers.add_parser("list", help="List configured MCP servers")
    list_parser.add_argument("--config", default="mcp_config.json", help="Configuration file")
    
    # Run server command
    run_parser = subparsers.add_parser("run", help="Run MCP servers")
    run_parser.add_argument("names", nargs="+", help="Names of the servers to run")
    run_parser.add_argument("--no-supergateway", action="store_true", help="Run without supergateway")
    run_parser.add_argument("--no-background", action="store_true", help="Don't run servers in background")
    run_parser.add_argument("--sequential", action="store_true", help="Run servers sequentially with the last one in foreground (legacy behavior)")
    run_parser.add_argument("--config", default="mcp_config.json", help="Configuration file")
    
    # Run all servers command
    run_all_parser = subparsers.add_parser("run-all", help="Run all configured MCP servers")
    run_all_parser.add_argument("--no-supergateway", action="store_true", help="Run without supergateway")
    run_all_parser.add_argument("--no-background", action="store_true", help="Don't run servers in background")
    run_all_parser.add_argument("--sequential", action="store_true", help="Run servers sequentially with the last one in foreground (legacy behavior)")
    run_all_parser.add_argument("--config", default="mcp_config.json", help="Configuration file")
    
    # Remove server command
    remove_parser = subparsers.add_parser("remove", help="Remove an MCP server configuration")
    remove_parser.add_argument("name", help="Name of the server to remove")
    remove_parser.add_argument("--config", default="mcp_config.json", help="Configuration file")
    
    # Stop background servers command
    stop_parser = subparsers.add_parser("stop", help="Stop all background servers")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create config file if it doesn't exist
    if args.command == "add" and not os.path.exists(args.config):
        save_config(args.config, [])
    
    # Handle commands
    if args.command == "add":
        env_vars = {}
        for env_var in args.env:
            key, value = env_var.split("=", 1)
            env_vars[key] = value
        
        try:
            servers = load_config(args.config)
        except FileNotFoundError:
            servers = []
        
        # Check if server with the same name already exists
        if any(server.name == args.name for server in servers):
            print(f"Server with name '{args.name}' already exists")
            return
        
        new_server = MCPServer(
            name=args.name,
            command=args.cmd,
            args=args.args,
            env=env_vars,
            port=args.port,
            server_type=args.type,  # Use the new server type parameter
        )
        
        servers.append(new_server)
        save_config(args.config, servers)
        print(f"Added MCP server: {args.name}")
    
    elif args.command == "list":
        try:
            servers = load_config(args.config)
            if not servers:
                print("No MCP servers configured")
                return
            
            for i, server in enumerate(servers):
                print(f"{i+1}. {server.name}")
                print(f"   Command: {server.command} {' '.join(server.args)}")
                print(f"   Server type: {server.server_type}")  # Display server type in list output
                if server.env:
                    print(f"   Environment variables: {server.env}")
                if server.port:
                    print(f"   Port: {server.port}")
                print()
        except FileNotFoundError:
            print(f"Config file {args.config} does not exist")
    
    elif args.command == "run":
        servers = load_config(args.config)
        # Find all requested servers
        servers_to_run = []
        missing_servers = []
        
        for name in args.names:
            server = next((s for s in servers if s.name == name), None)
            if server:
                servers_to_run.append(server)
            else:
                missing_servers.append(name)
        
        if missing_servers:
            print(f"The following servers were not found: {', '.join(missing_servers)}")
            if not servers_to_run:
                return
        
        # Determine how to run servers
        if args.sequential:
            # Run servers sequentially with the last one in foreground
            run_in_background = len(servers_to_run) > 1 and not args.no_background
            
            for i, server in enumerate(servers_to_run):
                # Don't run the last server in background
                is_last_server = i == len(servers_to_run) - 1
                background = run_in_background and not is_last_server
                success = run_server(server, not args.no_supergateway, background)
                if not success:
                    break
        else:
            # Run all servers in parallel (all in background)
            print(f"Starting {len(servers_to_run)} servers in parallel...")
            for server in servers_to_run:
                success = run_server(server, not args.no_supergateway, True)  # Always run in background
                if not success:
                    print(f"Failed to start server: {server.name}")
            
            # Keep the main process running to handle signals
            try:
                print("All servers started. Press Ctrl+C to stop all servers.")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping all servers...")
    
    elif args.command == "run-all":
        servers = load_config(args.config)
        
        if not servers:
            print("No MCP servers configured")
            return
        
        # Determine how to run servers
        if args.sequential:
            # Run servers sequentially with the last one in foreground
            run_in_background = len(servers) > 1 and not args.no_background
            
            for i, server in enumerate(servers):
                # Don't run the last server in background
                is_last_server = i == len(servers) - 1
                background = run_in_background and not is_last_server
                success = run_server(server, not args.no_supergateway, background)
                if not success:
                    break
        else:
            # Run all servers in parallel (all in background)
            print(f"Starting {len(servers)} servers in parallel...")
            for server in servers:
                success = run_server(server, not args.no_supergateway, True)  # Always run in background
                if not success:
                    print(f"Failed to start server: {server.name}")
            
            # Keep the main process running to handle signals
            try:
                print("All servers started. Press Ctrl+C to stop all servers.")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping all servers...")
    
    elif args.command == "remove":
        servers = load_config(args.config)
        
        before_count = len(servers)
        servers = [s for s in servers if s.name != args.name]
        
        if len(servers) == before_count:
            print(f"Server with name '{args.name}' not found")
            return
        
        save_config(args.config, servers)
        print(f"Removed MCP server: {args.name}")
    
    elif args.command == "stop":
        cleanup_background_processes()
        print("All background servers have been stopped")


if __name__ == "__main__":
    main() 