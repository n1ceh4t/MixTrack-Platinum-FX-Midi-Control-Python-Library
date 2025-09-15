# MixtrackPlatinumFX Python Library

A comprehensive Python library for controlling the Numark Mixtrack Platinum FX controller. This library provides complete control over all hardware features including LEDs, ring lights, displays, system monitoring, and audio effects control.

## 🎛️ Features

### Core Hardware Control
- **LED Control**: Control over button LEDs (hotcues, autoloops, loops, play, sync, cue, BPM arrows, keylock, wheel buttons, slip indicators)
- **Ring Light Control**: Spinner and position ring control with percentage-based positioning
- **Display Control**: BPM displays, time displays, and jogger displays (rate displays)
- **MIDI Input Handling**: Real-time MIDI message processing with callback system

### System Integration
- **System Monitoring**: Real-time CPU usage, memory usage, temperature monitoring with visual alerts
- **EasyEffects Integration**: Complete audio effects control including EQ, compression, reverb, and presets
- **Configuration Management**: JSON-based configuration with hot-reload support

### Advanced Features
- **Threading**: Non-blocking MIDI input handling
- **Context Manager**: Easy connection management with automatic cleanup
- **Callback System**: Extensible callback system for MIDI events and alerts
- **Error Handling**: Comprehensive error handling with graceful degradation

## 📦 Installation

### Prerequisites
- Python 3.7+
- Numark Mixtrack Platinum FX controller
- Linux system with PulseAudio
- EasyEffects (for audio effects control)

### Dependencies
```bash
pip install mido psutil
```

### Optional Dependencies
- `sensors` command (for temperature monitoring)
- `nvidia-smi` (for NVIDIA GPU temperature)
- `amdgpu` drivers (for AMD GPU temperature)

## 🚀 Quick Start

### Basic Usage
```python
from mixtrack_platinum_fx import create_controller, LEDType, RingType

# Create and connect to controller
with create_controller(debug=False) as controller:
    # Flash hotcue LEDs
    controller.set_led(1, LEDType.HOTCUE, True)
    
    # Set ring lights
    controller.set_ring_percentage(1, RingType.SPINNER, 50.0)
    
    # Set BPM display
    controller.set_bpm_display(1, 128.5)
    
    # Set jogger display
    controller.set_rate_display(1, 45.2)  # Show 45.2% on jogger
```

### System Monitoring
```python
from mixtrack_platinum_fx import create_controller
from system_monitor import create_system_monitor, AlertThresholds

with create_controller() as controller:
    # Create system monitor
    thresholds = AlertThresholds(cpu_temp=75.0, gpu_temp=80.0)
    monitor = create_system_monitor(controller, thresholds)
    
    # Start monitoring
    monitor.start_monitoring(update_interval=1.0)
```

### EasyEffects Control
```python
from mixtrack_platinum_fx import create_controller
from easyeffects_control import create_easyeffects_control

with create_controller() as controller:
    # Create EasyEffects control
    effects = create_easyeffects_control(controller)
    
    # Apply preset
    effects.apply_preset("gaming")
    
    # Control EQ
    effects.set_eq_band(0, 3.0, 60.0)  # Boost sub-bass
```

## 📚 API Reference

### MixtrackPlatinumFX Class

#### Initialization
```python
controller = MixtrackPlatinumFX(
    input_port="MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0",
    output_port="MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0",
    config_file="config.json",
    debug=False
)
```

#### Connection Management
```python
# Connect to controller
controller.connect()

# Start MIDI input handling
controller.start()

# Stop and disconnect
controller.stop()
controller.disconnect()

# Context manager (recommended)
with controller:
    # Controller is automatically connected and started
    pass
```

#### LED Control
```python
# Set individual LEDs
controller.set_led(deck, LEDType.HOTCUE, True)
controller.set_led(deck, LEDType.AUTOLOOP, False)

# Flash all LEDs on a deck
controller.flash_all_leds(deck, True)

# Clear all LEDs
controller.clear_all_leds()
```

#### Ring Light Control
```python
# Set ring position (0-52)
controller.set_ring(deck, RingType.SPINNER, 25)

# Set ring position as percentage
controller.set_ring_percentage(deck, RingType.POSITION, 75.0)

# Clear rings
controller.clear_rings(deck)
```

#### Display Control
```python
# Set BPM display
controller.set_bpm_display(deck, 128.5)

# Set time display
controller.set_time_display(deck, time_ms)

# Set jogger display (rate display)
controller.set_rate_display(deck, rate_percent)

# Set current time
controller.set_current_time_display(deck)
```

#### MIDI Callbacks
```python
def my_callback(msg):
    print(f"Received MIDI: {msg}")

controller.register_midi_callback("my_callback", my_callback)
controller.unregister_midi_callback("my_callback")
```

### SystemMonitor Class

#### Initialization
```python
monitor = SystemMonitor(
    controller=controller,
    thresholds=AlertThresholds(cpu_temp=75.0, gpu_temp=80.0),
    cache_interval=0.5,
    debug=False
)
```

#### Monitoring Control
```python
# Start monitoring
monitor.start_monitoring(update_interval=1.0)

# Stop monitoring
monitor.stop_monitoring()

# Get current vitals
vitals = monitor.get_system_vitals()
```

#### Alert Callbacks
```python
def alert_callback(alerts):
    if alerts['cpu_temp_alert']:
        print("CPU temperature alert!")

monitor.register_alert_callback("cpu_alert", alert_callback)
```

### EasyEffectsControl Class

#### Initialization
```python
effects = EasyEffectsControl(
    controller=controller,
    presets=custom_presets,
    debug=False
)
```

