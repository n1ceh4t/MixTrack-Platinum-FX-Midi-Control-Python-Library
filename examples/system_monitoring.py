#!/usr/bin/env python3
"""
System Monitoring Example v2 - Enhanced system monitoring with MixtrackPlatinumFX.

This example demonstrates the improved system monitoring library with:
- Clean separation between library and UI logic
- Enhanced error handling and logging
- Better configuration management
- Improved alert system with visual feedback
- Real-time system vitals display on controller

Features:
- Ring lights for temperature and usage visualization
- Rate displays for CPU and memory usage percentages
- BPM displays for temperature values
- Time displays for current time
- VU meter alerts with alternating patterns
- Button LED feedback for user interaction
- Comprehensive logging and error handling
"""

import time
import signal
import sys
import os
import logging
from typing import Dict, Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mixtrack_platinum_fx import create_controller, RingType, LEDType
from system_monitor import (
    create_system_monitor, 
    AlertThresholds, 
    AlertType, 
    AlertState,
    SystemVitals
)


class SystemMonitoringUI:
    """
    UI layer for system monitoring that handles controller display updates
    and visual feedback. Separated from the core monitoring logic.
    """
    
    def __init__(self, controller, config: Optional[Dict] = None, logger: Optional[logging.Logger] = None):
        self.controller = controller
        self.logger = logger or self._create_logger()
        self.config = config or self._get_default_config()
        
        # UI state
        self.flash_state = False
        self.last_alert_time = 0.0
        
        # Get display configuration
        self.ring_assignments = self.config.get('system_monitoring', {}).get('ring_assignments', {
            'deck1': {'red_ring': 'cpu_temp', 'white_ring': 'cpu_usage'},
            'deck2': {'red_ring': 'gpu_temp', 'white_ring': 'memory_usage'}
        })
        
        self.jogger_assignments = self.config.get('system_monitoring', {}).get('jogger_display_assignments', {
            'deck1': 'cpu_usage',
            'deck2': 'memory_usage'
        })
        
        self.alert_config = self.config.get('alert_behavior', {})
        
        self.logger.info("SystemMonitoringUI initialized")
    
    def _create_logger(self) -> logging.Logger:
        """Create logger for UI"""
        logger = logging.getLogger('SystemMonitoringUI')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _get_default_config(self) -> Dict:
        """Get default UI configuration"""
        return {
            'system_monitoring': {
                'ring_assignments': {
                    'deck1': {'red_ring': 'cpu_temp', 'white_ring': 'cpu_usage'},
                    'deck2': {'red_ring': 'gpu_temp', 'white_ring': 'memory_usage'}
                },
                'jogger_display_assignments': {
                    'deck1': 'cpu_usage',
                    'deck2': 'memory_usage'
                }
            },
            'alert_behavior': {
                'enabled': True,
                'flash_leds': False,  # Disabled for clean alerts
                'flash_rings': False,  # Disabled for clean alerts
                'flash_vu_meters': True,  # Only VU meters flash during alerts
                'led_types_to_flash': [],  # No LEDs flash
                'ring_behavior': {
                    'flash_both_rings': False,
                    'flash_red_ring_only': False,
                    'flash_white_ring_only': False
                },
                'vu_meter_behavior': {
                    'alternating_pattern': True,
                    'alert_level': 90  # 90% of max VU meter value
                }
            }
        }
    
    def update_display(self, vitals: SystemVitals, alert_state: AlertState):
        """Update controller display with current vitals and alert state"""
        try:
            if alert_state.any_alert:
                self._update_alert_display(alert_state)
            else:
                self._update_normal_display(vitals)
            
            # Always update these displays
            self._update_bpm_displays(vitals)
            self._update_rate_displays(vitals)
            self._update_time_displays()
            
        except Exception as e:
            self.logger.error(f"Error updating display: {e}")
    
    def _update_normal_display(self, vitals: SystemVitals):
        """Update display for normal (non-alert) state"""
        # Clear VU meters
        self.controller.clear_all_vu_meters()
        
        # Update rings with normal values
        self._update_rings_normal(vitals)
    
    def _update_alert_display(self, alert_state: AlertState):
        """Update display for alert state"""
        # Toggle flash state
        self.flash_state = not self.flash_state
        
        # Only flash VU meters during alerts (clean, minimal alert)
        self._flash_vu_meters(self.flash_state)
    
    def _update_rings_normal(self, vitals: SystemVitals):
        """Update rings with normal values"""
        # Deck 1 rings
        red_value = self._get_metric_value(vitals, self.ring_assignments['deck1']['red_ring'])
        white_value = self._get_metric_value(vitals, self.ring_assignments['deck1']['white_ring'])
        self.controller.set_ring_percentage(1, RingType.SPINNER, red_value)
        self.controller.set_ring_percentage(1, RingType.POSITION, white_value)
        
        # Deck 2 rings
        red_value = self._get_metric_value(vitals, self.ring_assignments['deck2']['red_ring'])
        white_value = self._get_metric_value(vitals, self.ring_assignments['deck2']['white_ring'])
        self.controller.set_ring_percentage(2, RingType.SPINNER, red_value)
        self.controller.set_ring_percentage(2, RingType.POSITION, white_value)
    
    def _update_bpm_displays(self, vitals: SystemVitals):
        """Update BPM displays with temperature values"""
        self.controller.set_bpm_display(1, round(vitals.cpu_temp, 1))
        self.controller.set_bpm_display(2, round(vitals.gpu_temp, 1))
    
    def _update_rate_displays(self, vitals: SystemVitals):
        """Update rate displays with usage percentages"""
        deck1_value = getattr(vitals, self.jogger_assignments['deck1'])
        deck2_value = getattr(vitals, self.jogger_assignments['deck2'])
        
        self.controller.set_rate_display(1, deck1_value)
        self.controller.set_rate_display(2, deck2_value)
    
    def _update_time_displays(self):
        """Update time displays"""
        self.controller.set_current_time_display(1)
        self.controller.set_current_time_display(2)
    
    def _get_metric_value(self, vitals: SystemVitals, metric_name: str) -> float:
        """Get metric value scaled to 0-100%"""
        if metric_name == 'cpu_temp':
            return min(vitals.cpu_temp * 100.0 / 80.0, 100.0)
        elif metric_name == 'gpu_temp':
            return min(vitals.gpu_temp * 100.0 / 80.0, 100.0)
        elif metric_name == 'cpu_usage':
            return vitals.cpu_usage
        elif metric_name == 'memory_usage':
            return vitals.memory_usage
        else:
            return 0.0
    
    def _flash_configured_leds(self, deck: int, state: bool):
        """Flash configured LED types during alerts"""
        led_types_to_flash = self.alert_config.get('led_types_to_flash', [])
        
        if not led_types_to_flash:
            self.controller.flash_all_leds(deck, state)
            return
        
        for led_name in led_types_to_flash:
            try:
                led_type = LEDType(led_name)
                self.controller.set_led(deck, led_type, state)
            except ValueError:
                self.logger.warning(f"Unknown LED type '{led_name}' in alert configuration")
    
    def _flash_rings(self, deck: int, state: bool):
        """Flash rings based on configuration"""
        ring_behavior = self.alert_config.get('ring_behavior', {})
        flash_value = 100.0 if state else 0.0
        
        if ring_behavior.get('flash_both_rings', True):
            self.controller.set_ring_percentage(deck, RingType.SPINNER, flash_value)
            self.controller.set_ring_percentage(deck, RingType.POSITION, flash_value)
        elif ring_behavior.get('flash_red_ring_only', False):
            self.controller.set_ring_percentage(deck, RingType.SPINNER, flash_value)
        elif ring_behavior.get('flash_white_ring_only', False):
            self.controller.set_ring_percentage(deck, RingType.POSITION, flash_value)
    
    def _flash_vu_meters(self, state: bool):
        """Flash VU meters with alternating pattern"""
        vu_behavior = self.alert_config.get('vu_meter_behavior', {})
        alert_percentage = vu_behavior.get('alert_level', 90)  # Default 90%
        
        # Calculate alert level as percentage of max VU meter value (90)
        alert_level = int(90 * (alert_percentage / 100.0))
        
        if state:
            # State 1: Deck 1 = alert_level%, Deck 2 = 0%
            self.controller.set_vu_meter(1, alert_level)
            self.controller.set_vu_meter(2, 0)
        else:
            # State 2: Deck 1 = 0%, Deck 2 = alert_level% (alternating)
            self.controller.set_vu_meter(1, 0)
            self.controller.set_vu_meter(2, alert_level)


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down...")
    sys.exit(0)


