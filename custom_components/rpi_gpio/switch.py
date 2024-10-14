"""Allows to configure a switch using RPi GPIO."""
from __future__ import annotations
from typing import Any, List

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_SWITCHES,
    CONF_UNIQUE_ID,
    DEVICE_DEFAULT_NAME,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.reload import setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.restore_state import RestoreEntity

from . import DOMAIN, PLATFORMS, setup_output, write_output

CONF_PULL_MODE = "pull_mode"
CONF_PORTS = "ports"
CONF_INVERT_LOGIC = "invert_logic"
CONF_PERSISTENT = "persistent"

DEFAULT_INVERT_LOGIC = False
DEFAULT_PERSISTENT = False

_SWITCHES_LEGACY_SCHEMA = vol.Schema({cv.positive_int: cv.string})

_SWITCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_PERSISTENT, default=DEFAULT_PERSISTENT): cv.boolean,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_PORTS, CONF_SWITCHES): _SWITCHES_LEGACY_SCHEMA,
            vol.Exclusive(CONF_SWITCHES, CONF_SWITCHES): vol.All(
                cv.ensure_list, [_SWITCH_SCHEMA]
            ),
            vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
            vol.Optional(CONF_PERSISTENT, default=DEFAULT_PERSISTENT): cv.boolean,
        },
    ),
    cv.has_at_least_one_key(CONF_PORTS, CONF_SWITCHES),
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Raspberry PI GPIO devices."""
    setup_reload_service(hass, DOMAIN, PLATFORMS)

    switches: List[SwitchEntity] = []

    switches_conf = config.get(CONF_SWITCHES)
    if switches_conf:
        for switch in switches_conf:
            switch_class = PersistentRPiGPIOSwitch if switch[CONF_PERSISTENT] else RPiGPIOSwitch
            switches.append(
                switch_class(
                    switch[CONF_NAME],
                    switch[CONF_PORT],
                    switch[CONF_INVERT_LOGIC],
                    switch.get(CONF_UNIQUE_ID),
                )
            )
    else:
        invert_logic = config[CONF_INVERT_LOGIC]
        persistent = config[CONF_PERSISTENT]
        ports = config[CONF_PORTS]
        for port, name in ports.items():
            switch_class = PersistentRPiGPIOSwitch if persistent else RPiGPIOSwitch
            switches.append(switch_class(name, port, invert_logic))

    add_entities(switches, True)

class RPiGPIOSwitch(SwitchEntity):
    """Representation of a Raspberry Pi GPIO."""

    def __init__(self, name: str, port: int, invert_logic: bool, unique_id: str | None = None, skip_reset: bool = False) -> None:
        """Initialize the pin."""
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_unique_id = unique_id
        self._attr_should_poll = False
        self._port = port
        self._invert_logic = invert_logic
        self._state = False
        setup_output(self._port)
        if not skip_reset:
            write_output(self._port, 1 if self._invert_logic else 0)

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self._state

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        try:
            write_output(self._port, 0 if self._invert_logic else 1)
            self._state = True
            self.async_write_ha_state()
        except Exception as e:
            self._handle_error(e)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        try:
            write_output(self._port, 1 if self._invert_logic else 0)
            self._state = False
            self.async_write_ha_state()
        except Exception as e:
            self._handle_error(e)

    def _handle_error(self, error: Exception) -> None:
        """Handle errors by logging them."""
        self._state = None
        self.async_write_ha_state()
        # Log the error (assuming a logger is available)
        # logger.error(f"Error controlling GPIO switch: {error}")

class PersistentRPiGPIOSwitch(RPiGPIOSwitch, RestoreEntity):
    """Representation of a persistent Raspberry Pi GPIO."""

    def __init__(self, name: str, port: int, invert_logic: bool, unique_id: str | None = None) -> None:
        """Initialize the pin."""
        super().__init__(name, port, invert_logic, unique_id, True)

    async def async_added_to_hass(self) -> None:
        """Call when the switch is added to hass."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._state = state.state == STATE_ON
            if self._state:
                await self.async_turn_on()
            else:
                await self.async_turn_off()
