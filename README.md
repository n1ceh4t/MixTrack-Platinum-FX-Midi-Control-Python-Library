# Mixtrack Platinum FX Python Library

A comprehensive Python library for controlling the Numark Mixtrack Platinum FX DJ controller as a Linux system control interface.

## Features

- **Complete MIDI Protocol Support** - Full control of all 50+ LEDs, displays, rings, and controls
- **System Monitoring** - Real-time CPU/GPU temperature and usage display
- **Audio Control** - Volume, effects, and routing control
- **Configurable** - JSON-based configuration for all settings
- **Linux Integration** - Designed for system control applications

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install mido psutil

# Install system monitoring tools (optional)
sudo apt install lm-sensors
```

### Setup

1. **Clone or download** the library files
2. **Connect** your Mixtrack Platinum FX via USB
3. **Configure** MIDI ports in `config.json` (auto-detected on first run)

## Quick Start

### Basic Usage

```python
from mixtrack_platinum_fx import MixtrackPlatinumFX

# Initialize controller
controller = MixtrackPlatinumFX()

# Connect to device
controller.connect()

# Control LEDs
controller.set_led(controller.led_config.hotcue_notes[0], True)  # Turn on first hotcue LED
controller.set_led(controller.led_config.bpm_up_note, True)     # Turn on BPM up LED

# Control displays
controller.set_display_bpm(1, 128.5)  # Set deck 1 BPM display to 128.5
controller.set_display_time(1, 180)   # Set deck 1 time display to 3:00

# Control ring lights
controller.set_ring(RingType.SPINNER, 1, 0.5)  # Set deck 1 spinner to 50%
controller.set_ring(RingType.POSITION, 1, 0.25) # Set deck 1 position to 25%

# Disconnect
controller.disconnect()
```

### System Monitoring

```python
from mixtrack_platinum_fx import MixtrackPlatinumFX
from system_monitor import SystemMonitor

# Initialize controller and system monitor
controller = MixtrackPlatinumFX()
monitor = controller.create_system_monitor()  # Uses config.json settings

# Start monitoring
monitor.start_monitoring()

# System vitals are automatically displayed on controller
# - CPU/GPU temps on ring lights
# - Usage percentages on displays
# - Alert LEDs for high temperatures
```

### Audio Control

```python
# Control audio routing (requires MIDI-compatible audio software)
controller.send_control_change(14, 35, 64)  # Set main gain to 50%
controller.send_control_change(15, 12, 96)  # Set cue gain to 75%
controller.send_note_on(0, 27, 127)         # Enable PFL on deck 1
```

## Configuration

Edit `config.json` to customize:

### MIDI Ports
```json
{
  "midi": {
    "input_port": "MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0",
    "output_port": "MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0"
  }
}
```

### System Monitoring
```json
{
  "alert_thresholds": {
    "cpu_temp_alert": 75.0,
    "gpu_temp_alert": 80.0,
    "cpu_usage_alert": 80.0
  },
  "system_monitoring": {
    "cache_interval": 0.5
  }
}
```

### LED Mapping
```json
{
  "leds": {
    "hotcue_notes": [24, 25, 26, 27],
    "bpm_up_note": 9,
    "bpm_down_note": 10,
    "velocity_on": 127,
    "velocity_off": 0
  }
}
```

## API Reference

### Core Controller

#### `MixtrackPlatinumFX(config_file=None, debug=False)`
Initialize the controller with optional config file and debug mode.

#### `connect(input_port=None, output_port=None)`
Connect to MIDI ports. Uses config.json settings if ports not specified.

#### `disconnect()`
Disconnect from MIDI ports.

### LED Control

#### `set_led(note, state, velocity=None)`
Control individual LEDs.
- `note`: MIDI note number
- `state`: True/False or velocity (0-127)
- `velocity`: Optional velocity override

#### `set_led_blink(note, enabled)`
Enable/disable LED blinking.

#### `all_leds_off()`
Turn off all LEDs.

### Display Control

#### `set_display_bpm(deck, bpm)`
Set BPM display for specified deck.

#### `set_display_time(deck, seconds)`
Set time display for specified deck.

#### `set_display_rate(deck, rate)`
Set rate display for specified deck.

#### `set_display_duration(deck, seconds)`
Set duration display for specified deck.

### Ring Light Control

#### `set_ring(ring_type, deck, position)`
Control ring lights.
- `ring_type`: `RingType.SPINNER` or `RingType.POSITION`
- `deck`: Deck number (1-4)
- `position`: Position (0.0-1.0)

### System Monitoring

#### `create_system_monitor(**kwargs)`
Create a SystemMonitor instance with config integration.

#### `SystemMonitor.start_monitoring(update_interval=1.0)`
Start real-time system monitoring.

#### `SystemMonitor.stop_monitoring()`
Stop system monitoring.

### MIDI Control

#### `send_note_on(channel, note, velocity)`
Send MIDI note on message.

#### `send_note_off(channel, note, velocity=0)`
Send MIDI note off message.

#### `send_control_change(channel, control, value)`
Send MIDI control change message.

#### `send_sysex(data)`
Send MIDI system exclusive message.

## Examples

### Basic LED Control
```python
controller = MixtrackPlatinumFX()
controller.connect()

# Turn on hotcue LEDs
for note in controller.led_config.hotcue_notes:
    controller.set_led(note, True)

# Blink BPM up LED
controller.set_led_blink(controller.led_config.bpm_up_note, True)
```

### Display Updates
```python
# Update displays with system info
controller.set_display_bpm(1, 128.5)
controller.set_display_time(1, 180)  # 3:00
controller.set_display_rate(1, 1.05)  # +5% rate
```

### Ring Light Visualization
```python
# Visualize CPU temperature on ring
cpu_temp = 65.0  # Celsius
temp_percent = min(cpu_temp / 80.0, 1.0)  # Scale to 0-1
controller.set_ring(RingType.SPINNER, 1, temp_percent)
```

### System Monitoring Dashboard
```python
# Complete system monitoring setup
controller = MixtrackPlatinumFX()
monitor = controller.create_system_monitor()

# Add custom alert callbacks
def cpu_alert(temp):
    print(f"CPU temperature alert: {temp}°C")
    controller.set_led(controller.led_config.bpm_up_note, True)

monitor.add_alert_callback('cpu_temp', cpu_alert)
monitor.start_monitoring()
```

## Troubleshooting

### MIDI Port Issues
```bash
# List available MIDI ports
python3 -c "import mido; print(mido.get_output_names())"

# Update config.json with correct port names
```

### Permission Issues
```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Restart session or reboot
```

### Temperature Detection
```bash
# Install and configure sensors
sudo apt install lm-sensors
sudo sensors-detect

# Test temperature reading
sensors
```

## File Structure

```
├── mixtrack_platinum_fx.py    # Main controller library
├── system_monitor.py          # System monitoring integration
├── easyeffects_control.py     # EasyEffects audio control
├── config.json               # Configuration file
├── MIDI_PROTOCOL.md          # MIDI protocol documentation
├── README.md                 # This file
└── examples/                 # Example scripts and usage
```

## License

This library is provided as-is for educational and personal use. The MIDI protocol documentation is based on reverse engineering of the Mixxx controller mapping.

## Contributing

Contributions welcome! Areas for improvement:
- Additional Linux system integrations
- More audio software support
- Enhanced configuration options
- Performance optimizations
