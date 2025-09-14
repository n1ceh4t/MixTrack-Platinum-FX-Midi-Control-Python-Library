# Mixtrack Platinum FX MIDI Protocol Documentation

## Overview

This document provides a comprehensive reference for the MIDI protocol used by the Numark Mixtrack Platinum FX controller. The protocol includes both standard MIDI messages and proprietary SysEx messages for advanced features.

## MIDI Port Configuration

### Port Names
- **Input Port**: `MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0`
- **Output Port**: `MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0`

### Channel Mapping
- **Deck 1**: Channel 0 (0x00)
- **Deck 2**: Channel 1 (0x01)
- **Deck 3**: Channel 2 (0x02) - Virtual deck
- **Deck 4**: Channel 3 (0x03) - Virtual deck
- **LED Control**: Channel 4+ (0x04+) - Offset for LED control

## Message Types

### 1. Note On/Off Messages (0x90/0x80)

#### LED Control System
**Format**: `0x90/0x80 | channel, note, velocity`

The Mixtrack Platinum FX uses a sophisticated LED control system with multiple channels and note mappings.

#### LED Channel Mapping
```javascript
// LED Control Channels
LED_CHANNELS = {
    DECK1_LEDS: 4,        // 0x04 - Deck 1 LED control
    DECK2_LEDS: 5,        // 0x05 - Deck 2 LED control
    DECK3_LEDS: 6,        // 0x06 - Deck 3 LED control (virtual)
    DECK4_LEDS: 7,        // 0x07 - Deck 4 LED control (virtual)
    EFFECT_UNIT1: 8,      // 0x08 - Effect unit 1 LEDs
    EFFECT_UNIT2: 9,      // 0x09 - Effect unit 2 LEDs
    PAD_SECTION: 3        // 0x03 - Pad section LEDs (0x93 + deckNumber)
}
```

#### LED Note Numbers and Functions
```javascript
// Hotcue LEDs (1-4) - Primary hotcue buttons
HOTCUE_NOTES = [24, 25, 26, 27]  // 0x18, 0x19, 0x1A, 0x1B

// Extended Hotcue LEDs (5-8) - Secondary hotcue buttons
HOTCUE_EXTENDED_NOTES = [32, 33, 34, 35]  // 0x20, 0x21, 0x22, 0x23

// AutoLoop LEDs - Beat loop buttons
AUTOLOOP_NOTES = [20, 21, 22, 23, 28, 29, 30, 31]  // 0x14-0x17, 0x1C-0x1F

// Loop LEDs - Manual loop controls
LOOP_NOTES = [50, 51, 52, 53, 56, 57]  // 0x32-0x35, 0x38-0x39

// Control LEDs - System control indicators
CONTROL_LED_NOTES = {
    BPM_UP: 9,           // 0x09 - BPM up arrow
    BPM_DOWN: 10,        // 0x0A - BPM down arrow
    KEYLOCK: 13,         // 0x0D - Keylock indicator
    WHEEL_BUTTON: 7,     // 0x07 - Jog wheel button
    SLIP: 15,            // 0x0F - Slip mode indicator
    PFL_CUE: 27,         // 0x1B - PFL/Cue indicator
    DECK_ACTIVE: 8,      // 0x08 - Deck active indicator
    RATE_DISPLAY: 14     // 0x0E - Rate display indicator
}

// Pad Mode LEDs - Mode selection buttons
PAD_MODE_LED_NOTES = {
    HOTCUE: 0,           // 0x00 - Hotcue mode
    AUTOLOOP: 13,        // 0x0D - AutoLoop mode
    FADERCUTS: 7,        // 0x07 - Fader cuts mode
    SAMPLE1: 11,         // 0x0B - Sample 1 mode
    SAMPLE2: 15,         // 0x0F - Sample 2 mode
    HOTCUE2: 2,          // 0x02 - Hotcue 2 mode
    BEATJUMP: 1,         // 0x01 - Beatjump mode (dummy)
    AUTOLOOP2: 14,       // 0x0E - AutoLoop 2 mode (dummy)
    KEYPLAY: 12,         // 0x0C - Keyplay mode (dummy)
    FADERCUTS2: 3,       // 0x03 - Fader cuts 2 mode (dummy)
    FADERCUTS3: 4,       // 0x04 - Fader cuts 3 mode (dummy)
    AUTOLOOP3: 5,        // 0x05 - AutoLoop 3 mode (dummy)
    STEMS: 6             // 0x06 - Stems mode (dummy)
}

// Pad LEDs - Individual pad buttons (0x14-0x1B, 0x1C-0x23)
PAD_LED_NOTES = {
    PAD1: 20,            // 0x14 - Pad 1
    PAD2: 21,            // 0x15 - Pad 2
    PAD3: 22,            // 0x16 - Pad 3
    PAD4: 23,            // 0x17 - Pad 4
    PAD5: 24,            // 0x18 - Pad 5
    PAD6: 25,            // 0x19 - Pad 6
    PAD7: 26,            // 0x1A - Pad 7
    PAD8: 27,            // 0x1B - Pad 8
    PAD9: 28,            // 0x1C - Pad 9 (shifted)
    PAD10: 29,           // 0x1D - Pad 10 (shifted)
    PAD11: 30,           // 0x1E - Pad 11 (shifted)
    PAD12: 31,           // 0x1F - Pad 12 (shifted)
    PAD13: 32,           // 0x20 - Pad 13 (shifted)
    PAD14: 33,           // 0x21 - Pad 14 (shifted)
    PAD15: 34,           // 0x22 - Pad 15 (shifted)
    PAD16: 35            // 0x23 - Pad 16 (shifted)
}

// Effect Unit LEDs - Effect control buttons
EFFECT_LED_NOTES = {
    EFFECT1: 0,          // 0x00 - Effect 1
    EFFECT2: 1,          // 0x01 - Effect 2
    EFFECT3: 2,          // 0x02 - Effect 3
    EFFECT4: 3,          // 0x03 - Effect 4
    EFFECT5: 4,          // 0x04 - Effect 5
    EFFECT6: 5           // 0x05 - Effect 6
}
```

