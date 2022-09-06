"""Support for binary sensor using RPi GPIO."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_BINARY_SENSORS,
    CONF_NAME,
    CONF_PORT,
    CONF_SENSORS,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import RpiGPIO
from .const import (
    CONF_BOUNCETIME,
    CONF_INVERT_LOGIC,
    CONF_PORTS,
    CONF_PULL_MODE,
    DEFAULT_BOUNCETIME,
    DEFAULT_INVERT_LOGIC,
    DEFAULT_PULL_MODE,
    DOMAIN,
)
from .entity import RpiGPIOEntity

_SENSORS_LEGACY_SCHEMA = vol.Schema({cv.positive_int: cv.string})

_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_PORT): cv.positive_int,
        vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
        vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
        vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
    }
)

PLATFORM_SCHEMA = vol.All(
    PLATFORM_SCHEMA.extend(
        {
            vol.Exclusive(CONF_PORTS, CONF_SENSORS): _SENSORS_LEGACY_SCHEMA,
            vol.Exclusive(CONF_SENSORS, CONF_SENSORS): vol.All(
                cv.ensure_list, [_SENSOR_SCHEMA]
            ),
            vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): cv.positive_int,
            vol.Optional(CONF_INVERT_LOGIC, default=DEFAULT_INVERT_LOGIC): cv.boolean,
            vol.Optional(CONF_PULL_MODE, default=DEFAULT_PULL_MODE): cv.string,
        },
    ),
    cv.has_at_least_one_key(CONF_PORTS, CONF_SENSORS),
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
    entities: list[RPiGPIOBinarySensor] = []
    for port in entry.data.get(CONF_BINARY_SENSORS, {}):
        entities.append(
            RPiGPIOBinarySensor(rpi_gpio, port, entry.data[CONF_BINARY_SENSORS][port])
        )

    async_add_entities(entities, True)


class RPiGPIOBinarySensor(RpiGPIOEntity, BinarySensorEntity):
    """Represent a binary sensor that uses Raspberry Pi GPIO."""

    async def async_update(self) -> None:
        """Update entity."""
        self._attr_is_on = (
            await self.rpi_gpio.async_read_input(self.port) != self._invert_logic
        )

    @callback
    def _update_callback(self) -> None:
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    async def async_added_to_hass(self) -> None:
        """Register callbacks"""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"port_{self.port}_edge_detected", self._update_callback
            )
        )
        await super().async_added_to_hass()

    async def async_will_remove_from_hass(self) -> None:
        """Remove edge detection."""
        await self.rpi_gpio.async_remove_edge_detection(self.port)
        await super().async_will_remove_from_hass()
