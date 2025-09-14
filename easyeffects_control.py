#!/usr/bin/env python3
"""
EasyEffects Control - Integration module for EasyEffects audio processing with MixtrackPlatinumFX.

This module provides EasyEffects control capabilities that integrate with the
MixtrackPlatinumFX controller for real-time audio effects control.
"""

import subprocess
import json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from mixtrack_platinum_fx import MixtrackPlatinumFX, LEDType


@dataclass
class EffectPreset:
    """Audio effect preset configuration"""
    name: str
    effects: Dict[str, bool]
    description: Optional[str] = None


@dataclass
class EQBand:
    """Equalizer band configuration"""
    frequency: float
    gain: float
    q_factor: float = 1.0


class EasyEffectsControl:
    """
    EasyEffects control class that integrates with MixtrackPlatinumFX.
    
    Provides real-time audio effects control including EQ, compression, reverb, etc.
    """
    
    def __init__(self, 
                 controller: MixtrackPlatinumFX,
                 presets: Optional[Dict[str, EffectPreset]] = None,
                 debug: bool = False):
        """
        Initialize EasyEffects control.
        
        Args:
            controller: MixtrackPlatinumFX controller instance
            presets: Dictionary of effect presets
            debug: Enable debug output
        """
        self.controller = controller
        self.debug = debug
        
        # Default presets
        self.presets = presets or self._get_default_presets()
        
        # Current state
        self.current_preset: Optional[str] = None
        self.effects_enabled = False
        
        # Available effects
        self.available_effects = [
            "autogain", "bassenhancer", "compressor", "convolver", "crossfeed",
            "crystalizer", "deesser", "delay", "equalizer", "exciter", "filter",
            "gate", "limiter", "loudness", "maximizer", "multibandcompressor",
            "multibandgate", "pitch", "reverb", "stereotools", "echocanceller"
        ]
        
        # Effects that work on both input and output
        self.bidirectional_effects = [
            "compressor", "deesser", "equalizer", "filter", "gate",
            "limiter", "multibandcompressor", "multibandgate", "pitch", "reverb", "echocanceller"
        ]
        
        # Callbacks
        self.preset_callbacks: Dict[str, Callable] = {}
        
        if self.debug:
            print("EasyEffectsControl initialized")
            print(f"Available presets: {list(self.presets.keys())}")
    
    def _get_default_presets(self) -> Dict[str, EffectPreset]:
        """Get default effect presets"""
        return {
            "gaming": EffectPreset(
                name="Gaming",
                effects={
                    "compressor": True,
                    "equalizer": True,
                    "limiter": True,
                    "bassenhancer": True
                },
                description="Enhanced bass and compression for gaming"
            ),
            "music": EffectPreset(
                name="Music",
                effects={
                    "compressor": True,
                    "equalizer": True,
                    "reverb": True,
                    "crystalizer": True
                },
                description="Music enhancement with reverb and clarity"
            ),
            "voice": EffectPreset(
                name="Voice",
                effects={
                    "compressor": True,
                    "deesser": True,
                    "gate": True,
                    "echocanceller": True
                },
                description="Voice optimization with noise reduction"
            ),
            "flat": EffectPreset(
                name="Flat",
                effects={},
                description="No effects - flat response"
            )
        }
    
    def toggle_effects(self) -> bool:
        """
        Toggle EasyEffects on/off.
        
        Returns:
            True if effects are now enabled, False if disabled
        """
        try:
            # Get current state
            result = subprocess.run(
                ["gsettings", "get", "com.github.wwmm.easyeffects", "enable-all-streaminputs"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                current_state = result.stdout.strip()
                new_state = "false" if current_state == "true" else "true"
                
                # Set new state
                subprocess.run([
                    "gsettings", "set", "com.github.wwmm.easyeffects", 
                    "enable-all-streaminputs", new_state
                ])
                
                self.effects_enabled = (new_state == "true")
                
                if self.debug:
                    status = "ON" if self.effects_enabled else "OFF"
                    print(f"🎵 EasyEffects {status}")
                
                return self.effects_enabled
            else:
                if self.debug:
                    print("❌ EasyEffects not found or gsettings error")
                return False
                
        except Exception as e:
            if self.debug:
                print(f"Error toggling EasyEffects: {e}")
            return False
    
    def apply_preset(self, preset_name: str) -> bool:
        """
        Apply an effect preset.
        
        Args:
            preset_name: Name of the preset to apply
            
        Returns:
            True if preset applied successfully, False otherwise
        """
        if preset_name not in self.presets:
            if self.debug:
                print(f"❌ Preset '{preset_name}' not found")
            return False
        
        try:
            preset = self.presets[preset_name]
            
            if self.debug:
                print(f"🎵 Applying preset: {preset.name}")
            
            # First disable all effects
            self.disable_all_effects()
            
            # Enable specified effects
            for effect, enabled in preset.effects.items():
                if enabled and effect in self.available_effects:
                    self._enable_effect(effect)
            
            self.current_preset = preset_name
            
            # Call preset callbacks
            for callback_name, callback in self.preset_callbacks.items():
                try:
                    callback(preset_name, preset)
                except Exception as e:
                    if self.debug:
                        print(f"Preset callback {callback_name} error: {e}")
            
            if self.debug:
                print(f"🎵 Preset '{preset.name}' applied successfully")
            
            return True
            
        except Exception as e:
            if self.debug:
                print(f"Error applying preset: {e}")
            return False
    
    def _enable_effect(self, effect: str):
        """Enable a specific effect"""
        try:
            # Enable for stream outputs (playback)
            subprocess.run([
                "gsettings", "set", 
                f"com.github.wwmm.easyeffects.{effect}:/com/github/wwmm/easyeffects/streamoutputs/{effect}/",
                "state", "true"
            ], capture_output=True)
            
            # Enable for stream inputs (recording) if applicable
            if effect in self.bidirectional_effects:
                subprocess.run([
                    "gsettings", "set", 
                    f"com.github.wwmm.easyeffects.{effect}:/com/github/wwmm/easyeffects/streaminputs/{effect}/",
                    "state", "true"
                ], capture_output=True)
            
            if self.debug:
                print(f"  ✅ Enabled {effect}")
                
        except Exception as e:
            if self.debug:
                print(f"  ❌ Error enabling {effect}: {e}")
    
    def _disable_effect(self, effect: str):
        """Disable a specific effect"""
        try:
            # Disable for stream outputs
            subprocess.run([
                "gsettings", "set", 
                f"com.github.wwmm.easyeffects.{effect}:/com/github/wwmm/easyeffects/streamoutputs/{effect}/",
                "state", "false"
            ], capture_output=True)
            
            # Disable for stream inputs if applicable
            if effect in self.bidirectional_effects:
                subprocess.run([
                    "gsettings", "set", 
                    f"com.github.wwmm.easyeffects.{effect}:/com/github/wwmm/easyeffects/streaminputs/{effect}/",
                    "state", "false"
                ], capture_output=True)
                
        except Exception as e:
            if self.debug:
                print(f"Error disabling {effect}: {e}")
    
    def disable_all_effects(self):
        """Disable all EasyEffects"""
        try:
            for effect in self.available_effects:
                self._disable_effect(effect)
            
            if self.debug:
                print("  🔇 All EasyEffects disabled")
                
        except Exception as e:
            if self.debug:
                print(f"Error disabling all effects: {e}")
    
    def set_eq_band(self, band: int, gain: float, frequency: Optional[float] = None):
        """
        Set equalizer band gain.
        
        Args:
            band: Band number (0-9)
            gain: Gain value in dB (-20 to +20)
            frequency: Frequency in Hz (optional, for logging)
        """
        try:
            # Clamp gain to valid range
            gain = max(-20.0, min(20.0, gain))
            
            # Set EQ band gain
            subprocess.run([
                "gsettings", "set",
                f"com.github.wwmm.easyeffects.equalizer:/com/github/wwmm/easyeffects/streamoutputs/equalizer/",
                f"band{band}-gain", str(gain)
            ], capture_output=True)
            
            if self.debug:
                freq_str = f" @ {frequency}Hz" if frequency else ""
                print(f"🎛️ EQ Band {band}: {gain:+.1f}dB{freq_str}")
                
        except Exception as e:
            if self.debug:
                print(f"Error setting EQ band {band}: {e}")
    
    def set_compressor_threshold(self, threshold: float):
        """
        Set compressor threshold.
        
        Args:
            threshold: Threshold value in dB (-60 to 0)
        """
        try:
            # Clamp threshold to valid range
            threshold = max(-60.0, min(0.0, threshold))
            
            subprocess.run([
                "gsettings", "set",
                "com.github.wwmm.easyeffects.compressor:/com/github/wwmm/easyeffects/streamoutputs/compressor/",
                "threshold", str(threshold)
            ], capture_output=True)
            
            if self.debug:
                print(f"🎛️ Compressor threshold: {threshold:.1f}dB")
                
        except Exception as e:
            if self.debug:
                print(f"Error setting compressor threshold: {e}")
    
    def set_reverb_room_size(self, room_size: float):
        """
        Set reverb room size.
        
        Args:
            room_size: Room size (0.0 to 1.0)
        """
        try:
            # Clamp room size to valid range
            room_size = max(0.0, min(1.0, room_size))
            
            subprocess.run([
                "gsettings", "set",
                "com.github.wwmm.easyeffects.reverb:/com/github/wwmm/easyeffects/streamoutputs/reverb/",
                "room-size", str(room_size)
            ], capture_output=True)
            
            if self.debug:
                print(f"🎛️ Reverb room size: {room_size:.2f}")
                
        except Exception as e:
            if self.debug:
                print(f"Error setting reverb room size: {e}")
    
    def get_current_preset(self) -> Optional[str]:
        """Get the currently applied preset name"""
        return self.current_preset
    
    def get_available_presets(self) -> List[str]:
        """Get list of available preset names"""
        return list(self.presets.keys())
    
    def add_preset(self, name: str, preset: EffectPreset):
        """
        Add a new preset.
        
        Args:
            name: Preset name
            preset: EffectPreset object
        """
        self.presets[name] = preset
        if self.debug:
            print(f"Added preset: {name}")
    
    def remove_preset(self, name: str):
        """
        Remove a preset.
        
        Args:
            name: Preset name to remove
        """
        if name in self.presets:
            del self.presets[name]
            if self.debug:
                print(f"Removed preset: {name}")
    
    def register_preset_callback(self, name: str, callback: Callable):
        """
        Register a preset callback.
        
        Args:
            name: Unique name for the callback
            callback: Function to call when presets are applied
        """
        self.preset_callbacks[name] = callback
    
    def unregister_preset_callback(self, name: str):
        """Unregister a preset callback"""
        if name in self.preset_callbacks:
            del self.preset_callbacks[name]
    
    def save_presets_to_file(self, filename: str):
        """
        Save presets to a JSON file.
        
        Args:
            filename: Path to save presets
        """
        try:
            presets_data = {}
            for name, preset in self.presets.items():
                presets_data[name] = {
                    'name': preset.name,
                    'effects': preset.effects,
                    'description': preset.description
                }
            
            with open(filename, 'w') as f:
                json.dump(presets_data, f, indent=2)
            
            if self.debug:
                print(f"Presets saved to {filename}")
                
        except Exception as e:
            if self.debug:
                print(f"Error saving presets: {e}")
    
    def load_presets_from_file(self, filename: str):
        """
        Load presets from a JSON file.
        
        Args:
            filename: Path to load presets from
        """
        try:
            with open(filename, 'r') as f:
                presets_data = json.load(f)
            
            self.presets = {}
            for name, data in presets_data.items():
                self.presets[name] = EffectPreset(
                    name=data['name'],
                    effects=data['effects'],
                    description=data.get('description')
                )
            
            if self.debug:
                print(f"Presets loaded from {filename}")
                
        except Exception as e:
            if self.debug:
                print(f"Error loading presets: {e}")


# Convenience functions

def create_easyeffects_control(controller: MixtrackPlatinumFX,
                              presets: Optional[Dict[str, EffectPreset]] = None,
                              debug: bool = False) -> EasyEffectsControl:
    """
    Create an EasyEffects control instance.
    
    Args:
        controller: MixtrackPlatinumFX controller instance
        presets: Dictionary of effect presets
        debug: Enable debug output
        
    Returns:
        EasyEffectsControl instance
    """
    return EasyEffectsControl(controller, presets, debug)


if __name__ == "__main__":
    # Example usage
    from mixtrack_platinum_fx import create_controller
    
    with create_controller(debug=True) as controller:
        # Create EasyEffects control
        effects = create_easyeffects_control(controller, debug=True)
        
        # Add preset callback
        def preset_callback(preset_name, preset):
            print(f"Preset applied: {preset.name} - {preset.description}")
        
        effects.register_preset_callback("test", preset_callback)
        
        # Test presets
        print("Available presets:", effects.get_available_presets())
        
        # Apply gaming preset
        effects.apply_preset("gaming")
        
        # Test EQ control
        effects.set_eq_band(0, 3.0, 60.0)  # Boost sub-bass
        effects.set_eq_band(4, -2.0, 2000.0)  # Cut mid-range
        
        # Test compressor
        effects.set_compressor_threshold(-12.0)
        
        # Test reverb
        effects.set_reverb_room_size(0.3)
        
        print("EasyEffects control example completed!")
