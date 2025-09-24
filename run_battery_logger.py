#!/usr/bin/env python3
"""
Entry point for the Battery Logger application
"""

import sys
import os
import multiprocessing
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

def main():
    """Main entry point."""
    try:
        # Create processes for the logger and the server
        logger_process = multiprocessing.Process(target=start_logger)
        server_process = multiprocessing.Process(target=start_server)

        # Start both processes
        logger_process.start()
        server_process.start()

        # Wait for both processes to complete
        logger_process.join()
        server_process.join()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