#### LED Velocities and States
```javascript
LED_VELOCITIES = {
    HIGH_LIGHT: 0x7F,    // 127 - Full brightness (ON)
    LOW_LIGHT: 0x01,     // 1 - Dimmed (OFF)
    OFF: 0x00,           // 0 - Completely off
    MEDIUM: 0x40,        // 64 - Medium brightness
    BRIGHT: 0x60,        // 96 - Bright
    MAXIMUM: 0x7F        // 127 - Maximum brightness
}

// Special LED states for different modes
LED_STATES = {
    NORMAL: 0x7F,        // Normal operation
    BLINKING: 0x01,      // Blinking state
    DIM: 0x01,           // Dimmed state
    OFF: 0x00            // Off state
}
```

#### LED Control Examples
```javascript
// Turn on hotcue LED 1 on deck 1
midi.sendShortMsg(0x90 | 4, 0x18, 0x7F);  // Channel 4, Note 24, ON

// Turn off hotcue LED 1 on deck 1
midi.sendShortMsg(0x80 | 4, 0x18, 0x00);  // Channel 4, Note 24, OFF

// Set pad mode LED (hotcue mode)
midi.sendShortMsg(0x90 | 3, 0x00, 0x7F);  // Channel 3, Note 0, ON

// Set effect unit LED
midi.sendShortMsg(0x90 | 8, 0x00, 0x7F);  // Channel 8, Note 0, ON

// Set BPM arrow LED
midi.sendShortMsg(0x90 | 0, 0x09, 0x7F);  // Channel 0, Note 9, ON

// Set deck active LED
midi.sendShortMsg(0x90 | 0, 0x08, 0x7F);  // Channel 0, Note 8, ON
```

#### LED Blinking System
The controller supports LED blinking with configurable timing:

```javascript
// Blink configuration
BLINK_CONFIG = {
    ENABLE_BLINK: true,      // Enable blinking system
    BLINK_DELAY: 700,        // Blink delay in milliseconds
    BLINK_STATE: true,       // Current blink state
    BLINK_STATE_SLOW: true   // Slow blink state
}

// Blink timer function
function BlinkFunc() {
    // Toggle global blink variables
    BLINK_STATE = !BLINK_STATE;
    if (BLINK_STATE) {
        BLINK_STATE_SLOW = !BLINK_STATE_SLOW;
    }
    
    // Update blinking LEDs
    if (FxBlinkState) {
        FxBlinkUpdateLEDs();
    }
    
    // Fire blink callbacks
    for (const i in CallBacks) {
        if (CallBacks[i]) {
            if (CallSpeed[i]) {
                if (BLINK_STATE) {
                    CallBacks[i](BLINK_STATE_SLOW);
                }
            } else {
                CallBacks[i](BLINK_STATE);
            }
        }
    }
}
```

#### Button Control
**Format**: `0x90/0x80 | channel, note, velocity`

