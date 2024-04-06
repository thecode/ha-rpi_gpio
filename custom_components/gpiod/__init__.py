"""Support for controlling GPIO pins of a device."""

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .hub import Hub

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    Platform,
    CONF_PATH
)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.COVER,
    Platform.SWITCH,
]

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({
            vol.Optional(CONF_PATH, default="/dev/gpiochip0"): cv.string
        })
    },
    extra=vol.ALLOW_EXTRA
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the GPIO component."""
    path = config.get(DOMAIN, {}).get(CONF_PATH) or "/dev/gpiochip0" # last part for backwards compatibility
    hub = Hub(hass, path)
    hass.data[DOMAIN] = hub

    return True

