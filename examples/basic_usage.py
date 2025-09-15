#!/usr/bin/env python3
"""
Basic Usage Example - Simple demonstration of MixtrackPlatinumFX library.

This example demonstrates the fundamental features of the MixtrackPlatinumFX controller:
- LED control (individual and group control)
- Ring light control (spinner and position rings)
- Display control (BPM, time, and rate displays)
- VU meter control
- Button LED feedback

Perfect for getting started with the library!
"""

import time
import os
import sys
import signal
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mixtrack_platinum_fx import create_controller, LEDType, RingType


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down...")
    sys.exit(0)


def demo_led_control(controller):
    """Demonstrate LED control functionality"""
    print("\n💡 LED Control Examples")
    print("-" * 40)
    
    # Basic LED control
    print("  • Flashing hotcue LEDs on deck 1...")
    controller.set_led(1, LEDType.HOTCUE, True)
    time.sleep(1)
    controller.set_led(1, LEDType.HOTCUE, False)
    
    print("  • Flashing autoloop LEDs on deck 2...")
    controller.set_led(2, LEDType.AUTOLOOP, True)
    time.sleep(1)
    controller.set_led(2, LEDType.AUTOLOOP, False)
    
    # Multiple LEDs
    print("  • Flashing BPM control LEDs...")
    controller.set_led(1, LEDType.BPM_UP, True)
    controller.set_led(1, LEDType.BPM_DOWN, True)
    time.sleep(1)
    controller.set_led(1, LEDType.BPM_UP, False)
    controller.set_led(1, LEDType.BPM_DOWN, False)
    
    # FX button LEDs
    print("  • Testing FX button LEDs...")
    controller.set_fx_button_led(0, True)  # FX1
    controller.set_fx_button_led(1, True)  # FX2
    time.sleep(1)
    controller.clear_all_fx_leds()


def demo_ring_control(controller):
    """Demonstrate ring light control functionality"""
    print("\n💍 Ring Light Control Examples")
    print("-" * 40)
    
    # Individual ring control
    print("  • Setting deck 1 rings (25% red, 75% white)...")
    controller.set_ring_percentage(1, RingType.SPINNER, 25.0)
    controller.set_ring_percentage(1, RingType.POSITION, 75.0)
    time.sleep(2)
    
    print("  • Setting deck 2 rings (50% red, 100% white)...")
    controller.set_ring_percentage(2, RingType.SPINNER, 50.0)
    controller.set_ring_percentage(2, RingType.POSITION, 100.0)
    time.sleep(2)
    
    # Clear rings
    print("  • Clearing all rings...")
    controller.clear_rings(1)
    controller.clear_rings(2)


def demo_display_control(controller):
    """Demonstrate display control functionality"""
    print("\n📊 Display Control Examples")
    print("-" * 40)
    
    # BPM displays
    print("  • Setting BPM displays (128.5, 140.0)...")
    controller.set_bpm_display(1, 128.5)
    controller.set_bpm_display(2, 140.0)
    time.sleep(2)
    
    # Time displays
    print("  • Setting time displays...")
    controller.set_current_time_display(1)
    controller.set_current_time_display(2)
    time.sleep(2)
    
    # Rate displays (jogger displays)
    print("  • Setting rate displays (45.2%, 67.8%)...")
    controller.set_rate_display(1, 45.2)
    controller.set_rate_display(2, 67.8)
    time.sleep(2)


def demo_vu_meter_control(controller):
    """Demonstrate VU meter control functionality"""
    print("\n📈 VU Meter Control Examples")
    print("-" * 40)
    
    # VU meter patterns
    print("  • Testing VU meter levels...")
    levels = [0, 25, 50, 75, 90, 75, 50, 25, 0]
    
    for level in levels:
        controller.set_vu_meter(1, level)
        controller.set_vu_meter(2, level)
        time.sleep(0.3)
    
    # Alternating pattern
    print("  • Alternating VU meter pattern...")
    for i in range(5):
        controller.set_vu_meter(1, 80)
        controller.set_vu_meter(2, 0)
        time.sleep(0.3)
        controller.set_vu_meter(1, 0)
        controller.set_vu_meter(2, 80)
        time.sleep(0.3)
    
    # Clear VU meters
    controller.clear_all_vu_meters()


def demo_button_feedback(controller):
    """Demonstrate button LED feedback functionality"""
    print("\n🎮 Button LED Feedback Demo")
    print("-" * 40)
    
    # Start MIDI input handling
    controller.start()
    print("  • Button LED feedback enabled!")
    print("  • Press any button on the controller to see LED feedback")
    print("  • Press Ctrl+C to continue...")
    
    try:
        # Let user test button feedback
        while True:
            controller.process_midi_events()
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("  • Continuing to next demo...")


def demo_all_leds(controller):
    """Demonstrate all LEDs functionality"""
    print("\n🌟 All LEDs Demo")
    print("-" * 40)
    
    print("  • Turning on ALL LEDs on both decks...")
    controller.flash_all_leds(1, True)
    controller.flash_all_leds(2, True)
    time.sleep(2)
    
    print("  • Turning off all LEDs...")
    controller.flash_all_leds(1, False)
    controller.flash_all_leds(2, False)


def cleanup(controller):
    """Clean up controller state"""
    print("\n🧹 Cleanup")
    print("-" * 40)
    
    print("  • Clearing all LEDs...")
    controller.clear_all_leds()
    controller.clear_all_fx_leds()
    
    print("  • Clearing all rings...")
    controller.clear_rings(1)
    controller.clear_rings(2)
    
    print("  • Clearing VU meters...")
    controller.clear_all_vu_meters()
    
    print("  • Controller cleaned up!")


def main():
    """Main function - run all demos"""
    print("🎛️ MixtrackPlatinumFX Basic Usage Example")
    print("=" * 60)
    print("This example demonstrates the core features of the controller:")
    print("• LED control (individual and group)")
    print("• Ring light control (spinner and position)")
    print("• Display control (BPM, time, rate)")
    print("• VU meter control")
    print("• Button LED feedback")
    print()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create controller with debug output
        with create_controller(debug=True) as controller:
            print("✅ Controller connected successfully!")
            
            # Run all demos
            demo_led_control(controller)
            demo_ring_control(controller)
            demo_display_control(controller)
            demo_vu_meter_control(controller)
            demo_button_feedback(controller)
            demo_all_leds(controller)
            cleanup(controller)
            
            print("\n🎉 Basic usage example completed successfully!")
            print("All controller features have been demonstrated.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
