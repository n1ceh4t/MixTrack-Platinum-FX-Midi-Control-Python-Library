# Mixtrack Platinum FX Python Library

A Python library for controlling the Numark Mixtrack Platinum FX DJ controller as a Linux system control interface.

## ✨ Features

- **🎛️ Complete MIDI Protocol Support** - Partial control of LEDs, full control of displays and rings
- **📊 Rate Display** - Jogger display percentage output
- **📈 System Monitoring** - Real-time CPU/GPU temperature and usage display with VU meter alerts
- **🎵 Audio Control** - Volume, effects, and routing control
- **⚙️ Advanced Configuration** - Type-safe configuration system with validation
- **🔧 Button LED Feedback** - Automatic LED feedback when buttons are pressed
- **🛡️ Error Handling** - Comprehensive error handling and logging
- **🐧 Linux Integration** - Designed for system control applications

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install mido psutil rtmidi

# Install system monitoring tools (optional)
sudo apt install lm-sensors
```

### Setup

1. **Clone or download** the library files
2. **Connect** your Mixtrack Platinum FX via USB
3. **Configure** MIDI ports in `config.json` (auto-detected on first run)

## 🚀 Quick Start

### Basic Usage

```python
from mixtrack_platinum_fx import create_controller, LEDType, RingType

# Initialize controller with context manager (recommended)
with create_controller(debug=False) as controller:
    # Control LEDs using the new unified API
    controller.set_led(1, LEDType.HOTCUE, True)      # Turn on hotcue LEDs on deck 1
    controller.set_led(1, LEDType.BPM_UP, True)      # Turn on BPM up LED on deck 1
    controller.set_led(2, LEDType.PLAY, True)        # Turn on play LED on deck 2
    
    # Control displays
    controller.set_bpm_display(1, 128.5)             # Set deck 1 BPM display to 128.5
    controller.set_time_display(1, 180)              # Set deck 1 time display to 3:00
    controller.set_rate_display(1, 5.0)              # Set deck 1 rate display to +5.0%
    
    # Control VU meters
    controller.set_vu_meter(1, 75)                   # Set deck 1 VU meter to 75%
    controller.set_vu_meter(2, 50)                   # Set deck 2 VU meter to 50%
    
    # Control ring lights
    controller.set_ring_percentage(1, RingType.SPINNER, 50.0)   # Set deck 1 spinner to 50%
    controller.set_ring_percentage(1, RingType.POSITION, 25.0)  # Set deck 1 position to 25%
    
    # Button LED feedback is automatically enabled!
    # Press any button on the controller to see its LED light up
```

### Advanced Usage with Configuration

```python
from mixtrack_platinum_fx import create_controller, ControllerConfig, LEDType

# Create custom configuration
config = ControllerConfig()
config.midi.button_led_feedback = True
config.midi.led_feedback_duration = 0.3
config.debug = {"enabled": false}

# Initialize with custom config
with create_controller(config=config) as controller:
    # Your code here
    pass
```

### System Monitoring

```python
from mixtrack_platinum_fx import create_controller
from system_monitor import SystemMonitor, AlertThresholds

# Initialize controller and system monitor
with create_controller(debug=False) as controller:
    # Create system monitor with custom thresholds
    thresholds = AlertThresholds(
        cpu_temp=77.0,      # Alert if CPU temp >= 77°C
        gpu_temp=80.0,      # Alert if GPU temp >= 80°C
        cpu_usage=80.0,     # Alert if CPU usage >= 80%
        memory_usage=90.0   # Alert if memory usage >= 90%
    )
    
    monitor = SystemMonitor(controller=controller, thresholds=thresholds)
    
    # Start monitoring
    monitor.start_monitoring()
    
    # System vitals are automatically displayed on controller:
    # - CPU/GPU temps on ring lights and BPM displays
    # - Usage percentages on jogger displays
    # - VU meter alerts with alternating patterns at 90%
    # - Button LED feedback for user interaction
```

### Raw MIDI (optional)

```python
# You can send raw MIDI with mido via the controller's outport
import mido
controller.outport.send(mido.Message('control_change', channel=14, control=35, value=64))
controller.outport.send(mido.Message('note_on', channel=0, note=27, velocity=127))
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
    "cpu_usage_alert": 80.0,
    "memory_usage_alert": 90.0
  },
  "system_monitoring": {
    "cache_interval": 1.0,
    "ring_assignments": {
      "deck1": {"red_ring": "cpu_temp", "white_ring": "cpu_usage"},
      "deck2": {"red_ring": "gpu_temp", "white_ring": "memory_usage"}
    },
    "jogger_display_assignments": {
      "deck1": "cpu_usage",
      "deck2": "memory_usage"
    }
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

#### `MixtrackPlatinumFX(input_port=None, output_port=None, config=None, debug=False)`
Initialize the controller. Ports may be auto-detected; config can be a dict or `ControllerConfig`.

#### `connect(input_port=None, output_port=None)`
Connect to MIDI ports. Uses config.json settings if ports not specified.

#### `disconnect()`
Disconnect from MIDI ports.

### LED Control

#### `set_led(deck, led_type, state)`
Control LEDs by type and deck via unified API.

### Display Control

#### `set_display_bpm(deck, bpm)`
Set BPM display for specified deck.

#### `set_display_time(deck, seconds)`
Set time display for specified deck.

#### `set_rate_display(deck, rate_percent)`
Set jogger display (rate display) for specified deck showing percentage.

#### `set_current_time_display(deck)`
Show current time (HH:MM) on deck display.

### Ring Light Control

#### `set_ring(deck, ring_type, position)`
Set ring light to a specific position (integer 0..max).

#### `set_ring_percentage(deck, ring_type, percentage)`
Set ring light using a percentage (0.0..100.0).

### System Monitoring

#### `create_system_monitor(**kwargs)`
Create a SystemMonitor instance with config integration.

#### `SystemMonitor.start_monitoring(update_interval=1.0)`
Start real-time system monitoring.

#### `SystemMonitor.stop_monitoring()`
Stop system monitoring.

### MIDI Control

Use `controller.outport.send(mido.Message(...))` for raw MIDI when needed.

## Rate Display

Use `set_rate_display(deck, percent)` to show a percentage on the jogger display.

## FX Button LEDs

FX button helper APIs were removed to keep the surface minimal. If needed, you can send MIDI note_on/note_off directly.

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
controller.set_bpm_display(1, 128.5)
controller.set_time_display(1, 180)  # 3:00
controller.set_rate_display(1, 45.2)  # 45.2% on jogger display
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

## Implementation Notes

### Channel Scheme

- Inputs: 0/1 (deck buttons), 4/5 (pads/LED layer), 8/9 (FX buttons)
- Outputs (LED): 4/5 for decks 1/2; FX use 8/9
- The library centralizes this mapping and automatically routes deck inputs (0/1) to LED outputs (4/5).

### LED Off Behavior

- LEDs clear reliably using `note_on` with velocity `1` instead of `note_off`.

### Debug Control

- Pass `debug=False` in code for normal use; set `config.debug.enabled` to toggle globally without code changes.

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
- Testing
- Additional Linux system integrations
- More audio software support
- Enhanced configuration options
- Performance optimizations
