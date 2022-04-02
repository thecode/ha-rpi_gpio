"""Allows to configure a switch using RPi GPIO."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import (
    CONF_NAME,
    CONF_PORT,
    CONF_SWITCHES,
    CONF_UNIQUE_ID,
    DEVICE_DEFAULT_NAME,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.reload import setup_reload_service
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, PLATFORMS, setup_output, write_output

CONF_PULL_MODE = "pull_mode"
CONF_PORTS = "ports"
CONF_INVERT_LOGIC = "invert_logic"

DEFAULT_INVERT_LOGIC = False

_SWITCHES_LEGACY_SCHEMA = vol.Schema({cv.positive_int: cv.string})

_SWITCH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
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

    switches = []

    switches_conf = config.get(CONF_SWITCHES)
    if switches_conf is not None:
        for switch in switches_conf:
            switches.append(
                RPiGPIOSwitch(
                    switch[CONF_NAME],
                    switch[CONF_PORT],
                    switch[CONF_INVERT_LOGIC],
                    switch.get(CONF_UNIQUE_ID),
                )
            )

        add_entities(switches, True)
        return

    invert_logic = config[CONF_INVERT_LOGIC]

    ports = config[CONF_PORTS]
    for port, name in ports.items():
        switches.append(RPiGPIOSwitch(name, port, invert_logic))

    add_entities(switches)


class RPiGPIOSwitch(SwitchEntity):
    """Representation of a  Raspberry Pi GPIO."""

    def __init__(self, name, port, invert_logic, unique_id=None):
        """Initialize the pin."""
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._attr_unique_id = unique_id
        self._attr_should_poll = False
        self._port = port
        self._invert_logic = invert_logic
        self._state = False
        setup_output(self._port)
        write_output(self._port, 1 if self._invert_logic else 0)

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the device on."""
        write_output(self._port, 0 if self._invert_logic else 1)
        self._state = True
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        write_output(self._port, 1 if self._invert_logic else 0)
        self._state = False
        self.schedule_update_ha_state()
