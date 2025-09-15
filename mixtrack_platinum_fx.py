#!/usr/bin/env python3
"""
MixtrackPlatinumFX - A comprehensive Python library for controlling the Numark Mixtrack Platinum FX controller.

This library provides complete control over all hardware features including:
- LED control (hotcues, autoloops, loops, play, sync, cue, etc.)
- FX button LED control (discovered through USB MIDI traffic analysis)
- Ring light control (spinner and position indicators)
- Display control (BPM displays, time displays, jog wheel displays)
- Rate display control (jogger displays with pitch percentage)
- VU meter control (alternating patterns for alerts)
- MIDI input handling with button LED feedback
- System monitoring integration
- Audio effects control (EasyEffects integration)

Based on the official Mixxx controller mapping, USB MIDI traffic analysis from Serato DJ Lite,
and extensive testing.

Architecture:
- MixtrackPlatinumFX: Main controller class
- LEDController: Handles all LED operations
- DisplayController: Manages displays and rings
- MIDIHandler: Handles MIDI input/output
- Configuration: Centralized configuration management
"""

import mido
import time
import threading
import queue
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager


class LEDType(Enum):
    """LED types available on the controller, organized by category"""
    
    # Basic Control LEDs
    PLAY = "play"
    SYNC = "sync"
    CUE = "cue"
    PFL_CUE = "pfl_cue"
    BPM_UP = "bpm_up"
    BPM_DOWN = "bpm_down"
    KEYLOCK = "keylock"
    WHEEL_BUTTON = "wheel_button"
    SLIP = "slip"
    DECK_ACTIVE = "deck_active"
    RATE_DISPLAY = "rate_display"
    
    # Hotcue LEDs
    HOTCUE = "hotcue"                    # Hotcues 1-4
    HOTCUE_EXTENDED = "hotcue_extended"  # Hotcues 5-8
    
    # Loop LEDs
    AUTOLOOP = "autoloop"                # Autoloop buttons
    LOOP = "loop"                        # Loop buttons
    
    # Pad Mode LEDs
    PAD_MODE_HOTCUE = "pad_mode_hotcue"
    PAD_MODE_AUTOLOOP = "pad_mode_autoloop"
    PAD_MODE_FADERCUTS = "pad_mode_fadercuts"
    PAD_MODE_SAMPLE1 = "pad_mode_sample1"
    PAD_MODE_SAMPLE2 = "pad_mode_sample2"
    PAD_MODE_HOTCUE2 = "pad_mode_hotcue2"
    PAD_MODE_BEATJUMP = "pad_mode_beatjump"
    PAD_MODE_AUTOLOOP2 = "pad_mode_autoloop2"
    PAD_MODE_KEYPLAY = "pad_mode_keyplay"
    PAD_MODE_FADERCUTS2 = "pad_mode_fadercuts2"
    PAD_MODE_FADERCUTS3 = "pad_mode_fadercuts3"
    PAD_MODE_AUTOLOOP3 = "pad_mode_autoloop3"
    PAD_MODE_STEMS = "pad_mode_stems"
    
    # Individual Pad LEDs (16 pads)
    PAD1 = "pad1"
    PAD2 = "pad2"
    PAD3 = "pad3"
    PAD4 = "pad4"
    PAD5 = "pad5"
    PAD6 = "pad6"
    PAD7 = "pad7"
    PAD8 = "pad8"
    PAD9 = "pad9"
    PAD10 = "pad10"
    PAD11 = "pad11"
    PAD12 = "pad12"
    PAD13 = "pad13"
    PAD14 = "pad14"
    PAD15 = "pad15"
    PAD16 = "pad16"
    
    # Effect LEDs
    EFFECT1 = "effect1"
    EFFECT2 = "effect2"
    EFFECT3 = "effect3"
    EFFECT4 = "effect4"
    EFFECT5 = "effect5"
    EFFECT6 = "effect6"
    
    @classmethod
    def get_pad_leds(cls) -> List['LEDType']:
        """Get all individual pad LED types"""
        return [led for led in cls if led.name.startswith('PAD') and led.name != 'PAD_MODE_']
    
    @classmethod
    def get_pad_mode_leds(cls) -> List['LEDType']:
        """Get all pad mode LED types"""
        return [led for led in cls if led.name.startswith('PAD_MODE_')]
    
    @classmethod
    def get_effect_leds(cls) -> List['LEDType']:
        """Get all effect LED types"""
        return [led for led in cls if led.name.startswith('EFFECT')]
    
    @classmethod
    def get_basic_control_leds(cls) -> List['LEDType']:
        """Get all basic control LED types"""
        basic_controls = {
            'PLAY', 'SYNC', 'CUE', 'PFL_CUE', 'BPM_UP', 'BPM_DOWN',
            'KEYLOCK', 'WHEEL_BUTTON', 'SLIP', 'DECK_ACTIVE', 'RATE_DISPLAY'
        }
        return [led for led in cls if led.name in basic_controls]


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
    """Configuration for LED control with organized note mappings"""
    
    # MIDI Configuration
    channel_offset: int = 4
    velocity_on: int = 127
    # Many Mixtrack LEDs expect Note On with velocity 1 to turn off (dim/off)
    velocity_off: int = 1
    
    # Basic Control Notes
    # Basic transport/button notes (per Mixxx mapping, same note per deck; channel varies)
    play_notes: List[int] = field(default_factory=lambda: [0, 0])      # 0x00
    sync_notes: List[int] = field(default_factory=lambda: [2, 2])      # 0x02
    cue_notes: List[int] = field(default_factory=lambda: [5, 5])       # 0x05
    bpm_up_note: int = 11                                              # 0x0B (pitch bend up)
    bpm_down_note: int = 12                                            # 0x0C (pitch bend down)
    keylock_note: int = 13
    pfl_cue_note: int = 27
    wheel_button_note: int = 7
    slip_note: int = 15
    deck_active_note: int = 8
    rate_display_note: int = 14
    
    # Hotcue Notes
    hotcue_notes: List[int] = field(default_factory=lambda: [24, 25, 26, 27])
    hotcue_extended_notes: List[int] = field(default_factory=lambda: [32, 33, 34, 35])
    
    # Loop Notes
    autoloop_notes: List[int] = field(default_factory=lambda: [20, 21, 22, 23, 28, 29, 30, 31])
    loop_notes: List[int] = field(default_factory=lambda: [50, 51, 52, 53, 56, 57])
    
    # Pad Mode Notes
    pad_mode_notes: Dict[str, int] = field(default_factory=lambda: {
                'hotcue': 0, 'autoloop': 13, 'fadercuts': 7, 'sample1': 11, 'sample2': 15,
                'hotcue2': 2, 'beatjump': 1, 'autoloop2': 14, 'keyplay': 12,
                'fadercuts2': 3, 'fadercuts3': 4, 'autoloop3': 5, 'stems': 6
    })
    
    # Individual Pad Notes
    pad_notes: Dict[str, int] = field(default_factory=lambda: {
                'pad1': 20, 'pad2': 21, 'pad3': 22, 'pad4': 23, 'pad5': 24, 'pad6': 25,
                'pad7': 26, 'pad8': 27, 'pad9': 28, 'pad10': 29, 'pad11': 30, 'pad12': 31,
                'pad13': 32, 'pad14': 33, 'pad15': 34, 'pad16': 35
    })
    
    # Effect Notes
    effect_notes: Dict[str, int] = field(default_factory=lambda: {
                'effect1': 0, 'effect2': 1, 'effect3': 2, 'effect4': 3, 'effect5': 4, 'effect6': 5
    })
    
    def get_note_for_led_type(self, led_type: LEDType, deck: int = 1) -> Optional[int]:
        """Get MIDI note for a specific LED type and deck"""
        if led_type == LEDType.PLAY:
            return self.play_notes[deck - 1] if deck <= len(self.play_notes) else None
        elif led_type == LEDType.SYNC:
            return self.sync_notes[deck - 1] if deck <= len(self.sync_notes) else None
        elif led_type == LEDType.CUE:
            return self.cue_notes[deck - 1] if deck <= len(self.cue_notes) else None
        elif led_type == LEDType.BPM_UP:
            return self.bpm_up_note
        elif led_type == LEDType.BPM_DOWN:
            return self.bpm_down_note
        elif led_type == LEDType.KEYLOCK:
            return self.keylock_note
        elif led_type == LEDType.PFL_CUE:
            return self.pfl_cue_note
        elif led_type == LEDType.WHEEL_BUTTON:
            return self.wheel_button_note
        elif led_type == LEDType.SLIP:
            return self.slip_note
        elif led_type == LEDType.DECK_ACTIVE:
            return self.deck_active_note
        elif led_type == LEDType.RATE_DISPLAY:
            return self.rate_display_note
        return None
    
    def get_notes_for_led_type(self, led_type: LEDType) -> List[int]:
        """Get all MIDI notes for a specific LED type"""
        if led_type == LEDType.HOTCUE:
            return self.hotcue_notes
        elif led_type == LEDType.HOTCUE_EXTENDED:
            return self.hotcue_extended_notes
        elif led_type == LEDType.AUTOLOOP:
            return self.autoloop_notes
        elif led_type == LEDType.LOOP:
            return self.loop_notes
        elif led_type == LEDType.PLAY:
            return self.play_notes
        elif led_type == LEDType.SYNC:
            return self.sync_notes
        elif led_type == LEDType.CUE:
            return self.cue_notes
        return []


