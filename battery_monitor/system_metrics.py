#!/usr/bin/env python3
"""
System metrics collection for battery logging
"""

import psutil
import subprocess
from typing import Tuple
from .utils import SystemUtilities, PlatformDetector


class SystemMetrics:
    """Collect various system metrics beyond battery information."""
    
    def __init__(self, platform_detector: PlatformDetector):
        self.platform = platform_detector
    
    def get_brightness(self) -> str:
        """Get current display brightness (0-100) - cross-platform."""
        try:
            if self.platform.is_windows():
                success, output = SystemUtilities.safe_run_command([
                    'powershell', '-Command',
                    '(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness'
                ], timeout=5)
                if success and output.isdigit():
                    return output
                    
            elif self.platform.is_linux():
                brightness_paths = [
                    '/sys/class/backlight/intel_backlight/brightness',
                    '/sys/class/backlight/acpi_video0/brightness'
                ]
                for path in brightness_paths:
                    brightness_value = SystemUtilities.safe_file_read(path)
                    if brightness_value:
                        brightness = SystemUtilities.safe_int_conversion(brightness_value)
                        if brightness is not None:
                            # Get max brightness
                            max_path = path.replace('brightness', 'max_brightness')
                            max_brightness_value = SystemUtilities.safe_file_read(max_path)
                            if max_brightness_value:
                                max_brightness = SystemUtilities.safe_int_conversion(max_brightness_value)
                                if max_brightness and max_brightness > 0:
                                    return str(round((brightness / max_brightness) * 100))
                        
            elif self.platform.is_macos():
                success, output = SystemUtilities.safe_run_command([
                    'osascript', '-e', 
                    'tell application "System Events" to get brightness of item 1 of (displays whose it is main display)'
                ], timeout=5)
                if success:
                    brightness_value = SystemUtilities.safe_float_conversion(output)
                    if brightness_value is not None:
                        brightness = round(brightness_value * 100)
                        return str(brightness)
                        
        except Exception as e:
            print(f"Error getting brightness: {e}")
        
        return "N/A"
    
    def get_cpu_temperature(self) -> str:
        """Get CPU temperature if available - cross-platform."""
        try:
            # Try psutil sensors first
            temps = psutil.sensors_temperatures()
            if temps:
                # Try to find CPU temperature
                for name, entries in temps.items():
                    if 'cpu' in name.lower() or 'core' in name.lower():
                        if entries:
                            return str(round(entries[0].current, 1))
                # If no CPU temp found, return first available
                for name, entries in temps.items():
                    if entries:
                        return str(round(entries[0].current, 1))
                        
        except Exception:
            # Fallback methods for different platforms
            if self.platform.is_linux():
                temp_value = SystemUtilities.safe_file_read('/sys/class/thermal/thermal_zone0/temp')
                if temp_value:
                    temp_int = SystemUtilities.safe_int_conversion(temp_value)
                    if temp_int:
                        temp = temp_int / 1000
                        return str(round(temp, 1))
                    
            elif self.platform.is_macos():
                success, output = SystemUtilities.safe_run_command([
                    'sysctl', '-n', 'machdep.xcpm.cpu_thermal_state'
                ])
                if success:
                    return f"State: {output}"
        
        return "N/A"
    
    def get_network_stats(self) -> int:
        """Get total network bytes sent + received."""
        try:
            net_io = psutil.net_io_counters()
            return net_io.bytes_sent + net_io.bytes_recv
        except:
            return 0
    
    def get_charging_info(self, battery) -> Tuple[str, str]:
        """Get charging time estimate and charging status."""
        if not battery or not battery.power_plugged:
            return "N/A", "N/A"
        
        try:
            current_percent = battery.percent
            if current_percent >= 100:
                return "0", "Full"
            
            # Rough estimate: assume ~2 hours to charge from 0 to 100%
            estimated_minutes = (100 - current_percent) * 1.2
            
            if estimated_minutes <= 5:
                return str(estimated_minutes), "Nearly Full"
            elif estimated_minutes <= 30:
                return str(estimated_minutes), "Fast Charging"
            else:
                return str(estimated_minutes), "Charging"
        except:
            return "N/A", "N/A"
    
    def get_top_processes(self, limit: int = 10) -> str:
        """Get top processes by CPU usage."""
        try:
            processes = [(p.info['name'], p.info['cpu_percent']) 
                        for p in psutil.process_iter(['name', 'cpu_percent'])]
            top_processes = sorted(processes, key=lambda x: x[1] if x[1] is not None else 0, reverse=True)[:limit]
            return "; ".join([f"{name}:{cpu}%" for name, cpu in top_processes])
        except:
            return "N/A"
    
    def get_system_stats(self) -> dict:
        """Get comprehensive system statistics."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'ram_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent if self.platform.is_linux() or self.platform.is_macos() 
                             else psutil.disk_usage('C:\\').percent
            }
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return {
                'cpu_percent': "N/A",
                'ram_percent': "N/A", 
                'disk_percent': "N/A"
            }
