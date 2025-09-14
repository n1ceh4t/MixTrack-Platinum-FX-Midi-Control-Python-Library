#!/usr/bin/env python3
"""
System Monitoring Example - Real-time system monitoring with MixtrackPlatinumFX.

This example shows how to use the system monitoring integration to display
real-time system vitals on the controller.
"""

import time
import signal
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mixtrack_platinum_fx import create_controller
from system_monitor import create_system_monitor, AlertThresholds


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down...")
    sys.exit(0)


def main():
    """System monitoring example"""
    print("📊 MixtrackPlatinumFX System Monitoring Example")
    print("=" * 50)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create controller
    with create_controller(debug=True) as controller:
        print("✅ Controller connected successfully!")
        
        # Create system monitor with custom thresholds
        thresholds = AlertThresholds(
            cpu_temp=75.0,      # Alert if CPU temp >= 75°C
            gpu_temp=80.0,      # Alert if GPU temp >= 80°C
            cpu_usage=80.0,     # Alert if CPU usage >= 80%
            memory_usage=90.0   # Alert if memory usage >= 90%
        )
        
        monitor = create_system_monitor(controller, thresholds, debug=True)
        
        # Add alert callback
        def alert_callback(alerts):
            """Handle alert conditions"""
            alert_types = [k for k, v in alerts.items() if v and k != 'any_alert']
            if alert_types:
                print(f"🚨 ALERT: {', '.join(alert_types)}")
        
        monitor.register_alert_callback("main", alert_callback)
        
        # Start monitoring
        print("\n📊 Starting system monitoring...")
        print("Deck 1: Red=CPU Usage, White=Memory Usage")
        print("Deck 2: Red=CPU Temperature, White=GPU Temperature")
        print("BPM Displays: Show temperature values")
        print("Time Displays: Show current time")
        print("\nPress Ctrl+C to stop monitoring")
        
        monitor.start_monitoring(update_interval=1.0)
        
        try:
            # Keep running until interrupted
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitoring...")
            monitor.stop_monitoring()
            print("✅ Monitoring stopped successfully!")


if __name__ == "__main__":
    main()
