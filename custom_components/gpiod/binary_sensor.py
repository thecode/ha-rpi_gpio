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
CONF_ACTIVE_LOW = "active_low"
DEFAULT_ACTIVE_LOW = False
CONF_BIAS = "bias"
DEFAULT_BIAS = "PULL_UP"
CONF_DEBOUNCE= "debounce"
DEFAULT_DEBOUNCE = 50

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend({
        vol.Exclusive(CONF_SENSORS, CONF_SENSORS): vol.All(
            cv.ensure_list, [{
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_PORT): cv.positive_int,
                vol.Optional(CONF_UNIQUE_ID): cv.string,
                vol.Optional(vol.Any(CONF_ACTIVE_LOW, "invert_logic")): cv.boolean,
                vol.Optional(vol.Any(CONF_BIAS, "pull_mode")): vol.In(BIAS.keys()),
                vol.Optional(CONF_DEBOUNCE, default=DEFAULT_DEBOUNCE): cv.positive_int
            }]
        )
    }
                           )
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
                sensor.get(CONF_ACTIVE_LOW) or sensor.get("invert_logic") or DEFAULT_ACTIVE_LOW,
                sensor.get(CONF_BIAS) or sensor.get("pull_mode") or DEFAULT_BIAS,
                sensor.get(CONF_DEBOUNCE)
            )
        )

    async_add_entities(sensors)


class GPIODBinarySensor(BinarySensorEntity):
    should_poll = False

    def __init__(self, hub, name, port, unique_id, active_low, bias, debounce):
        _LOGGER.debug(f"GPIODBinarySensor init: {port} - {name} - {unique_id}")
        self._hub = hub
        self.name = name
        self.unique_id = unique_id
        self._port = port
        self._active_low = active_low
        self._bias = bias
        self._debounce = debounce
        hub.add_sensor(self, port, active_low, bias, debounce)

    def update(self):
        self.is_on = self._hub.update(self._port)
        self.schedule_update_ha_state(False)
