"""Support for binary sensor using RPi GPIO."""
from __future__ import annotations
from datetime import timedelta

import asyncio

import voluptuous as vol

from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_SENSORS,
    CONF_UNIQUE_ID,
    DEVICE_DEFAULT_NAME,
)
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.reload import setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.event import async_track_time_interval

from . import DOMAIN, PLATFORMS, edge_detect, read_input, setup_input

CONF_BOUNCETIME = "bouncetime"
CONF_INVERT_LOGIC = "invert_logic"
CONF_PORTS = "ports"
CONF_PULL_MODE = "pull_mode"

DEFAULT_BOUNCETIME = 50
DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = "UP"

_SENSORS_LEGACY_SCHEMA = vol.Schema({cv.positive_int: cv.string})

_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
        vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_PORTS, CONF_SENSORS): _SENSORS_LEGACY_SCHEMA,
            vol.Exclusive(CONF_SENSORS, CONF_SENSORS): vol.All(
                cv.ensure_list, [_SENSOR_SCHEMA]
            ),
            vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
            vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
            vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
        },
    ),
    cv.has_at_least_one_key(CONF_PORTS, CONF_SENSORS),
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Raspberry PI GPIO devices."""
    setup_reload_service(hass, DOMAIN, PLATFORMS)

    sensors = []

    sensors_conf = config.get(CONF_SENSORS)
    if sensors_conf is not None:
        for sensor in sensors_conf:
            sensors.append(
                RPiGPIOBinarySensor(
                    sensor[CONF_NAME],
                    sensor[CONF_PORT],
                    sensor[CONF_PULL_MODE],
                    sensor[CONF_BOUNCETIME],
                    sensor[CONF_INVERT_LOGIC],
                    sensor.get(CONF_UNIQUE_ID),
                )
            )

        add_entities(sensors, True)
        return

    pull_mode = config[CONF_PULL_MODE]
    bouncetime = config[CONF_BOUNCETIME]
    invert_logic = config[CONF_INVERT_LOGIC]

    ports = config[CONF_PORTS]
    for port_num, port_name in ports.items():
        sensors.append(
            RPiGPIOBinarySensor(
                port_name, port_num, pull_mode, bouncetime, invert_logic
            )
        )

    add_entities(sensors, True)


class RPiGPIOBinarySensor(BinarySensorEntity):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    @callback
    async def async_added_to_hass(self):
        # Arm the timer
        timer_cancel = async_track_time_interval(
            self.hass,
            self.update_gpio,   # launch every second
            interval=timedelta(seconds=1),
        )
        # stop the timer
        self.async_on_remove(timer_cancel)

    async def update_gpio(self, _):
        event = edge_detect(self._port, self._bouncetime)
        if event is True:
            self._state = read_input(self._port)
        self.async_write_ha_state()

    def __init__(self, name, port, pull_mode, bouncetime, invert_logic, unique_id=None):
        """Initialize the RPi binary sensor."""
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_unique_id = unique_id
        self._attr_should_poll = False
        self._port = port
        self._pull_mode = pull_mode
        self._bouncetime = bouncetime
        self._invert_logic = invert_logic
        self._state = None

        setup_input(self._port, self._pull_mode)

        event = edge_detect(self._port, self._bouncetime)

    @property
    def is_on(self):
        """Return the state of the entity."""
        return self._state != self._invert_logic

    def update(self):
        """Update the GPIO state."""
        self._state = read_input(self._port)