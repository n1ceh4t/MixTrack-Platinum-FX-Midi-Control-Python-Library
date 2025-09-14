#!/usr/bin/env python3
"""
MixtrackPlatinumFX - A comprehensive Python library for controlling the Numark Mixtrack Platinum FX controller.

This library provides complete control over all hardware features including:
- LED control (hotcues, autoloops, loops, play, sync, cue, etc.)
- Ring light control (spinner and position indicators)
- Display control (BPM displays, time displays, jog wheel displays)
- MIDI input handling
- System monitoring integration
- Audio effects control (EasyEffects integration)

Based on the official Mixxx controller mapping and extensive testing.
"""

import mido
import time
import threading
import queue
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum


class LEDType(Enum):
    """LED types available on the controller"""
    HOTCUE = "hotcue"
    HOTCUE_EXTENDED = "hotcue_extended"
    AUTOLOOP = "autoloop"
    LOOP = "loop"
    PLAY = "play"
    SYNC = "sync"
    CUE = "cue"
    PFL_CUE = "pfl_cue"
    BPM_UP = "bpm_up"
    BPM_DOWN = "bpm_down"
    KEYLOCK = "keylock"
    WHEEL_BUTTON = "wheel_button"
    SLIP = "slip"


class RingType(Enum):
    """Ring light types"""
    SPINNER = "spinner"  # Red ring (CC 0x06)
    POSITION = "position"  # White ring (CC 0x3F)


class DisplayType(Enum):
    """Display types"""
    BPM = "bpm"
    TIME = "time"


@dataclass
class LEDConfig:
    """Configuration for LED control"""
    channel_offset: int = 4
    hotcue_notes: List[int] = None
    hotcue_extended_notes: List[int] = None
    autoloop_notes: List[int] = None
    loop_notes: List[int] = None
    play_notes: List[int] = None
    sync_notes: List[int] = None
    cue_notes: List[int] = None
    bpm_up_note: int = 9
    bpm_down_note: int = 10
    keylock_note: int = 13
    pfl_cue_note: int = 27
    wheel_button_note: int = 7
    slip_note: int = 15
    velocity_on: int = 127
    velocity_off: int = 0

    def __post_init__(self):
        if self.hotcue_notes is None:
            self.hotcue_notes = [24, 25, 26, 27]
        if self.hotcue_extended_notes is None:
            self.hotcue_extended_notes = [32, 33, 34, 35]
        if self.autoloop_notes is None:
            self.autoloop_notes = [20, 21, 22, 23, 28, 29, 30, 31]
        if self.loop_notes is None:
            self.loop_notes = [50, 51, 52, 53, 56, 57]
        if self.play_notes is None:
            self.play_notes = [0, 4]
        if self.sync_notes is None:
            self.sync_notes = [0, 4]
        if self.cue_notes is None:
            self.cue_notes = [0, 4]


@dataclass
class RingConfig:
    """Configuration for ring light control"""
    spinner_control: int = 6
    position_control: int = 63
    spinner_offset: int = 64
    max_position: int = 52
    temp_max: int = 80


@dataclass
class DisplayConfig:
    """Configuration for display control"""
    bpm_display_type: int = 1
    time_display_type: int = 4


