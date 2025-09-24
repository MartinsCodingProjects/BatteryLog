#!/usr/bin/env python3
"""
Utility functions for system operations and data formatting
"""

import subprocess
import re
import platform
from typing import List, Tuple, Optional


class PlatformDetector:
    """Handles platform detection and module imports."""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.wmi_available = False
        self._setup_platform_modules()
    
    def _setup_platform_modules(self):
        """Import platform-specific modules."""
        if self.platform == 'windows':
            try:
                import wmi
                self.wmi_available = True
                self.wmi = wmi
            except ImportError:
                print("Warning: WMI module not available. Some Windows features will be disabled.")
                print("Install with: pip install WMI")
    
    def is_windows(self) -> bool:
        return self.platform == 'windows'
    
    def is_linux(self) -> bool:
        return self.platform == 'linux'
    
    def is_macos(self) -> bool:
        return self.platform == 'darwin'


class SystemUtilities:
    """Utility functions for system operations and formatting."""
    
    @staticmethod
    def format_secs(secs: Optional[int]) -> str:
        """Format seconds to HH:MM:SS format."""
        if secs is None or secs == -2 or secs < 0:  # psutil uses -2 for "power plugged"
            return "N/A"
        h = secs // 3600
        m = (secs % 3600) // 60
        s = secs % 60
        return f"{h:02}:{m:02}:{s:02}"
    
    @staticmethod
    def safe_run_command(command: List[str], timeout: int = 10) -> Tuple[bool, str]:
        """Safely run a system command and return success status and output."""
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'  # Ignore encoding errors
            )
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def extract_numbers_from_text(text: str) -> List[int]:
        """Extract all numbers from text."""
        try:
            return [int(match) for match in re.findall(r'\b(\d+)\b', text)]
        except ValueError:
            return []
    
    @staticmethod
    def safe_file_read(file_path: str) -> Optional[str]:
        """Safely read a file and return its content."""
        try:
            with open(file_path, 'r') as f:
                return f.read().strip()
        except Exception:
            return None
    
    @staticmethod
    def safe_int_conversion(value: str) -> Optional[int]:
        """Safely convert string to integer."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def safe_float_conversion(value: str) -> Optional[float]:
        """Safely convert string to float."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
