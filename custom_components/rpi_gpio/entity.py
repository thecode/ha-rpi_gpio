"""Base entity for Rpi GPIO ports."""

from typing import Any
from homeassistant.const import CONF_NAME, CONF_UNIQUE_ID
from homeassistant.core import callback
from homeassistant.helpers import entity_registry

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, Entity

from . import RpiGPIO
from .const import CONF_INVERT_LOGIC, DOMAIN


class RpiGPIOEntity(Entity):
    """Representation of a Raspberry Pi GPIO."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, rpi_gpio: RpiGPIO, port: str, data: dict[str, Any]) -> None:
        """Initialize the RPi GPIO entity."""
        self.rpi_gpio = rpi_gpio
        self.port = int(port)
        self._invert_logic: bool = data[CONF_INVERT_LOGIC]
        if name := data.get(CONF_NAME):
            self._attr_has_entity_name = False
        self._attr_name = name or port
        self._attr_unique_id = data.get(CONF_UNIQUE_ID) or port
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "Raspberry Pi")}, name="Raspberry Pi GPIO"
        )

    @callback
    async def async_remove_entity(self) -> None:
        """Remove entity from registry."""

        if self.registry_entry:
            entity_registry.async_get(self.hass).async_remove(self.entity_id)
        else:
            await self.async_remove(force_remove=True)

    async def async_added_to_hass(self) -> None:
        """Register callbacks"""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"port_{self.port}_removed", self.async_remove_entity
            ),
        )

    async def async_will_remove_from_hass(self) -> None:
        """Reset port to input."""
        await self.rpi_gpio.async_reset_port(self.port)
