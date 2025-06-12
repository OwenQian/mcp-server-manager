#!/usr/bin/env python3

import argparse
import os
import subprocess
import signal
import sys
import time
import socket
import psutil
from typing import Dict, List, Tuple

# Keep track of background process for cleanup
inspector_process = None


def signal_handler(sig, frame):
    """Handle keyboard interrupt and other signals"""
    print("\nShutting down MCP Inspector server...")
    if inspector_process and inspector_process.poll() is None:
        inspector_process.terminate()
        time.sleep(1)
        if inspector_process.poll() is None:
            inspector_process.kill()
    sys.exit(0)


def check_port_in_use(port: int) -> List[Tuple[int, str]]:
    """Check if a port is already in use and return a list of (pid, name) tuples of conflicting processes"""
    conflicts = []
    
    # Create a socket to test if the port is in use
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        # Port is free
    except socket.error:
        # Port is in use, find which process is using it
        try:
            # On macOS, use lsof to find processes using the port
            output = subprocess.check_output(
                ["lsof", "-i", f":{port}"], 
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Parse lsof output (skip header line)
            for line in output.strip().split('\n')[1:]:
                parts = line.split()
                if len(parts) >= 2:
                    process_name = parts[0]
                    pid = parts[1]
                    try:
                        pid = int(pid)
                        conflicts.append((pid, process_name))
                    except ValueError:
                        # Skip if pid isn't numeric
                        pass
        except subprocess.CalledProcessError:
            # lsof didn't find anything or command failed
            pass
    finally:
        s.close()
    
    return conflicts


def check_ports(client_port: int, server_port: int, inspector_port: int) -> bool:
    """Check if any of the required ports are in use"""
    ports_to_check = [
        (client_port, "CLIENT_PORT"),
        (server_port, "SERVER_PORT"),
        (inspector_port, "INSPECTOR_PORT"),
    ]
    
    has_conflicts = False
    
    for port, port_name in ports_to_check:
        conflicts = check_port_in_use(port)
        if conflicts:
            print(f"ERROR: {port_name} ({port}) is already in use by:")
            for pid, name in conflicts:
                print(f"  - PID {pid}: {name}")
            has_conflicts = True
    
    return not has_conflicts


def kill_conflicting_processes(client_port: int, server_port: int, inspector_port: int) -> bool:
    """Kill processes using the specified ports"""
    ports_to_check = [
        (client_port, "CLIENT_PORT"),
        (server_port, "SERVER_PORT"),
        (inspector_port, "INSPECTOR_PORT"),
    ]
    
    all_killed = True
    killed_pids = []
    
    for port, port_name in ports_to_check:
        conflicts = check_port_in_use(port)
        if conflicts:
            print(f"Killing processes using {port_name} ({port}):")
            for pid, name in conflicts:
                try:
                    print(f"  - Sending SIGTERM to PID {pid} ({name})")
                    os.kill(pid, signal.SIGTERM)
                    killed_pids.append(pid)
                except OSError as e:
                    print(f"    Error killing process {pid}: {e}")
                    all_killed = False
    
    # If any processes were killed with SIGTERM, give them a moment to shut down
    if killed_pids:
        time.sleep(1)
    
    # Do a final check
    has_conflicts = False
    for port, port_name in ports_to_check:
        if check_port_in_use(port):
            has_conflicts = True
            all_killed = False
    
    if has_conflicts:
        print("Some processes could not be killed. You may need to kill them manually.")
    else:
        print("All conflicting processes have been terminated.")
    
    return all_killed


def run_inspector(
    client_port: int = 5173,
    server_port: int = 8089,
    inspector_port: int = 8000,
    foreground: bool = False,
    env_vars: Dict[str, str] = None,
    force: bool = False,
    server_name: str = None
):
    """Run the MCP inspector server"""
    
    # Check if ports are free
    if not force and not check_ports(client_port, server_port, inspector_port):
        print("Port conflicts detected. Use --force to start anyway.")
        return False
    
    # Set up environment variables
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    # Always set these environment variables - MCP Inspector uses these specific env vars
    env["CLIENT_PORT"] = str(client_port)
    env["SERVER_PORT"] = str(server_port)
    
    # Set up configuration for inspector to use
    # The inspector needs both config file AND server name
    config_path = "mcp_config.json"
    if os.path.exists(config_path) and server_name:
        # Construct the command with config file and server name
        cmd = ["npx", "-y", "@modelcontextprotocol/inspector", "--config", config_path, "--server", server_name]
    else:
        # Try to run without config - this runs in standalone mode where you can manually connect
        cmd = ["npx", "-y", "@modelcontextprotocol/inspector"]
    
    print(f"Starting MCP Inspector server...")
    print(f"Command: {' '.join(cmd)}")
    print(f"Environment: CLIENT_PORT={client_port}, SERVER_PORT={server_port}")
    
    try:
        if foreground:
            # Run in foreground mode
            subprocess.run(cmd, env=env, check=True)
        else:
            # Run in background mode
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file_path = f"{log_dir}/mcp-inspector.log"
            log_file = open(log_file_path, "w")
            
            global inspector_process
            inspector_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
            )
            
            # Write PID to file for easier management
            with open(".mcp-inspector.pid", "w") as pid_file:
                pid_file.write(str(inspector_process.pid))
            
            print(f"MCP Inspector server launched with PID {inspector_process.pid}")
            print(f"Client available at: http://localhost:{client_port}")
            print(f"Inspector SSE endpoint: http://localhost:{inspector_port}/sse")
            print(f"Logs are written to {log_file_path}")
            
            # Check if process exited immediately (indicating a failure)
            time.sleep(0.5)
            if inspector_process.poll() is not None:
                print(f"ERROR: MCP Inspector server exited immediately with code {inspector_process.returncode}")
                print(f"Check logs at {log_file_path}")
                return False
            
            # Keep the script running to handle signals in background mode
            while inspector_process.poll() is None:
                time.sleep(1)
            
            print(f"MCP Inspector server stopped with exit code {inspector_process.returncode}")
            
    except subprocess.CalledProcessError as e:
        print(f"Error running MCP Inspector server: {e}")
        return False
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Run MCP Inspector server")
    
    parser.add_argument("--client-port", type=int, default=5173,
                        help="Port for inspector client (default: 5173)")
    parser.add_argument("--server-port", type=int, default=8089,
                        help="Port for inspector server (default: 8089)")
    parser.add_argument("--inspector-port", type=int, default=8000,
                        help="Port for SSE connections (default: 8000)")
    parser.add_argument("--foreground", action="store_true",
                        help="Run in foreground instead of background")
    parser.add_argument("--env", nargs="+", default=[],
                        help="Additional environment variables in KEY=VALUE format")
    parser.add_argument("--force", action="store_true",
                        help="Force start even if ports are in use")
    parser.add_argument("--check-ports-only", action="store_true",
                        help="Only check if ports are available and exit")
    parser.add_argument("--kill-conflicts", action="store_true",
                        help="Kill processes using conflicting ports")
    parser.add_argument("--server", type=str,
                        help="Server name from config file to connect to")
    
    args = parser.parse_args()
    
    # Process environment variables
    env_vars = {}
    for env_var in args.env:
        try:
            key, value = env_var.split("=", 1)
            env_vars[key] = value
        except ValueError:
            print(f"Warning: Ignoring invalid environment variable format: {env_var}")
    
    # If we're killing conflicts
    if args.kill_conflicts:
        success = kill_conflicting_processes(
            args.client_port, 
            args.server_port, 
            args.inspector_port
        )
        sys.exit(0 if success else 1)
    
    # If we're only checking ports, do that and exit
    if args.check_ports_only:
        ports_available = check_ports(args.client_port, args.server_port, args.inspector_port)
        if ports_available:
            print("All ports are available.")
            sys.exit(0)
        else:
            print("Port conflicts detected.")
            sys.exit(1)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the inspector
    run_inspector(
        client_port=args.client_port,
        server_port=args.server_port,
        inspector_port=args.inspector_port,
        foreground=args.foreground,
        env_vars=env_vars,
        force=args.force,
        server_name=args.server
    )


if __name__ == "__main__":
    main() 
