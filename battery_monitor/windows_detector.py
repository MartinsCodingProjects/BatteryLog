#!/usr/bin/env python3
"""
Windows-specific battery detection using WMI
"""

import os
import tempfile
import subprocess
from typing import Dict, Any, List
from .utils import SystemUtilities, PlatformDetector
from .config import CYCLE_COUNT_RANGE, POWERSHELL_TIMEOUT, POWERSHELL_EXECUTION_POLICY


class WindowsBatteryDetector:
    """Windows-specific battery detection using WMI."""
    
    def __init__(self, platform_detector: PlatformDetector):
        self.platform = platform_detector
        self.wmi = platform_detector.wmi if platform_detector.wmi_available else None
    
    def get_battery_details(self) -> Dict[str, Any]:
        """Get comprehensive battery details from Windows WMI."""
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
        
        if not self.platform.wmi_available:
            return details
        
        try:
            self._extract_static_data(details)
            self._extract_status_data(details)
            self._extract_win32_battery_data(details)
            self._detect_cycle_count(details)
            self._calculate_health(details)
        except Exception as e:
            pass  # Silently handle errors
        
        return details
    
    def _extract_static_data(self, details: Dict[str, Any]):
        """Extract data from BatteryStaticData WMI class."""
        try:
            w_wmi = self.wmi.WMI(namespace='root/WMI')
            battery_static = w_wmi.query('Select * from BatteryStaticData')
            
            if battery_static:
                static_data = battery_static[0]
                
                # Extract properties safely
                if hasattr(static_data, 'DesignedCapacity'):
                    details['design_capacity'] = static_data.DesignedCapacity
                
                if hasattr(static_data, 'DeviceName'):
                    details['name'] = static_data.DeviceName
                
                if hasattr(static_data, 'ManufactureName'):
                    details['manufacturer'] = static_data.ManufactureName
                
                if hasattr(static_data, 'DeviceChemistry'):
                    chemistry_map = {
                        1: 'Lead Acid', 2: 'Nickel Cadmium', 3: 'Nickel Metal Hydride', 
                        4: 'Lithium Ion', 5: 'Nickel Zinc', 6: 'Lithium Polymer'
                    }
                    details['chemistry'] = chemistry_map.get(
                        static_data.DeviceChemistry, 
                        f"Type {static_data.DeviceChemistry}"
                    )
                    
        except Exception as e:
            pass  # Silently handle errors
    
    def _extract_status_data(self, details: Dict[str, Any]):
        """Extract data from BatteryStatus WMI class."""
        try:
            import psutil
            w_wmi = self.wmi.WMI(namespace='root/WMI')
            battery_status = w_wmi.query('Select * from BatteryStatus')
            
            if battery_status:
                status_data = battery_status[0]
                
                if hasattr(status_data, 'RemainingCapacity'):
                    remaining = status_data.RemainingCapacity
                    
                    # Estimate full capacity from current percentage and remaining capacity
                    battery = psutil.sensors_battery()
                    if battery and battery.percent > 0:
                        estimated_full = round((remaining * 100) / battery.percent)
                        details['full_charge_capacity'] = estimated_full
                
                if hasattr(status_data, 'Voltage') and status_data.Voltage:
                    voltage = round(status_data.Voltage / 1000, 2)  # Convert mV to V
                    details['design_voltage'] = voltage
                    
        except Exception as e:
            pass  # Silently handle errors
    
    def _extract_win32_battery_data(self, details: Dict[str, Any]):
        """Extract data from Win32_Battery WMI class."""
        try:
            w = self.wmi.WMI()
            batteries = w.query("Select * from Win32_Battery")
            
            if batteries:
                battery = batteries[0]
                
                # Extract basic properties
                for prop in ['Chemistry', 'Name', 'Status']:
                    try:
                        val = getattr(battery, prop, None)
                        if val is not None and details[prop.lower()] == "N/A":
                            details[prop.lower()] = str(val).strip()
                    except Exception as e:
                        pass  # Silently ignore errors
                        
        except Exception as e:
            pass  # Silently handle errors
    
    def _detect_cycle_count(self, details: Dict[str, Any]):
        """Detect battery cycle count using multiple PowerShell methods."""
        cycle_methods = self._get_cycle_detection_methods()
        
        for i, method in enumerate(cycle_methods, 1):
            try:
                success, output = SystemUtilities.safe_run_command([
                    'powershell', '-ExecutionPolicy', POWERSHELL_EXECUTION_POLICY, '-Command', method
                ], timeout=POWERSHELL_TIMEOUT)
                
                if success and output:
                    cycle_count = self._extract_cycle_count_from_output(output)
                    
                    if cycle_count is not None:
                        details['cycle_count'] = cycle_count
                        if cycle_count > 0:  # Prefer non-zero values
                            return
                            
            except Exception as e:
                pass  # Silently try next method
        
        self._add_cycle_count_info_message(details)
    
    def _get_cycle_detection_methods(self) -> List[str]:
        """Get list of PowerShell methods for cycle count detection."""
        return [
            'Get-WmiObject -Class "BatteryCycleCount" -Namespace "root/WMI" | Select-Object -ExpandProperty CycleCount',
            'Get-WmiObject -Class "BatteryStaticData" -Namespace "root/WMI" | Select-Object -ExpandProperty CycleCount',
            'Get-WmiObject -Class "MSBatteryClass" -Namespace "root/WMI" | Select-Object -ExpandProperty CycleCount',
            'powercfg /batteryreport /xml /output temp_report.xml 2>$null; if($?) { [xml]$xml = Get-Content temp_report.xml -ErrorAction SilentlyContinue; $xml.BatteryReport.Batteries.Battery.CycleCount; Remove-Item temp_report.xml -Force -ErrorAction SilentlyContinue }',
            'Get-CimInstance -Namespace "root/WMI" -ClassName "BatteryCycleCount" | Select-Object -ExpandProperty CycleCount',
            'Get-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{72631e54-78a4-11d0-bcf7-00aa00b7b32a}\\*" -Name "CycleCount" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty CycleCount',
            '$bat = Get-WmiObject -Namespace "root\\wmi" -Query "SELECT InstanceName FROM BatteryStatus WHERE Tag=1"; if($bat) { Get-WmiObject -Namespace "root\\wmi" -Query "SELECT CycleCount FROM BatteryCycleCount WHERE InstanceName=\'$($bat.InstanceName)\'" | Select-Object -ExpandProperty CycleCount }',
            'Get-WmiObject -Class "Dell_BatteryStatistics" -Namespace "root\\dcim\\sysman" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty CycleCount',
            'Get-ChildItem -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\ACPI\\*BAT*" -Recurse -ErrorAction SilentlyContinue | Get-ItemProperty | Where-Object {$_.CycleCount -ne $null} | Select-Object -ExpandProperty CycleCount'
        ]
    
    def _extract_cycle_count_from_output(self, output: str) -> int:
        """Extract cycle count from PowerShell output."""
        numbers = SystemUtilities.extract_numbers_from_text(output)
        for num in numbers:
            if CYCLE_COUNT_RANGE['min'] <= num <= CYCLE_COUNT_RANGE['max']:
                return num
        return None
    
    def _add_cycle_count_info_message(self, details: Dict[str, Any]):
        """Add informative message about cycle count - now silent."""
        pass  # Removed console output to reduce spam
    
    def _calculate_health(self, details: Dict[str, Any]):
        """Calculate battery health percentage."""
        try:
            # Try to get full capacity from WMI first
            w_wmi = self.wmi.WMI(namespace='root/WMI')
            full_capacity_query = w_wmi.query('Select * from BatteryFullChargedCapacity')
            
            if full_capacity_query:
                full_cap_data = full_capacity_query[0]
                if hasattr(full_cap_data, 'FullChargedCapacity'):
                    details['full_charge_capacity'] = full_cap_data.FullChargedCapacity
            
            # Calculate health if we have both values
            if (details['design_capacity'] != "N/A" and 
                details['full_charge_capacity'] != "N/A" and 
                isinstance(details['design_capacity'], (int, float)) and 
                isinstance(details['full_charge_capacity'], (int, float)) and
                details['design_capacity'] > 0):
                
                health_pct = (details['full_charge_capacity'] / details['design_capacity']) * 100
                details['health'] = round(health_pct, 1)
                
        except Exception as e:
            pass  # Silently continue on error
    
    def get_voltage_and_power(self) -> Dict[str, Any]:
        """Get voltage and power information from Windows WMI."""
        result = {
            'voltage': "N/A",
            'power_draw': "N/A",
            'load_severity': "Unknown",
            'voltage_status': "Unknown"
        }
        
        if not self.platform.wmi_available:
            return result
        
        try:
            w_wmi = self.wmi.WMI(namespace='root/WMI')
            battery_status = w_wmi.query('Select * from BatteryStatus')
            
            if battery_status:
                status_data = battery_status[0]
                
                # Get voltage
                if hasattr(status_data, 'Voltage') and status_data.Voltage:
                    voltage = round(status_data.Voltage / 1000, 2)  # Convert mV to V
                    result['voltage'] = voltage
                
                # Get power draw (discharge rate)
                if hasattr(status_data, 'DischargeRate') and status_data.DischargeRate:
                    power_draw = round(status_data.DischargeRate / 1000, 2)  # Convert mW to W
                    result['power_draw'] = power_draw
            
            self._classify_power_metrics(result)
            
        except Exception as e:
            pass  # Silently handle errors
        
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
        
        # Determine voltage status
        if result['voltage'] != "N/A" and isinstance(result['voltage'], (int, float)):
            if result['voltage'] > VOLTAGE_THRESHOLDS['normal']:
                result['voltage_status'] = "Normal"
            elif result['voltage'] > VOLTAGE_THRESHOLDS['low']:
                result['voltage_status'] = "Low"
            else:
                result['voltage_status'] = "Critical"
    
    def get_battery_temperature(self) -> str:
        """Get battery temperature from Windows WMI."""
        if not self.platform.wmi_available:
            return "N/A"
        
        try:
            w_wmi = self.wmi.WMI(namespace='root/WMI')
            
            # Try battery-specific temperature
            try:
                battery_temp = w_wmi.query('Select * from BatteryTemperature')
                if battery_temp:
                    temp_kelvin = battery_temp[0].Temperature
                    if temp_kelvin and temp_kelvin > 0:
                        temp_celsius = round((temp_kelvin / 10) - 273.15, 1)
                        return temp_celsius
            except Exception as e:
                pass  # Silently try next method
            
            # Try thermal zones as fallback
            try:
                thermal_zones = w_wmi.query('Select * from MSAcpi_ThermalZoneTemperature')
                if thermal_zones:
                    temp_kelvin = thermal_zones[0].CurrentTemperature
                    if temp_kelvin and temp_kelvin > 0:
                        temp_celsius = round((temp_kelvin / 10) - 273.15, 1)
                        return temp_celsius
            except Exception as e:
                pass  # Silently handle thermal zone errors
                
        except Exception as e:
            pass  # Silently handle errors
        
        return "N/A"
