"""Support for controlling GPIO pins of a Raspberry Pi."""

from RPi import GPIO  # pylint: disable=import-error

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


def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Raspberry PI GPIO component."""

    def cleanup_gpio(event):
        """Stuff to do before stopping."""
        GPIO.cleanup()

    def prepare_gpio(event):
        """Stuff to do when Home Assistant starts."""
        hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, cleanup_gpio)

    hass.bus.listen_once(EVENT_HOMEASSISTANT_START, prepare_gpio)
    GPIO.setmode(GPIO.BCM)
    return True


def setup_output(port):
    """Set up a GPIO as output."""
    GPIO.setup(port, GPIO.OUT)


def setup_input(port, pull_mode):
    """Set up a GPIO as input."""
    GPIO.setup(port, GPIO.IN, GPIO.PUD_DOWN if pull_mode == "DOWN" else GPIO.PUD_UP)


def write_output(port, value):
    """Write a value to a GPIO."""
    GPIO.output(port, value)


def read_input(port):
    """Read a value from a GPIO."""
    return GPIO.input(port)


def edge_detect(port, event_callback, bounce):
    """Add detection for RISING and FALLING events."""
    GPIO.add_event_detect(port, GPIO.BOTH, callback=event_callback, bouncetime=bounce)
