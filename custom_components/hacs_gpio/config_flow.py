"""Adds config flow for HA GPIO"""
from __future__ import annotations

import voluptuous as vol
import gpiod
from homeassistant import config_entries
from homeassistant.const import CONF_CHIP

from .const import DOMAIN, LOGGER

class HaGPIODFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for ha-gpiod"""

    VERRSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                """test gpio access"""
                with gpiod.Chip(user_input[CONF_CHIP]) as chip:
                    info = chip.get_info()
            except OSError as ex:
                LOGGER.warning(f"GPIOChip: {user_input[CONF_CHIP]} failed to initialise\n{ex}")
                _errors["base"] = "gpiochip initialization failed"
            else: 
                LOGGER.info(f"GPIOChip: {user_input[CONF_CHIP]} initialised")
                return self.async_create(
                    title=user_input[CONF_CHIP], data=user_input)
    return self.async_show_form(
        step_id="user",
        data_schema=vol.Schema(
            {
                vol.Required(
                    CONF_CHIP,
                    default=(user_input or {}).get(CONF_CHIP),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT
                        ),
                    ),
                }
            ),
            errors=_errors,
    )
        

                
                    

