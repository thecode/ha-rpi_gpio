"""Support for controlling a Raspberry Pi cover."""
from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant.components.cover import PLATFORM_SCHEMA, CoverEntity
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_COVERS, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, RpiGPIO
from .const import (
    CONF_INVERT_RELAY,
    CONF_INVERT_STATE,
    CONF_RELAY_PIN,
    CONF_RELAY_TIME,
    CONF_STATE_PIN,
    CONF_STATE_PULL_MODE,
    DEFAULT_INVERT_RELAY,
    DEFAULT_INVERT_STATE,
    DEFAULT_RELAY_TIME,
    DEFAULT_STATE_PULL_MODE,
)

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
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the RPi cover platform."""
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
    entities: list[RPiGPIOCover] = []
    for cover in entry.data.get(CONF_COVERS, {}):
        entities.append(RPiGPIOCover(rpi_gpio, cover, entry.data[CONF_COVERS][cover]))

    async_add_entities(entities, True)


class RPiGPIOCover(CoverEntity):
    """Representation of a Raspberry GPIO cover."""

    _attr_has_entity_name = True

    def __init__(
        self,
        rpi_gpio: RpiGPIO,
        cover: str,
        data: dict[str, Any],
    ):
        """Initialize the cover."""
        self.rpi_gpio = rpi_gpio
        self._relay_pin = int(data[CONF_RELAY_PIN])
        self._relay_time = int(data[CONF_RELAY_TIME])
        self._state_pin = int(data[CONF_STATE_PIN])
        self._invert_relay = int(data[CONF_INVERT_RELAY])
        self._invert_state: bool = data[CONF_INVERT_STATE]
        if name := data.get(CONF_NAME):
            self._attr_has_entity_name = False
        self._attr_name = name or cover
        self._attr_unique_id = data.get(CONF_UNIQUE_ID) or cover
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "Raspberry Pi")}, name="Raspberry Pi GPIO"
        )

    async def async_update(self) -> None:
        """Update entity."""
        self._attr_is_closed = (
            await self.rpi_gpio.async_read_input(self._state_pin) != self._invert_state
        )

    async def _async_trigger(self):
        """Trigger the cover."""
        await self.rpi_gpio.async_write_output(
            self._relay_pin, 1 if self._invert_relay else 0
        )
        await asyncio.sleep(self._relay_time)
        await self.rpi_gpio.async_write_output(
            self._relay_pin, 0 if self._invert_relay else 1
        )
        self.async_schedule_update_ha_state(True)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        if not self.is_closed:
            await self._async_trigger()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        if self.is_closed:
            await self._async_trigger()
