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

CONF_RELAY_PORT = "relay_port"
CONF_RELAY_TIME = "relay_time"
DEFAULT_RELAY_TIME = 2000
CONF_RELAY_ACTIVE_LOW = "relay_active_low"
DEFAULT_RELAY_ACTIVE_LOW = False
CONF_RELAY_BIAS = "relay_bias"
DEFAULT_RELAY_BIAS = "AS_IS"
CONF_RELAY_DRIVE = "relay_drive"
DEFAULT_RELAY_DRIVE = "PUSH_PULL"
CONF_STATE_PORT = "state_port"
CONF_STATE_BIAS = "state_pull_mode"
DEFAULT_STATE_BIAS = "PULL_UP"
CONF_STATE_ACTIVE_LOW = "state_active_low"
DEFAULT_STATE_ACTIVE_LOW = False

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_COVERS, CONF_COVERS): vol.All(
                cv.ensure_list, [{
                    vol.Required(CONF_NAME): cv.string,
                    vol.Optional(CONF_RELAY_PORT): cv.positive_int,
                    vol.Optional("relay_pin"): cv.positive_int, # backwards compatibility for now
                    vol.Optional(CONF_RELAY_TIME, default=DEFAULT_RELAY_TIME): cv.positive_int,
                    vol.Optional(CONF_RELAY_ACTIVE_LOW): cv.boolean,
                    vol.Optional("invert_relay"): cv.boolean, # backwards compatibility for now
                    vol.Optional(CONF_RELAY_BIAS, default=DEFAULT_RELAY_BIAS): vol.In(BIAS.keys()),
                    vol.Optional(CONF_RELAY_DRIVE, default=DEFAULT_RELAY_DRIVE): vol.In(DRIVE.keys()),
                    vol.Optional(CONF_STATE_PORT): cv.positive_int,
                    vol.Optional("state_pin"): cv.positive_int,  # backwards compatibility for now
                    vol.Optional(CONF_STATE_BIAS): vol.In(BIAS.keys()),
                    vol.Optional("state_pull_mode"): vol.In(BIAS.keys()), # backwards compatibility for now
                    vol.Optional(CONF_STATE_ACTIVE_LOW): cv.boolean,
                    vol.Optional("invert_state"): cv.boolean, # backwards compatibility for now
                    vol.Optional(CONF_UNIQUE_ID): cv.string,
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

    covers = []
    for cover in config.get(CONF_COVERS):
        covers.append(
            GPIODCover(
                hub,
                cover[CONF_NAME],
                cover.get(CONF_RELAY_PORT) or cover.get("relay_pin"),
                cover[CONF_RELAY_TIME],
                cover.get(CONF_RELAY_ACTIVE_LOW) or cover.get("invert_relay") or DEFAULT_RELAY_ACTIVE_LOW,
                cover.get(CONF_RELAY_BIAS),
                cover.get(CONF_RELAY_DRIVE),
                cover.get(CONF_STATE_PORT) or cover.get("state_pin"),
                cover.get(CONF_STATE_BIAS) or cover.get("state_bias") or DEFAULT_STATE_BIAS,
                cover.get(CONF_STATE_ACTIVE_LOW) or cover.get("invert_state") or DEFAULT_STATE_ACTIVE_LOW,
                cover.get(CONF_UNIQUE_ID) or f"{DOMAIN}_{cover.get(CONF_RELAY_PORT) or cover.get("relay_pin")}_{cover[CONF_NAME].lower().replace(' ', '_')}",
            )
        )

    async_add_entities(covers)

class GPIODCover(CoverEntity):
    should_poll = False

    def __init__(self, hub, name, relay_port, relay_time, relay_active_low, relay_bias, relay_drive,
                 state_port, state_bias, state_active_low, unique_id):
        _LOGGER.debug(f"GPIODCover init: {relay_port}:{state_port} - {name} - {unique_id} - {relay_time}")
        self._hub = hub
        self.name = name
        self._relay_port = relay_port
        self._relay_time = relay_time
        self._relay_active_low = relay_active_low
        self._relay_bias = relay_bias
        self._relay_drive = relay_drive
        self._state_port = state_port
        self._state_bias = state_bias
        self._start_active_low = state_active_low
        self.unique_id = unique_id
        self._attr_is_closed = False != state_active_low
        hub.add_cover(self, relay_port, relay_active_low, relay_bias, relay_drive,
                      state_port, state_bias, state_active_low)

    def update(self):
        self.is_closed = self._hub.update(self._state_port)
        self.schedule_update_ha_state(False)

    def close_cover(self, **kwargs):
        if self.is_closed:
            return
        self._hub.turn_on(self._relay_port)
        self.is_closing = True
        # self.is_closed = None
        self.schedule_update_ha_state(False)
        sleep(self._relay_time/1000)
        if not self.is_closing:
            # closing stopped
            return
        self._hub.turn_off(self._relay_port)
        self.is_closing = False
        self.update()

    def open_cover(self, **kwargs):
        if not self.is_closed:
            return
        self._hub.turn_on(self._relay_port)
        self.is_opening = True
        # self.is_closed = None
        self.schedule_update_ha_state(False)
        sleep(self._relay_time/1000)
        if not self.is_opening:
            # opening stopped
            return
        self._hub.turn_off(self._relay_port)
        self.is_opening = False
        self.update()

    def stop_cover(self, **kwargs):
        if not (self.is_closing or self.is_opening):
            return
        self._hub.turn_off(self._relay_port)
        self.is_opening = False
        self.is_closing = False
        self.schedule_update_ha_state(False)