def main():
    """Enhanced system monitoring example"""
    print("📊 MixtrackPlatinumFX System Monitoring Example v2")
    print("=" * 60)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger('SystemMonitoring')
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create controller
        with create_controller(debug=False) as controller:
            logger.info("✅ Controller connected successfully!")
            
            # Create system monitor with custom thresholds
            thresholds = AlertThresholds(
                cpu_temp=77.0,      # Alert if CPU temp >= 77°C
                gpu_temp=80.0,      # Alert if GPU temp >= 80°C
                cpu_usage=80.0,     # Alert if CPU usage >= 80%
                memory_usage=90.0   # Alert if memory usage >= 90%
            )
            
            monitor = create_system_monitor(controller, thresholds, logger=logger)
            
            # Create UI layer
            ui = SystemMonitoringUI(controller, logger=logger)
            
            # Add alert callback
            def alert_callback(alert_state: AlertState):
                """Handle alert conditions with enhanced feedback"""
                active_alerts = alert_state.get_active_alerts()
                if active_alerts:
                    alert_names = [alert.value for alert in active_alerts]
                    logger.warning(f"🚨 ALERT: {', '.join(alert_names)}")
                else:
                    pass
            
            monitor.register_alert_callback("main", alert_callback)
            
            # Start MIDI input handling for button LED feedback
            controller.start()
            logger.info("🎛️  Button LED Feedback Enabled!")
            
            # Start monitoring
            logger.info("📊 Starting system monitoring...")
            print("\n🎛️  Controller Display Layout:")
            print("  Deck 1: Red Ring=CPU Temperature, White Ring=CPU Usage")
            print("  Deck 2: Red Ring=GPU Temperature, White Ring=Memory Usage")
            print("  BPM Displays: Show temperature values in °C")
            print("  Rate Displays: Show CPU usage % (Deck 1) and Memory usage % (Deck 2)")
            print("  Time Displays: Show current time")
            # FX button LEDs removed for minimal implementation
            print("  🎮 BUTTON LED FEEDBACK: Press any button to see LED feedback!")
            print("  🚨 VU METER ALERTS: Clean alternating pattern at 90% during system alerts!")
            print("\nPress Ctrl+C to stop monitoring")
            
            # Respect config.json system_monitoring.cache_interval (default 1.0s)
            cfg_interval = monitor.config.get('system_monitoring', {}).get('cache_interval', 1.0)
            cfg_interval = max(0.1, float(cfg_interval))
            monitor.start_monitoring(update_interval=cfg_interval)
            
            # Main loop: realtime MIDI processing + UI updates at cfg_interval
            try:
                next_update = time.time()
                while True:
                    # Always process MIDI events quickly for realtime LED feedback
                    controller.process_midi_events()

                    now = time.time()
                    if now >= next_update:
                        # Get current vitals and alerts
                        vitals = monitor.get_current_vitals()
                        alert_state = monitor.get_current_alerts()

                        # Update UI
                        ui.update_display(vitals, alert_state)

                        # Log current status
                        if alert_state.any_alert:
                            active_alerts = alert_state.get_active_alerts()
                            alert_names = [alert.value for alert in active_alerts]
                            print(f"🚨 ALERT: {', '.join(alert_names)} - CPU: {vitals.cpu_temp:.1f}°C, GPU: {vitals.gpu_temp:.1f}°C, CPU: {vitals.cpu_usage:.1f}%, Memory: {vitals.memory_usage:.1f}%")
                        else:
                            print(f"🌡️  CPU: {vitals.cpu_temp:.1f}°C, GPU: {vitals.gpu_temp:.1f}°C, CPU Usage: {vitals.cpu_usage:.1f}%, Memory: {vitals.memory_usage:.1f}%")

                        next_update = now + cfg_interval

                    # Tiny sleep to yield CPU while keeping feedback snappy
                    time.sleep(0.005)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Stopping monitoring...")
                monitor.stop_monitoring()
                logger.info("✅ Monitoring stopped successfully!")
                
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
