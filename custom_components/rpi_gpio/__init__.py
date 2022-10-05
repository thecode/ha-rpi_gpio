"""The Raspberry Pi GPIO integration."""
from __future__ import annotations

import asyncio
from typing import Any

from RPi import GPIO  # pylint: disable=import-error

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PLATFORM,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_BOUNCETIME,
    CONF_CONFIGURED_PORTS,
    CONF_GPIO,
    CONF_PULL_MODE,
    DEFAULT_BOUNCETIME,
    DEFAULT_PULL_MODE,
    DOMAIN,
)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Raspberry Pi GPIO from a config entry."""

    @callback
    def cleanup_gpio(event: Any) -> None:
        """Cleanup before stopping."""
        GPIO.cleanup()

    if DOMAIN not in hass.data:
        # actions that should be done the first time only
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][CONF_CONFIGURED_PORTS] = []
        hass.data[DOMAIN][CONF_GPIO] = RpiGPIO(hass)
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, cleanup_gpio)

    await hass.config_entries.async_forward_entry_setup(
        entry, entry.data[CONF_PLATFORM]
    )

    hass.data[DOMAIN][CONF_CONFIGURED_PORTS].append(entry.data[CONF_PORT])

    entry.async_on_unload(entry.add_update_listener(options_updated))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_forward_entry_unload(
        entry, entry.data[CONF_PLATFORM]
    ):
        if not hass.data[DOMAIN][CONF_CONFIGURED_PORTS]:
            del hass.data[DOMAIN]
    return unload_ok


async def options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update when config_entry options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class RpiGPIO:
    """Base class for Rpi GPIOs."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the class."""
        self.hass = hass
        GPIO.setmode(GPIO.BCM)

    async def async_reset_port(self, port: str) -> None:
        """Reset removed port to input."""
        await self.hass.async_add_executor_job(GPIO.setup, int(port), GPIO.IN)

    async def async_read_input(self, port: str) -> bool:
        """Read a value from a GPIO."""
        return await self.hass.async_add_executor_job(GPIO.input, int(port))

    async def async_write_output(self, port: str, value: int) -> None:
        """Write value to a GPIO."""
        await self.hass.async_add_executor_job(GPIO.output, int(port), value)

    async def async_remove_edge_detection(self, port: str) -> None:
        """Remove edge detection if input is deleted."""
        await self.hass.async_add_executor_job(GPIO.remove_event_detect, int(port))

    @callback
    async def async_signal_edge_detected(self, port: int, bounce_time: int) -> None:
        """Send signal that input edge is detected."""
        await asyncio.sleep(float(bounce_time / 1000))
        async_dispatcher_send(self.hass, f"port_{port}_edge_detected")

    def setup_port(self, entry: ConfigEntry) -> None:
        """Setup GPIO ports."""

        @callback
        def edge_detected(port: int) -> None:
            """Edge detection handler."""
            self.hass.add_job(
                self.async_signal_edge_detected,
                port,
                entry.options.get(CONF_BOUNCETIME, DEFAULT_BOUNCETIME),
            )

        if entry.data[CONF_PLATFORM] == Platform.BINARY_SENSOR:
            # Setup input
            GPIO.setup(
                int(entry.data[CONF_PORT]),
                GPIO.IN,
                int(entry.options.get(CONF_PULL_MODE, DEFAULT_PULL_MODE)),
            )
            # Add edge detection
            GPIO.add_event_detect(
                int(entry.data[CONF_PORT]),
                GPIO.BOTH,
                callback=edge_detected,
                bouncetime=entry.options.get(CONF_BOUNCETIME, DEFAULT_BOUNCETIME),
            )
