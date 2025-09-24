#!/usr/bin/env python3
"""
Configuration settings for the Battery Logger
"""

import json
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
USER_SETTINGS_FILE = PROJECT_ROOT / "user_settings.json"

def load_user_settings():
    """Load user settings from JSON file, create with defaults if not exists"""
    default_settings = {
        "logging": {
            "log_interval": 60
        },
        "visualization": {
            "time_range": "1h",
            "custom_date": None,
            "auto_refresh": True,
            "refresh_interval": 60000
        }
    }
    
    try:
        if USER_SETTINGS_FILE.exists():
            with open(USER_SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key in default_settings:
                    if key not in settings:
                        settings[key] = default_settings[key]
                    elif isinstance(default_settings[key], dict):
                        for subkey in default_settings[key]:
                            if subkey not in settings[key]:
                                settings[key][subkey] = default_settings[key][subkey]
                return settings
        else:
            # Create default settings file
            save_user_settings(default_settings)
            return default_settings
    except Exception as e:
        print(f"Warning: Failed to load user settings: {e}")
        return default_settings

def save_user_settings(settings):
    """Save user settings to JSON file"""
    try:
        with open(USER_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Warning: Failed to save user settings: {e}")

def get_setting(category, key, default=None):
    """Get a specific setting value"""
    settings = load_user_settings()
    return settings.get(category, {}).get(key, default)

def update_setting(category, key, value):
    """Update a specific setting value"""
    settings = load_user_settings()
    if category not in settings:
        settings[category] = {}
    settings[category][key] = value
    save_user_settings(settings)

# Load user settings
USER_SETTINGS = load_user_settings()

# Logging configuration
LOG_INTERVAL = USER_SETTINGS['logging']['log_interval']  # seconds between log entries
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
