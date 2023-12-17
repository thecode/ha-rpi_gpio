"""Support for controlling GPIO pins of a Raspberry Pi."""

from collections import defaultdict

import gpiod
import time

from homeassistant.const import (
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "rpi_gpio"
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.COVER,
    Platform.SWITCH,
]

# Using globals like this seems a bit icky, but since GPIO pins
# are global in very physical sense it might be fine.
gpiod_config = defaultdict(gpiod.LineSettings)
gpiod_lines = None

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Raspberry PI GPIO component."""

    def cleanup_gpio(event):
        """Stuff to do before stopping."""
        global gpiod_config, gpiod_lines
        gpiod_config.clear()
        if gpiod_lines:
            gpiod_lines.release()

    def prepare_gpio(event):
        """Stuff to do when Home Assistant starts."""
        hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup_gpio)

    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, prepare_gpio)
    return True

def update_gpiod_lines():
    global gpiod_config, gpiod_lines
    
    if gpiod_lines:
        gpiod_lines.__exit__(None,None,None)

    gpiod_lines = gpiod.request_lines(
        "/dev/gpiochip4",
        consumer="ha-rpi_gpio",
        config=gpiod_config)

def setup_output(port, invert_logic):
    """Set up a GPIO as output."""
    global gpiod_config
    gpiod_config[port].direction = gpiod.line.Direction.OUTPUT
    gpiod_config[port].output_value = gpiod.line.Value.ACTIVE if invert_logic else gpiod.line.Value.INACTIVE

    update_gpiod_lines()

def setup_input(port, pull_mode):
    """Set up a GPIO as input."""
    global gpiod_config
    gpiod_config[port].direction = gpiod.line.Direction.INPUT
    gpiod_config[port].bias = gpiod.line.Bias.PULL_DOWN if pull_mode == "DOWN" else gpiod.line.Bias.PULL_UP

    update_gpiod_lines()

def write_output(port, value):
    """Write a value to a GPIO."""
    global gpiod_lines
    gpiod_lines.set_value(port, gpiod.line.Value.ACTIVE if value else gpiod.line.Value.INACTIVE)

def read_input(port):
    """Read a value from a GPIO."""
    global gpiod_lines
    return gpiod_lines.get_value(port) == gpiod.line.Value.ACTIVE

def edge_detect(port, event_callback, bounce):
    """Add detection for RISING and FALLING events."""
    # TODO
