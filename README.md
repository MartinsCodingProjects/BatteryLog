# Battery Log

## Overview
Battery Log is a tool designed to monitor and log battery performance metrics on Windows systems. It provides insights into battery health, power consumption, and system resource usage over time. The tool is ideal for diagnosing battery calibration issues and understanding power usage patterns.

## Features
- Logs battery percentage, voltage, and health.
- Tracks system resource usage (CPU, RAM, Disk, etc.).
- Detects rapid battery percentage drops and calibration issues.
- Visualizes data with interactive charts and tables.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/MartinsCodingProjects/BatteryLog.git
   ```
2. Navigate to the project directory:
   ```bash
   cd BatteryLog
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Start the battery logger and settings server:
   ```bash
   python settings_server.py
   ```
   This will serve the visualization and settings API at:
   ```
   http://localhost:8081
   ```
2. Open your browser and navigate to:
   ```
   http://localhost:8081
   ```
   The visualization will load and display the battery data.

## Configuration
The application uses a `user_settings.json` file for configuration:
- **Log Interval**: How often to log battery data (default: 60 seconds)
- **Visualization Settings**: Default time range, auto-refresh preferences, etc.

A template is provided as `user_settings.template.json`. Copy it to `user_settings.json` and modify as needed.

## File Descriptions
- `run_battery_logger.py`: Main script for logging battery data.
- `settings_server.py`: HTTP server for serving the visualization and handling settings updates.
- `battery_log_visualization.html`: Displays interactive charts for logged data.
- `battery_log_viewer.html`: Displays logged data in a table format.
- `user_settings.json`: Configuration file (created from template).
- `run_on_startup.bat`: Windows batch file to start both logger and settings server on system startup.

## Notes
- Ensure Python 3.7+ is installed.
- The tool is optimized for Windows systems.

## Contributing
Feel free to submit issues or pull requests to improve the project.

## License
This project is licensed under the MIT License.