**Button Note Numbers**:
```javascript
// Deck buttons
PLAY_NOTES = [0, 4]      // 0x00, 0x04
SYNC_NOTES = [0, 4]      // 0x00, 0x04 (with shift)
CUE_NOTES = [0, 4]       // 0x00, 0x04 (with shift)

// Pad mode buttons
PAD_MODE_NOTES = {
    HOTCUE: 0x00,
    AUTOLOOP: 0x0D,
    FADERCUTS: 0x07,
    SAMPLE1: 0x0B,
    SAMPLE2: 0x0F,
    HOTCUE2: 0x02,
    BEATJUMP: 0x01,      // DUMMY - not used by controller
    AUTOLOOP2: 0x0E,     // DUMMY - not used by controller
    KEYPLAY: 0x0C,       // DUMMY - not used by controller
    FADERCUTS2: 0x03,    // DUMMY - not used by controller
    FADERCUTS3: 0x04,    // DUMMY - not used by controller
    AUTOLOOP3: 0x05,     // DUMMY - not used by controller
    STEMS: 0x06          // DUMMY - not used by controller
}
```

### 2. Control Change Messages (0xB0)

#### Ring Light Control
**Format**: `0xB0 | channel, control, value`

**Control Numbers**:
```javascript
SPINNER_CONTROL = 6      // 0x06 - Red ring (spinner)
POSITION_CONTROL = 63    // 0x3F - White ring (position)
```

**Value Ranges**:
- **Spinner Ring**: 64-115 (0x40-0x73) - 52 values total
- **Position Ring**: 0-52 (0x00-0x34) - 53 values total

**Examples**:
```javascript
// Set spinner ring to 50% (position 26)
midi.sendShortMsg(0xB0 | 0, 0x06, 0x40 + 26);  // Channel 0, CC 6, Value 90

// Set position ring to 75% (position 39)
midi.sendShortMsg(0xB0 | 0, 0x3F, 39);  // Channel 0, CC 63, Value 39
```

#### VU Meter Control
**Format**: `0xB0 | channel, control, value`

**Control Number**: `0x1F` (31)

**Value Range**: 0-90 (0x00-0x5A)

**VU Meter Implementation**:
```javascript
// VU meter callback function
MixtrackPlatinumFX.vuCallback = function(value, group) {
    const level = value * 90;  // Convert to 0-90 range
    const deckOffset = script.deckFromGroup(group) - 1;
    midi.sendShortMsg(0xB0 + deckOffset, 0x1F, level);
};

// VU meter examples
// Set VU meter to 50% (value 45)
midi.sendShortMsg(0xB0 | 0, 0x1F, 45);  // Channel 0, CC 31, Value 45

// Set VU meter to 75% (value 67)
midi.sendShortMsg(0xB0 | 0, 0x1F, 67);  // Channel 0, CC 31, Value 67

// Set VU meter to 0% (value 0)
midi.sendShortMsg(0xB0 | 0, 0x1F, 0);   // Channel 0, CC 31, Value 0
```

#### Control Change Message Summary
```javascript
CONTROL_CHANGE_MESSAGES = {
    // Ring Light Controls
    SPINNER_RING: {
        CONTROL: 0x06,           // CC 6
        RANGE: [64, 115],        // 0x40-0x73 (52 values)
        OFFSET: 64,              // 0x40
        DESCRIPTION: "Red ring (spinner) - shows track position"
    },
    POSITION_RING: {
        CONTROL: 0x3F,           // CC 63
        RANGE: [0, 52],          // 0x00-0x34 (53 values)
        OFFSET: 0,               // No offset
        DESCRIPTION: "White ring (position) - shows playback position"
    },
    
    // VU Meter Control
    VU_METER: {
        CONTROL: 0x1F,           // CC 31
        RANGE: [0, 90],          // 0x00-0x5A (91 values)
        OFFSET: 0,               // No offset
        DESCRIPTION: "VU meter - shows audio level"
    },
    
    // Other Control Changes (from JavaScript analysis)
    UNKNOWN_CC_1: {
        CONTROL: 0x0E,           // CC 14
        DESCRIPTION: "Rate display control"
    },
    UNKNOWN_CC_2: {
        CONTROL: 0x46,           // CC 70
        DESCRIPTION: "Time display control (elapsed/remaining)"
    }
}
```

#### Control Change Examples
```javascript
// Ring Light Examples
// Set spinner ring to 50% (position 26, value 90)
midi.sendShortMsg(0xB0 | 0, 0x06, 0x40 + 26);  // Channel 0, CC 6, Value 90

// Set position ring to 75% (position 39)
midi.sendShortMsg(0xB0 | 0, 0x3F, 39);  // Channel 0, CC 63, Value 39

// Clear both rings
midi.sendShortMsg(0xB0 | 0, 0x06, 0);   // Channel 0, CC 6, Value 0
midi.sendShortMsg(0xB0 | 0, 0x3F, 0);   // Channel 0, CC 63, Value 0

// VU Meter Examples
// Set VU meter to 50% (value 45)
midi.sendShortMsg(0xB0 | 0, 0x1F, 45);  // Channel 0, CC 31, Value 45

// Set VU meter to 75% (value 67)
midi.sendShortMsg(0xB0 | 0, 0x1F, 67);  // Channel 0, CC 31, Value 67

// Clear VU meter
midi.sendShortMsg(0xB0 | 0, 0x1F, 0);   // Channel 0, CC 31, Value 0
```

