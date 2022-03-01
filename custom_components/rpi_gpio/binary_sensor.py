"""Support for binary sensor using RPi GPIO."""
from __future__ import annotations

import asyncio

import voluptuous as vol

from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.const import DEVICE_DEFAULT_NAME
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.reload import setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, PLATFORMS, edge_detect, read_input, setup_input

CONF_BOUNCETIME = "bouncetime"
CONF_INVERT_LOGIC = "invert_logic"
CONF_PORTS = "ports"
CONF_PULL_MODE = "pull_mode"

DEFAULT_BOUNCETIME = 50
DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = "UP"

_SENSORS_SCHEMA = vol.Schema({cv.positive_int: cv.string})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_PORTS): _SENSORS_SCHEMA,
        vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Raspberry PI GPIO devices."""
    setup_reload_service(hass, DOMAIN, PLATFORMS)

    pull_mode = config[CONF_PULL_MODE]
    bouncetime = config[CONF_BOUNCETIME]
    invert_logic = config[CONF_INVERT_LOGIC]

    binary_sensors = []
    ports = config[CONF_PORTS]
    for port_num, port_name in ports.items():
        binary_sensors.append(
            RPiGPIOBinarySensor(
                port_name, port_num, pull_mode, bouncetime, invert_logic
            )
        )
    add_entities(binary_sensors, True)


class RPiGPIOBinarySensor(BinarySensorEntity):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    async def async_read_gpio(self):
        """Read state from GPIO."""
        await asyncio.sleep(float(self._bouncetime) / 1000)
        self._state = await self.hass.async_add_executor_job(read_input, self._port)
        self.async_write_ha_state()

    def __init__(self, name, port, pull_mode, bouncetime, invert_logic):
        """Initialize the RPi binary sensor."""
        self._name = name or DEVICE_DEFAULT_NAME
        self._port = port
        self._pull_mode = pull_mode
        self._bouncetime = bouncetime
        self._invert_logic = invert_logic
        self._state = None

        setup_input(self._port, self._pull_mode)

        def edge_detected(port):
            """Edge detection handler."""
            if self.hass is not None:
                self.hass.add_job(self.async_read_gpio)

        edge_detect(self._port, edge_detected, self._bouncetime)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self._state != self._invert_logic

    def update(self):
        """Update the GPIO state."""
        self._state = read_input(self._port)