#### Effect Control
```python
# Toggle EasyEffects
effects.toggle_effects()

# Apply preset
effects.apply_preset("gaming")

# Disable all effects
effects.disable_all_effects()
```

#### EQ Control
```python
# Set EQ band gain
effects.set_eq_band(band=0, gain=3.0, frequency=60.0)

# Set compressor threshold
effects.set_compressor_threshold(-12.0)

# Set reverb room size
effects.set_reverb_room_size(0.5)
```

#### Preset Management
```python
# Add custom preset
custom_preset = EffectPreset(
    name="Custom",
    effects={"compressor": True, "equalizer": True},
    description="Custom preset"
)
effects.add_preset("custom", custom_preset)

# Save/load presets
effects.save_presets_to_file("presets.json")
effects.load_presets_from_file("presets.json")
```

## 🎮 LED Types

The library supports all available LED types on the controller:

- `LEDType.HOTCUE` - Hotcue buttons 1-4
- `LEDType.HOTCUE_EXTENDED` - Hotcue buttons 5-8
- `LEDType.AUTOLOOP` - Auto-loop buttons 1-8
- `LEDType.LOOP` - Manual loop buttons
- `LEDType.PLAY` - Play/pause buttons
- `LEDType.SYNC` - Sync buttons
- `LEDType.CUE` - Cue buttons
- `LEDType.PFL_CUE` - PFL/Cue button
- `LEDType.BPM_UP` - BPM up arrow
- `LEDType.BPM_DOWN` - BPM down arrow
- `LEDType.KEYLOCK` - Keylock button
- `LEDType.WHEEL_BUTTON` - Jog wheel button
- `LEDType.SLIP` - Slip mode indicator

## 🎛️ Ring Types

- `RingType.SPINNER` - Red ring (spinner, CC 0x06)
- `RingType.POSITION` - White ring (position, CC 0x3F)

## ⚙️ Configuration

The library uses JSON configuration files for all settings:

```json
{
  "midi": {
    "input_port": "MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0",
    "output_port": "MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0"
  },
  "leds": {
    "channel_offset": 4,
    "hotcue_notes": [24, 25, 26, 27],
    "velocity_on": 127,
    "velocity_off": 0
  },
  "rings": {
    "spinner_control": 6,
    "position_control": 63,
    "spinner_offset": 64,
    "max_position": 52
  }
}
```

## Implementation Notes

### Channel Scheme

- Inputs: 0/1 (decks), 4/5 (pads/LED layer), 8/9 (FX)
- Outputs: 4/5 for deck LEDs (via `channel_offset`), 8/9 for FX
- The library centralizes routing so inputs on 0/1 are rendered on 4/5 automatically.

### LED Off Behavior

- LEDs are cleared using `note_on` with velocity `1` for reliable off state.

## 📁 Project Structure

```
Midi Control/
├── mixtrack_platinum_fx.py      # Core library
├── system_monitor.py            # System monitoring integration
├── easyeffects_control.py       # EasyEffects integration
├── config.json                  # Configuration file
├── examples/                    # Example scripts
│   ├── basic_usage.py
│   ├── system_monitoring.py
│   └── easyeffects_control.py
├── README.md                    # Main documentation
├── LIBRARY_README.md            # This file
```

## 🧪 Examples

### Basic LED Control
```python
from mixtrack_platinum_fx import create_controller, LEDType

with create_controller(debug=True) as controller:
    # Flash hotcue LEDs
    controller.set_led(1, LEDType.HOTCUE, True)
    time.sleep(1)
    controller.set_led(1, LEDType.HOTCUE, False)
```

### System Monitoring
```python
from mixtrack_platinum_fx import create_controller
from system_monitor import create_system_monitor, AlertThresholds

with create_controller() as controller:
    thresholds = AlertThresholds(cpu_temp=75.0, gpu_temp=80.0)
    monitor = create_system_monitor(controller, thresholds)
    monitor.start_monitoring(update_interval=1.0)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
```

### EasyEffects Control
```python
from mixtrack_platinum_fx import create_controller
from easyeffects_control import create_easyeffects_control

with create_controller() as controller:
    effects = create_easyeffects_control(controller)
    effects.apply_preset("gaming")
    effects.set_eq_band(0, 3.0, 60.0)  # Boost sub-bass
```

## 🐛 Troubleshooting

### Common Issues

#### Controller Not Detected
- Ensure controller is connected via USB
- Check MIDI port names in configuration
- Enable debug mode to see available ports

#### LEDs Not Working
- Some LEDs may require a controller reboot to work properly
- Check LED note numbers and channels in configuration
- Verify MIDI output port is correct

#### Temperature Shows 0°C
- Install `sensors` command: `sudo apt install lm-sensors`
- Run `sensors-detect` to configure temperature sensors
- Check thermal zone paths in configuration

#### EasyEffects Not Working
- Ensure EasyEffects is installed and running
- Check `gsettings` command is available
- Verify EasyEffects is not in demo mode

### Debug Mode
- Prefer `debug=False` for normal use. Set `debug=True` only when diagnosing.
- Alternatively, set `debug.enabled` in `config.json` to control logs globally.

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Add docstrings to all functions
- Include error handling
- Update configuration as needed

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🙏 Acknowledgments

- **Numark** for the Mixtrack Platinum FX controller
- **Mixxx** project for MIDI mapping reference
- **EasyEffects** for audio processing capabilities
- **Python community** for excellent libraries
- **ending2020** for their work porting the device to Mixxx mappings
- **qgazq** for their contributions porting the device to Mixxx mappings

## 📞 Support

For issues, questions, or feature requests:
1. Check the troubleshooting section
2. Review the examples
3. Enable debug mode for detailed logging
4. Create an issue with system details

---

**Happy controlling!** 🎛️✨