class MixtrackPlatinumFX:
    """
    Main class for controlling the Numark Mixtrack Platinum FX controller.
    
    This class provides comprehensive control over all hardware features including
    LEDs, ring lights, displays, and MIDI input handling.
    """
    
    def __init__(self, 
                 input_port: Optional[str] = None,
                 output_port: Optional[str] = None,
                 config_file: Optional[str] = None,
                 debug: bool = False):
        """
        Initialize the MixtrackPlatinumFX controller.
        
        Args:
            input_port: MIDI input port name (auto-detect if None)
            output_port: MIDI output port name (auto-detect if None)
            config_file: Path to configuration file (optional)
            debug: Enable debug output
        """
        self.debug = debug
        self.running = False
        self.midi_queue = queue.Queue()
        self.midi_thread = None
        self.inport = None
        self.outport = None
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Initialize hardware configurations
        self.led_config = LEDConfig(**self.config.get('leds', {}))
        self.ring_config = RingConfig(**self.config.get('rings', {}))
        self.display_config = DisplayConfig(**self.config.get('display', {}))
        
        # MIDI port configuration
        self.input_port_name = input_port or self.config.get('midi', {}).get('input_port')
        self.output_port_name = output_port or self.config.get('midi', {}).get('output_port')
        
        # Debug configuration
        self.debug = debug if debug is not None else self.config.get('debug', {}).get('enabled', False)
        self.show_midi_ports = self.config.get('debug', {}).get('show_midi_ports', False)
        
        # Threading configuration
        self.midi_sleep = self.config.get('threading', {}).get('midi_sleep', 0.001)
        self.main_loop_sleep = self.config.get('threading', {}).get('main_loop_sleep', 0.001)
        
        # Callback functions
        self.midi_callbacks: Dict[str, Callable] = {}
        
        if self.debug:
            print("MixtrackPlatinumFX initialized")
            print(f"LED Config: {self.led_config}")
            print(f"Ring Config: {self.ring_config}")
            print(f"Display Config: {self.display_config}")
    
    def create_system_monitor(self, **kwargs):
        """Create a SystemMonitor instance with config integration"""
        from system_monitor import SystemMonitor
        return SystemMonitor(controller=self, config=self.config, **kwargs)
    
    def _load_config(self, config_file: Optional[str] = None) -> Dict:
        """Load configuration from file or use defaults"""
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            if self.debug:
                print(f"Config file not found: {config_file}, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            if self.debug:
                print(f"Error parsing config file: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'midi': {
                'input_port': 'MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0',
                'output_port': 'MixTrack Platinum FX:MixTrack Platinum FX MIDI 1 32:0'
            },
            'leds': {
                'channel_offset': 4,
                'hotcue_notes': [24, 25, 26, 27],
                'hotcue_extended_notes': [32, 33, 34, 35],
                'autoloop_notes': [20, 21, 22, 23, 28, 29, 30, 31],
                'loop_notes': [50, 51, 52, 53, 56, 57],
                'play_notes': [0, 4],
                'sync_notes': [0, 4],
                'cue_notes': [0, 4],
                'bpm_up_note': 9,
                'bpm_down_note': 10,
                'keylock_note': 13,
                'pfl_cue_note': 27,
                'wheel_button_note': 7,
                'slip_note': 15,
                'velocity_on': 127,
                'velocity_off': 0
            },
            'rings': {
                'spinner_control': 6,
                'position_control': 63,
                'spinner_offset': 64,
                'max_position': 52,
                'temp_max': 80
            },
            'display': {
                'bpm_display_type': 1,
                'time_display_type': 4
            }
        }
    
    def connect(self) -> bool:
        """
        Connect to the MIDI controller.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.input_port_name:
                self.inport = mido.open_input(self.input_port_name)
            else:
                # Auto-detect input port
                input_ports = [name for name in mido.get_input_names() if 'MixTrack' in name]
                if input_ports:
                    self.inport = mido.open_input(input_ports[0])
                else:
                    raise OSError("No MixTrack input port found")
            
            if self.output_port_name:
                self.outport = mido.open_output(self.output_port_name)
            else:
                # Auto-detect output port
                output_ports = [name for name in mido.get_output_names() if 'MixTrack' in name]
                if output_ports:
                    self.outport = mido.open_output(output_ports[0])
                else:
                    raise OSError("No MixTrack output port found")
            
            if self.debug:
                print(f"Connected to input: {self.inport.name}")
                print(f"Connected to output: {self.outport.name}")
            
            # Exit demo mode
            self.exit_demo_mode()
            
            # Clear all LEDs
            self.clear_all_leds()
            
            return True
            
        except OSError as e:
            if self.debug:
                print(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the MIDI controller"""
        self.stop()
        if self.inport:
            self.inport.close()
            self.inport = None
        if self.outport:
            self.outport.close()
            self.outport = None
        if self.debug:
            print("Disconnected from controller")
    
    def start(self):
        """Start the MIDI input handler thread"""
        if not self.outport:
            raise RuntimeError("Not connected to controller")
        
        self.running = True
        self.midi_thread = threading.Thread(target=self._midi_handler, daemon=True)
        self.midi_thread.start()
        
        if self.debug:
            print("MIDI handler started")
    
    def stop(self):
        """Stop the MIDI input handler thread"""
        self.running = False
        if self.midi_thread and self.midi_thread.is_alive():
            self.midi_thread.join(timeout=1.0)
        if self.debug:
            print("MIDI handler stopped")
    
    def _midi_handler(self):
        """Handle MIDI input in a separate thread"""
        while self.running:
            try:
                if self.inport.poll():
                    msg = self.inport.receive()
                    if msg:
                        if self.debug:
                            print(f"MIDI received: {msg}")
                        self.midi_queue.put(msg)
                else:
                    time.sleep(0.001)
            except Exception as e:
                if self.running and self.debug:
                    print(f"MIDI error: {e}")
                break
    
    def process_midi_events(self):
        """Process MIDI events from the queue"""
        while not self.midi_queue.empty():
            try:
                msg = self.midi_queue.get_nowait()
                self._handle_midi_message(msg)
            except queue.Empty:
                break
            except Exception as e:
                if self.debug:
                    print(f"MIDI processing error: {e}")
    
    def _handle_midi_message(self, msg):
        """Handle individual MIDI messages"""
        # Call registered callbacks
        for callback_name, callback in self.midi_callbacks.items():
            try:
                callback(msg)
            except Exception as e:
                if self.debug:
                    print(f"Callback {callback_name} error: {e}")
    
    def register_midi_callback(self, name: str, callback: Callable):
        """
        Register a MIDI message callback.
        
        Args:
            name: Unique name for the callback
            callback: Function to call when MIDI messages are received
        """
        self.midi_callbacks[name] = callback
    
    def unregister_midi_callback(self, name: str):
        """Unregister a MIDI message callback"""
        if name in self.midi_callbacks:
            del self.midi_callbacks[name]
    
    # LED Control Methods
    
    def set_led(self, deck: int, led_type: LEDType, state: bool):
        """
        Set a specific LED on a deck.
        
        Args:
            deck: Deck number (1-2)
            led_type: Type of LED to control
            state: True to turn on, False to turn off
        """
        if not self.outport:
            return
        
        if led_type == LEDType.HOTCUE:
            self._set_hotcue_leds(deck, state)
        elif led_type == LEDType.HOTCUE_EXTENDED:
            self._set_extended_hotcue_leds(deck, state)
        elif led_type == LEDType.AUTOLOOP:
            self._set_autoloop_leds(deck, state)
        elif led_type == LEDType.LOOP:
            self._set_loop_leds(deck, state)
        elif led_type == LEDType.PLAY:
            self._set_play_leds(deck, state)
        elif led_type == LEDType.SYNC:
            self._set_sync_leds(deck, state)
        elif led_type == LEDType.CUE:
            self._set_cue_leds(deck, state)
        elif led_type == LEDType.PFL_CUE:
            self._set_pfl_cue_led(deck, state)
        elif led_type == LEDType.BPM_UP:
            self._set_bpm_up_led(deck, state)
        elif led_type == LEDType.BPM_DOWN:
            self._set_bpm_down_led(deck, state)
        elif led_type == LEDType.KEYLOCK:
            self._set_keylock_led(deck, state)
        elif led_type == LEDType.WHEEL_BUTTON:
            self._set_wheel_button_led(deck, state)
        elif led_type == LEDType.SLIP:
            self._set_slip_led(deck, state)
    
    def _set_hotcue_leds(self, deck: int, state: bool):
        """Set hotcue LEDs (1-4)"""
        channel = self.led_config.channel_offset + (deck - 1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        for note in self.led_config.hotcue_notes:
            if state:
                self.outport.send(mido.Message('note_on', channel=channel, note=note, velocity=velocity))
            else:
                self.outport.send(mido.Message('note_off', channel=channel, note=note, velocity=velocity))
        
        if self.debug:
            print(f"Hotcue LEDs: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_extended_hotcue_leds(self, deck: int, state: bool):
        """Set extended hotcue LEDs (5-8)"""
        channel = self.led_config.channel_offset + (deck - 1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        for note in self.led_config.hotcue_extended_notes:
            if state:
                self.outport.send(mido.Message('note_on', channel=channel, note=note, velocity=velocity))
            else:
                self.outport.send(mido.Message('note_off', channel=channel, note=note, velocity=velocity))
        
        if self.debug:
            print(f"Extended Hotcue LEDs: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_autoloop_leds(self, deck: int, state: bool):
        """Set autoloop LEDs"""
        channel = self.led_config.channel_offset + (deck - 1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        for note in self.led_config.autoloop_notes:
            if state:
                self.outport.send(mido.Message('note_on', channel=channel, note=note, velocity=velocity))
            else:
                self.outport.send(mido.Message('note_off', channel=channel, note=note, velocity=velocity))
        
        if self.debug:
            print(f"AutoLoop LEDs: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_loop_leds(self, deck: int, state: bool):
        """Set loop LEDs"""
        channel = self.led_config.channel_offset + (deck - 1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        for note in self.led_config.loop_notes:
            if state:
                self.outport.send(mido.Message('note_on', channel=channel, note=note, velocity=velocity))
            else:
                self.outport.send(mido.Message('note_off', channel=channel, note=note, velocity=velocity))
        
        if self.debug:
            print(f"Loop LEDs: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_play_leds(self, deck: int, state: bool):
        """Set play LEDs"""
        channel = deck - 1  # Deck channels (0-1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        for note in self.led_config.play_notes:
            if state:
                self.outport.send(mido.Message('note_on', channel=channel, note=note, velocity=velocity))
            else:
                self.outport.send(mido.Message('note_off', channel=channel, note=note, velocity=velocity))
        
        if self.debug:
            print(f"Play LEDs: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_sync_leds(self, deck: int, state: bool):
        """Set sync LEDs"""
        channel = deck - 1  # Deck channels (0-1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        for note in self.led_config.sync_notes:
            if state:
                self.outport.send(mido.Message('note_on', channel=channel, note=note, velocity=velocity))
            else:
                self.outport.send(mido.Message('note_off', channel=channel, note=note, velocity=velocity))
        
        if self.debug:
            print(f"Sync LEDs: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_cue_leds(self, deck: int, state: bool):
        """Set cue LEDs"""
        channel = deck - 1  # Deck channels (0-1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        for note in self.led_config.cue_notes:
            if state:
                self.outport.send(mido.Message('note_on', channel=channel, note=note, velocity=velocity))
            else:
                self.outport.send(mido.Message('note_off', channel=channel, note=note, velocity=velocity))
        
        if self.debug:
            print(f"Cue LEDs: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_pfl_cue_led(self, deck: int, state: bool):
        """Set PFL/Cue LED"""
        channel = deck - 1  # Deck channels (0-1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        if state:
            self.outport.send(mido.Message('note_on', channel=channel, note=self.led_config.pfl_cue_note, velocity=velocity))
        else:
            self.outport.send(mido.Message('note_off', channel=channel, note=self.led_config.pfl_cue_note, velocity=velocity))
        
        if self.debug:
            print(f"PFL/Cue LED: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_bpm_up_led(self, deck: int, state: bool):
        """Set BPM up arrow LED"""
        channel = deck - 1  # Deck channels (0-1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        if state:
            self.outport.send(mido.Message('note_on', channel=channel, note=self.led_config.bpm_up_note, velocity=velocity))
        else:
            self.outport.send(mido.Message('note_off', channel=channel, note=self.led_config.bpm_up_note, velocity=velocity))
        
        if self.debug:
            print(f"BPM Up LED: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_bpm_down_led(self, deck: int, state: bool):
        """Set BPM down arrow LED"""
        channel = deck - 1  # Deck channels (0-1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        if state:
            self.outport.send(mido.Message('note_on', channel=channel, note=self.led_config.bpm_down_note, velocity=velocity))
        else:
            self.outport.send(mido.Message('note_off', channel=channel, note=self.led_config.bpm_down_note, velocity=velocity))
        
        if self.debug:
            print(f"BPM Down LED: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_keylock_led(self, deck: int, state: bool):
        """Set keylock LED"""
        channel = deck - 1  # Deck channels (0-1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        if state:
            self.outport.send(mido.Message('note_on', channel=channel, note=self.led_config.keylock_note, velocity=velocity))
        else:
            self.outport.send(mido.Message('note_off', channel=channel, note=self.led_config.keylock_note, velocity=velocity))
        
        if self.debug:
            print(f"Keylock LED: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_wheel_button_led(self, deck: int, state: bool):
        """Set wheel button LED"""
        channel = deck - 1  # Deck channels (0-1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        if state:
            self.outport.send(mido.Message('note_on', channel=channel, note=self.led_config.wheel_button_note, velocity=velocity))
        else:
            self.outport.send(mido.Message('note_off', channel=channel, note=self.led_config.wheel_button_note, velocity=velocity))
        
        if self.debug:
            print(f"Wheel Button LED: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def _set_slip_led(self, deck: int, state: bool):
        """Set slip LED"""
        channel = deck - 1  # Deck channels (0-1)
        velocity = self.led_config.velocity_on if state else self.led_config.velocity_off
        
        if state:
            self.outport.send(mido.Message('note_on', channel=channel, note=self.led_config.slip_note, velocity=velocity))
        else:
            self.outport.send(mido.Message('note_off', channel=channel, note=self.led_config.slip_note, velocity=velocity))
        
        if self.debug:
            print(f"Slip LED: Deck {deck} {'ON' if state else 'OFF'} (ch={channel})")
    
    def clear_all_leds(self):
        """Clear all LEDs on all decks"""
        if not self.outport:
            return
        
        for deck in [1, 2]:
            # Clear all LED types
            for led_type in LEDType:
                self.set_led(deck, led_type, False)
        
        if self.debug:
            print("All LEDs cleared")
    
    def flash_all_leds(self, deck: int, state: bool):
        """
        Flash all LEDs on a specific deck.
        
        Args:
            deck: Deck number (1-2)
            state: True to turn on all LEDs, False to turn off
        """
        for led_type in LEDType:
            self.set_led(deck, led_type, state)
    
    # Ring Light Control Methods
    
    def set_ring(self, deck: int, ring_type: RingType, position: int):
        """
        Set ring light position.
        
        Args:
            deck: Deck number (1-2)
            ring_type: Type of ring (spinner or position)
            position: Position value (0-max_position)
        """
        if not self.outport:
            return
        
        # Clamp position to valid range
        position = max(0, min(position, self.ring_config.max_position))
        
        channel = deck - 1  # Deck channels (0-1)
        
        if ring_type == RingType.SPINNER:
            # Spinner ring (red) - values 64-115
            value = position + self.ring_config.spinner_offset
            self.outport.send(mido.Message('control_change', 
                                         channel=channel, 
                                         control=self.ring_config.spinner_control, 
                                         value=value))
        elif ring_type == RingType.POSITION:
            # Position ring (white) - values 0-52
            self.outport.send(mido.Message('control_change', 
                                         channel=channel, 
                                         control=self.ring_config.position_control, 
                                         value=position))
        
        if self.debug:
            print(f"Ring {ring_type.value}: Deck {deck} position={position}")
    
    def set_ring_percentage(self, deck: int, ring_type: RingType, percentage: float):
        """
        Set ring light position as percentage.
        
        Args:
            deck: Deck number (1-2)
            ring_type: Type of ring (spinner or position)
            percentage: Percentage value (0.0-100.0)
        """
        position = int(percentage * self.ring_config.max_position / 100.0)
        self.set_ring(deck, ring_type, position)
    
    def clear_rings(self, deck: int):
        """Clear ring lights on a specific deck"""
        self.set_ring(deck, RingType.SPINNER, 0)
        self.set_ring(deck, RingType.POSITION, 0)
    
    # Display Control Methods
    
    def set_bpm_display(self, deck: int, value: Union[int, float]):
        """
        Set BPM display value.
        
        Args:
            deck: Deck number (1-2)
            value: BPM value to display
        """
        if not self.outport:
            return
        
        # Convert value to integer (multiply by 100 for decimal precision)
        if isinstance(value, float):
            int_value = int(value * 100)
        else:
            int_value = int(value)
        
        # Encode to array format
        value_array = self._encode_number_to_array(int_value)
        
        # Remove first two bytes (from Mixxx source)
        value_array = value_array[2:]
        
        # Create SysEx message
        byte_prefix = [0x00, 0x20, 0x7F, deck, self.display_config.bpm_display_type]
        sysex_data = byte_prefix + value_array
        
        msg = mido.Message('sysex', data=sysex_data)
        self.outport.send(msg)
        
        if self.debug:
            print(f"BPM Display: Deck {deck} value={value}")
    
    def set_time_display(self, deck: int, time_ms: int):
        """
        Set time display value.
        
        Args:
            deck: Deck number (1-2)
            time_ms: Time in milliseconds
        """
        if not self.outport:
            return
        
        # Encode time to array format
        time_array = self._encode_number_to_array(time_ms)
        
        # Create SysEx message
        byte_prefix = [0x00, 0x20, 0x7F, deck, self.display_config.time_display_type]
        sysex_data = byte_prefix + time_array
        
        msg = mido.Message('sysex', data=sysex_data)
        self.outport.send(msg)
        
        if self.debug:
            print(f"Time Display: Deck {deck} time={time_ms}ms")
    
    def set_current_time_display(self, deck: int):
        """Set current time on display"""
        now = datetime.now()
        hour_12 = now.hour % 12
        if hour_12 == 0:
            hour_12 = 12
        
        # Convert to milliseconds (HH:MM format)
        time_ms = (hour_12 * 60 + now.minute) * 1000
        self.set_time_display(deck, time_ms)
    
    def _encode_number_to_array(self, number: int) -> List[int]:
        """
        Encode number to array format used by Mixxx.
        
        Args:
            number: Number to encode
            
        Returns:
            List of encoded bytes
        """
        # Ensure number is within valid range for MIDI
        if number < 0:
            number = 0
        elif number > 0x0FFFFFFF:  # 28-bit max
            number = 0x0FFFFFFF
        
        number_array = [
            (number >> 28) & 0x0F,
            (number >> 24) & 0x0F,
            (number >> 20) & 0x0F,
            (number >> 16) & 0x0F,
            (number >> 12) & 0x0F,
            (number >> 8) & 0x0F,
            (number >> 4) & 0x0F,
            number & 0x0F,
        ]
        
        if number < 0:
            number_array[0] = 0x07
        else:
            number_array[0] = 0x08
        
        # Ensure all values are in valid MIDI range (0-127)
        for i in range(len(number_array)):
            number_array[i] = number_array[i] & 0x7F
        
        return number_array
    
    # System Control Methods
    
    def exit_demo_mode(self):
        """Exit demo mode using SysEx message"""
        if not self.outport:
            return
        
        # SysEx message to exit demo mode
        demo_exit_data = [0x7E, 0x00, 0x06, 0x01]
        msg = mido.Message('sysex', data=demo_exit_data)
        self.outport.send(msg)
        
        if self.debug:
            print("Demo mode exit message sent")
    
    def enter_demo_mode(self):
        """Enter demo mode using SysEx message"""
        if not self.outport:
            return
        
        # SysEx message to enter demo mode
        demo_enter_data = [0x7E, 0x00, 0x06, 0x00]
        msg = mido.Message('sysex', data=demo_enter_data)
        self.outport.send(msg)
        
        if self.debug:
            print("Demo mode enter message sent")
    
    # Context Manager Support
    
    def __enter__(self):
        """Context manager entry"""
        if self.connect():
            self.start()
            return self
        else:
            raise RuntimeError("Failed to connect to controller")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Convenience functions for backward compatibility

def create_controller(input_port: Optional[str] = None, 
                     output_port: Optional[str] = None,
                     config_file: Optional[str] = None,
                     debug: bool = False) -> MixtrackPlatinumFX:
    """
    Create and return a MixtrackPlatinumFX controller instance.
    
    Args:
        input_port: MIDI input port name (auto-detect if None)
        output_port: MIDI output port name (auto-detect if None)
        config_file: Path to configuration file (optional)
        debug: Enable debug output
        
    Returns:
        MixtrackPlatinumFX instance
    """
    return MixtrackPlatinumFX(input_port, output_port, config_file, debug)


if __name__ == "__main__":
    # Example usage
    with create_controller(debug=True) as controller:
        print("Controller connected and ready!")
        
        # Flash all LEDs on deck 1
        controller.flash_all_leds(1, True)
        time.sleep(1)
        controller.flash_all_leds(1, False)
        
        # Set ring lights
        controller.set_ring_percentage(1, RingType.SPINNER, 50.0)
        controller.set_ring_percentage(1, RingType.POSITION, 75.0)
        
        # Set displays
        controller.set_bpm_display(1, 128.5)
        controller.set_current_time_display(1)
        
        print("Example completed!")
