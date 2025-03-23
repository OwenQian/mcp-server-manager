#!/usr/bin/env python3
import subprocess
import sys
import time
import signal
import os

def run_with_retries(command, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            process = subprocess.Popen(command, shell=True)
            # Reset retries if the process runs for more than 30 seconds
            # This indicates a successful start
            start_time = time.time()
            
            def signal_handler(signum, frame):
                if process:
                    process.terminate()
                sys.exit(0)
            
            # Handle termination signals
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
            
            process.wait()
            
            # If process ran for more than 30 seconds before exiting
            # reset the retry counter as it was a successful run
            if time.time() - start_time > 30:
                retries = 0
                print(f"\nProcess ran successfully for over 30 seconds. Resetting retry counter.")
            else:
                retries += 1
                print(f"\nProcess exited quickly. Retry {retries}/{max_retries}")
            
            # If process exited with non-zero status
            if process.returncode != 0:
                if retries < max_retries:
                    print(f"Process failed with exit code {process.returncode}. Restarting in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"Process failed {max_retries} times. Giving up.")
                    sys.exit(1)
            # If process exited with zero status but quickly
            elif time.time() - start_time <= 30:
                if retries < max_retries:
                    print("Process exited successfully but too quickly. Restarting in 5 seconds...")
                    time.sleep(5)
                else:
                    print(f"Process exited quickly {max_retries} times. Giving up.")
                    sys.exit(1)
            
        except KeyboardInterrupt:
            if process:
                process.terminate()
            sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python keep_alive.py <command>")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    run_with_retries(command) 