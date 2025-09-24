#!/usr/bin/env python3
"""
macOS-specific battery detection using system utilities
"""

import re
from typing import Dict, Any
from .utils import SystemUtilities


class MacOSBatteryDetector:
    """macOS-specific battery detection using system utilities."""
    
    def get_battery_details(self) -> Dict[str, Any]:
        """Get battery details from macOS system utilities."""
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
        
        print("Getting battery details from macOS...")
        
        try:
            success, output = SystemUtilities.safe_run_command([
                'ioreg', '-rc', 'AppleSmartBattery'
            ], timeout=10)
            
            if success:
                self._parse_ioreg_output(output, details)
                self._calculate_health(details)
                
        except Exception as e:
            print(f"Error getting macOS battery details: {e}")
        
        return details
    
    def _parse_ioreg_output(self, output: str, details: Dict[str, Any]):
        """Parse ioreg output for battery information."""
        patterns = {
            'cycle_count': r'"CycleCount" = (\d+)',
            'design_capacity': r'"DesignCapacity" = (\d+)',
            'full_charge_capacity': r'"MaxCapacity" = (\d+)',
            'manufacturer': r'"Manufacturer" = "([^"]+)"',
            'name': r'"DeviceName" = "([^"]+)"',
            'chemistry': r'"DeviceChemistry" = "([^"]+)"',
            'status': r'"ExternalConnected" = (Yes|No)',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                value = match.group(1)
                # Convert numeric values
                if key in ['cycle_count', 'design_capacity', 'full_charge_capacity']:
                    numeric_value = SystemUtilities.safe_int_conversion(value)
                    if numeric_value is not None:
                        details[key] = numeric_value
                        print(f"{key}: {numeric_value}")
                else:
                    details[key] = value
                    print(f"{key}: {value}")
    
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
        """Get voltage and power information from macOS."""
        result = {
            'voltage': "N/A",
            'power_draw': "N/A",
            'load_severity': "Unknown",
            'voltage_status': "Unknown"
        }
        
        try:
            print("Getting voltage and power from macOS...")
            success, output = SystemUtilities.safe_run_command([
                'ioreg', '-rc', 'AppleSmartBattery'
            ], timeout=10)
            
            if success:
                # Look for voltage in ioreg output
                voltage_match = re.search(r'"Voltage" = (\d+)', output)
                if voltage_match:
                    voltage_mv = int(voltage_match.group(1))
                    result['voltage'] = round(voltage_mv / 1000, 2)
                    print(f"macOS voltage: {result['voltage']}V")
                
                # Look for power draw (calculate from amperage)
                power_match = re.search(r'"InstantAmperage" = (-?\d+)', output)
                if power_match and result['voltage'] != "N/A":
                    amperage = abs(int(power_match.group(1))) / 1000  # Convert to amps
                    result['power_draw'] = round(result['voltage'] * amperage, 2)
                    print(f"macOS power draw: {result['power_draw']}W")
            
            self._classify_power_metrics(result)
                        
        except Exception as e:
            print(f"Error getting macOS voltage/power: {e}")
        
        return result
    
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
        """Get battery temperature from macOS."""
        print("Getting battery temperature from macOS...")
        
        try:
            # Try powermetrics for thermal data
            success, output = SystemUtilities.safe_run_command([
                'powermetrics', '--sample-interval', '100', '--sample-count', '1', '-f', 'csv'
            ], timeout=10)
            
            if success:
                # Look for battery temperature in the output
                temp_match = re.search(r'Battery.*?(\d+\.?\d*)', output)
                if temp_match:
                    temp_celsius = round(float(temp_match.group(1)), 1)
                    print(f"macOS temperature from powermetrics: {temp_celsius}°C")
                    return temp_celsius
                    
        except Exception as e:
            print(f"Error with macOS powermetrics: {e}")
        
        try:
            # Try ioreg as fallback
            success, output = SystemUtilities.safe_run_command([
                'ioreg', '-rc', 'AppleSmartBattery'
            ], timeout=10)
            
            if success:
                # Look for temperature-related fields
                temp_match = re.search(r'"Temperature" = (\d+)', output)
                if temp_match:
                    # ioreg typically reports in tenths of degrees Celsius
                    temp_celsius = round(int(temp_match.group(1)) / 10, 1)
                    print(f"macOS temperature from ioreg: {temp_celsius}°C")
                    return temp_celsius
                    
        except Exception as e:
            print(f"Error with macOS ioreg: {e}")
        
        print("Final battery temperature result: N/A")
        return "N/A"
