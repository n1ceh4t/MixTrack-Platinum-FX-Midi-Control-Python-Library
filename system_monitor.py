#!/usr/bin/env python3
"""
System Monitor Library - Core system monitoring functionality for MixtrackPlatinumFX.

This module provides the core system monitoring capabilities that integrate with the
MixtrackPlatinumFX controller. It focuses on data collection, alert detection, and
basic controller updates without UI-specific logic.

For examples and demonstrations, see examples/system_monitoring.py
"""

import psutil
import subprocess
import time
import os
import threading
import json
import logging
from typing import Dict, Optional, Callable, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from mixtrack_platinum_fx import MixtrackPlatinumFX, RingType, LEDType


class AlertType(Enum):
    """Types of system alerts"""
    CPU_TEMP = "cpu_temp"
    GPU_TEMP = "gpu_temp"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"


@dataclass
class AlertThresholds:
    """Alert threshold configuration"""
    cpu_temp: float = 75.0
    gpu_temp: float = 80.0
    cpu_usage: float = 80.0
    memory_usage: float = 90.0
    
    @classmethod
    def from_config(cls, config: Dict) -> 'AlertThresholds':
        """Create AlertThresholds from config dictionary"""
        thresholds = config.get('alert_thresholds', {})
        return cls(
            cpu_temp=thresholds.get('cpu_temp_alert', 75.0),
            gpu_temp=thresholds.get('gpu_temp_alert', 80.0),
            cpu_usage=thresholds.get('cpu_usage_alert', 80.0),
            memory_usage=thresholds.get('memory_usage_alert', 90.0)
        )
    
    def get_threshold(self, alert_type: AlertType) -> float:
        """Get threshold for specific alert type"""
        return getattr(self, alert_type.value)


@dataclass
class SystemVitals:
    """System vitals data"""
    cpu_usage: float
    memory_usage: float
    cpu_temp: float
    gpu_temp: float
    timestamp: float = field(default_factory=time.time)
    
    @classmethod
    def from_test_config(cls, config: Dict) -> 'SystemVitals':
        """Create SystemVitals from test mode config"""
        test_config = config.get('test_mode', {})
        return cls(
            cpu_usage=test_config.get('cpu_usage', 20.0),
            memory_usage=test_config.get('memory_usage', 30.0),
            cpu_temp=test_config.get('cpu_temp', 50.0),
            gpu_temp=test_config.get('gpu_temp', 45.0)
        )
    
    def get_metric(self, metric_name: str) -> float:
        """Get metric value by name"""
        return getattr(self, metric_name, 0.0)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'cpu_temp': self.cpu_temp,
            'gpu_temp': self.gpu_temp,
            'timestamp': self.timestamp
        }


@dataclass
class AlertState:
    """Current alert state"""
    alerts: Dict[AlertType, bool] = field(default_factory=dict)
    any_alert: bool = False
    timestamp: float = field(default_factory=time.time)
    
    def update(self, vitals: SystemVitals, thresholds: AlertThresholds):
        """Update alert state based on vitals and thresholds"""
        self.alerts = {
            AlertType.CPU_TEMP: vitals.cpu_temp >= thresholds.cpu_temp,
            AlertType.GPU_TEMP: vitals.gpu_temp >= thresholds.gpu_temp,
            AlertType.CPU_USAGE: vitals.cpu_usage >= thresholds.cpu_usage,
            AlertType.MEMORY_USAGE: vitals.memory_usage >= thresholds.memory_usage
        }
        self.any_alert = any(self.alerts.values())
        self.timestamp = time.time()
    
    def get_active_alerts(self) -> List[AlertType]:
        """Get list of active alert types"""
        return [alert_type for alert_type, active in self.alerts.items() if active]


