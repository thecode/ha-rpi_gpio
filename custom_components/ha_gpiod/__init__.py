"""Platform for GPIO switch integration"""

import logging
_LOGGER = logging.getLogger(__name__)

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import (
    DEVICE_DEFAULT_NAME,
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID
)
from collections import defaultdict
from datetime import timedelta
import gpiod
from gpiod.line import Bias, Direction, Value

DOMAIN = "ha_gpiod"
CONF_GPIO_DEVICE_PATH = "gpio_device_path"
CONF_SWITCHES = "switches"
CONF_BINARY_SENSORS = "binary_sensors"
CONF_BOUNCE="bounce"
CONF_BIAS="bias"

# Define the schema for switch validation
SWITCH_SCHEMA = vol.Schema({
    vol.Required(CONF_PORT): cv.positive_int,
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_UNIQUE_ID): cv.string
})

# Define the schema for binary_sensor validation
BINARY_SENSOR_SCHEMA = vol.Schema({
    vol.Required(CONF_PORT): cv.positive_int,
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
    vol.Optional(CONF_BOUNCE, default=250): cv.positive_int,
    vol.Optional(CONF_BIAS, default="UP"): cv.string
})

# Define the schema for configuration
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema({
            vol.Optional(CONF_GPIO_DEVICE_PATH, default="/dev/gpiochip0"): cv.string,
            vol.Optional(CONF_SWITCHES, default = []): vol.All([ SWITCH_SCHEMA ]),
            vol.Optional(CONF_BINARY_SENSORS, default = []): vol.All([ BINARY_SENSOR_SCHEMA ]),
        })
    },
    extra=vol.ALLOW_EXTRA,
)

gpiod_lines = []

def setup(hass, config):
    """setup gpio device"""
    global gpiod_lines
    gpio_device_path = config.get(DOMAIN, {}).get(CONF_GPIO_DEVICE_PATH)
    switches_config = config.get(DOMAIN, {}).get(CONF_SWITCHES, [])
    binary_sensors_config = config.get(DOMAIN, {}).get(CONF_BINARY_SENSORS, [])

    _LOGGER.debug(f"initializing: {gpio_device_path}")

    if not gpiod.is_gpiochip_device(gpio_device_path):
        _LOGGER.warning(f"initilization failed: {gpio_device_path} not a gpiochip_device")
        return False
    chip = gpiod.Chip(gpio_device_path)
    info = chip.get_info()
    _LOGGER.debug(f"initializing: {gpio_device_path}, {info}")
    # true if valid gpiochip
    has_pinctrl = "pinctrl" in info.label
    if not has_pinctrl:
        _LOGGER.warning(f"initialization failed: {gpio_device_path} no pinctrl")
        return False
    _LOGGER.debug(f"initialized: {gpio_device_path}")

    gpiod_config = defaultdict(gpiod.LineSettings)
    for config in switches_config:
        _LOGGER.debug(config)
        gpiod_config[config[CONF_PORT]].direction = Direction.OUTPUT
        gpiod_config[config[CONF_PORT]].output_value = Value.INACTIVE

    for config in binary_sensors_config:
        _LOGGER.debug(config)
        gpiod_config[config[CONF_PORT]].direction = Direction.INPUT
        gpiod_config[config[CONF_PORT]].bias = Bias.PULL_UP if config[CONF_BIAS] == "UP" else Bias.PULL_DOWN
        gpiod_config[config[CONF_PORT]].debounce_period = timedelta(milliseconds=config[CONF_BOUNCE])

    _LOGGER.debug(gpiod_config)
    return True

def unload ():
    """Unload gpio device"""
    global gpiod_lines
    _LOGGER.debug("unloading")
    if gpiod_lines: 
        _LOGGER.debug(f"Releasing {gpiod_lines}")
        gpiod_lines.release()

    return True


def setup_switch(hass, config):
    _LOGGER.debug(f"adding switch: {config[CONF_NAME]}")

    return True

def setup_binary_sensor(hass, config):
    _LOGGER.debug(f"adding binary_sensor: {config[CONF_NAME]}")

    return True

class GPIODSwitch(SwitchEntity):
    """Representation of a GPIO"""

    def __init__(self, name, port, invert_logic = False, unique_id = None):
        """Initialize the gpio pin"""
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_unique_id = unique_id
        self._attr_should_poll = False
        self._port = port
        self._invert_logic = invert_logic
        self._state = False
        # setup gpio here

    def is_on(self):
        """Return true if devices is on"""
        return self._state

    def turn_on(self, **kwargs):
        """Turn on the device"""
        # turn gpio on
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn off the device"""
        # turn gpio off
        self._state = False
        self.schedule_update_ha_state()