### 3. SysEx Messages (0xF0)

#### Demo Mode Control
**Exit Demo Mode**:
```javascript
[0xF0, 0x7E, 0x00, 0x06, 0x01, 0xF7]
```

**Enter Demo Mode**:
```javascript
[0xF0, 0x7E, 0x00, 0x06, 0x00, 0xF7]
```

#### Status Messages
**Status Request**:
```javascript
[0xF0, 0x00, 0x20, 0x7F, 0x03, 0x01, 0xF7]
```

**Shutdown**:
```javascript
[0xF0, 0x00, 0x20, 0x7F, 0x02, 0xF7]
```

#### Fader Cut Mode Control
**Enable 8 Fader Cuts**:
```javascript
[0xF0, 0x00, 0x20, 0x7F, 0x03, 0xF7]
```

**Enable 4 Fader Cuts**:
```javascript
[0xF0, 0x00, 0x20, 0x7F, 0x13, 0xF7]
```

#### Display Control System
**Format**: `[0xF0, 0x00, 0x20, 0x7F, deck, type, ...data, 0xF7]`

The Mixtrack Platinum FX features a sophisticated display system with multiple display types and custom encoding.

#### Display Types and Functions
```javascript
DISPLAY_TYPES = {
    BPM: 0x01,          // BPM display (shows tempo)
    RATE: 0x02,         // Rate display (shows pitch/rate percentage)
    DURATION: 0x03,     // Duration display (shows track length)
    TIME: 0x04          // Time display (shows current time or elapsed time)
}
```

#### Display Data Encoding Algorithm
The display system uses a custom 8-byte encoding format that converts numbers into a specific byte array:

```javascript
function encodeNumToArray(number, drop, unsigned) {
    // Ensure number is within valid range for MIDI
    if (number < 0) {
        number = 0;
    } else if (number > 0x0FFFFFFF) {  // 28-bit max
        number = 0x0FFFFFFF;
    }
    
    // Extract individual nibbles (4-bit values)
    const numberarray = [
        (number >> 28) & 0x0F,  // Byte 0 - Most significant nibble
        (number >> 24) & 0x0F,  // Byte 1
        (number >> 20) & 0x0F,  // Byte 2
        (number >> 16) & 0x0F,  // Byte 3
        (number >> 12) & 0x0F,  // Byte 4
        (number >> 8) & 0x0F,   // Byte 5
        (number >> 4) & 0x0F,   // Byte 6
        number & 0x0F,          // Byte 7 - Least significant nibble
    ];
    
    // Remove leading bytes if specified
    if (drop !== undefined) {
        numberarray.splice(0, drop);
    }
    
    // Set sign indicator
    if (number < 0) {
        numberarray[0] = 0x07;  // Negative number indicator
    } else if (!unsigned) {
        numberarray[0] = 0x08;  // Positive number indicator
    }
    
    // Ensure all values are in valid MIDI range (0-127)
    for (let i = 0; i < numberarray.length; i++) {
        numberarray[i] = numberarray[i] & 0x7F;
    }
    
    return numberarray;
}
```

#### Display Message Construction
Each display type has specific message construction rules:

```javascript
// BPM Display - Shows tempo in BPM
function sendScreenBpmMidi(deck, bpm) {
    const bpmArray = encodeNumToArray(bpm);
    bpmArray.shift(); // Remove first byte
    bpmArray.shift(); // Remove second byte
    
    const bytePrefix = [0xF0, 0x00, 0x20, 0x7F, deck, 0x01];
    const bytePostfix = [0xF7];
    const byteArray = bytePrefix.concat(bpmArray, bytePostfix);
    
    midi.sendSysexMsg(byteArray, byteArray.length);
}

// Time Display - Shows time in milliseconds
function sendScreenTimeMidi(deck, time) {
    const timeArray = encodeNumToArray(time);
    
    const bytePrefix = [0xF0, 0x00, 0x20, 0x7F, deck, 0x04];
    const bytePostfix = [0xF7];
    const byteArray = bytePrefix.concat(timeArray, bytePostfix);
    
    midi.sendSysexMsg(byteArray, byteArray.length);
}

// Duration Display - Shows track duration in milliseconds
function sendScreenDurationMidi(deck, duration) {
    if (duration < 1) {
        duration = 1;
    }
    const durationArray = encodeNumToArray(duration - 1);
    
    const bytePrefix = [0xF0, 0x00, 0x20, 0x7F, deck, 0x03];
    const bytePostfix = [0xF7];
    const byteArray = bytePrefix.concat(durationArray, bytePostfix);
    
    midi.sendSysexMsg(byteArray, byteArray.length);
}

// Rate Display - Shows pitch/rate percentage
function sendScreenRateMidi(deck, rate) {
    const rateArray = encodeNumToArray(rate, 2); // Drop first 2 bytes
    
    const bytePrefix = [0xF0, 0x00, 0x20, 0x7F, deck, 0x02];
    const bytePostfix = [0xF7];
    const byteArray = bytePrefix.concat(rateArray, bytePostfix);
    
    midi.sendSysexMsg(byteArray, byteArray.length);
}
```

