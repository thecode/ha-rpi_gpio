from __future__ import annotations
from functools import cached_property

from . import DOMAIN

from time import sleep

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
from homeassistant.components.cover import CoverEntity
from homeassistant.const import CONF_COVERS, CONF_NAME, CONF_UNIQUE_ID
from .hub import BIAS, DRIVE
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import asyncio

CONF_RELAY_PIN = "relay_pin"
CONF_RELAY_TIME = "relay_time"
CONF_STATE_PIN = "state_pin"
CONF_STATE_PULL_MODE = "state_pull_mode"
CONF_INVERT_STATE = "invert_state"
CONF_INVERT_RELAY = "invert_relay"
DEFAULT_RELAY_TIME = 0.2
DEFAULT_STATE_PULL_MODE = "UP"
DEFAULT_INVERT_STATE = False
DEFAULT_INVERT_RELAY = False

_COVERS_SCHEMA = vol.All(
    cv.ensure_list,
    [
        vol.Schema(
            {
                CONF_NAME: cv.string,
                CONF_RELAY_PIN: cv.positive_int,
                CONF_STATE_PIN: cv.positive_int,
                vol.Optional(CONF_UNIQUE_ID): cv.string,
            }
        )
    ],
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_COVERS): _COVERS_SCHEMA,
        vol.Optional(CONF_STATE_PULL_MODE, default=DEFAULT_STATE_PULL_MODE): cv.string,
        vol.Optional(CONF_RELAY_TIME, default=DEFAULT_RELAY_TIME): cv.positive_int,
        vol.Optional(CONF_INVERT_STATE, default=DEFAULT_INVERT_STATE): cv.boolean,
        vol.Optional(CONF_INVERT_RELAY, default=DEFAULT_INVERT_RELAY): cv.boolean,
    }
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

    relay_time = config[CONF_RELAY_TIME]
    state_pull_mode = config[CONF_STATE_PULL_MODE]
    invert_state = config[CONF_INVERT_STATE]
    invert_relay = config[CONF_INVERT_RELAY]
    covers = []
    for cover in config.get(CONF_COVERS):
        try:
            covers.append(
                GPIODCover(
                    hub,
                    cover[CONF_NAME],
                    cover.get(CONF_RELAY_PIN),
                    relay_time,
                    invert_relay,
                    "AS_IS",
                    "PUSH_PULL",
                    cover.get(CONF_STATE_PIN),
                    state_pull_mode,
                    invert_state,
                    cover.get(CONF_UNIQUE_ID) or f"{DOMAIN}_{cover.get(CONF_RELAY_PIN)}_{cover[CONF_NAME].lower().replace(' ', '_')}",
                )
            )
        except Exception as e:
            _LOGGER.error(f"Failed to add cover {cover[CONF_NAME]} for port {cover.get(CONF_RELAY_PIN)}:{cover.get(CONF_STATE_PIN)}: {e}")

    async_add_entities(covers)

class GPIODCover(CoverEntity):
    _attr_should_poll = False

    def __init__(self, hub, name, relay_port, relay_time, relay_active_low, relay_bias, relay_drive,
                 state_port, state_bias, state_active_low, unique_id):
        _LOGGER.debug(f"GPIODCover init: {relay_port}:{state_port} - {name} - {unique_id} - {relay_time}")
        self._hub = hub
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._relay_port = relay_port
        self._relay_time = relay_time
        self._relay_active_low = relay_active_low
        self._relay_bias = relay_bias
        self._relay_drive = relay_drive
        self._state_port = state_port
        self._state_bias = state_bias
        self._state_active_low = state_active_low
        self._relay_line, self._state_line, current_is_on = self._hub.add_cover(
            self._relay_port, self._relay_active_low, self._relay_bias, self._relay_drive,
            self._state_port, self._state_bias, self._state_active_low)        
        self._attr_is_closed = current_is_on
        self.is_on = current_is_on

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        _LOGGER.debug(f"GPIODCover async_added_to_hass: Adding fd:{self._state_line.fd}")
        self._hub._hass.loop.add_reader(self._state_line.fd, self.handle_event)

    async def async_will_remove_from_hass(self) -> None:
        await super().async_will_remove_from_hass()
        _LOGGER.debug(f"GPIODCover async_will_remove_from_hass: Removing fd:{self._state_line.fd}")
        self._hub._hass.loop.remove_reader(self._state_line.fd)
        self._relay_line.release()
        self._state_line.release()

    def handle_event(self):
        for event in self._state_line.read_edge_events():
            self._attr_is_closed = True if event.event_type is event.Type.RISING_EDGE else False
            _LOGGER.debug(f"Event: {event}. New _attr_is_closed value: {self._attr_is_closed}")
        self.schedule_update_ha_state(False)

    async def async_close_cover(self, **kwargs):
        _LOGGER.debug(f"GPIODCover async_close_cover: is_closed: {self.is_closed}. is_closing: {self.is_closing}, is_opening: {self.is_opening}")
        if self.is_closed:
            return
        self._hub.turn_on(self._relay_line, self._relay_port)
        self._attr_is_closing = True
        self.async_write_ha_state()
        await asyncio.sleep(self._relay_time)
        if not self.is_closing:
            # closing stopped
            return
        self._hub.turn_off(self._relay_line, self._relay_port)
        self._attr_is_closing = False
        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs):
        _LOGGER.debug(f"GPIODCover async_open_cover: is_closed: {self.is_closed}. is_closing: {self.is_closing}, is_opening: {self.is_opening}")
        if not self.is_closed:
            return
        self._hub.turn_on(self._relay_line, self._relay_port)
        self._attr_is_opening = True
        self.async_write_ha_state()
        await asyncio.sleep(self._relay_time)
        if not self.is_opening:
            # opening stopped
            return
        self._hub.turn_off(self._relay_line, self._relay_port)
        self._attr_is_opening = False
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs):
        _LOGGER.debug(f"GPIODCover async_stop_cover: is_closed: {self.is_closed}. is_closing: {self.is_closing}, is_opening: {self.is_opening}")
        if not (self.is_closing or self.is_opening):
            return
        self._hub.turn_off(self._relay_line, self._relay_port)
        self._attr_is_opening = False
        self._attr_is_closing = False
        self.async_write_ha_state()