@dataclass
class RingConfig:
    """Configuration for ring light control"""
    spinner_control: int = 6      # CC 6 for spinner (red) ring
    position_control: int = 63    # CC 63 for position (white) ring
    spinner_offset: int = 64      # Offset for spinner ring
    max_position: int = 52        # Maximum position value
    temp_max: int = 80            # Maximum temperature for scaling


@dataclass
class DisplayConfig:
    """Configuration for display control"""
    bpm_display_type: int = 1     # BPM display type
    time_display_type: int = 4    # Time display type
    vu_meter_control: int = 31    # CC 31 for VU meters
    vu_meter_max: int = 90        # Maximum VU meter value


@dataclass
class MIDIConfig:
    """Configuration for MIDI handling"""
    input_port: Optional[str] = None
    output_port: Optional[str] = None
    input_port_pattern: str = "Mixtrack Platinum FX"
    output_port_pattern: str = "Mixtrack Platinum FX"
    button_led_feedback: bool = True
    led_feedback_duration: float = 0.2
    midi_timeout: float = 0.001


@dataclass
class ControllerConfig:
    """Main configuration class combining all sub-configurations"""
    led: LEDConfig = field(default_factory=LEDConfig)
    ring: RingConfig = field(default_factory=RingConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    midi: MIDIConfig = field(default_factory=MIDIConfig)
    debug: bool = False
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ControllerConfig':
        """Create configuration from dictionary (supports legacy keys)"""
        led_cfg = config_dict.get('led') or config_dict.get('leds') or {}
        ring_cfg = config_dict.get('ring') or config_dict.get('rings') or {}
        display_cfg = config_dict.get('display') or {}
        midi_cfg = config_dict.get('midi') or {}
        dbg_cfg = config_dict.get('debug', False)
        dbg_enabled = bool(dbg_cfg.get('enabled', False)) if isinstance(dbg_cfg, dict) else bool(dbg_cfg)
        return cls(
            led=LEDConfig(**led_cfg),
            ring=RingConfig(**ring_cfg),
            display=DisplayConfig(**display_cfg),
            midi=MIDIConfig(**midi_cfg),
            debug=dbg_enabled
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'led': self.led.__dict__,
            'ring': self.ring.__dict__,
            'display': self.display.__dict__,
            'midi': self.midi.__dict__,
            'debug': self.debug
        }


class MixtrackPlatinumFX:
    """
    Main class for controlling the Numark Mixtrack Platinum FX controller.
    
    This class provides comprehensive control over all hardware features including
    LEDs, ring lights, displays, VU meters, and MIDI input handling with button
    LED feedback.
    
    Features:
    - LED control (all types: hotcues, loops, pads, effects, etc.)
    - Ring light control (spinner and position indicators)
    - Display control (BPM, time, rate displays)
    - VU meter control (for system monitoring alerts)
    - FX button LED control
    - MIDI input handling with button LED feedback
    - System monitoring integration
    - EasyEffects audio effects control
    
    Example:
        with create_controller(debug=True) as controller:
            controller.set_led(1, LEDType.PLAY, True)
            controller.set_ring_percentage(1, RingType.SPINNER, 50.0)
            controller.set_vu_meter(1, 75)
    """
    
    def __init__(self, 
                 input_port: Optional[str] = None,
                 output_port: Optional[str] = None,
                 config: Optional[Union[Dict[str, Any], ControllerConfig]] = None,
                 debug: bool = False,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the MixtrackPlatinumFX controller.
        
        Args:
            input_port: MIDI input port name (auto-detect if None)
            output_port: MIDI output port name (auto-detect if None)
            config: Configuration dictionary or ControllerConfig object
            debug: Enable debug output
            logger: Logger instance (creates default if None)
        """
        # Preserve debug flag for backward-compat (avoid AttributeError before logger exists)
        self.debug = debug
        # Initialize logger
        self.logger = logger or self._create_logger(debug)
        
        # Initialize configuration
        self.config = self._initialize_config(config, debug)
        
        # MIDI ports
        self.input_port = input_port
        self.output_port = output_port
        self.inport = None
        self.outport = None
        
        # Back-compat attributes used elsewhere in the file
        self.led_config = self.config.led
        self.ring_config = self.config.ring
        self.display_config = self.config.display
        
        # MIDI handling
        self.running = False
        self.midi_queue = queue.Queue()
        self.midi_thread = None
        self.midi_callbacks: Dict[str, Callable] = {}
        
        # Button LED feedback
        self.button_led_feedback = self.config.midi.button_led_feedback
        self.led_feedback_duration = self.config.midi.led_feedback_duration
        
        self.logger.info("MixtrackPlatinumFX initialized")
    
    def _create_logger(self, debug: bool) -> logging.Logger:
        """Create logger instance"""
        logger = logging.getLogger('MixtrackPlatinumFX')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG if debug else logging.INFO)
        # Prevent duplicate logs via root logger
        logger.propagate = False
        return logger
    
    def _initialize_config(self, config: Optional[Union[Dict[str, Any], ControllerConfig]], debug: bool) -> ControllerConfig:
        """Initialize configuration from various sources"""
        if isinstance(config, ControllerConfig):
            return config
        elif isinstance(config, dict):
            return ControllerConfig.from_dict(config)
        else:
            # Load from file or use defaults
            config_dict = self._load_config()
            # Only force debug if explicitly requested; otherwise honor config file
            if debug:
                cfg_dbg = config_dict.get('debug')
                if isinstance(cfg_dbg, dict):
                    cfg_dbg['enabled'] = True
                else:
                    config_dict['debug'] = True
            return ControllerConfig.from_dict(config_dict)
    
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
            self.logger.debug(f"Config file not found: {config_file}, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            self.logger.debug(f"Error parsing config file: {e}, using defaults")
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
            },
            'button_led_feedback': {
                'enabled': True,
                'duration': 0.2
            }
        }
    
    def connect(self) -> bool:
        """
        Connect to the MIDI controller.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Connect input port (check both constructor and config)
            input_port = self.input_port or self.config.midi.input_port
            if input_port:
                self.inport = mido.open_input(input_port)
                self.logger.info(f"Connected to input: {self.inport.name}")
            else:
                # Auto-detect input port
                input_ports = [name for name in mido.get_input_names() 
                             if self.config.midi.input_port_pattern in name]
                if input_ports:
                    self.inport = mido.open_input(input_ports[0])
                    self.logger.info(f"Auto-detected input: {self.inport.name}")
                else:
                    raise OSError(f"No input port found matching pattern: {self.config.midi.input_port_pattern}")
            
            # Connect output port (check both constructor and config)
            output_port = self.output_port or self.config.midi.output_port
            if output_port:
                self.outport = mido.open_output(output_port)
                self.logger.info(f"Connected to output: {self.outport.name}")
            else:
                # Auto-detect output port
                output_ports = [name for name in mido.get_output_names() 
                              if self.config.midi.output_port_pattern in name]
                if output_ports:
                    self.outport = mido.open_output(output_ports[0])
                    self.logger.info(f"Auto-detected output: {self.outport.name}")
                else:
                    raise OSError(f"No output port found matching pattern: {self.config.midi.output_port_pattern}")
            
            # Initialize controller
            self.exit_demo_mode()
            self.clear_all_leds()
            
            self.logger.info("Controller connected successfully")
            return True
            
        except OSError as e:
            self.logger.error(f"Connection error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the MIDI controller"""
        try:
            self.stop()
            
            if self.inport:
                self.inport.close()
                self.inport = None
                self.logger.info("Input port disconnected")
            
            if self.outport:
                self.outport.close()
                self.outport = None
                self.logger.info("Output port disconnected")
                
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    def start(self):
        """Start the MIDI input handler thread"""
        if not self.outport:
            raise RuntimeError("Not connected to controller")
        
        if self.running:
            self.logger.warning("MIDI handler already running")
            return
        
        self.running = True
        self.midi_thread = threading.Thread(target=self._midi_handler, daemon=True)
        self.midi_thread.start()
        
        self.logger.info("MIDI handler started")
    
    def stop(self):
        """Stop the MIDI input handler thread"""
        if not self.running:
            return
            
        self.running = False
        if self.midi_thread and self.midi_thread.is_alive():
            self.midi_thread.join(timeout=1.0)
            if self.midi_thread.is_alive():
                self.logger.warning("MIDI thread did not stop gracefully")
        
        self.logger.info("MIDI handler stopped")
    
    def _midi_handler(self):
        """Handle MIDI input in a separate thread"""
        while self.running:
            try:
                if self.inport and self.inport.poll():
                    msg = self.inport.receive()
                    if msg:
                        self.logger.debug(f"MIDI received: {msg}")
                        self.midi_queue.put(msg)
                else:
                    # Very small sleep to keep feedback realtime while yielding CPU
                    time.sleep(self.config.midi.midi_timeout)
            except Exception as e:
                if self.running:
                    self.logger.error(f"MIDI handler error: {e}")
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
                self.logger.error(f"MIDI processing error: {e}")
    
    def _handle_midi_message(self, msg):
        """Handle individual MIDI messages"""
        # Handle button LED feedback
        if self.button_led_feedback and msg.type in ['note_on', 'note_off']:
            self._handle_button_led_feedback(msg)
        
        # Call registered callbacks
        for callback_name, callback in self.midi_callbacks.items():
            try:
                callback(msg)
            except Exception as e:
                self.logger.error(f"Callback {callback_name} error: {e}")
    
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
    
    # ===== Channel/Deck Mapping Helpers =====
    def _get_deck_for_channel(self, channel: int) -> Optional[int]:
        """Map an incoming MIDI channel to logical deck number (1 or 2)."""
        if channel in [0, 4, 8]:
            return 1
        if channel in [1, 5, 9]:
            return 2
        return None

    def _get_output_channel_for_led(self, deck: int, input_channel: int) -> int:
        """Determine the output channel for LED control based on deck and input channel."""
        # If input on deck channels 0/1, map to LED channels via channel_offset
        if input_channel in [0, 1]:
            return (deck - 1) + self.led_config.channel_offset
        # If already an LED channel (4/5) or FX (8/9), keep as-is
        if input_channel in [4, 5, 8, 9]:
            return input_channel
        # Fallback to LED channel by deck
        return (deck - 1) + self.led_config.channel_offset
    
    def _handle_button_led_feedback(self, msg):
        """Handle LED feedback for button presses"""
        if msg.type != 'note_on' or msg.velocity == 0:
            return  # Only handle note_on with velocity > 0
        
        channel = msg.channel
        note = msg.note
        
        self.logger.debug(f"Button LED Feedback: Channel {channel}, Note {note}, Velocity {msg.velocity}")
        
        # Handle FX button channels first
        if channel == 8:  # FX buttons channel 8
            self._flash_fx_button_led(note, channel)
            return
        elif channel == 9:  # FX buttons channel 9
            self._flash_fx_button_led(note, channel)
            return
        
        # Determine deck from channel
        deck = self._get_deck_for_channel(channel)
            
        if deck is None:
            self.logger.debug(f"Button LED Feedback: No deck mapping for channel {channel}")
            return
            
        # Map note to LED type and provide feedback
        led_type = self._map_note_to_led_type(note, channel)
        if led_type:
            # For LED types that have multiple buttons (hotcues, autoloops, loops, pads, effects),
            # use specific button LED feedback instead of turning on all LEDs of that type
            if led_type in [LEDType.HOTCUE, LEDType.HOTCUE_EXTENDED, LEDType.AUTOLOOP, LEDType.LOOP]:
                self._flash_specific_button_led(deck, note, channel)
            elif led_type.name.startswith('PAD') and led_type.name != 'PAD_MODE_':
                self._flash_specific_button_led(deck, note, channel)
            elif led_type.name.startswith('EFFECT'):
                self._flash_specific_button_led(deck, note, channel)
            else:
                self._flash_led_feedback(deck, led_type)
        else:
            self.logger.debug(f"Button LED Feedback: No LED type mapping for note {note} on channel {channel}")
    
    def _map_note_to_led_type(self, note: int, channel: int) -> Optional[LEDType]:
        """Map MIDI note to LED type for feedback"""
        # Deck control LEDs (channels 0-1)
        if channel in [0, 1]:
            if note in self.led_config.play_notes:
                return LEDType.PLAY
            elif note in self.led_config.sync_notes:
                return LEDType.SYNC
            elif note in self.led_config.cue_notes:
                return LEDType.CUE
            elif note == self.led_config.pfl_cue_note:
                return LEDType.PFL_CUE
            elif note == self.led_config.bpm_up_note:
                return LEDType.BPM_UP
            elif note == self.led_config.bpm_down_note:
                return LEDType.BPM_DOWN
            elif note == self.led_config.keylock_note:
                return LEDType.KEYLOCK
            elif note == self.led_config.wheel_button_note:
                return LEDType.WHEEL_BUTTON
            elif note == self.led_config.slip_note:
                return LEDType.SLIP
            elif note == self.led_config.deck_active_note:
                return LEDType.DECK_ACTIVE
            elif note == self.led_config.rate_display_note:
                return LEDType.RATE_DISPLAY
        
        # LED control LEDs were previously on channels 4-5 via mapping; support both
        elif channel in [4, 5, 0, 1]:
            if note in self.led_config.hotcue_notes:
                return LEDType.HOTCUE
            elif note in self.led_config.hotcue_extended_notes:
                return LEDType.HOTCUE_EXTENDED
            elif note in self.led_config.autoloop_notes:
                return LEDType.AUTOLOOP
            elif note in self.led_config.loop_notes:
                return LEDType.LOOP
            elif note in self.led_config.pad_notes.values():
                # Find the pad LED type
                for pad_name, pad_note in self.led_config.pad_notes.items():
                    if pad_note == note:
                        # Map configuration key to LEDType enum name
                        led_name = pad_name.upper()
                        try:
                            return LEDType[led_name]
                        except KeyError:
                            self.logger.warning(f"LEDType {led_name} not found for pad {pad_name}")
                            return None
            elif note in self.led_config.effect_notes.values():
                # Find the effect LED type
                for effect_name, effect_note in self.led_config.effect_notes.items():
                    if effect_note == note:
                        # Map configuration key to LEDType enum name
                        led_name = effect_name.upper()
                        try:
                            return LEDType[led_name]
                        except KeyError:
                            self.logger.warning(f"LEDType {led_name} not found for effect {effect_name}")
                            return None
            elif note in self.led_config.pad_mode_notes.values():
                # Find the pad mode LED type
                for mode_name, mode_note in self.led_config.pad_mode_notes.items():
                    if mode_note == note:
                        # Map configuration key to LEDType enum name
                        led_name = f"PAD_MODE_{mode_name.upper()}"
                        try:
                            return LEDType[led_name]
                        except KeyError:
                            self.logger.warning(f"LEDType {led_name} not found for mode {mode_name}")
                            return None
        
        return None
    
    def _flash_led_feedback(self, deck: int, led_type: LEDType):
        """Flash LED feedback for button press"""
        if not self.outport:
            return
            
        # Turn on LED
        self.set_led(deck, led_type, True)
        
        # Schedule turn off after duration
        def turn_off_led():
            time.sleep(self.led_feedback_duration)
            self.set_led(deck, led_type, False)
        
        # Run in separate thread to avoid blocking
        import threading
        thread = threading.Thread(target=turn_off_led, daemon=True)
        thread.start()
        
        self.logger.debug(f"LED Feedback: {led_type.value} on Deck {deck} for {self.led_feedback_duration}s")
    
    def _flash_specific_button_led(self, deck: int, note: int, channel: int):
        """Flash specific button LED for individual button press"""
        if not self.outport:
            return
            
        # Determine correct output channel for LED control
        out_channel = self._get_output_channel_for_led(deck, channel)
        
        # Send note_on to turn on the specific LED
        import mido
        msg = mido.Message('note_on', channel=out_channel, note=note, velocity=127)
        self.outport.send(msg)
        
        # Schedule turn off after duration
        def turn_off_led():
            time.sleep(self.led_feedback_duration)
            # Send note_on with velocity_off to clear
            msg = mido.Message('note_on', channel=out_channel, note=note, velocity=self.led_config.velocity_off)
            self.outport.send(msg)
        
        # Run in separate thread to avoid blocking
        import threading
        thread = threading.Thread(target=turn_off_led, daemon=True)
        thread.start()
        
        self.logger.debug(f"Specific LED Feedback: Note {note} on Channel {channel} for {self.led_feedback_duration}s")
    
    def _flash_fx_button_led(self, note: int, channel: int):
        """Flash FX button LED feedback"""
        if not self.outport:
            return
            
        # Turn on FX button LED
        # Minimal implementation: send note_on directly
        # FX buttons use channels 8/9 as received; if deck channels arrive, map to 8/9
        import mido
        deck = self._get_deck_for_channel(channel)
        out_channel = channel if channel in [8, 9] else (8 + ((deck - 1) if deck else 0))
        msg = mido.Message('note_on', channel=out_channel, note=note, velocity=127)
        self.outport.send(msg)
        
        # Schedule turn off after duration
        def turn_off_fx_led():
            time.sleep(self.led_feedback_duration)
            msg = mido.Message('note_on', channel=out_channel, note=note, velocity=self.led_config.velocity_off)
            self.outport.send(msg)
        
        # Run in separate thread to avoid blocking
        import threading
        thread = threading.Thread(target=turn_off_fx_led, daemon=True)
        thread.start()
        
        self.logger.debug(f"FX LED Feedback: Button {note} on Channel {channel} for {self.led_feedback_duration}s")
    
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
            self.logger.warning("Cannot set LED: not connected to controller")
            return
            
        try:
            # Use the new unified LED control system
            self._set_led_unified(deck, led_type, state)
        except Exception as e:
            self.logger.error(f"Error setting LED {led_type} on deck {deck}: {e}")
    
    def _set_led_unified(self, deck: int, led_type: LEDType, state: bool):
        """Unified LED control method using configuration-based approach"""
        velocity = self.config.led.velocity_on if state else self.config.led.velocity_off
        channel = (deck - 1) + self.config.led.channel_offset
        
        # Handle different LED types
        if led_type in [LEDType.HOTCUE, LEDType.HOTCUE_EXTENDED, LEDType.AUTOLOOP, LEDType.LOOP]:
            # Multi-note LEDs
            notes = self.config.led.get_notes_for_led_type(led_type)
            for note in notes:
                self._send_note_message(channel, note, velocity)
                
        elif led_type in LEDType.get_basic_control_leds():
            # Single-note basic control LEDs
            note = self.config.led.get_note_for_led_type(led_type, deck)
            if note is not None:
                self._send_note_message(channel, note, velocity)
                
        elif led_type in LEDType.get_pad_mode_leds():
            # Pad mode LEDs
            mode_name = led_type.name.replace('PAD_MODE_', '').lower()
            if mode_name in self.config.led.pad_mode_notes:
                note = self.config.led.pad_mode_notes[mode_name]
                self._send_note_message(channel, note, velocity)
                
        elif led_type in LEDType.get_pad_leds():
            # Individual pad LEDs
            pad_name = led_type.name.lower()
            if pad_name in self.config.led.pad_notes:
                note = self.config.led.pad_notes[pad_name]
                self._send_note_message(channel, note, velocity)
                
        elif led_type in LEDType.get_effect_leds():
            # Effect LEDs
            effect_name = led_type.name.lower()
            if effect_name in self.config.led.effect_notes:
                note = self.config.led.effect_notes[effect_name]
                self._send_note_message(channel, note, velocity)
        
        self.logger.debug(f"Set {led_type} on deck {deck} to {'ON' if state else 'OFF'}")
    
    def _send_note_message(self, channel: int, note: int, velocity: int):
        """Send a MIDI note message"""
        if not self.outport:
            return
            
        # Use note_on for both ON and OFF (velocity 1 off), per controller behavior
        use_velocity = velocity
        if velocity == 0:
            use_velocity = self.config.led.velocity_off
        msg = mido.Message('note_on', channel=channel, note=note, velocity=use_velocity)
        self.outport.send(msg)
    
    def clear_all_leds(self):
        """Clear all LEDs on all decks"""
        if not self.outport:
            return
        
        for deck in [1, 2]:
            # Clear all LED types
            for led_type in LEDType:
                self.set_led(deck, led_type, False)
        
        # Log
        self.logger.debug("All LEDs cleared")
    
    # flash_all_leds removed for simplicity; use targeted UI flashing instead
    
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
        
        self.logger.debug(f"Ring {ring_type.value}: Deck {deck} position={position}")
    
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
    
    # VU Meter Control Methods
    
    def set_vu_meter(self, deck: int, level: float):
        """
        Set VU meter level for a specific deck.
        
        Based on MIDI protocol documentation, VU meters are controlled using
        MIDI Control Change messages with control number 31 (0x1F).
        
        Args:
            deck: Deck number (1-2)
            level: Level as percentage (0.0-100.0) or value (0-90)
        """
        if not self.outport:
            return
        
        # Convert percentage to value if needed
        if level > 1.0:  # Assume percentage if > 1.0
            value = int((level / 100.0) * 90)
        else:  # Assume 0.0-1.0 range
            value = int(level * 90)
        
        # Clamp to valid range (0-90)
        value = max(0, min(90, value))
        
        # Send control change message
        channel = deck - 1  # Deck 1 = Channel 0, Deck 2 = Channel 1
        msg = mido.Message('control_change', 
                          channel=channel, 
                          control=31,  # CC 31 for VU meters
                          value=value)
        self.outport.send(msg)
        
        if self.debug:
            percentage = (value / 90) * 100
            self.logger.debug(f"VU Meter: Deck {deck} -> {value}/90 ({percentage:.1f}%)")
    
    def clear_vu_meter(self, deck: int):
        """Clear VU meter (set to 0)"""
        self.set_vu_meter(deck, 0)
    
    def clear_all_vu_meters(self):
        """Clear all VU meters"""
        for deck in [1, 2]:
            self.clear_vu_meter(deck)
    
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
            self.logger.debug(f"Time Display: Deck {deck} time={time_ms}ms")
    
    def set_rate_display(self, deck: int, rate_percent: float):
        """
        Set rate display value (jogger display) showing percentage.
        
        Based on USB MIDI traffic analysis from Serato DJ Lite, the rate display
        uses a specific encoding format that matches the controller's expectations.
        
        Args:
            deck: Deck number (1-2)
            rate_percent: Rate percentage (e.g., 50.0 for 50.0%, -25.0 for -25.0%)
        """
        if not self.outport:
            return
        
        # Convert percentage to rate display format
        # Based on USB traffic analysis: rate data is encoded as 6-byte values
        # Examples from capture:
        # - 080000000000 = 0% (neutral)
        # - 080000030200 = +3.2%
        # - 070f0f0f0f0d = +15.9% (maximum positive)
        # - 080000010e09 = +1.4%
        
        # The rate display uses a special encoding where:
        # - First byte: 0x08 for positive, 0x07 for negative
        # - Remaining bytes: encoded rate value
        
        if rate_percent >= 0:
            # Positive rate
            sign_byte = 0x08
            rate_value = int(abs(rate_percent) * 100)  # Convert to integer (e.g., 50.0% -> 5000)
        else:
            # Negative rate
            sign_byte = 0x07
            rate_value = int(abs(rate_percent) * 100)  # Convert to integer (e.g., -25.0% -> 2500)
        
        # Encode the rate value into 5 bytes
        # Based on the USB traffic analysis, we need to encode the value properly
        rate_bytes = []
        
        # For small values, use simple encoding
        if rate_value < 10000:  # Less than 100%
            # Simple encoding for values under 100%
            rate_bytes = [
                (rate_value >> 16) & 0x0F,
                (rate_value >> 12) & 0x0F,
                (rate_value >> 8) & 0x0F,
                (rate_value >> 4) & 0x0F,
                rate_value & 0x0F
            ]
        else:
            # For larger values, use the complex encoding seen in USB traffic
            # This matches the pattern seen in the capture data
            rate_bytes = [
                0x0F, 0x0F, 0x0F, 0x0F, 0x0D  # Maximum positive rate pattern
            ]
        
        # Create the complete rate display data
        rate_data = [sign_byte] + rate_bytes
        
        # Create SysEx message for rate display (type 0x02)
        byte_prefix = [0x00, 0x20, 0x7F, deck, 0x02]
        sysex_data = byte_prefix + rate_data
        
        msg = mido.Message('sysex', data=sysex_data)
        self.outport.send(msg)
        
        if self.debug:
            self.logger.debug(f"Rate Display: Deck {deck} rate={rate_percent:.1f}% -> {rate_data}")
    
    # set_rate_display_from_serato_data removed (not used by examples)
    
    # decode_rate_display_data removed (not used by examples)
    
    # FX Button LED Control Methods
    
    # FX button LED helpers removed for minimal surface area
    
    # set_serato_fx_buttons removed (not used by examples)
    
    def clear_all_fx_leds(self):
        if not self.outport:
            return
        # Minimal: clear a small set of known FX notes on channels 8 and 9
        for ch, buttons in ((8, [0,1,2]), (9, [3,4,5])):
            for note in buttons:
                self.outport.send(mido.Message('note_off', channel=ch, note=note, velocity=0))
    
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
        # Store original sign for later use
        is_negative = number < 0
        
        # Ensure number is within valid range for MIDI (use absolute value)
        if number < 0:
            number = abs(number)
        if number > 0x0FFFFFFF:  # 28-bit max
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
        
        # Set sign indicator based on original sign
        if is_negative:
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
            self.logger.debug("Demo mode exit message sent")
    
    def enter_demo_mode(self):
        """Enter demo mode using SysEx message"""
        if not self.outport:
            return
        
        # SysEx message to enter demo mode
        demo_enter_data = [0x7E, 0x00, 0x06, 0x00]
        msg = mido.Message('sysex', data=demo_enter_data)
        self.outport.send(msg)
        
        if self.debug:
            self.logger.debug("Demo mode enter message sent")
    
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
    # Minimal smoke test
    with create_controller(debug=False) as controller:
        controller.clear_all_leds()
