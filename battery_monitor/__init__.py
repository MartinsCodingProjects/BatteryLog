#!/usr/bin/env python3
"""
Battery Logger Package
Cross-platform battery monitoring and logging system
"""

__version__ = "2.0.0"
__author__ = "Battery Logger Team" 
__description__ = "Cross-platform battery monitoring and logging system"

from .battery_logger_main import BatteryLogger
from .battery_detector import BatteryDetectorFactory
from .utils import PlatformDetector, SystemUtilities
from .system_metrics import SystemMetrics
from . import estimations

__all__ = [
    'BatteryLogger',
    'BatteryDetectorFactory', 
    'PlatformDetector',
    'SystemUtilities',
    'SystemMetrics',
    'estimations'
]
