#!/usr/bin/env python3
"""
VU Meter Control - VU meter control script for Mixtrack Platinum FX

This script demonstrates VU meter control functionality on the Mixtrack Platinum FX.
VU meters are controlled using MIDI Control Change messages with:
- Control Number: 31 (0x1F)
- Value Range: 0-90 (0x00-0x5A)
- Channels: 0 (Deck 1), 1 (Deck 2)

The script provides various VU meter patterns and simulations including:
- Basic level control
- Pattern sequences
- Audio simulation scenarios
- Random patterns
- Breathing effects
- Peak hold simulation
"""

import sys
import os
import time
import math
import random
import signal

# Add the parent directory to the path to import the library
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mixtrack_platinum_fx import create_controller


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down...")
    sys.exit(0)

# VU Meter controller now uses the built-in controller methods
# No need for custom implementation

def test_basic_vu_control(controller):
    """Test basic VU meter control"""
    print("📊 Testing Basic VU Meter Control")
    print("-" * 50)
    
    # Test different levels
    levels = [0, 25, 50, 75, 90, 75, 50, 25, 0]
    
    for deck in [1, 2]:
        print(f"  Testing Deck {deck}...")
        for level in levels:
            controller.set_vu_meter(deck, level)
            time.sleep(0.5)
        time.sleep(0.5)
    
    print("✅ Basic VU meter control test completed\n")

def test_vu_patterns(controller):
    """Test VU meter patterns"""
    print("🎨 Testing VU Meter Patterns")
    print("-" * 50)
    
    # Pattern 1: Alternating decks
    print("  Pattern 1: Alternating Decks")
    for i in range(5):
        controller.set_vu_meter(1, 80)
        controller.set_vu_meter(2, 0)
        time.sleep(0.3)
        controller.set_vu_meter(1, 0)
        controller.set_vu_meter(2, 80)
        time.sleep(0.3)
    
    # Pattern 2: Symmetric levels
    print("  Pattern 2: Symmetric Levels")
    symmetric_levels = [0, 20, 40, 60, 80, 60, 40, 20, 0]
    for level in symmetric_levels:
        controller.set_vu_meter(1, level)
        controller.set_vu_meter(2, level)
        time.sleep(0.4)
    
    # Pattern 3: Wave pattern
    print("  Pattern 3: Wave Pattern")
    for i in range(20):
        # Create a wave pattern
        wave1 = int(45 + 35 * math.sin(i * 0.3))
        wave2 = int(45 + 35 * math.cos(i * 0.3))
        controller.set_vu_meter(1, wave1)
        controller.set_vu_meter(2, wave2)
        time.sleep(0.1)
    
    print("✅ VU meter patterns test completed\n")

def test_vu_simulation(controller):
    """Test VU meter simulation with audio-like patterns"""
    print("🎵 Testing VU Meter Simulation")
    print("-" * 50)
    
    # Simulate different audio scenarios
    scenarios = [
        ("Silence", 0, 0),
        ("Low Level", 15, 20),
        ("Medium Level", 40, 45),
        ("High Level", 70, 75),
        ("Peak", 85, 90),
        ("Beat Pattern", None, None),  # Special case
    ]
    
    for scenario_name, deck1_level, deck2_level in scenarios:
        print(f"  Scenario: {scenario_name}")
        
        if scenario_name == "Beat Pattern":
            # Simulate beat pattern
            for beat in range(16):
                if beat % 4 == 0:  # Strong beat
                    controller.set_vu_meter(1, 80)
                    controller.set_vu_meter(2, 75)
                elif beat % 2 == 0:  # Medium beat
                    controller.set_vu_meter(1, 50)
                    controller.set_vu_meter(2, 45)
                else:  # Weak beat
                    controller.set_vu_meter(1, 25)
                    controller.set_vu_meter(2, 20)
                time.sleep(0.2)
        else:
            controller.set_vu_meter(1, deck1_level)
            controller.set_vu_meter(2, deck2_level)
            time.sleep(2)
    
    print("✅ VU meter simulation test completed\n")

