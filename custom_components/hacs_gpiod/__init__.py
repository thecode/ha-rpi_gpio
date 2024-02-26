"""Platform for GPIO switch integration"""

from logging import Logger, getLogger
_LOGGER: Logger = getLogger(__package__)

import voluptuous as vol
import homeassistant.helpers.config_validation as cv

import gpiod

DOMAIN = "hacs_gpiod"
CONF_GPIO_DEVICE_PATH = "gpio_device_path"
CONF_SWITCHES = "switches"
CONF_BINARY_SENSORS = "binary_sensors"
CONF_GPIO_PIN = "gpio_pin"
CONF_NAME = "name"

# Define the schema for switch validation
SWITCH_SCHEMA = vol.Schema({
    vol.Required(CONF_GPIO_PIN): cv.positive_int,
    vol.Required(CONF_NAME): cv.string
})

# Define the schema for binary_sensor validation
BINARY_SENSOR_SCHEMA = vol.Schema({
    vol.Required(CONF_GPIO_PIN): cv.positive_int,
    vol.Required(CONF_NAME): cv.string
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

async def async_setup(hass, config):
    gpio_device_path = config.get(DOMAIN, {}).get(CONF_GPIO_DEVICE_PATH)
    switches = config.get(DOMAIN, {}).get(CONF_SWITCHES, [])
    binary_sensors = config.get(DOMAIN, {}).get(CONF_BINARY_SENSORS, [])

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

    for switch_config in switches:
        result = await async_setup_switch(hass, switch_config)
        if not result:
            return False

    for binary_sensor_config in binary_sensors:
        result = await async_setup_binary_sensor(hass, binary_sensor_config)
        if not result:
            return False

    return True


async def async_setup_switch(hass, config):
    _LOGGER.debug(f"adding switch: {config[CONF_NAME]}")

    return True

async def async_setup_binary_sensor(hass, config):
    _LOGGER.debug(f"adding binary_sensor: {config[CONF_NAME]}")

    return True