#### Display Examples and Use Cases
```javascript
// BPM Display Examples
// Display 128.5 BPM (stored as 12850)
const bpmArray = encodeNumToArray(12850);
bpmArray.shift(); // Remove first byte
bpmArray.shift(); // Remove second byte
const bpmSysex = [0xF0, 0x00, 0x20, 0x7F, 1, 0x01, ...bpmArray, 0xF7];

// Display 85.0 BPM (stored as 8500)
const bpmArray2 = encodeNumToArray(8500);
bpmArray2.shift(); // Remove first byte
bpmArray2.shift(); // Remove second byte
const bpmSysex2 = [0xF0, 0x00, 0x20, 0x7F, 1, 0x01, ...bpmArray2, 0xF7];

// Time Display Examples
// Display 5 minutes 30 seconds (330000ms)
const timeArray = encodeNumToArray(330000);
const timeSysex = [0xF0, 0x00, 0x20, 0x7F, 1, 0x04, ...timeArray, 0xF7];

// Display 1 hour 23 minutes 45 seconds (5025000ms)
const timeArray2 = encodeNumToArray(5025000);
const timeSysex2 = [0xF0, 0x00, 0x20, 0x7F, 1, 0x04, ...timeArray2, 0xF7];

// Rate Display Examples
// Display +5% rate (500, drop 2 bytes)
const rateArray = encodeNumToArray(500, 2);
const rateSysex = [0xF0, 0x00, 0x20, 0x7F, 1, 0x02, ...rateArray, 0xF7];

// Display -3% rate (300, drop 2 bytes)
const rateArray2 = encodeNumToArray(300, 2);
const rateSysex2 = [0xF0, 0x00, 0x20, 0x7F, 1, 0x02, ...rateArray2, 0xF7];

// Duration Display Examples
// Display 3 minutes 45 seconds (225000ms)
const durationArray = encodeNumToArray(225000 - 1); // Subtract 1
const durationSysex = [0xF0, 0x00, 0x20, 0x7F, 1, 0x03, ...durationArray, 0xF7];
```

#### Display Data Format Details
```javascript
// Display data structure
DISPLAY_DATA_FORMAT = {
    SYSEX_START: 0xF0,           // SysEx start byte
    MANUFACTURER_ID: [0x00, 0x20, 0x7F], // Numark manufacturer ID
    DECK_NUMBER: 1,              // Deck number (1-4)
    DISPLAY_TYPE: 0x01,          // Display type (0x01-0x04)
    DATA_BYTES: [],              // Encoded data bytes
    SYSEX_END: 0xF7              // SysEx end byte
}

// Data encoding rules
ENCODING_RULES = {
    MAX_VALUE: 0x0FFFFFFF,       // 28-bit maximum value
    NIBBLE_SIZE: 4,              // 4 bits per nibble
    BYTE_COUNT: 8,               // 8 bytes total
    SIGN_POSITIVE: 0x08,         // Positive number indicator
    SIGN_NEGATIVE: 0x07,         // Negative number indicator
    MIDI_MAX: 0x7F               // Maximum MIDI value
}

// Display-specific encoding
DISPLAY_ENCODING = {
    BPM: {
        MULTIPLIER: 100,         // BPM * 100 for decimal precision
        DROP_BYTES: 2,           // Remove first 2 bytes
        UNSIGNED: true           // Always positive
    },
    TIME: {
        MULTIPLIER: 1,           // Time in milliseconds
        DROP_BYTES: 0,           // Keep all bytes
        UNSIGNED: true           // Always positive
    },
    DURATION: {
        MULTIPLIER: 1,           // Duration in milliseconds
        DROP_BYTES: 0,           // Keep all bytes
        UNSIGNED: true,          // Always positive
        OFFSET: -1               // Subtract 1 from duration
    },
    RATE: {
        MULTIPLIER: 100,         // Rate * 100 for decimal precision
        DROP_BYTES: 2,           // Remove first 2 bytes
        UNSIGNED: false          // Can be positive or negative
    }
}
```

