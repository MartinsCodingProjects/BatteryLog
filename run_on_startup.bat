@echo off
REM Add this script to Windows startup
cd /d "C:\Users\Pc\Coding\BatteryLog"
start /min pythonw settings_server.py
start /min pythonw run_battery_logger.py
