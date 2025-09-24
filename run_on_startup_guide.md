# Guide to Run Battery Log on System Startup

## Windows
1. Create a shortcut for the `run_on_startup.bat` file:
   - Right-click on `run_on_startup.bat`.
   - Select `Create Shortcut`.
2. Move the shortcut to the Startup folder:
   - Press `Win + R`, type `shell:startup`, and press Enter.
   - Copy the shortcut into the opened folder.
3. Restart your computer to verify the script runs on startup.


## Linux
1. Create a shell script to run the logger:
   ```bash
   #!/bin/bash
   python3 /path/to/BatteryLog/run_battery_logger.py
   ```
   Save this script as `run_on_startup.sh`.
2. Make the script executable:
   ```bash
   chmod +x /path/to/run_on_startup.sh
   ```
3. Add the script to startup applications:
   - Open the terminal and edit the crontab file:
     ```bash
     crontab -e
     ```
   - Add the following line to run the script at startup:
     ```bash
     @reboot /path/to/run_on_startup.sh
     ```
4. Save and exit the crontab editor.
5. Restart your computer to verify the script runs on startup.
