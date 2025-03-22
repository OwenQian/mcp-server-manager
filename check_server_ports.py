#!/usr/bin/env python3

import argparse
import json
import os
import socket
import subprocess
import sys
from typing import Dict, List, Tuple, Set

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

def load_ports_from_config(config_file: str) -> Set[int]:
    """Load server ports from the config file"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            ports = set()
            for server in config.get("servers", []):
                port = server.get("port")
                if port is not None and isinstance(port, int):
                    ports.add(port)
            return ports
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)

def check_ports(ports: Set[int], kill_conflicts: bool = False) -> bool:
    """Check if any of the required ports are in use"""
    ports_to_check = [(port, f"Server port {port}") for port in ports]
    
    has_conflicts = False
    killed_pids = []
    
    for port, port_name in ports_to_check:
        conflicts = check_port_in_use(port)
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
        for port, port_name in ports_to_check:
            if check_port_in_use(port):
                print(f"WARNING: {port_name} ({port}) is still in use after kill attempt.")
                has_conflicts = True
                
        if has_conflicts:
            print("Some processes could not be killed. You may need to kill them manually.")
        else:
            print("All conflicting processes have been terminated.")
    
    return not has_conflicts

def main():
    parser = argparse.ArgumentParser(description="Check for port conflicts in MCP server ports")
    parser.add_argument("--config", type=str, default="mcp_config.json",
                        help="Path to configuration file (default: mcp_config.json)")
    parser.add_argument("--kill-conflicts", action="store_true",
                        help="Kill processes using conflicting ports")
    
    args = parser.parse_args()
    
    ports = load_ports_from_config(args.config)
    
    if not ports:
        print("No ports found in the configuration file.")
        return 0
        
    print(f"Found {len(ports)} server ports to check in {args.config}: {', '.join(map(str, sorted(ports)))}")
    
    result = check_ports(ports, args.kill_conflicts)
    
    if result:
        print("All server ports are available.")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main()) 