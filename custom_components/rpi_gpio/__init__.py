"""The Raspberry Pi GPIO integration."""
from __future__ import annotations

import asyncio
from typing import Any

from RPi import GPIO  # pylint: disable=import-error

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_BINARY_SENSORS,
    CONF_COVERS,
    CONF_SWITCHES,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_BOUNCETIME,
    CONF_INVERT_LOGIC,
    CONF_INVERT_RELAY,
    CONF_PULL_MODE,
    CONF_RELAY_PIN,
    CONF_STATE_PIN,
    CONF_STATE_PULL_MODE,
    DOMAIN,
)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SWITCH, Platform.COVER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Raspberry Pi GPIO from a config entry."""

    rpigpio = RpiGPIO(hass, entry)
    await hass.async_add_executor_job(rpigpio.setup_ports)

    hass.data[DOMAIN] = rpigpio

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, rpigpio.cleanup_gpio)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        del hass.data[DOMAIN]
    return unload_ok


class RpiGPIO:
    """Base class for Rpi GPIOs."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the class."""
        self.hass = hass
        self.entry: ConfigEntry = entry
        GPIO.setmode(GPIO.BCM)

    @property
    def binary_sensors(self) -> dict[str, dict[str, Any]]:
        """Return the configured binary sensor ports."""
        return self.entry.data.get(CONF_BINARY_SENSORS, {})

    @property
    def switches(self) -> dict[str, dict[str, Any]]:
        """Return the configured switch ports."""
        return self.entry.data.get(CONF_SWITCHES, {})

    @property
    def covers(self) -> dict[str, dict[str, Any]]:
        """Return the configured cover ports."""
        return self.entry.data.get(CONF_COVERS, {})

    @callback
    def cleanup_gpio(self, _: Any = None) -> None:
        """Cleanup before stopping."""
        GPIO.cleanup()

    async def async_reset_port(self, port: int) -> None:
        """Reset removed port to input."""
        await self.hass.async_add_executor_job(GPIO.setup, port, GPIO.IN)

    async def async_read_input(self, port: int) -> bool:
        """Read a value from a GPIO."""
        return await self.hass.async_add_executor_job(GPIO.input, port)

    async def async_write_output(self, port: int, value: int) -> None:
        """Write value to a GPIO."""
        await self.hass.async_add_executor_job(GPIO.output, port, value)

    async def async_remove_edge_detection(self, port: int) -> None:
        """Remove edge detection if input is deleted."""
        await self.hass.async_add_executor_job(GPIO.remove_event_detect, port)

    @callback
    async def async_signal_edge_detected(self, port: int) -> None:
        """Send signal that input edge is detected."""
        await asyncio.sleep(
            float(self.binary_sensors[str(port)][CONF_BOUNCETIME]) / 1000
        )
        async_dispatcher_send(self.hass, f"port_{port}_edge_detected")

    def setup_ports(self) -> None:
        """Setup GPIO inputs."""

        @callback
        def edge_detected(port: int) -> None:
            """Edge detection handler."""
            self.hass.add_job(self.async_signal_edge_detected, port)

        for binary_sensor in self.binary_sensors:
            # Setup input
            GPIO.setup(
                int(binary_sensor),
                GPIO.IN,
                int(self.binary_sensors[binary_sensor][CONF_PULL_MODE]),
            )
            # Add edge detection
            GPIO.add_event_detect(
                int(binary_sensor),
                GPIO.BOTH,
                callback=edge_detected,
                bouncetime=self.binary_sensors[binary_sensor][CONF_BOUNCETIME],
            )

        for switch in self.switches:
            # Setup output
            GPIO.setup(
                int(switch),
                GPIO.OUT,
                initial=GPIO.LOW
                if self.switches[switch][CONF_INVERT_LOGIC]
                else GPIO.HIGH,
            )

        for cover in self.covers:
            # setup state pin
            GPIO.setup(
                int(self.covers[cover][CONF_STATE_PIN]),
                GPIO.IN,
                int(self.covers[cover][CONF_STATE_PULL_MODE]),
            )

            # Setup relay pin
            GPIO.setup(
                int(self.covers[cover][CONF_RELAY_PIN]),
                GPIO.OUT,
                initial=GPIO.LOW
                if self.covers[cover][CONF_INVERT_RELAY]
                else GPIO.HIGH,
            )
