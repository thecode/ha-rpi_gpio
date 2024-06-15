from __future__ import annotations

from . import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_SWITCHES, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID
from .hub import BIAS, DRIVE
CONF_ACTIVE_LOW ="active_low"
DEFAULT_ACTIVE_LOW = False
CONF_BIAS="bias"
DEFAULT_BIAS = "AS_IS"
CONF_DRIVE ="drive"
DEFAULT_DRIVE = "PUSH_PULL"

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend({
        vol.Exclusive(CONF_SWITCHES, CONF_SWITCHES): vol.All(
            cv.ensure_list, [{
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_PORT): vol.In(list(range(1,40))),
                vol.Optional(CONF_UNIQUE_ID): cv.string,
                vol.Optional(CONF_ACTIVE_LOW): cv.boolean,
                vol.Optional("invert_logic"): cv.boolean, # backwards compatibility for now
                vol.Optional(CONF_BIAS, default=DEFAULT_BIAS): vol.In(BIAS.keys()),
                vol.Optional(CONF_DRIVE, default=DEFAULT_DRIVE): vol.In(DRIVE.keys()) 
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

    switches = []
    for switch in config.get(CONF_SWITCHES):
        switches.append(
            GPIODSwitch(
                hub,
                switch[CONF_NAME],
                switch[CONF_PORT],
                switch.get(CONF_UNIQUE_ID) or f"{DOMAIN}_{switch[CONF_PORT]}_{switch[CONF_NAME].lower().replace(' ', '_')}",
                switch.get(CONF_ACTIVE_LOW) or switch.get("invert_logic") or DEFAULT_ACTIVE_LOW,
                switch.get(CONF_BIAS),
                switch.get(CONF_DRIVE)
            )
        )

    async_add_entities(switches)


class GPIODSwitch(SwitchEntity):
    should_poll = False

    def __init__(self, hub, name, port, unique_id, active_low, bias, drive):
        _LOGGER.debug(f"GPIODSwitch init: {port} - {name} - {unique_id} - active_low: {active_low} - bias: {bias} - drive: {drive}")
        self._hub = hub
        # self._attr_name = name
        self.name = name
        self.unique_id = unique_id
        self._port = port
        self._attr_unique_id = unique_id
        self._active_low = active_low
        self._bias = bias
        self._drive_mode = drive
        hub.add_switch(self, port, active_low, bias, drive)

    def turn_on(self, **kwargs):
        self._hub.turn_on(self._port)
        self.is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        self._hub.turn_off(self._port)
        self.is_on = False
        self.schedule_update_ha_state()

    def update(self):
        self.is_on = self._hub.update(self._port)
        self.schedule_update_ha_state(False)
