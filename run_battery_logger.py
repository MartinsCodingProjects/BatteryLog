#!/usr/bin/env python3
"""
Entry point for the Battery Logger application
"""

import sys
import os
import multiprocessing
import signal
import time
from battery_monitor import BatteryLogger
from settings_server import run_settings_server

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def start_logger():
    logger = BatteryLogger()
    logger.log_battery()

def start_server():
    os.chdir(os.path.dirname(__file__))  # Serve files from the current directory
    run_settings_server()

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down gracefully...")
    sys.exit(0)

def main():
    """Main entry point."""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create processes for the logger and the server
        logger_process = multiprocessing.Process(target=start_logger)
        server_process = multiprocessing.Process(target=start_server)

        # Start both processes
        logger_process.start()
        server_process.start()
        
        print("Battery logger and settings server started. Press Ctrl+C to stop.")

        try:
            # Wait for processes with timeout to allow graceful shutdown
            while logger_process.is_alive() or server_process.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nReceived interrupt signal. Stopping processes...")
            
            # Terminate processes gracefully
            if logger_process.is_alive():
                logger_process.terminate()
            if server_process.is_alive():
                server_process.terminate()
            
            # Wait a bit for graceful termination
            time.sleep(1)
            
            # Force kill if still alive
            if logger_process.is_alive():
                logger_process.kill()
            if server_process.is_alive():
                server_process.kill()
            
            # Final cleanup
            logger_process.join(timeout=2)
            server_process.join(timeout=2)
            
            print("All processes stopped.")
            
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
