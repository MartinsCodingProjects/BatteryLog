#!/usr/bin/env python3
"""
Linux-specific battery detection using /sys filesystem
"""

import os
import re
from typing import Dict, Any, Optional
from .utils import SystemUtilities


class LinuxBatteryDetector:
    """Linux-specific battery detection using /sys filesystem."""
    
    def get_battery_details(self) -> Dict[str, Any]:
        """Get battery details from Linux /sys filesystem."""
        details = {
            'health': "N/A",
            'design_capacity': "N/A",
            'full_charge_capacity': "N/A",
            'chemistry': "N/A",
            'name': "N/A",
            'manufacturer': "N/A",
            'cycle_count': "N/A",
            'status': "N/A",
            'design_voltage': "N/A"
        }
        
        print("Getting battery details from Linux /sys filesystem...")
        battery_path = self._find_battery_path()
        
        if battery_path:
            self._extract_linux_battery_info(battery_path, details)
            self._calculate_health(details)
        
        return details
    
    def _find_battery_path(self) -> Optional[str]:
        """Find the battery path in /sys/class/power_supply/."""
        battery_path = '/sys/class/power_supply/BAT0'
        
        if os.path.exists(battery_path):
            return battery_path
        
        # Try alternative paths
        for i in range(5):
            alt_path = f'/sys/class/power_supply/BAT{i}'
            if os.path.exists(alt_path):
                print(f"Using battery path: {alt_path}")
                return alt_path
        
        return None
    
    def _extract_linux_battery_info(self, battery_path: str, details: Dict[str, Any]):
        """Extract battery information from Linux sysfs."""
        info_files = {
            'energy_full_design': 'design_capacity',
            'energy_full': 'full_charge_capacity',
            'manufacturer': 'manufacturer',
            'model_name': 'name',
            'technology': 'chemistry',
            'cycle_count': 'cycle_count',
            'status': 'status'
        }
        
        for file_name, detail_key in info_files.items():
            file_path = os.path.join(battery_path, file_name)
            value = SystemUtilities.safe_file_read(file_path)
            
            if value and value != 'Unknown':
                # Convert numeric values appropriately
                if detail_key in ['design_capacity', 'full_charge_capacity', 'cycle_count']:
                    numeric_value = SystemUtilities.safe_int_conversion(value)
                    if numeric_value is not None:
                        details[detail_key] = numeric_value
                        print(f"{detail_key}: {numeric_value}")
                else:
                    details[detail_key] = value
                    print(f"{detail_key}: {value}")
    
    def _calculate_health(self, details: Dict[str, Any]):
        """Calculate battery health from design and full capacity."""
        if (details['design_capacity'] != "N/A" and 
            details['full_charge_capacity'] != "N/A" and 
            isinstance(details['design_capacity'], (int, float)) and 
            isinstance(details['full_charge_capacity'], (int, float)) and
            details['design_capacity'] > 0):
            
            health_pct = (details['full_charge_capacity'] / details['design_capacity']) * 100
            details['health'] = round(health_pct, 1)
            print(f"Calculated health: {details['health']}%")
    
    def get_voltage_and_power(self) -> Dict[str, Any]:
        """Get voltage and power information from Linux."""
        result = {
            'voltage': "N/A",
            'power_draw': "N/A",
            'load_severity': "Unknown",
            'voltage_status': "Unknown"
        }
        
        battery_path = self._find_battery_path()
        if not battery_path:
            return result
        
        try:
            print("Getting voltage and power from Linux /sys...")
            
            # Get voltage
            self._get_linux_voltage(battery_path, result)
            
            # Get power draw
            self._get_linux_power(battery_path, result)
            
            # Classify metrics
            self._classify_power_metrics(result)
            
        except Exception as e:
            print(f"Error getting Linux voltage/power: {e}")
        
        return result
    
    def _get_linux_voltage(self, battery_path: str, result: Dict[str, Any]):
        """Get voltage from Linux battery path."""
        voltage_files = ['voltage_now', 'voltage_avg']
        for voltage_file in voltage_files:
            file_path = os.path.join(battery_path, voltage_file)
            value = SystemUtilities.safe_file_read(file_path)
            
            if value:
                voltage_uv = SystemUtilities.safe_int_conversion(value)
                if voltage_uv and voltage_uv > 0:
                    voltage = round(voltage_uv / 1000000, 2)  # Convert microvolts to volts
                    result['voltage'] = voltage
                    print(f"Linux voltage from {voltage_file}: {voltage}V")
                    break
    
    def _get_linux_power(self, battery_path: str, result: Dict[str, Any]):
        """Get power draw from Linux battery path."""
        # Try direct power reading first
        power_file = os.path.join(battery_path, 'power_now')
        value = SystemUtilities.safe_file_read(power_file)
        
        if value:
            power_uw = SystemUtilities.safe_int_conversion(value)
            if power_uw:
                power = round(abs(power_uw) / 1000000, 2)  # Convert microwatts to watts
                result['power_draw'] = power
                print(f"Linux power draw: {power}W")
                return
        
        # Calculate from current and voltage if direct power not available
        self._calculate_power_from_current(battery_path, result)
    
    def _calculate_power_from_current(self, battery_path: str, result: Dict[str, Any]):
        """Calculate power from current and voltage."""
        current_file = os.path.join(battery_path, 'current_now')
        current_value = SystemUtilities.safe_file_read(current_file)
        
        if current_value and result['voltage'] != "N/A":
            current_ua = SystemUtilities.safe_int_conversion(current_value)
            if current_ua:
                current_a = abs(current_ua) / 1000000  # Convert to amps
                power = round(result['voltage'] * current_a, 2)
                result['power_draw'] = power
                print(f"Linux calculated power: {power}W (V*I)")
    
    def _classify_power_metrics(self, result: Dict[str, Any]):
        """Classify power draw and voltage status."""
        from .config import POWER_DRAW_THRESHOLDS, VOLTAGE_THRESHOLDS
        
        # Calculate load severity
        if result['power_draw'] != "N/A" and isinstance(result['power_draw'], (int, float)):
            if result['power_draw'] < POWER_DRAW_THRESHOLDS['light']:
                result['load_severity'] = "Light"
            elif result['power_draw'] < POWER_DRAW_THRESHOLDS['moderate']:
                result['load_severity'] = "Moderate"
            else:
                result['load_severity'] = "Heavy"
            print(f"Load severity: {result['load_severity']}")
        
        # Determine voltage status
        if result['voltage'] != "N/A" and isinstance(result['voltage'], (int, float)):
            if result['voltage'] > VOLTAGE_THRESHOLDS['normal']:
                result['voltage_status'] = "Normal"
            elif result['voltage'] > VOLTAGE_THRESHOLDS['low']:
                result['voltage_status'] = "Low"
            else:
                result['voltage_status'] = "Critical"
            print(f"Voltage status: {result['voltage_status']}")
    
    def get_battery_temperature(self) -> str:
        """Get battery temperature from Linux."""
        battery_path = self._find_battery_path()
        if not battery_path:
            return "N/A"
        
        print("Getting battery temperature from Linux /sys...")
        
        # Check for battery temperature files
        temp_files = ['temp', 'temperature']
        
        for temp_file in temp_files:
            file_path = os.path.join(battery_path, temp_file)
            value = SystemUtilities.safe_file_read(file_path)
            
            if value:
                temp_value = SystemUtilities.safe_int_conversion(value)
                if temp_value:
                    # Most Linux systems report in millidegrees or decidegrees Celsius
                    if temp_value > 1000:  # Likely in millidegrees
                        temp_celsius = round(temp_value / 1000, 1)
                    elif temp_value > 100:  # Likely in decidegrees
                        temp_celsius = round(temp_value / 10, 1)
                    else:  # Already in degrees
                        temp_celsius = round(temp_value, 1)
                    
                    print(f"Battery temperature from {temp_file}: {temp_celsius}°C")
                    return temp_celsius
        
        # Try thermal zones as fallback
        thermal_files = [
            '/sys/class/thermal/thermal_zone0/temp',
            '/sys/class/thermal/thermal_zone1/temp'
        ]
        
        for thermal_file in thermal_files:
            value = SystemUtilities.safe_file_read(thermal_file)
            if value:
                temp_value = SystemUtilities.safe_int_conversion(value)
                if temp_value:
                    temp_celsius = round(temp_value / 1000, 1)  # Usually millidegrees
                    print(f"Temperature from thermal zone: {temp_celsius}°C")
                    return temp_celsius
        
        # Try sensors command as last resort
        try:
            success, output = SystemUtilities.safe_run_command(['sensors'], timeout=5)
            if success:
                # Look for battery or ACPI temperature
                temp_matches = re.findall(r'(Battery|ACPI|temp\d+).*?(\d+\.?\d*)\s*°C', output)
                if temp_matches:
                    temp_celsius = round(float(temp_matches[0][1]), 1)
                    print(f"Linux temperature from sensors: {temp_celsius}°C")
                    return temp_celsius
        except Exception as e:
            print(f"Error with sensors command: {e}")
        
        print("Final battery temperature result: N/A")
        return "N/A"
