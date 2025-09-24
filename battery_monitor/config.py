#!/usr/bin/env python3
"""
Configuration settings for the Battery Logger
"""

# Logging configuration
LOG_INTERVAL = 60  # seconds between log entries
LOG_FILE = "battery_log.csv"

# Battery monitoring thresholds
VOLTAGE_THRESHOLDS = {
    'normal': 11.0,
    'low': 10.0,
    'critical': 9.0
}

POWER_DRAW_THRESHOLDS = {
    'light': 5.0,    # watts
    'moderate': 15.0  # watts
}

CYCLE_COUNT_RANGE = {
    'min': 0,
    'max': 15000
}

# Temperature settings
TEMP_TIMEOUT = 10  # seconds for temperature queries

# PowerShell execution settings
POWERSHELL_TIMEOUT = 15  # seconds
POWERSHELL_EXECUTION_POLICY = 'Bypass'

# CSV Headers
CSV_HEADERS = [
    "timestamp", "percentage", "time_left_hms", "power_plugged", "script_runtime_hms",
    "cpu_percent", "ram_percent", "disk_percent", "brightness_percent", 
    "network_activity_mb", "battery_temperature_c", "system_temperature_c", 
    "charge_time_min", "charge_status", "power_draw_w", "battery_drain_rate_pct_per_hour", 
    "battery_health_pct", "voltage_v", "load_severity", "voltage_status", 
    "cycle_count", "top_10_processes"
]
