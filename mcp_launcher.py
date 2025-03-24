#!/usr/bin/env python3
import argparse
import subprocess
import sys
import json
import multiprocessing
import signal
import time
import os
from keep_alive import run_with_retries

def get_server_list(config_file='mcp_config.json'):
    """Get list of configured servers"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            return [server['name'] for server in config.get('servers', [])]
    except FileNotFoundError:
        print(f"Error: Configuration file {config_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Configuration file {config_file} is not valid JSON")
        sys.exit(1)

def launch_single_server(server_name, keep_alive=False):
    """Launch a single MCP server"""
    cmd = f"python mcp_servers.py run {server_name}"
    
    if keep_alive:
        run_with_retries(cmd)
    else:
        subprocess.run(cmd, shell=True)

def server_process(server_name, keep_alive):
    """Function to run in a separate process for each server"""
    try:
        print(f"Starting server: {server_name}")
        launch_single_server(server_name, keep_alive)
    except KeyboardInterrupt:
        print(f"\nStopping server: {server_name}")
    except Exception as e:
        print(f"Error in server {server_name}: {e}")

def launch_servers(keep_alive=False, config_file='mcp_config.json'):
    """Launch all MCP servers in parallel with independent monitoring"""
    servers = get_server_list(config_file)
    processes = []
    
    try:
        # Launch each server in its own process
        for server in servers:
            p = multiprocessing.Process(
                target=server_process,
                args=(server, keep_alive),
                name=f"server-{server}"
            )
            p.start()
            processes.append(p)
        
        # Wait for all processes to complete
        # This allows us to catch keyboard interrupts
        for p in processes:
            p.join()
            
    except KeyboardInterrupt:
        print("\nShutting down all servers...")
        # Terminate all processes on keyboard interrupt
        for p in processes:
            if p.is_alive():
                # First try SIGTERM for clean shutdown
                p.terminate()
                
        # Give a short grace period
        time.sleep(1.0)
        
        # Force kill any remaining processes
        for p in processes:
            if p.is_alive():
                try:
                    # Try to get the process ID and kill the process group
                    os.kill(p.pid, signal.SIGKILL)
                    print(f"Force killed process {p.pid}")
                except OSError:
                    pass
                
                # Make sure to join after killing
                p.join(timeout=0.1)
        
        # Additionally, run the stop command to clean up any lingering processes
        try:
            print("Running additional cleanup...")
            subprocess.run(["python", "mcp_servers.py", "stop"], 
                           timeout=2, 
                           check=False)
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
            
        print("All servers stopped")
        sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="MCP Server Launcher")
    parser.add_argument("--keep-alive", action="store_true", help="Enable keep-alive functionality")
    parser.add_argument("--config", default="mcp_config.json", help="Path to config file")
    args = parser.parse_args()
    
    # Set multiprocessing start method
    multiprocessing.set_start_method('spawn')
    launch_servers(args.keep_alive, args.config)

if __name__ == "__main__":
    main() 