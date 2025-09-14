#!/usr/bin/env python3
"""
EasyEffects Control Example - Audio effects control with MixtrackPlatinumFX.

This example shows how to use the EasyEffects integration to control
audio effects and equalizer settings.
"""

import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mixtrack_platinum_fx import create_controller
from easyeffects_control import create_easyeffects_control, EffectPreset


def main():
    """EasyEffects control example"""
    print("🎵 MixtrackPlatinumFX EasyEffects Control Example")
    print("=" * 50)
    
    # Create controller
    with create_controller(debug=True) as controller:
        print("✅ Controller connected successfully!")
        
        # Create EasyEffects control
        effects = create_easyeffects_control(controller, debug=True)
        
        # Add preset callback
        def preset_callback(preset_name, preset):
            """Handle preset changes"""
            print(f"🎵 Preset applied: {preset.name}")
            if preset.description:
                print(f"   Description: {preset.description}")
        
        effects.register_preset_callback("main", preset_callback)
        
        print("\n🎵 Available presets:")
        for name in effects.get_available_presets():
            preset = effects.presets[name]
            print(f"  - {name}: {preset.description or 'No description'}")
        
        # Example 1: Toggle EasyEffects
        print("\n1. Toggle EasyEffects:")
        print("-" * 30)
        
        print("Turning EasyEffects ON...")
        effects.toggle_effects()
        time.sleep(2)
        
        print("Turning EasyEffects OFF...")
        effects.toggle_effects()
        time.sleep(2)
        
        # Example 2: Apply Presets
        print("\n2. Apply Effect Presets:")
        print("-" * 30)
        
        # Apply gaming preset
        print("Applying Gaming preset...")
        effects.apply_preset("gaming")
        time.sleep(3)
        
        # Apply music preset
        print("Applying Music preset...")
        effects.apply_preset("music")
        time.sleep(3)
        
        # Apply voice preset
        print("Applying Voice preset...")
        effects.apply_preset("voice")
        time.sleep(3)
        
        # Apply flat preset (no effects)
        print("Applying Flat preset (no effects)...")
        effects.apply_preset("flat")
        time.sleep(2)
        
        # Example 3: EQ Control
        print("\n3. Equalizer Control:")
        print("-" * 30)
        
        # Turn on EasyEffects and apply gaming preset first
        effects.toggle_effects()
        effects.apply_preset("gaming")
        
        print("Adjusting EQ bands...")
        
        # Boost sub-bass (60Hz)
        effects.set_eq_band(0, 3.0, 60.0)
        time.sleep(1)
        
        # Boost bass (250Hz)
        effects.set_eq_band(1, 2.0, 250.0)
        time.sleep(1)
        
        # Cut mid-range (2kHz)
        effects.set_eq_band(4, -2.0, 2000.0)
        time.sleep(1)
        
        # Boost presence (8kHz)
        effects.set_eq_band(8, 1.5, 8000.0)
        time.sleep(1)
        
        # Example 4: Compressor Control
        print("\n4. Compressor Control:")
        print("-" * 30)
        
        print("Adjusting compressor threshold...")
        effects.set_compressor_threshold(-12.0)
        time.sleep(1)
        
        effects.set_compressor_threshold(-6.0)
        time.sleep(1)
        
        effects.set_compressor_threshold(-18.0)
        time.sleep(1)
        
        # Example 5: Reverb Control
        print("\n5. Reverb Control:")
        print("-" * 30)
        
        print("Adjusting reverb room size...")
        effects.set_reverb_room_size(0.2)
        time.sleep(1)
        
        effects.set_reverb_room_size(0.5)
        time.sleep(1)
        
        effects.set_reverb_room_size(0.8)
        time.sleep(1)
        
        # Example 6: Create Custom Preset
        print("\n6. Custom Preset:")
        print("-" * 30)
        
        # Create a custom preset
        custom_preset = EffectPreset(
            name="Custom",
            effects={
                "compressor": True,
                "equalizer": True,
                "limiter": True,
                "crystalizer": True,
                "bassenhancer": True
            },
            description="Custom preset with enhanced bass and clarity"
        )
        
        effects.add_preset("custom", custom_preset)
        print("Created custom preset")
        
        # Apply custom preset
        print("Applying custom preset...")
        effects.apply_preset("custom")
        time.sleep(3)
        
        # Clean up
        print("\n7. Cleanup:")
        print("-" * 30)
        
        print("Disabling all effects...")
        effects.disable_all_effects()
        time.sleep(1)
        
        print("Turning off EasyEffects...")
        effects.toggle_effects()
        
        print("\n✅ EasyEffects control example completed!")
        print("All effects should now be disabled.")


if __name__ == "__main__":
    main()
