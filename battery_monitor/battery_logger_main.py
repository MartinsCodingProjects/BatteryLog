#!/usr/bin/env python3
"""
Main battery logging class that coordinates all components
"""

import time
import csv
import psutil
from datetime import datetime
from typing import Optional
from .config import LOG_FILE, LOG_INTERVAL, CSV_HEADERS
from .utils import PlatformDetector, SystemUtilities
from .battery_detector import BatteryDetectorFactory
from .system_metrics import SystemMetrics


class BatteryLogger:
    """Main battery logging class that coordinates all components."""
    
    def __init__(self, log_file: str = LOG_FILE, log_interval: int = LOG_INTERVAL):
        self.log_file = log_file
        self.log_interval = log_interval
        self.platform = PlatformDetector()
        self.system_metrics = SystemMetrics(self.platform)
        self.battery_detector = BatteryDetectorFactory.create_detector(self.platform)
        self._last_net_bytes = self.system_metrics.get_network_stats()
    
    def _write_csv_header(self):
        """Write CSV header if file is new."""
        try:
            with open(self.log_file, "x", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
        except FileExistsError:
            pass  # File already exists
    
    def _print_initial_info(self):
        """Print initial platform and battery information."""
        print(f"Battery Logger starting on {self.platform.platform.title()}")
        
        if self.platform.is_windows() and not self.platform.wmi_available:
            print("Warning: WMI not available. Install with: pip install WMI")
    
    def log_battery(self):
        """Main logging loop."""
        start_time = time.time()
        
        self._print_initial_info()
        self._write_csv_header()
        
        with open(self.log_file, "a", newline="") as f:
            writer = csv.writer(f)
            
            while True:
                try:
                    self._log_single_entry(writer, f, start_time)
                    time.sleep(self.log_interval)
                    
                except KeyboardInterrupt:
                    print("\nBattery logging stopped by user.")
                    break
                except Exception as e:
                    print(f"Error in logging loop: {e}")
                    time.sleep(self.log_interval)
    
    def _log_single_entry(self, writer, f, start_time: float):
        """Log a single entry to the CSV file."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        runtime = time.time() - start_time
        runtime_str = SystemUtilities.format_secs(int(runtime))
        
        # Get basic battery info
        battery_info = self._get_battery_info()
        
        # Get system metrics
        system_stats = self.system_metrics.get_system_stats()
        brightness = self.system_metrics.get_brightness()
        
        # Get network activity
        net_activity_mb = self._get_network_activity()
        
        # Get temperature data
        temperature_data = self._get_temperature_data()
        
        # Get battery-specific data
        battery_data = self._get_battery_specific_data()
        
        # Get charging info
        charge_time_min, charge_status = self.system_metrics.get_charging_info(battery_info['battery'])
        
        # Get top processes
        top_proc_str = self.system_metrics.get_top_processes()
        
        # Calculate battery drain rate (placeholder - would need historical data)
        battery_drain_rate = "N/A"  # This would require tracking over time
        
        # Write to CSV
        csv_row = [
            now, battery_info['percent'], battery_info['time_left'], battery_info['plugged'], runtime_str,
            system_stats['cpu_percent'], system_stats['ram_percent'], system_stats['disk_percent'], brightness,
            net_activity_mb, temperature_data['battery_temp'], temperature_data['system_temp'], 
            charge_time_min, charge_status, battery_data['power_draw'], battery_drain_rate, 
            battery_data['health'], battery_data['voltage'], battery_data['load_severity'], 
            battery_data['voltage_status'], battery_data['cycle_count'], top_proc_str
        ]
        
        writer.writerow(csv_row)
        f.flush()
        
        # Print status
        self._print_status(now, battery_info, battery_data, temperature_data, system_stats)
    
    def _get_battery_info(self) -> dict:
        """Get basic battery information from psutil."""
        battery = psutil.sensors_battery()
        return {
            'battery': battery,
            'percent': battery.percent if battery else "N/A",
            'time_left': SystemUtilities.format_secs(battery.secsleft if battery else None),
            'plugged': battery.power_plugged if battery else "N/A"
        }
    
    def _get_network_activity(self) -> float:
        """Get network activity since last measurement."""
        current_net_bytes = self.system_metrics.get_network_stats()
        net_activity = current_net_bytes - self._last_net_bytes
        self._last_net_bytes = current_net_bytes
        return round(net_activity / (1024*1024), 2)
    
    def _get_temperature_data(self) -> dict:
        """Get temperature data from various sources."""
        system_temperature = self.system_metrics.get_cpu_temperature()
        battery_temperature = "N/A"
        
        if self.battery_detector and hasattr(self.battery_detector, 'get_battery_temperature'):
            battery_temperature = self.battery_detector.get_battery_temperature()
        
        return {
            'battery_temp': battery_temperature,
            'system_temp': system_temperature,
            'display_temp': battery_temperature if battery_temperature != "N/A" else system_temperature
        }
    
    def _get_battery_specific_data(self) -> dict:
        """Get battery-specific data like voltage, power, health, etc."""
        default_data = {
            'health': "N/A",
            'voltage': "N/A",
            'power_draw': "N/A",
            'load_severity': "Unknown",
            'voltage_status': "Unknown",
            'cycle_count': "N/A"
        }
        
        if not self.battery_detector:
            return default_data
        
        try:
            # Get detailed battery info (cached from initial call for performance)
            battery_details = self.battery_detector.get_battery_details()
            
            # Get voltage and power info
            voltage_power = {}
            if hasattr(self.battery_detector, 'get_voltage_and_power'):
                voltage_power = self.battery_detector.get_voltage_and_power()
            
            return {
                'health': battery_details.get('health', "N/A"),
                'voltage': voltage_power.get('voltage', "N/A"),
                'power_draw': voltage_power.get('power_draw', "N/A"),
                'load_severity': voltage_power.get('load_severity', "Unknown"),
                'voltage_status': voltage_power.get('voltage_status', "Unknown"),
                'cycle_count': battery_details.get('cycle_count', "N/A")
            }
        except Exception as e:
            print(f"Error getting battery-specific data: {e}")
            return default_data
    
    def _print_status(self, timestamp: str, battery_info: dict, battery_data: dict, 
                     temperature_data: dict, system_stats: dict):
        """Print current status to console."""
        status = "Plugged" if battery_info['plugged'] else "On Battery"
        print(f"{timestamp} | {battery_info['percent']}% | {status} | {temperature_data['display_temp']}°C")
    
    def get_single_battery_snapshot(self) -> dict:
        """Get a single snapshot of battery data without logging."""
        battery_info = self._get_battery_info()
        system_stats = self.system_metrics.get_system_stats()
        temperature_data = self._get_temperature_data()
        battery_data = self._get_battery_specific_data()
        
        return {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'battery_info': battery_info,
            'system_stats': system_stats,
            'temperature_data': temperature_data,
            'battery_data': battery_data
        }
