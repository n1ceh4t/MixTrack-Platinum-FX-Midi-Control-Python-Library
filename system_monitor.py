#!/usr/bin/env python3
"""
System Monitor - Integration module for system monitoring with MixtrackPlatinumFX.

This module provides system monitoring capabilities that integrate with the
MixtrackPlatinumFX controller for real-time system vitals display.
"""

import psutil
import subprocess
import time
import os
import threading
import json
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from mixtrack_platinum_fx import MixtrackPlatinumFX, RingType, LEDType


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


@dataclass
class SystemVitals:
    """System vitals data"""
    cpu_usage: float
    memory_usage: float
    cpu_temp: float
    gpu_temp: float
    timestamp: float
    
    @classmethod
    def from_test_config(cls, config: Dict) -> 'SystemVitals':
        """Create SystemVitals from test mode config"""
        test_config = config.get('test_mode', {})
        return cls(
            cpu_usage=test_config.get('cpu_usage', 20.0),
            memory_usage=test_config.get('memory_usage', 30.0),
            cpu_temp=test_config.get('cpu_temp', 50.0),
            gpu_temp=test_config.get('gpu_temp', 45.0),
            timestamp=time.time()
        )


class SystemMonitor:
    """
    System monitoring class that integrates with MixtrackPlatinumFX.
    
    Provides real-time system monitoring with visual feedback on the controller.
    """
    
    def __init__(self, 
                 controller: MixtrackPlatinumFX,
                 config: Optional[Dict] = None,
                 thresholds: Optional[AlertThresholds] = None,
                 cache_interval: Optional[float] = None,
                 debug: Optional[bool] = None):
        """
        Initialize system monitor.
        
        Args:
            controller: MixtrackPlatinumFX controller instance
            config: Configuration dictionary (loads from config.json if None)
            thresholds: Alert thresholds configuration (overrides config)
            cache_interval: Cache update interval in seconds (overrides config)
            debug: Enable debug output (overrides config)
        """
        self.controller = controller
        
        # Load configuration
        if config is None:
            config = self._load_config()
        
        # Initialize from config with overrides
        self.config = config
        self.thresholds = thresholds or AlertThresholds.from_config(config)
        self.cache_interval = cache_interval or config.get('system_monitoring', {}).get('cache_interval', 0.5)
        self.debug = debug if debug is not None else config.get('debug', {}).get('enabled', False)
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
        self.flash_state = False
        
        if self.debug:
            print("SystemMonitor initialized")
    
    def _load_config(self) -> Dict:
        """Load configuration from config.json file"""
        config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            if self.debug:
                print(f"Config file not found: {config_file}, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            if self.debug:
                print(f"Error parsing config file: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'debug': {'enabled': False},
            'system_monitoring': {'cache_interval': 0.5},
            'alert_thresholds': {
                'cpu_temp_alert': 75.0,
                'gpu_temp_alert': 80.0,
                'cpu_usage_alert': 80.0,
                'memory_usage_alert': 90.0
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
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(update_interval,),
            daemon=True
        )
        self.monitor_thread.start()
        
        if self.debug:
            print(f"System monitoring started (interval: {update_interval}s)")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        
        if self.debug:
            print("System monitoring stopped")
    
    def _monitor_loop(self, update_interval: float):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get current system vitals
                vitals = self.get_system_vitals()
                
                # Check for alerts
                alerts = self.check_alerts(vitals)
                
                # Update controller display
                self._update_controller_display(vitals, alerts)
                
                # Handle alerts
                if alerts['any_alert']:
                    self._handle_alerts(alerts)
                
                # Wait for next update
                time.sleep(update_interval)
                
            except Exception as e:
                if self.debug:
                    print(f"Monitoring error: {e}")
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
            if self.debug:
                print(f"Error updating system cache: {e}")
        
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
            if self.debug:
                print(f"CPU temp error: {e}")
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
            if self.debug:
                print(f"GPU temp error: {e}")
            return 0.0
    
    def check_alerts(self, vitals: SystemVitals) -> Dict[str, bool]:
        """
        Check for alert conditions.
        
        Args:
            vitals: System vitals to check
            
        Returns:
            Dictionary of alert states
        """
        alerts = {
            'cpu_temp_alert': vitals.cpu_temp >= self.thresholds.cpu_temp,
            'gpu_temp_alert': vitals.gpu_temp >= self.thresholds.gpu_temp,
            'cpu_usage_alert': vitals.cpu_usage >= self.thresholds.cpu_usage,
            'memory_usage_alert': vitals.memory_usage >= self.thresholds.memory_usage
        }
        
        alerts['any_alert'] = any(alerts.values())
        
        return alerts
    
    def _update_controller_display(self, vitals: SystemVitals, alerts: Dict[str, bool]):
        """Update controller display with system vitals"""
        if alerts['any_alert']:
            # Flash mode - toggle flash state
            self.flash_state = not self.flash_state
        else:
            # Normal mode
            self.flash_state = False
        
        # Update deck 1 (CPU usage and memory usage)
        if alerts['any_alert']:
            # Flash all LEDs and rings
            self.controller.flash_all_leds(1, self.flash_state)
            self.controller.set_ring_percentage(1, RingType.SPINNER, 100.0 if self.flash_state else 0.0)
            self.controller.set_ring_percentage(1, RingType.POSITION, 100.0 if self.flash_state else 0.0)
        else:
            # Normal display
            self.controller.clear_all_leds()
            self.controller.set_ring_percentage(1, RingType.SPINNER, vitals.cpu_usage)
            self.controller.set_ring_percentage(1, RingType.POSITION, vitals.memory_usage)
        
        # Update deck 2 (CPU temp and GPU temp)
        if alerts['any_alert']:
            # Flash all LEDs and rings
            self.controller.flash_all_leds(2, self.flash_state)
            self.controller.set_ring_percentage(2, RingType.SPINNER, 100.0 if self.flash_state else 0.0)
            self.controller.set_ring_percentage(2, RingType.POSITION, 100.0 if self.flash_state else 0.0)
        else:
            # Normal display
            self.controller.clear_all_leds()
            # Scale temperatures to 0-100% (assuming max 80°C)
            cpu_temp_percent = min(vitals.cpu_temp * 100.0 / 80.0, 100.0)
            gpu_temp_percent = min(vitals.gpu_temp * 100.0 / 80.0, 100.0)
            self.controller.set_ring_percentage(2, RingType.SPINNER, cpu_temp_percent)
            self.controller.set_ring_percentage(2, RingType.POSITION, gpu_temp_percent)
        
        # Update BPM displays with temperatures
        self.controller.set_bpm_display(1, vitals.cpu_temp)
        self.controller.set_bpm_display(2, vitals.gpu_temp)
        
        # Update time display
        self.controller.set_current_time_display(1)
        self.controller.set_current_time_display(2)
        
        if self.debug and alerts['any_alert']:
            alert_types = [k for k, v in alerts.items() if v and k != 'any_alert']
            print(f"🚨 ALERT: {', '.join(alert_types)}")
    
    def _handle_alerts(self, alerts: Dict[str, bool]):
        """Handle alert conditions"""
        # Call registered alert callbacks
        for callback_name, callback in self.alert_callbacks.items():
            try:
                callback(alerts)
            except Exception as e:
                if self.debug:
                    print(f"Alert callback {callback_name} error: {e}")
    
    def register_alert_callback(self, name: str, callback: Callable):
        """
        Register an alert callback.
        
        Args:
            name: Unique name for the callback
            callback: Function to call when alerts occur
        """
        self.alert_callbacks[name] = callback
    
    def unregister_alert_callback(self, name: str):
        """Unregister an alert callback"""
        if name in self.alert_callbacks:
            del self.alert_callbacks[name]
    
    def set_alert_thresholds(self, thresholds: AlertThresholds):
        """Update alert thresholds"""
        self.thresholds = thresholds
        if self.debug:
            print(f"Alert thresholds updated: {thresholds}")


# Convenience functions

def create_system_monitor(controller: MixtrackPlatinumFX,
                         thresholds: Optional[AlertThresholds] = None,
                         debug: bool = False) -> SystemMonitor:
    """
    Create a system monitor instance.
    
    Args:
        controller: MixtrackPlatinumFX controller instance
        thresholds: Alert thresholds configuration
        debug: Enable debug output
        
    Returns:
        SystemMonitor instance
    """
    return SystemMonitor(controller, thresholds, debug=debug)


if __name__ == "__main__":
    # Example usage
    from mixtrack_platinum_fx import create_controller
    
    with create_controller(debug=True) as controller:
        # Create system monitor
        thresholds = AlertThresholds(
            cpu_temp=75.0,
            gpu_temp=80.0,
            cpu_usage=80.0,
            memory_usage=90.0
        )
        
        monitor = create_system_monitor(controller, thresholds, debug=True)
        
        # Add alert callback
        def alert_callback(alerts):
            print(f"Alert triggered: {alerts}")
        
        monitor.register_alert_callback("test", alert_callback)
        
        # Start monitoring
        monitor.start_monitoring(update_interval=1.0)
        
        try:
            print("System monitoring started. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping monitoring...")
            monitor.stop_monitoring()
