#!/usr/bin/env python3
"""
Verify LED Mapping - lights each mapped LED briefly on both decks.

This script uses the unified set_led API and cycles through:
- Basic control LEDs (play, sync, cue, etc.)
- Group LEDs (hotcues, extended hotcues, autoloops, loops)
- Pad mode LEDs
- Individual pad LEDs
- Effect LEDs

It will flash each LED briefly on Deck 1 and Deck 2.
"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mixtrack_platinum_fx import create_controller, LEDType


def flash_led(controller, deck, led_type, duration=0.12):
    try:
        controller.set_led(deck, led_type, True)
        time.sleep(duration)
    finally:
        controller.set_led(deck, led_type, False)


def main():
    print("🧪 Verifying LED mappings (Deck 1 and Deck 2)...")
    with create_controller(debug=False) as controller:
        # Basic controls
        basics = LEDType.get_basic_control_leds()
        print(f"- Basic controls: {len(basics)}")
        for deck in (1, 2):
            for led in basics:
                flash_led(controller, deck, led)

        # Group LEDs
        groups = [LEDType.HOTCUE, LEDType.HOTCUE_EXTENDED, LEDType.AUTOLOOP, LEDType.LOOP]
        print(f"- Groups (hotcues/loops): {len(groups)}")
        for deck in (1, 2):
            for led in groups:
                flash_led(controller, deck, led)

        # Pad modes
        pad_modes = LEDType.get_pad_mode_leds()
        print(f"- Pad modes: {len(pad_modes)}")
        for deck in (1, 2):
            for led in pad_modes:
                flash_led(controller, deck, led)

        # Individual pads
        pads = LEDType.get_pad_leds()
        print(f"- Pads: {len(pads)}")
        for deck in (1, 2):
            for led in pads:
                flash_led(controller, deck, led, duration=0.06)

        # Effect LEDs
        effects = LEDType.get_effect_leds()
        print(f"- Effects: {len(effects)}")
        for deck in (1, 2):
            for led in effects:
                flash_led(controller, deck, led)

        controller.clear_all_leds()
        print("✅ LED mapping verification complete.")

        # Listen for raw MIDI so you can report any missing LEDs/notes
        print("\n🔎 Listening for MIDI input (press Ctrl+C to exit)...")

        def midi_logger(msg):
            try:
                if msg.type in ("note_on", "note_off"):
                    print(f"MIDI {msg.type}: ch={msg.channel} note={msg.note} vel={msg.velocity}")
                elif msg.type == "control_change":
                    print(f"MIDI cc: ch={msg.channel} control={msg.control} value={msg.value}")
            except Exception:
                pass

        controller.register_midi_callback("verify_logger", midi_logger)

        try:
            while True:
                controller.process_midi_events()
                time.sleep(0.01)
        except KeyboardInterrupt:
            controller.unregister_midi_callback("verify_logger")
            print("\n👋 Exiting listener.")


if __name__ == "__main__":
    main()


