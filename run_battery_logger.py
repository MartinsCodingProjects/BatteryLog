#!/usr/bin/env python3
"""
Entry point for the Battery Logger application
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from battery_monitor import BatteryLogger


def main():
    """Main entry point."""
    try:
        logger = BatteryLogger()
        logger.log_battery()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
