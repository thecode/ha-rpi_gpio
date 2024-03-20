from __future__ import annotations

from . import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)


from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_UNIQUE_ID, DEVICE_DEFAULT_NAME

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive("switches", "switches"): vol.All(
                cv.ensure_list, [{
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_PORT): cv.positive_int,
                    vol.Optional(CONF_UNIQUE_ID): cv.string
                }]
            )
        }
    )
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None) -> None:
    
    _LOGGER.debug(f"@start of setup_platform {config} {DEVICE_DEFAULT_NAME}")
    hub = hass.data[DOMAIN]

    switches = []
    for switch in config.get("switches"):
        switches.append(GPIODSwitch(
                hub,
                switch[CONF_NAME],
                switch[CONF_PORT],
                switch.get(CONF_UNIQUE_ID) or f"gpio_{switch[CONF_PORT]}_{switch[CONF_NAME].lower().replace(' ', '_')}"
            )
        )

    add_entities(switches)


class GPIODSwitch(SwitchEntity):
    def __init__(self, hub, name, port, unique_id):
        _LOGGER.debug(f"in GPIODSwitch __init__ {name} {port} {unique_id}")
        self._hub = hub
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_unique_id = unique_id
        self._attr_should_poll = False
        self._port = port
        self._state = False
        hub.add_switch(port)

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def is_on(self): 
        return self._state

    def turn_on(self, **kwargs):
        self._hub.turn_on(self._port)
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        self._hub.turn_off(self._port)
        self._state = False
        self.schedule_update_ha_state()

