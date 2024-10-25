from __future__ import annotations

from . import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import CONF_SENSORS, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID
from .hub import BIAS
CONF_INVERT_LOGIC = "invert_logic"
DEFAULT_INVERT_LOGIC = False
CONF_BOUNCETIME = "bouncetime"
DEFAULT_BOUNCETIME = 50
CONF_PULL_MODE = "pull_mode"
DEFAULT_PULL_MODE = "UP"

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend({
        vol.Exclusive(CONF_SENSORS, CONF_SENSORS): vol.All(
            cv.ensure_list, [{
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_PORT): cv.positive_int,
                vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
                vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
                vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
                vol.Optional(CONF_UNIQUE_ID): cv.string,
            }]
        )
    })
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None) -> None:

    _LOGGER.debug(f"setup_platform: {config}")
    hub = hass.data[DOMAIN]
    if not hub._online:
        _LOGGER.error("hub not online, bailing out")

    sensors = []
    for sensor in config.get(CONF_SENSORS):
        sensors.append(
            GPIODBinarySensor(
                hub,
                sensor[CONF_NAME],
                sensor[CONF_PORT],
                sensor.get(CONF_UNIQUE_ID) or f"{DOMAIN}_{sensor[CONF_PORT]}_{sensor[CONF_NAME].lower().replace(' ', '_')}",
                sensor.get(CONF_INVERT_LOGIC),
                sensor.get(CONF_PULL_MODE),
                sensor.get(CONF_BOUNCETIME)
            )
        )

    async_add_entities(sensors)


class GPIODBinarySensor(BinarySensorEntity):
    _attr_should_poll = False

    def __init__(self, hub, name, port, unique_id, active_low, bias, debounce):
        _LOGGER.debug(f"GPIODBinarySensor init: {port} - {name} - {unique_id}")
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._port = port
        self._active_low = active_low
        self._bias = bias
        self._debounce = debounce

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._hub.add_sensor(self, self._port, self._active_low, self._bias, self._debounce)
        self.async_write_ha_state()

    def handle_event(self):
        self._attr_is_on = self._hub.get_line_value(self._port)
        self.schedule_update_ha_state(False)
