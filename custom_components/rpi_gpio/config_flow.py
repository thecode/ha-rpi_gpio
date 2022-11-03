"""Config flow for Raspberry Pi Power Supply Checker."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_NAME,
    CONF_PLATFORM,
    CONF_PORT,
    TIME_MILLISECONDS,
    TIME_SECONDS,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_BOUNCETIME,
    CONF_CONFIGURED_PORTS,
    CONF_INVERT_LOGIC,
    CONF_INVERT_RELAY,
    CONF_INVERT_STATE,
    CONF_PULL_MODE,
    CONF_RELAY_PIN,
    CONF_RELAY_TIME,
    CONF_STATE_PIN,
    CONF_STATE_PULL_MODE,
    DEFAULT_BOUNCETIME,
    DEFAULT_INVERT_LOGIC,
    DEFAULT_INVERT_RELAY,
    DEFAULT_INVERT_STATE,
    DEFAULT_PULL_MODE,
    DEFAULT_RELAY_TIME,
    DOMAIN,
    GPIO_PIN_MAP,
    PUD_DOWN,
    PUD_UP,
)

PULL_MODES = [
    selector.SelectOptionDict(value=PUD_UP, label="UP"),
    selector.SelectOptionDict(value=PUD_DOWN, label="DOWN"),
]

BINARY_SENSOR_OPTIONS_SCHEMA = {
    vol.Optional(CONF_INVERT_LOGIC, default=False): selector.BooleanSelector(),
    vol.Optional(CONF_BOUNCETIME, default=DEFAULT_BOUNCETIME): vol.All(
        selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=50,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement=TIME_MILLISECONDS,
            )
        ),
        vol.Coerce(int),
    ),
    vol.Optional(CONF_PULL_MODE, default=PUD_UP): selector.SelectSelector(
        selector.SelectSelectorConfig(options=PULL_MODES)
    ),
}


def _get_options_schema(platform: Platform, options: dict[str, Any]) -> vol.Schema:
    """Return options schema based on platform."""
    if platform == Platform.BINARY_SENSOR:
        return vol.Schema(
            {
                vol.Optional(
                    CONF_INVERT_LOGIC,
                    default=options.get(CONF_INVERT_LOGIC, DEFAULT_INVERT_LOGIC),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_BOUNCETIME,
                    default=options.get(CONF_BOUNCETIME, DEFAULT_BOUNCETIME),
                ): vol.All(
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=50,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement=TIME_MILLISECONDS,
                        )
                    ),
                    vol.Coerce(int),
                ),
                vol.Optional(
                    CONF_PULL_MODE,
                    default=options.get(CONF_PULL_MODE, DEFAULT_PULL_MODE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=PULL_MODES)
                ),
            }
        )
    if platform == Platform.SWITCH:
        return vol.Schema(
            {
                vol.Optional(
                    CONF_INVERT_LOGIC,
                    default=options.get(CONF_INVERT_LOGIC, DEFAULT_INVERT_LOGIC),
                ): selector.BooleanSelector()
            }
        )
    if platform == Platform.COVER:
        return vol.Schema(
            {
                vol.Optional(
                    CONF_STATE_PULL_MODE,
                    default=options.get(CONF_STATE_PULL_MODE, DEFAULT_PULL_MODE),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=PULL_MODES)
                ),
                vol.Optional(
                    CONF_INVERT_STATE,
                    default=options.get(CONF_INVERT_STATE, DEFAULT_INVERT_STATE),
                ): selector.BooleanSelector(),
                vol.Optional(
                    CONF_BOUNCETIME,
                    default=options.get(CONF_BOUNCETIME, DEFAULT_BOUNCETIME),
                ): vol.All(
                    selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=50,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement=TIME_MILLISECONDS,
                        )
                    ),
                    vol.Coerce(int),
                ),
                vol.Optional(
                    CONF_RELAY_TIME,
                    default=options.get(CONF_RELAY_TIME, DEFAULT_RELAY_TIME),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        step=0.1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement=TIME_SECONDS,
                    )
                ),
                vol.Optional(
                    CONF_INVERT_RELAY,
                    default=options.get(CONF_INVERT_RELAY, DEFAULT_INVERT_RELAY),
                ): selector.BooleanSelector(),
            }
        )


def _get_avaiable_ports(hass: HomeAssistant) -> list[selector.SelectOptionDict]:
    """Return schema with availble ports."""
    if DOMAIN in hass.data:
        configured_ports = hass.data[DOMAIN][CONF_CONFIGURED_PORTS]
    else:
        configured_ports = []

    return [
        selector.SelectOptionDict(
            value=port,
            label=f"GPIO{port} - PIN {GPIO_PIN_MAP[port]}",
        )
        for port in list(GPIO_PIN_MAP)
        if port not in configured_ports
    ]


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Raspberry Pi GPIO."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["add_binary_sensor", "add_switch", "add_cover"],
        )

    async def async_step_add_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a binary sensor entry."""
        if user_input is None:

            return self.async_show_form(
                step_id="add_binary_sensor",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): selector.TextSelector(),
                        vol.Required(CONF_PORT, default=[]): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=_get_avaiable_ports(self.hass),
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        ),
                    }
                ),
            )

        await self.async_set_unique_id(user_input[CONF_PORT])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"{user_input[CONF_NAME]} (GPIO {user_input[CONF_PORT]})",
            data={CONF_PLATFORM: Platform.BINARY_SENSOR, **user_input},
        )

    async def async_step_add_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a switch."""
        if user_input is None:
            return self.async_show_form(
                step_id="add_switch",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NAME): selector.TextSelector(),
                        vol.Required(CONF_PORT, default=[]): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=_get_avaiable_ports(self.hass),
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        ),
                    }
                ),
            )

        await self.async_set_unique_id(user_input[CONF_PORT])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"{user_input[CONF_NAME]} (GPIO {user_input[CONF_PORT]})",
            data={CONF_PLATFORM: Platform.SWITCH, **user_input},
        )

    async def async_step_add_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a cover."""
        available_ports = _get_avaiable_ports(self.hass)
        error = {}
        if user_input is not None:
            if user_input[CONF_RELAY_PIN] == user_input[CONF_STATE_PIN]:
                error = {"base": "not_unique"}
            if not error:
                unique_id = f"{user_input[CONF_RELAY_PIN]}-{user_input[CONF_STATE_PIN]}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"{user_input[CONF_NAME]} (GPIOs {unique_id})",
                    data={CONF_PLATFORM: Platform.COVER, **user_input},
                )
        return self.async_show_form(
            step_id="add_cover",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): selector.TextSelector(),
                    vol.Required(CONF_RELAY_PIN, default=[]): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=available_ports,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_STATE_PIN, default=[]): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=available_ports,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=error,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> RpiGPIOOptionsFlowHandler:
        """Options callback for Rpi GPIO."""
        return RpiGPIOOptionsFlowHandler(config_entry)


class RpiGPIOOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle integration options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize integration options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_get_options_schema(
                self.config_entry.data[CONF_PLATFORM],
                dict(self.config_entry.options),
            ),
        )