#### Display Update Timing
```javascript
// Display update intervals
DISPLAY_TIMING = {
    NORMAL_UPDATE: 5000,         // 5 seconds between updates
    ALERT_UPDATE: 500,           // 0.5 seconds during alerts
    IMMEDIATE_UPDATE: 0,         // Immediate update
    BLINK_UPDATE: 700            // 700ms blink interval
}

// Display state management
DISPLAY_STATE = {
    CURRENT_BPM: [0, 0, 0, 0],   // Current BPM for each deck
    CURRENT_TIME: [0, 0, 0, 0],  // Current time for each deck
    CURRENT_RATE: [0, 0, 0, 0],  // Current rate for each deck
    CURRENT_DURATION: [0, 0, 0, 0] // Current duration for each deck
}
```

## Channel Usage Summary

### Input Channels (Controller → Software)
- **Channel 0**: Deck 1 controls (buttons, knobs, jog wheel)
- **Channel 1**: Deck 2 controls (buttons, knobs, jog wheel)
- **Channel 2**: Deck 3 controls (virtual deck)
- **Channel 3**: Deck 4 controls (virtual deck)

### Output Channels (Software → Controller)
- **Channel 0**: Deck 1 LEDs and displays
- **Channel 1**: Deck 2 LEDs and displays
- **Channel 2**: Deck 3 LEDs and displays
- **Channel 3**: Deck 4 LEDs and displays
- **Channel 4+**: LED control offset (for hotcue, autoloop LEDs)

## Message Timing and Performance

### Update Rates
- **Normal Operation**: 5 seconds between updates
- **Alert Mode**: 0.5 seconds between updates
- **LED Updates**: Immediate (no throttling)
- **Display Updates**: Immediate (no throttling)

### Latency
- **MIDI Response**: < 10ms
- **LED Response**: < 5ms
- **Display Response**: < 20ms

## Error Handling

### Common Issues
1. **LEDs Not Responding**: Some LEDs may require specific timing or may not be controllable via MIDI
2. **Display Garbled**: Check encoding format and byte order
3. **Ring Lights Not Working**: Verify control numbers and value ranges
4. **SysEx Not Working**: Ensure proper message format and timing

### Debugging Tips
1. Enable debug mode to see all MIDI messages
2. Use MIDI monitor to capture traffic
3. Test individual components systematically
4. Verify port names and channel assignments

## Implementation Notes

### Python Implementation
```python
# LED Control Example
def set_led(self, deck, led_type, state):
    channel = 4 + (deck - 1)  # LED control channel
    velocity = 127 if state else 0
    note = self.get_led_note(led_type)
    
    if state:
        self.outport.send(mido.Message('note_on', channel=channel, note=note, velocity=velocity))
    else:
        self.outport.send(mido.Message('note_off', channel=channel, note=note, velocity=velocity))

# Ring Control Example
def set_ring(self, deck, ring_type, position):
    channel = deck - 1
    control = 6 if ring_type == RingType.SPINNER else 63
    value = position + 64 if ring_type == RingType.SPINNER else position
    
    self.outport.send(mido.Message('control_change', 
                                 channel=channel, 
                                 control=control, 
                                 value=value))

# Display Control Example
def set_bpm_display(self, deck, bpm):
    int_value = int(bpm * 100)
    value_array = self._encode_number_to_array(int_value)
    value_array = value_array[2:]  # Remove first two bytes
    
    sysex_data = [0x00, 0x20, 0x7F, deck, 0x01] + value_array
    msg = mido.Message('sysex', data=sysex_data)
    self.outport.send(msg)
```

### JavaScript Implementation
```javascript
// LED Control Example
function setLED(deck, ledType, state) {
    const channel = 4 + (deck - 1);
    const velocity = state ? 0x7F : 0x00;
    const note = getLEDNote(ledType);
    
    midi.sendShortMsg(0x90 | channel, note, velocity);
}

// Ring Control Example
function setRing(deck, ringType, position) {
    const channel = deck - 1;
    const control = ringType === 'spinner' ? 0x06 : 0x3F;
    const value = ringType === 'spinner' ? position + 0x40 : position;
    
    midi.sendShortMsg(0xB0 | channel, control, value);
}

// Display Control Example
function setBPMDisplay(deck, bpm) {
    const intValue = Math.round(bpm * 100);
    const bpmArray = encodeNumToArray(intValue);
    bpmArray.shift(); // Remove first byte
    bpmArray.shift(); // Remove second byte
    
    const sysex = [0xF0, 0x00, 0x20, 0x7F, deck, 0x01, ...bpmArray, 0xF7];
    midi.sendSysexMsg(sysex, sysex.length);
}
```

## Audio Routing Controls

The Mixtrack Platinum FX provides comprehensive audio routing controls through MIDI control change messages. These controls manage audio levels, routing, and monitoring.

### Audio Control Overview

