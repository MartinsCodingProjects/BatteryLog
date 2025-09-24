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
1. Start the battery logger:
   ```bash
   python run_battery_logger.py
   ```
2. View the logged data:
   - Open `battery_log_visualization.html` in a browser for charts.
   - Open `battery_log_viewer.html` for tabular data.

## File Descriptions
- `run_battery_logger.py`: Main script for logging battery data.
- `battery_log_visualization.html`: Displays interactive charts for logged data.
- `battery_log_viewer.html`: Displays logged data in a table format.
- `battery_calibration_guide.md`: Guide for calibrating your battery.

## Notes
- Ensure Python 3.7+ is installed.
- The tool is optimized for Windows systems.

## Contributing
Feel free to submit issues or pull requests to improve the project.

## License
This project is licensed under the MIT License.