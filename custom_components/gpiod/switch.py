from __future__ import annotations

from . import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import CONF_SWITCHES, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID
CONF_INVERT_LOGIC="invert_logic"
DEFAULT_INVERT_LOGIC = False
CONF_BIAS="bias"
DEFAULT_BIAS = "AS_IS"
CONF_DRIVE ="drive"
DEFAULT_DRIVE = "PUSH_PULL"

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_SWITCHES, CONF_SWITCHES): vol.All(
                cv.ensure_list, [{
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_PORT): cv.positive_int,
                    vol.Optional(CONF_UNIQUE_ID): cv.string,
                    vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
                    vol.Optional(CONF_BIAS, default=DEFAULT_BIAS): cv.string,
                    vol.Optional(CONF_DRIVE, default=DEFAULT_DRIVE): cv.string
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

    switches = []
    for switch in config.get(CONF_SWITCHES):
        switches.append(
            GPIODSwitch(
                hub,
                switch[CONF_NAME],
                switch[CONF_PORT],
                switch.get(CONF_UNIQUE_ID) or f"{DOMAIN}_{switch[CONF_PORT]}_{switch[CONF_NAME].lower().replace(' ', '_')}",
                switch.get(CONF_INVERT_LOGIC),
                switch.get(CONF_BIAS),
                switch.get(CONF_DRIVE)
            )
        )

    async_add_entities(switches)


class GPIODSwitch(SwitchEntity):
    should_poll = False

    def __init__(self, hub, name, port, unique_id, invert_logic, bias, drive):
        _LOGGER.debug(f"GPIODSwitch init: {port} - {name} - {unique_id} - invert_logic: {invert_logic} - bias: {bias} - drive: {drive}")
        self._hub = hub
        self._attr_name = name
        self._port = port
        self._attr_unique_id = unique_id
        self._invert_logic = invert_logic
        self._bias = bias
        self._drive_mode = drive
        self._is_on = False != invert_logic
        hub.add_switch(self, port, invert_logic, bias, drive)

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def is_on(self): 
        return self._is_on

    def turn_on(self, **kwargs):
        self._hub.turn_on(self._port)
        self._is_on = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        self._hub.turn_off(self._port)
        self._is_on = False
        self.schedule_update_ha_state()

    def update(self):
        self._is_on = self._hub.update(self._port)
        self.schedule_update_ha_state(False)
