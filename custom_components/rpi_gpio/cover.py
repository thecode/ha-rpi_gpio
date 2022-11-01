"""Support for controlling a Raspberry Pi cover."""
from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant.components.cover import PLATFORM_SCHEMA, CoverEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_COVERS, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN, RpiGPIO
from .const import (
    CONF_CONFIGURED_PORTS,
    CONF_GPIO,
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
from .entity import RpiGPIOEntity

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
        breaks_in_ha_version="2023.1.0",
        is_fixable=False,
        severity=IssueSeverity.WARNING,
        translation_key="deprecated_yaml",
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up rpi_gpio cover."""
    rpi_gpio: RpiGPIO = hass.data[DOMAIN][CONF_GPIO]
    await hass.async_add_executor_job(rpi_gpio.setup_port, entry)

    async_add_entities([RPiGPIOCover(hass, entry, rpi_gpio)], True)


class RPiGPIOCover(CoverEntity):
    """Representation of a Raspberry GPIO cover."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, rpi_gpio: RpiGPIO
    ) -> None:
        """Initialize the RPi GPIO entity."""
        self.hass = hass
        self.entry = entry
        self.rpi_gpio = rpi_gpio
        self.relay_pin: str = entry.data[CONF_RELAY_PIN]
        self.state_pin: str = entry.data[CONF_STATE_PIN]
        self._attr_unique_id = f"{self.relay_pin}-{self.state_pin}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=f"{entry.data[CONF_NAME]} (GPIOs {self._attr_unique_id})",
            manufacturer="Raspberry Pi",
        )

    @property
    def invert_relay(self) -> bool:
        """Return if relay state should be inverted."""
        return self.entry.options.get(CONF_INVERT_RELAY, DEFAULT_INVERT_RELAY)

    @property
    def invert_state(self) -> bool:
        """Return if state port should be inverted."""
        return self.entry.options.get(CONF_INVERT_STATE, DEFAULT_INVERT_STATE)

    @property
    def relay_time(self) -> float:
        """Return the relay turn on duration."""
        return self.entry.options.get(CONF_RELAY_TIME, DEFAULT_RELAY_TIME)

    async def async_update(self) -> None:
        """Update entity."""
        self._attr_is_closed = (
            await self.rpi_gpio.async_read_input(self.state_pin) != self.invert_state
        )

    async def _async_trigger(self) -> None:
        """Trigger the cover."""
        await self.rpi_gpio.async_write_output(
            self.relay_pin, 1 if self.invert_relay else 0
        )
        await asyncio.sleep(self.relay_time)
        await self.rpi_gpio.async_write_output(
            self.relay_pin, 0 if self.invert_relay else 1
        )

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        if not self.is_closed:
            await self._async_trigger()

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        if self.is_closed:
            await self._async_trigger()

    @callback
    def _update_callback(self) -> None:
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    async def async_added_to_hass(self) -> None:
        """Register callbacks"""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"port_{self.state_pin}_edge_detected", self._update_callback
            )
        )
        await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        """Reset relay pin to input and remove from configured ports."""
        await self.rpi_gpio.async_reset_port(self.relay_pin)
        await self.rpi_gpio.async_remove_edge_detection(self.state_pin)
        self.hass.data[DOMAIN][CONF_CONFIGURED_PORTS].remove(self.relay_pin)
        self.hass.data[DOMAIN][CONF_CONFIGURED_PORTS].remove(self.state_pin)
