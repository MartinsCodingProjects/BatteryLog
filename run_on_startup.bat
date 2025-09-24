@echo off
REM Add this script to Windows startup
start python "run_battery_logger.py"
start "" "http://localhost:8081/battery_log_visualization.html"
