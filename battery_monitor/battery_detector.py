#!/usr/bin/env python3
"""
Battery detector factory for creating platform-specific detectors
"""

from typing import Optional, Union
from .utils import PlatformDetector
from .windows_detector import WindowsBatteryDetector
from .linux_detector import LinuxBatteryDetector
from .macos_detector import MacOSBatteryDetector


class BatteryDetectorFactory:
    """Factory for creating appropriate battery detector based on platform."""
    
    @staticmethod
    def create_detector(platform: PlatformDetector) -> Optional[Union[WindowsBatteryDetector, LinuxBatteryDetector, MacOSBatteryDetector]]:
        """Create appropriate battery detector based on platform."""
        if platform.is_windows():
            return WindowsBatteryDetector(platform)
        elif platform.is_linux():
            return LinuxBatteryDetector()
        elif platform.is_macos():
            return MacOSBatteryDetector()
        else:
            print(f"Unsupported platform: {platform.platform}")
            return None
