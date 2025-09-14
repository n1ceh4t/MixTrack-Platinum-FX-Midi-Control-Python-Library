#!/usr/bin/env python3
"""
Basic Usage Example - Simple demonstration of MixtrackPlatinumFX library.

This example shows basic LED control, ring light control, and display control.
"""

import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mixtrack_platinum_fx import create_controller, LEDType, RingType


def main():
    """Basic usage example"""
    print("🎛️ MixtrackPlatinumFX Basic Usage Example")
    print("=" * 50)
    
    # Create controller with debug output
    with create_controller(debug=True) as controller:
        print("✅ Controller connected successfully!")
        
        # Example 1: LED Control
        print("\n1. LED Control Examples:")
        print("-" * 30)
        
        # Flash hotcue LEDs on deck 1
        print("Flashing hotcue LEDs on deck 1...")
        controller.set_led(1, LEDType.HOTCUE, True)
        time.sleep(1)
        controller.set_led(1, LEDType.HOTCUE, False)
        
        # Flash autoloop LEDs on deck 2
        print("Flashing autoloop LEDs on deck 2...")
        controller.set_led(2, LEDType.AUTOLOOP, True)
        time.sleep(1)
        controller.set_led(2, LEDType.AUTOLOOP, False)
        
        # Flash BPM arrows
        print("Flashing BPM arrows...")
        controller.set_led(1, LEDType.BPM_UP, True)
        controller.set_led(1, LEDType.BPM_DOWN, True)
        time.sleep(1)
        controller.set_led(1, LEDType.BPM_UP, False)
        controller.set_led(1, LEDType.BPM_DOWN, False)
        
        # Example 2: Ring Light Control
        print("\n2. Ring Light Control Examples:")
        print("-" * 30)
        
        # Set ring lights to different positions
        print("Setting ring lights...")
        controller.set_ring_percentage(1, RingType.SPINNER, 25.0)  # 25% red ring
        controller.set_ring_percentage(1, RingType.POSITION, 75.0)  # 75% white ring
        time.sleep(2)
        
        controller.set_ring_percentage(2, RingType.SPINNER, 50.0)  # 50% red ring
        controller.set_ring_percentage(2, RingType.POSITION, 100.0)  # 100% white ring
        time.sleep(2)
        
        # Clear ring lights
        print("Clearing ring lights...")
        controller.clear_rings(1)
        controller.clear_rings(2)
        
        # Example 3: Display Control
        print("\n3. Display Control Examples:")
        print("-" * 30)
        
        # Set BPM displays
        print("Setting BPM displays...")
        controller.set_bpm_display(1, 128.5)
        controller.set_bpm_display(2, 140.0)
        time.sleep(2)
        
        # Set time displays
        print("Setting time displays...")
        controller.set_current_time_display(1)
        controller.set_current_time_display(2)
        time.sleep(2)
        
        # Example 4: Flash All LEDs
        print("\n4. Flash All LEDs Example:")
        print("-" * 30)
        
        print("Flashing all LEDs on both decks...")
        controller.flash_all_leds(1, True)
        controller.flash_all_leds(2, True)
        time.sleep(2)
        
        print("Turning off all LEDs...")
        controller.flash_all_leds(1, False)
        controller.flash_all_leds(2, False)
        
        print("\n✅ Basic usage example completed!")
        print("All LEDs and rings should now be off.")


if __name__ == "__main__":
    main()
