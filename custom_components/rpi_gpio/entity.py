"""Base entity for Rpi GPIO ports."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, Entity

from . import RpiGPIO
from .const import (
    CONF_CONFIGURED_PORTS,
    CONF_INVERT_LOGIC,
    DEFAULT_INVERT_LOGIC,
    DOMAIN,
)


class RpiGPIOEntity(Entity):
    """Representation of a Raspberry Pi GPIO."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, rpi_gpio: RpiGPIO
    ) -> None:
        """Initialize the RPi GPIO entity."""
        self.hass = hass
        self.entry = entry
        self.rpi_gpio = rpi_gpio
        self.port: str = entry.data[CONF_PORT]
        self._attr_unique_id = self.port
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=f"{entry.data[CONF_NAME]} (GPIO {self.port})",
            manufacturer="Raspberry Pi",
        )

    @property
    def invert_logic(self) -> bool:
        """Return if port state should be inverted."""
        return self.entry.options.get(CONF_INVERT_LOGIC, DEFAULT_INVERT_LOGIC)

    async def async_will_remove_from_hass(self) -> None:
        """Reset port to input."""
        await self.rpi_gpio.async_reset_port(self.port)
        self.hass.data[DOMAIN][CONF_CONFIGURED_PORTS].remove(self.port)
