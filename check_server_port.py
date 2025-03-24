#!/usr/bin/env python3

import argparse
import json
import os
import socket
import subprocess
import sys
from typing import Dict, List, Tuple, Optional

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

def get_server_port(config_file: str, server_name: str) -> Optional[int]:
    """Get the port for a specific server by name"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            
            for server in config.get("servers", []):
                if server.get("name") == server_name:
                    port = server.get("port")
                    if port is not None and isinstance(port, int):
                        return port
            
            print(f"Error: Server '{server_name}' not found in config or has no port defined")
            return None
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)

def check_server_port(port: int, kill_conflicts: bool = False) -> bool:
    """Check if a server port is in use and optionally kill the conflicting processes"""
    if port is None:
        return False
        
    port_name = f"Server port {port}"
    conflicts = check_port_in_use(port)
    
    if not conflicts:
        print(f"Port {port} is available.")
        return True
        
    has_conflicts = False
    killed_pids = []
    
    if conflicts:
        if kill_conflicts:
            print(f"Killing processes using {port_name} ({port}):")
            for pid, name in conflicts:
                try:
                    # Send SIGTERM
                    print(f"  - Sending SIGTERM to PID {pid} ({name})")
                    os.kill(pid, 15)  # SIGTERM
                    killed_pids.append(pid)
                except OSError as e:
                    print(f"    Error killing process {pid}: {e}")
                    has_conflicts = True
        else:
            print(f"ERROR: {port_name} ({port}) is already in use by:")
            for pid, name in conflicts:
                print(f"  - PID {pid}: {name}")
            has_conflicts = True
    
    # If any processes were killed with SIGTERM, give them a moment to shut down
    if killed_pids:
        import time
        time.sleep(1)
    
    # Do a final check after killing processes
    if kill_conflicts:
        has_conflicts = False
        if check_port_in_use(port):
            print(f"WARNING: {port_name} ({port}) is still in use after kill attempt.")
            has_conflicts = True
            
        if has_conflicts:
            print("Some processes could not be killed. You may need to kill them manually.")
        else:
            print("All conflicting processes for this server have been terminated.")
    
    return not has_conflicts

def main():
    parser = argparse.ArgumentParser(description="Check for port conflicts for a specific MCP server")
    parser.add_argument("--config", type=str, default="mcp_config.json",
                        help="Path to configuration file (default: mcp_config.json)")
    parser.add_argument("--server", type=str, required=True,
                        help="Name of the server to check")
    parser.add_argument("--kill-conflicts", action="store_true",
                        help="Kill processes using conflicting ports")
    
    args = parser.parse_args()
    
    port = get_server_port(args.config, args.server)
    
    if port is None:
        return 1
        
    print(f"Checking port {port} for server '{args.server}'")
    
    result = check_server_port(port, args.kill_conflicts)
    
    if result:
        print(f"Port {port} for server '{args.server}' is available.")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 