def test_vu_random_patterns(controller):
    """Test random VU meter patterns"""
    print("🎲 Testing Random VU Meter Patterns")
    print("-" * 50)
    
    # Random levels for both decks
    for i in range(30):
        level1 = random.randint(0, 90)
        level2 = random.randint(0, 90)
        controller.set_vu_meter(1, level1)
        controller.set_vu_meter(2, level2)
        time.sleep(0.2)
    
    print("✅ Random VU meter patterns test completed\n")

def test_vu_breathing_effect(controller):
    """Test breathing effect on VU meters"""
    print("🫁 Testing VU Meter Breathing Effect")
    print("-" * 50)
    
    # Create breathing effect
    for cycle in range(3):
        print(f"  Breathing cycle {cycle + 1}/3")
        for i in range(50):
            # Create smooth breathing pattern
            breath = (math.sin(i * 0.2) + 1) / 2  # 0 to 1
            level = int(breath * 80)  # 0 to 80
            
            controller.set_vu_meter(1, level)
            controller.set_vu_meter(2, level)
            time.sleep(0.05)
    
    print("✅ VU meter breathing effect test completed\n")

def test_vu_peak_hold(controller):
    """Test peak hold effect"""
    print("📈 Testing VU Meter Peak Hold")
    print("-" * 50)
    
    # Simulate peak hold behavior
    peaks = [30, 50, 70, 85, 90, 75, 60, 40, 20, 0]
    
    for peak in peaks:
        print(f"  Peak: {peak}/90")
        controller.set_vu_meter(1, peak)
        controller.set_vu_meter(2, peak)
        time.sleep(0.8)
    
    print("✅ VU meter peak hold test completed\n")

def run_vu_meter_tests():
    """Run all VU meter tests"""
    print("📊 Mixtrack Platinum FX - VU Meter Control Test")
    print("=" * 60)
    print("This script tests VU meter control functionality.")
    print("VU meters use MIDI CC 31 with values 0-90.")
    print()
    
    try:
        # Create controller instance using the new API
        with create_controller(debug=True) as controller:
            print("✅ Controller connected successfully")
            print()
            
            # Clear all VU meters first
            controller.clear_all_vu_meters()
            time.sleep(0.5)
            
            # Run all tests
            test_basic_vu_control(controller)
            test_vu_patterns(controller)
            test_vu_simulation(controller)
            test_vu_random_patterns(controller)
            test_vu_breathing_effect(controller)
            test_vu_peak_hold(controller)
            
            # Final cleanup
            print("🧹 Final Cleanup")
            print("-" * 50)
            controller.clear_all_vu_meters()
            print("✅ All VU meters cleared")
            
            print("\n🎉 VU meter control test completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("📊 Mixtrack Platinum FX - VU Meter Control")
    print("=" * 60)
    print("This script demonstrates VU meter control functionality:")
    print()
    print("VU Meter Control:")
    print("• Control Number: 31 (0x1F)")
    print("• Value Range: 0-90 (0x00-0x5A)")
    print("• Deck 1: Channel 0")
    print("• Deck 2: Channel 1")
    print()
    print("Test Patterns:")
    print("• Basic level control")
    print("• Pattern sequences")
    print("• Audio simulation")
    print("• Random patterns")
    print("• Breathing effects")
    print("• Peak hold simulation")
    print()
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python3 vu_meter_control.py")
        print()
        print("This script will:")
        print("1. Connect to the Mixtrack Platinum FX controller")
        print("2. Test basic VU meter control")
        print("3. Test various VU meter patterns")
        print("4. Test audio simulation scenarios")
        print("5. Test random and breathing effects")
        print("6. Clean up and disconnect")
        print()
        print("Make sure your controller is connected before running!")
        return
    
    # Ask for confirmation
    try:
        response = input("Ready to start VU meter testing? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Testing cancelled.")
            return
    except KeyboardInterrupt:
        print("\nTesting cancelled.")
        return
    
    # Run the tests
    success = run_vu_meter_tests()
    
    if success:
        print("\n✅ All VU meter tests completed successfully!")
        print("Your controller's VU meter functionality is working properly.")
        sys.exit(0)
    else:
        print("\n❌ Some VU meter tests failed!")
        print("Check the error messages above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
