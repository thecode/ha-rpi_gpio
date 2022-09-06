"""Allows to configure a switch using RPi GPIO."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_NAME, CONF_PORT, CONF_SWITCHES, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import RpiGPIO
from .const import CONF_INVERT_LOGIC, CONF_PORTS, DOMAIN
from .entity import RpiGPIOEntity

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


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Raspberry PI GPIO devices."""
    async_create_issue(
        hass,
        DOMAIN,
        "deprecated_yaml",
        breaks_in_ha_version="2022.11.0",
        is_fixable=False,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up rpi_power binary sensor."""
    rpi_gpio: RpiGPIO = hass.data[DOMAIN]
    entities: list[RPiGPIOSwitch] = []
    for port in entry.data.get(CONF_SWITCHES, {}):
        entities.append(RPiGPIOSwitch(rpi_gpio, port, entry.data[CONF_SWITCHES][port]))

    async_add_entities(entities, True)


class RPiGPIOSwitch(RpiGPIOEntity, SwitchEntity):
    """Representation of an output port as switch."""

    async def async_update(self) -> None:
        """Update entity."""
        self._attr_is_on = (
            await self.rpi_gpio.async_read_input(self.port) != self._invert_logic
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        await self.rpi_gpio.async_write_output(
            self.port, 0 if self._invert_logic else 1
        )
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device off."""
        await self.rpi_gpio.async_write_output(
            self.port, 1 if self._invert_logic else 0
        )
        self.async_schedule_update_ha_state(True)