The controller provides three main audio control categories:
1. **Master Audio Controls** - Global audio routing and levels
2. **Deck Audio Controls** - Individual deck volume and gain
3. **Cue/Monitor Controls** - Headphone monitoring and cue mixing

### Master Audio Controls

#### Main Gain Control
**Format**: `0xBE | 0x23, value`

**MIDI Mapping**:
- **Status**: `0xBE` (Control Change on Channel 14)
- **Control**: `0x23` (35)
- **Group**: `[Master]`
- **Key**: `gain`

**Function**: Controls the master output gain/volume for the entire system.

**Implementation**:
```javascript
this.mainGain = new components.Pot({
    group: "[Master]",
    inKey: "gain"
});
```

#### Cue Gain Control
**Format**: `0xBF | 0x0C, value`

**MIDI Mapping**:
- **Status**: `0xBF` (Control Change on Channel 15)
- **Control**: `0x0C` (12)
- **Group**: `[Master]`
- **Key**: `headGain`

**Function**: Controls the headphone/cue output gain level.

**Shift Functionality**: When shift is pressed, this control switches to sampler pregain control for all 16 samplers.

**Implementation**:
```javascript
this.cueGain = new components.Pot({
    group: "[Master]",
    inKey: "headGain",
    shift: function() {
        this.disconnect();
        this.group = "[Sampler1]";
        this.inKey = "pregain";
        this.input = function(channel, control, value, _status, _group) {
            const newValue = this.inValueScale(value);
            for (let i=1; i<=16; i++) {
                engine.setParameter(`[Sampler${i}]`, "pregain", newValue);
            }
        };
    },
    unshift: function() {
        this.disconnect();
        this.firstValueReceived=false;
        this.group = "[Master]";
        this.inKey = "headGain";
        this.input = components.Pot.prototype.input;
    },
});
```

#### Cue Mix Control
**Format**: `0xBF | 0x0D, value`

**MIDI Mapping**:
- **Status**: `0xBF` (Control Change on Channel 15)
- **Control**: `0x0D` (13)
- **Group**: `[Master]`
- **Key**: `headMix`

**Function**: Controls the mix between main output and cue output in headphones.

**Implementation**:
```javascript
this.cueMix = new components.Pot({
    group: "[Master]",
    inKey: "headMix"
});
```

### Deck Audio Controls

#### Deck Volume Control
**Format**: `0xB0 | channel, 0x1C, value`

**MIDI Mapping**:
- **Status**: `0xB0` (Control Change on deck channel)
- **Control**: `0x1C` (28)
- **Group**: `[Channel1]`, `[Channel2]`, `[Channel3]`, `[Channel4]`
- **Key**: `volume`

**Function**: Controls the individual deck volume level.

**Implementation**:
```javascript
this.volume = new components.Pot({
    inKey: "volume"
});
```

#### Deck Gain Control
**Format**: `0xB0 | channel, 0x16, value`

**MIDI Mapping**:
- **Status**: `0xB0` (Control Change on deck channel)
- **Control**: `0x16` (22)
- **Group**: `[Channel1]`, `[Channel2]`, `[Channel3]`, `[Channel4]`
- **Key**: `pregain`

**Function**: Controls the individual deck input gain/pregain level.

**Implementation**:
```javascript
this.gain = new components.Pot({
    inKey: "pregain"
});
```

### Cue/Monitor Controls

#### PFL (Pre-Fader Listen) Button
**Format**: `0x90/0x80 | channel, 0x1B, velocity`

**MIDI Mapping**:
- **Status**: `0x90/0x80` (Note On/Off on deck channel)
- **Note**: `0x1B` (27)
- **Group**: `[Channel1]`, `[Channel2]`, `[Channel3]`, `[Channel4]`
- **Key**: `pfl` (normal) / `slip_enabled` (shifted)

**Function**: Enables/disables Pre-Fader Listen for the deck, allowing monitoring of the deck signal in headphones before the volume fader.

**Shift Functionality**: When shift is pressed, this button controls slip mode instead of PFL.

**Implementation**:
```javascript
this.pflButton = new components.Button({
    shift: function() {
        this.disconnect();
        this.inKey = "slip_enabled";
        this.outKey = "slip_enabled";
        this.connect();
        this.trigger();
    },
    unshift: function() {
        this.disconnect();
        this.inKey = "pfl";
        this.outKey = "pfl";
        this.connect();
        this.trigger();
    },
    type: components.Button.prototype.types.toggle,
    midi: [0x90 + channel, 0x1B],
});
```

### Audio Control Examples

#### Master Audio Control Examples
```javascript
// Set main gain to 50% (value 64)
midi.sendShortMsg(0xBE, 0x23, 64);  // Channel 14, CC 35, Value 64

// Set cue gain to 75% (value 96)
midi.sendShortMsg(0xBF, 0x0C, 96);  // Channel 15, CC 12, Value 96

// Set cue mix to 50% (value 64)
midi.sendShortMsg(0xBF, 0x0D, 64);  // Channel 15, CC 13, Value 64
```

