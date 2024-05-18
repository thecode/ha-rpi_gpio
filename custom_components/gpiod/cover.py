from __future__ import annotations

from . import DOMAIN

from time import sleep

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.cover import PLATFORM_SCHEMA, CoverEntity
from homeassistant.const import CONF_COVERS, CONF_NAME, CONF_PORT, CONF_UNIQUE_ID
CONF_RELAY_PIN = "relay_pin"
CONF_RELAY_TIME = "relay_time"
DEFAULT_RELAY_TIME = 200
CONF_INVERT_RELAY = "invert_relay"
DEFAULT_INVERT_RELAY = False
CONF_STATE_PIN = "state_pin"
CONF_STATE_PULL_MODE = "state_pull_mode"
DEFAULT_STATE_PULL_MODE = "UP"
CONF_INVERT_STATE = "invert_state"
DEFAULT_INVERT_STATE = False

import homeassistant.helpers.config_validation as cv
import voluptuous as vol

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_COVERS, CONF_COVERS): vol.All(
                cv.ensure_list, [{
                    vol.Required(CONF_NAME): cv.string,
                    vol.Required(CONF_RELAY_PIN): cv.positive_int,
                    vol.Optional(CONF_RELAY_TIME, default=DEFAULT_RELAY_TIME): cv.positive_int,
                    vol.Optional(CONF_INVERT_RELAY, default=DEFAULT_INVERT_RELAY): cv.boolean,
                    vol.Required(CONF_STATE_PIN): cv.positive_int,
                    vol.Optional(CONF_STATE_PULL_MODE, default=DEFAULT_STATE_PULL_MODE): cv.string,
                    vol.Optional(CONF_INVERT_STATE, default=DEFAULT_INVERT_STATE): cv.boolean,
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
                cover[CONF_RELAY_PIN],
                cover[CONF_RELAY_TIME],
                cover.get(CONF_INVERT_RELAY),
                cover[CONF_STATE_PIN],
                cover.get(CONF_STATE_PULL_MODE),
                cover.get(CONF_INVERT_STATE),
                cover.get(CONF_UNIQUE_ID) or f"{DOMAIN}_{cover[CONF_RELAY_PIN]}_{cover[CONF_NAME].lower().replace(' ', '_')}",
            )
        )

    async_add_entities(covers)


class GPIODCover(CoverEntity):
    should_poll = False
    is_opening = False
    is_closing = False

    def __init__(self, hub, name, relay_pin, relay_time, invert_relay, 
                 state_pin, state_pull_mode, invert_state, unique_id):
        _LOGGER.debug(f"GPIODCover init: {relay_pin}:{state_pin} - {name} - {unique_id} - {relay_time}")
        self._hub = hub
        self._attr_name = name
        self._relay_pin = relay_pin
        self._relay_time = relay_time
        self._invert_relay = invert_relay
        self._state_pin = state_pin
        self._state_pull_mode = state_pull_mode
        self._invert_state = invert_state
        self._attr_unique_id = unique_id
        self._is_closed = False != invert_state
        hub.add_cover(self, relay_pin, invert_relay, 
                      state_pin, state_pull_mode, invert_state)

    async def async_added_to_hass(self):
        # start listener
        self._hub.edge_detect()

    @property
    def name(self) -> str:
        return self._attr_name

    @property
    def unique_id(self) -> str:
        return self._attr_unique_id

    @property
    def is_closed(self):
        return self._is_closed

    def update(self):
        self._is_closed = self._hub.update(self._state_pin)
        self.schedule_update_ha_state(False)

    def close_cover(self, **kwargs):
        if self.is_closed:
            return
        self._hub.turn_on(self._relay_pin)
        self.is_closing = True
        self.schedule_update_ha_state(False)
        sleep(self._relay_time/1000)
        self._hub.turn_off(self._relay_pin)
        self.is_closing = False
        self.schedule_update_ha_state(False)

    def open_cover(self, **kwargs):
        if not self.is_closed:
            return
        self._hub.turn_on(self._relay_pin)
        self.is_opening = True
        self.schedule_update_ha_state(False)
        sleep(self._relay_time/1000)
        self._hub.turn_off(self._relay_pin)
        self.is_opening = False
        self.schedule_update_ha_state(False)

    def set(self, is_closed: bool):
        self._is_closed = is_closed
        self.schedule_update_ha_state(False)
