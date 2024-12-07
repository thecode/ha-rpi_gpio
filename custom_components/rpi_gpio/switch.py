from __future__ import annotations
from typing import Any

from . import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_SWITCHES, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID, STATE_ON
from homeassistant.helpers.restore_state import RestoreEntity
from .hub import BIAS, DRIVE
CONF_INVERT_LOGIC = "invert_logic"
DEFAULT_INVERT_LOGIC = False
CONF_PULL_MODE="pull_mode"
DEFAULT_PULL_MODE = "AS_IS"
CONF_DRIVE ="drive"
DEFAULT_DRIVE = "PUSH_PULL"
CONF_PERSISTENT = "persistent"
DEFAULT_PERSISTENT = False

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend({
        vol.Exclusive(CONF_SWITCHES, CONF_SWITCHES): vol.All(
            cv.ensure_list, [{
                vol.Required(CONF_NAME): cv.string,
                vol.Required(CONF_PORT): cv.positive_int,
                vol.Optional(CONF_UNIQUE_ID): cv.string,
                vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
                vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): vol.In(BIAS.keys()),
                vol.Optional(CONF_DRIVE, default=DEFAULT_DRIVE): vol.In(DRIVE.keys()), 
                vol.Optional(CONF_PERSISTENT, default=DEFAULT_PERSISTENT): cv.boolean,
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
                switch.get(CONF_INVERT_LOGIC),
                switch.get(CONF_PULL_MODE),
                switch.get(CONF_DRIVE),
                switch[CONF_PERSISTENT]
            )
        )

    async_add_entities(switches)


class GPIODSwitch(SwitchEntity, RestoreEntity):
    _attr_should_poll = False

    def __init__(self, hub, name, port, unique_id, active_low, bias, drive, persistent):
        _LOGGER.debug(f"GPIODSwitch init: {port} - {name} - {unique_id} - active_low: {active_low} - bias: {bias} - drive: {drive} - persistent: {persistent}")
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._port = port
        self._active_low = active_low
        self._bias = bias
        self._drive_mode = drive
        self._persistent = persistent
        self._line = None
        
    async def async_added_to_hass(self) -> None:
        """Call when the switch is added to hass."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if not state or not self._persistent:
            self._attr_is_on = False
        else: 
            _LOGGER.debug(f"setting initial persistent state for: {self._port}. state: {state.state}")
            self._attr_is_on = True if state.state == STATE_ON else False
            self.async_write_ha_state()
        self._line = self._hub.add_switch(self, self._port, self._active_low, self._bias, self._drive_mode)

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        _LOGGER.debug(f"GPIODSwitch async_will_remove_from_hass")
        if self._line:
            self._line.release()

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._hub.turn_on(self._line, self._port)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._hub.turn_off(self._line, self._port)
        self._attr_is_on = False
        self.async_write_ha_state()