#### Deck Audio Control Examples
```javascript
// Set deck 1 volume to 50% (value 64)
midi.sendShortMsg(0xB0 | 0, 0x1C, 64);  // Channel 0, CC 28, Value 64

// Set deck 1 gain to 75% (value 96)
midi.sendShortMsg(0xB0 | 0, 0x16, 96);  // Channel 0, CC 22, Value 96

// Set deck 2 volume to 25% (value 32)
midi.sendShortMsg(0xB0 | 1, 0x1C, 32);  // Channel 1, CC 28, Value 32
```

#### PFL Control Examples
```javascript
// Enable PFL on deck 1
midi.sendShortMsg(0x90 | 0, 0x1B, 0x7F);  // Channel 0, Note 27, ON

// Disable PFL on deck 1
midi.sendShortMsg(0x80 | 0, 0x1B, 0x00);  // Channel 0, Note 27, OFF

// Enable PFL on deck 2
midi.sendShortMsg(0x90 | 1, 0x1B, 0x7F);  // Channel 1, Note 27, ON
```

### Audio Control Summary

#### Control Change Messages for Audio
```javascript
AUDIO_CONTROL_CHANGES = {
    // Master Controls
    MAIN_GAIN: {
        STATUS: 0xBE,           // Channel 14
        CONTROL: 0x23,          // CC 35
        GROUP: "[Master]",
        KEY: "gain",
        DESCRIPTION: "Master output gain"
    },
    CUE_GAIN: {
        STATUS: 0xBF,           // Channel 15
        CONTROL: 0x0C,          // CC 12
        GROUP: "[Master]",
        KEY: "headGain",
        DESCRIPTION: "Headphone/cue output gain"
    },
    CUE_MIX: {
        STATUS: 0xBF,           // Channel 15
        CONTROL: 0x0D,          // CC 13
        GROUP: "[Master]",
        KEY: "headMix",
        DESCRIPTION: "Cue mix level"
    },
    
    // Deck Controls
    DECK_VOLUME: {
        STATUS: 0xB0,           // Deck channel
        CONTROL: 0x1C,          // CC 28
        GROUP: "[ChannelN]",
        KEY: "volume",
        DESCRIPTION: "Deck volume level"
    },
    DECK_GAIN: {
        STATUS: 0xB0,           // Deck channel
        CONTROL: 0x16,          // CC 22
        GROUP: "[ChannelN]",
        KEY: "pregain",
        DESCRIPTION: "Deck input gain"
    }
}
```

#### Note Messages for Audio
```javascript
AUDIO_NOTE_MESSAGES = {
    PFL_BUTTON: {
        STATUS: 0x90/0x80,      // Note On/Off
        NOTE: 0x1B,             // Note 27
        GROUP: "[ChannelN]",
        KEY: "pfl",
        DESCRIPTION: "Pre-Fader Listen toggle"
    }
}
```

### Audio Routing Use Cases

#### For Linux System Control
1. **System Volume Control** - Use main gain for system-wide volume
2. **Application Volume** - Use deck volume for individual application levels
3. **Audio Monitoring** - Use PFL for monitoring specific audio sources
4. **Audio Mixing** - Use cue mix for blending different audio sources

#### For DJ Software
1. **Master Output** - Main gain controls overall output level
2. **Headphone Monitoring** - Cue gain and mix for DJ monitoring
3. **Deck Levels** - Individual deck volume and gain control
4. **Pre-Listen** - PFL for previewing tracks before mixing

### Implementation Notes

1. **Value Range**: All audio controls use standard MIDI values (0-127)
2. **Channel Mapping**: Deck controls use deck channels (0-3), master controls use channels 14-15
3. **Shift Functionality**: Cue gain has special shift behavior for sampler control
4. **Toggle Behavior**: PFL button is a toggle control with LED feedback
5. **Real-time Control**: All audio controls provide real-time parameter adjustment

## References

- [MIDI Specification](https://www.midi.org/specifications)
- [Mixxx Controller Mapping Documentation](https://manual.mixxx.org/2.3/en/chapters/appendix/mixxx_controls.html)
- [Numark Mixtrack Platinum FX Manual](https://www.numark.com/product/mixtrack-platinum-fx)

## Version History

- **v1.0** - Initial documentation based on JavaScript implementation analysis
- **v1.1** - Added Python implementation examples
- **v1.2** - Added error handling and debugging tips

---

*This documentation is based on reverse engineering of the Mixtrack Platinum FX controller using the unstable JavaScript implementation and Python testing. Some features may not be fully documented or tested.*
