@echo off
cd /d "%~dp0"
REM Activate virtual environment and run the battery logger
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call "venv\Scripts\activate.bat"
) else (
    echo Warning: Virtual environment not found, using system Python
)

echo Starting battery logger...
start /min python "run_battery_logger.py"

REM Wait a moment for the server to start
timeout /t 3 /nobreak >nul

echo Opening browser...
start "" "http://localhost:8081"