class SystemMonitor:
    """
    Core system monitoring class for MixtrackPlatinumFX integration.
    
    Provides system vitals collection, alert detection, and basic controller updates.
    Focuses on data collection and alert logic without UI-specific implementations.
    """
    
    def __init__(self, 
                 controller: MixtrackPlatinumFX,
                 config: Optional[Dict] = None,
                 thresholds: Optional[AlertThresholds] = None,
                 cache_interval: Optional[float] = None,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize system monitor.
        
        Args:
            controller: MixtrackPlatinumFX controller instance
            config: Configuration dictionary (loads from config.json if None)
            thresholds: Alert thresholds configuration (overrides config)
            cache_interval: Cache update interval in seconds (overrides config)
            logger: Logger instance (creates default if None)
        """
        self.controller = controller
        self.logger = logger or self._create_logger()
        
        # Load configuration
        if config is None:
            config = self._load_config()
        
        # Initialize from config with overrides
        self.config = config
        self.thresholds = thresholds or AlertThresholds.from_config(config)
        self.cache_interval = cache_interval or config.get('system_monitoring', {}).get('cache_interval', 0.5)
        self.test_mode = config.get('test_mode', {}).get('enabled', False)
        
        # Thermal detection configuration
        self.thermal_paths = config.get('thermal_paths', [
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/class/thermal/thermal_zone1/temp",
            "/sys/class/thermal/thermal_zone2/temp",
            "/sys/devices/virtual/thermal/thermal_zone0/temp"
        ])
        self.temperature_keywords = config.get('temperature_keywords', [
            "core", "cpu", "k10temp", "amd"
        ])
        self.temperature_patterns = config.get('temperature_patterns', [
            "Core 0:", "Package id 0:", "Tdie:", "Tctl:", "CPU Temperature"
        ])
        self.gpu_keywords = config.get('gpu_keywords', [
            "amdgpu", "radeon"
        ])
        
        # Cache for system monitoring
        self._cache = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'cpu_temp': 0.0,
            'gpu_temp': 0.0,
            'last_update': 0.0
        }
        
        # Callbacks
        self.alert_callbacks: Dict[str, Callable] = {}
        
        # Monitoring state
        self.running = False
        self.monitor_thread = None
        self.alert_state = AlertState()
        
        self.logger.info("SystemMonitor initialized")
    
    def _create_logger(self) -> logging.Logger:
        """Create default logger"""
        logger = logging.getLogger('SystemMonitor')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _load_config(self) -> Dict:
        """Load configuration from config.json file"""
        config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.debug(f"Config file not found: {config_file}, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            self.logger.debug(f"Error parsing config file: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'debug': {'enabled': False},
            'system_monitoring': {
                'cache_interval': 0.5,
                'jogger_display_assignments': {
                    'deck1': 'cpu_usage',
                    'deck2': 'memory_usage'
                }
            },
            'alert_thresholds': {
                'cpu_temp_alert': 75.0,
                'gpu_temp_alert': 80.0,
                'cpu_usage_alert': 80.0,
                'memory_usage_alert': 90.0
            },
            'alert_behavior': {
                'enabled': True,
                'flash_leds': True,
                'flash_rings': True,
                'flash_vu_meters': True,
                'led_types_to_flash': [
                    'hotcue', 'extended_hotcue', 'autoloop', 'loop', 'play', 'sync', 'cue',
                    'pfl_cue', 'bpm_up', 'bpm_down', 'keylock', 'wheel_button', 'slip',
                    'deck_active', 'rate_display', 'pad_mode_hotcue', 'pad_mode_autoloop',
                    'pad_mode_fadercuts', 'pad_mode_sample1', 'pad_mode_sample2',
                    'pad1', 'pad2', 'pad3', 'pad4', 'pad5', 'pad6', 'pad7', 'pad8',
                    'effect1', 'effect2', 'effect3'
                ],
                'ring_behavior': {
                    'flash_both_rings': True,
                    'flash_red_ring_only': False,
                    'flash_white_ring_only': False
                },
                'vu_meter_behavior': {
                    'alternating_pattern': True,
                    'deck1_level': 0,
                    'deck2_level': 67
                }
            },
            'test_mode': {'enabled': False},
            'thermal_paths': [
                "/sys/class/thermal/thermal_zone0/temp",
                "/sys/class/thermal/thermal_zone1/temp",
                "/sys/class/thermal/thermal_zone2/temp",
                "/sys/devices/virtual/thermal/thermal_zone0/temp"
            ],
            'temperature_keywords': ["core", "cpu", "k10temp", "amd"],
            'temperature_patterns': [
                "Core 0:", "Package id 0:", "Tdie:", "Tctl:", "CPU Temperature"
            ],
            'gpu_keywords': ["amdgpu", "radeon"]
        }
    
    def start_monitoring(self, update_interval: float = 1.0):
        """
        Start system monitoring.
        
        Args:
            update_interval: Update interval in seconds
        """
        if self.running:
            self.logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(update_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.info(f"System monitoring started (interval: {update_interval}s)")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        if not self.running:
            return
            
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        
        # Clean up controller state
        try:
            self.controller.clear_all_vu_meters()
        except Exception as e:
            self.logger.error(f"Error cleaning up controller: {e}")
        
        self.logger.info("System monitoring stopped")
    
    def _monitor_loop(self, update_interval: float):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get current system vitals
                vitals = self.get_system_vitals()
                
                # Update alert state
                self.alert_state.update(vitals, self.thresholds)
                
                # Handle alerts
                if self.alert_state.any_alert:
                    self._handle_alerts()
                
                # Wait for next update
                time.sleep(update_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(1.0)
    
    def get_system_vitals(self) -> SystemVitals:
        """
        Get current system vitals.
        
        Returns:
            SystemVitals object with current system data
        """
        current_time = time.time()
        
        # Use cache if still valid
        if current_time - self._cache['last_update'] < self.cache_interval:
            return SystemVitals(
                cpu_usage=self._cache['cpu_usage'],
                memory_usage=self._cache['memory_usage'],
                cpu_temp=self._cache['cpu_temp'],
                gpu_temp=self._cache['gpu_temp'],
                timestamp=current_time
            )
        
        # Update cache
        try:
            self._cache['cpu_usage'] = psutil.cpu_percent(interval=0.1)
            self._cache['memory_usage'] = psutil.virtual_memory().percent
            self._cache['cpu_temp'] = self._get_cpu_temp()
            self._cache['gpu_temp'] = self._get_gpu_temp()
            self._cache['last_update'] = current_time
        except Exception as e:
            self.logger.error(f"Error updating system cache: {e}")
        
        return SystemVitals(
            cpu_usage=self._cache['cpu_usage'],
            memory_usage=self._cache['memory_usage'],
            cpu_temp=self._cache['cpu_temp'],
            gpu_temp=self._cache['gpu_temp'],
            timestamp=current_time
        )
    
    def _get_cpu_temp(self) -> float:
        """Get CPU temperature using configured thermal paths and keywords"""
        if self.test_mode:
            return self.config.get('test_mode', {}).get('cpu_temp', 50.0)
        
        try:
            # Try psutil first
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if any(keyword in name.lower() for keyword in self.temperature_keywords):
                        for entry in entries:
                            if entry.label and 'tctl' in entry.label.lower():
                                if entry.current and entry.current > 0:
                                    return entry.current
                        # If no Tctl, use first valid temperature
                        for entry in entries:
                            if entry.current and entry.current > 0:
                                return entry.current
            
            # Try thermal zones using configured paths
            for thermal_path in self.thermal_paths:
                if os.path.exists(thermal_path):
                    try:
                        with open(thermal_path, 'r') as f:
                            temp = int(f.read().strip()) / 1000.0
                            if temp > 0:
                                return temp
                    except:
                        continue
            
            # Try sensors command
            try:
                result = subprocess.run(['sensors'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if any(pattern in line for pattern in ['Core 0:', 'Package id 0:', 'Tdie:', 'Tctl:', 'CPU Temperature']):
                            parts = line.split()
                            for part in parts:
                                if '°C' in part:
                                    temp_str = part.replace('°C', '').replace('+', '').replace('*', '')
                                    try:
                                        temp = float(temp_str)
                                        if temp > 0:
                                            return temp
                                    except:
                                        pass
            except:
                pass
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"CPU temp error: {e}")
            return 0.0
    
    def _get_gpu_temp(self) -> float:
        """Get GPU temperature using configured GPU keywords"""
        if self.test_mode:
            return self.config.get('test_mode', {}).get('gpu_temp', 45.0)
        
        try:
            # Try nvidia-smi first
            result = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
            
            # Try AMD GPU using configured keywords
            result = subprocess.run(['sensors'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(keyword in line.lower() for keyword in self.gpu_keywords):
                        if '°C' in line:
                            parts = line.split()
                            for part in parts:
                                if '°C' in part:
                                    temp_str = part.replace('°C', '').replace('+', '')
                                    try:
                                        return float(temp_str)
                                    except:
                                        pass
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"GPU temp error: {e}")
            return 0.0
    
    def get_current_vitals(self) -> SystemVitals:
        """Get current system vitals (public interface)"""
        return self.get_system_vitals()
    
    def get_current_alerts(self) -> AlertState:
        """Get current alert state (public interface)"""
        return self.alert_state
    
    def _handle_alerts(self):
        """Handle alert conditions by calling registered callbacks"""
        try:
            # Call registered alert callbacks
            for callback_name, callback in self.alert_callbacks.items():
                try:
                    callback(self.alert_state)
                except Exception as e:
                    self.logger.error(f"Alert callback {callback_name} error: {e}")
        except Exception as e:
            self.logger.error(f"Error handling alerts: {e}")
    
    def get_metric_value(self, vitals: SystemVitals, metric_name: str) -> float:
        """
        Get the appropriate value for a metric, scaling temperatures to 0-100%
        
        Args:
            vitals: System vitals data
            metric_name: Name of the metric (cpu_temp, gpu_temp, cpu_usage, memory_usage)
            
        Returns:
            Scaled value (0-100%)
        """
        if metric_name == 'cpu_temp':
            # Scale CPU temperature to 0-100% (assuming max 80°C)
            return min(vitals.cpu_temp * 100.0 / 80.0, 100.0)
        elif metric_name == 'gpu_temp':
            # Scale GPU temperature to 0-100% (assuming max 80°C)
            return min(vitals.gpu_temp * 100.0 / 80.0, 100.0)
        elif metric_name == 'cpu_usage':
            return vitals.cpu_usage
        elif metric_name == 'memory_usage':
            return vitals.memory_usage
        else:
            # Default to 0 if unknown metric
            return 0.0
    
    def register_alert_callback(self, name: str, callback: Callable):
        """
        Register an alert callback.
        
        Args:
            name: Unique name for the callback
            callback: Function to call when alerts occur (receives AlertState)
        """
        self.alert_callbacks[name] = callback
        self.logger.info(f"Registered alert callback: {name}")
    
    def unregister_alert_callback(self, name: str):
        """Unregister an alert callback"""
        if name in self.alert_callbacks:
            del self.alert_callbacks[name]
            self.logger.info(f"Unregistered alert callback: {name}")
    
    def set_alert_thresholds(self, thresholds: AlertThresholds):
        """Update alert thresholds"""
        self.thresholds = thresholds
        self.logger.info(f"Alert thresholds updated: {thresholds}")


# Convenience functions

def create_system_monitor(controller: MixtrackPlatinumFX,
                         thresholds: Optional[AlertThresholds] = None,
                         config: Optional[Dict] = None,
                         logger: Optional[logging.Logger] = None) -> SystemMonitor:
    """
    Create a system monitor instance.
    
    Args:
        controller: MixtrackPlatinumFX controller instance
        thresholds: Alert thresholds configuration
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        SystemMonitor instance
    """
    return SystemMonitor(controller, config=config, thresholds=thresholds, logger=logger)
