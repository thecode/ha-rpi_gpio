"""Config flow for Raspberry Pi Power Supply Checker."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_BINARY_SENSORS,
    CONF_COVERS,
    CONF_ENTITIES,
    CONF_NAME,
    CONF_PORT,
    CONF_SENSORS,
    CONF_SWITCHES,
    TIME_MILLISECONDS,
    TIME_SECONDS,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import entity_registry, selector
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import (
    CONF_BOUNCETIME,
    CONF_INVERT_LOGIC,
    CONF_INVERT_RELAY,
    CONF_INVERT_STATE,
    CONF_PORTS,
    CONF_PULL_MODE,
    CONF_RELAY_PIN,
    CONF_RELAY_TIME,
    CONF_STATE_PIN,
    CONF_STATE_PULL_MODE,
    DEFAULT_BOUNCETIME,
    DEFAULT_INVERT_RELAY,
    DEFAULT_INVERT_STATE,
    DEFAULT_RELAY_TIME,
    DEFAULT_STATE_PULL_MODE,
    DOMAIN,
    GPIO_PIN_MAP,
    PUD_DOWN,
    PUD_UP,
)

PULL_MODES = [
    selector.SelectOptionDict(value=PUD_UP, label="UP"),
    selector.SelectOptionDict(value=PUD_DOWN, label="DOWN"),
]

SWITCH_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_INVERT_LOGIC, default=False): selector.BooleanSelector(),
    }
)

BINARY_SENSOR_DATA_SCHEMA = SWITCH_DATA_SCHEMA.extend(
    {
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
)


COVER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_RELAY_TIME, default=DEFAULT_RELAY_TIME
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.1,
                step=0.1,
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement=TIME_SECONDS,
            )
        ),
        vol.Optional(
            CONF_INVERT_RELAY, default=DEFAULT_INVERT_RELAY
        ): selector.BooleanSelector(),
        vol.Optional(
            CONF_STATE_PULL_MODE, default=DEFAULT_STATE_PULL_MODE
        ): selector.SelectSelector(selector.SelectSelectorConfig(options=PULL_MODES)),
        vol.Optional(
            CONF_INVERT_STATE, default=DEFAULT_INVERT_STATE
        ): selector.BooleanSelector(),
    }
)


def _get_schema_with_available_ports(
    platform: Platform, configured_ports: list[str]
) -> vol.Schema:
    """Add ports key with available ports."""

    available_ports = [
        port for port in list(GPIO_PIN_MAP) if port not in configured_ports
    ]
    options = [
        selector.SelectOptionDict(
            value=port,
            label=f"GPIO{port} - PIN {GPIO_PIN_MAP[port]}",
        )
        for port in available_ports
    ]
    if platform == Platform.BINARY_SENSOR:
        return BINARY_SENSOR_DATA_SCHEMA.extend(
            {
                vol.Required(CONF_PORTS, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
    if platform == Platform.COVER:
        return COVER_DATA_SCHEMA.extend(
            {
                vol.Required(CONF_RELAY_PIN, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_STATE_PIN, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
    if platform == Platform.SWITCH:
        return SWITCH_DATA_SCHEMA.extend(
            {
                vol.Required(CONF_PORTS, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )


def _get_list_of_configured_ports(data: Mapping[str, Any]) -> list[str]:
    """Return list of configured ports."""
    configured_ports: list[str] = list(
        data.get(CONF_BINARY_SENSORS, []),
    ) + list(data.get(CONF_SWITCHES, []))

    if covers := data.get(CONF_COVERS):
        for cover in covers:
            configured_ports.extend(list(cover.split("-")))
    return configured_ports


def _async_get_registered_entities(
    hass: HomeAssistant, entry_id: str
) -> list[selector.SelectOptionDict]:
    """Return list of configured entities."""
    entity_reg = entity_registry.async_get(hass)
    registered_entries = entity_registry.async_entries_for_config_entry(
        entity_reg, entry_id
    )
    return [
        selector.SelectOptionDict(
            value=f"{entity.entity_id.split('.')[0]}/{entity.unique_id}",
            label=entity.name or entity.original_name or entity.entity_id,
        )
        for entity in registered_entries
    ]


def board_supported(hass: HomeAssistant) -> bool:
    """Return if the system baord is a rapsberry."""
    try:
        import RPi.GPIO
    except RuntimeError:
        return False
    return True


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Raspberry Pi GPIO."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user")

        if not board_supported:
            return self.async_abort(reason="not_supported")
        return self.async_create_entry(title="Raspberry Pi GPIO", data={})

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Import a config entry from configuration.yaml."""
        existing_entry: config_entries.ConfigEntry | None = None
        configured_ports: list[str] = []

        if entries := self._async_current_entries():
            existing_entry = entries[0]
            configured_ports = _get_list_of_configured_ports(existing_entry.data)

        data: dict[str, Any] = {}

        if sensors := import_config.get(CONF_SENSORS):
            for sensor in sensors:
                if str(sensor[CONF_PORT]) not in configured_ports:
                    sensor[CONF_PULL_MODE] = (
                        PUD_UP if sensor[CONF_PULL_MODE] == "UP" else PUD_DOWN
                    )
                    data.setdefault(CONF_BINARY_SENSORS, {})[
                        str(sensor[CONF_PORT])
                    ] = sensor
        elif switches := import_config.get(CONF_SWITCHES):
            for switch in switches:
                if str(switch[CONF_PORT]) not in configured_ports:
                    data.setdefault(CONF_SWITCHES, {})[str(switch[CONF_PORT])] = switch
        elif covers := import_config.get(CONF_COVERS):
            import_config.pop(CONF_COVERS)
            for cover in covers:
                if (
                    str(cover[CONF_RELAY_PIN]) not in configured_ports
                    and str(cover[CONF_STATE_PIN]) not in configured_ports
                    and cover[CONF_RELAY_PIN] != cover[CONF_STATE_PIN]
                ):
                    cover[CONF_STATE_PULL_MODE] = (
                        PUD_UP if cover[CONF_STATE_PULL_MODE] == "UP" else PUD_DOWN
                    )
                    data.setdefault(CONF_COVERS, {})[
                        f"{cover[CONF_RELAY_PIN]}-{cover[CONF_STATE_PIN]}"
                    ] = {**cover, **import_config}
        elif ports := import_config.get(CONF_PORTS):
            import_config.pop(CONF_PORTS)
            if CONF_BOUNCETIME in import_config:  # these are binary_sensors
                key = data[CONF_BINARY_SENSORS] = {}
            else:
                key = data[CONF_SWITCHES] = {}
            for port in ports:
                if str(port) not in configured_ports:
                    key[str(port)] = {CONF_NAME: ports[port], **import_config}
        if existing_entry:
            self.hass.config_entries.async_update_entry(
                existing_entry, data={**existing_entry.data, **data}
            )
            return self.async_abort(reason="already_configured")
        return self.async_create_entry(title="Raspberry Pi GPIO", data=data)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> RpiGPIOOptionsFlowHandler:
        """Options callback for AccuWeather."""
        return RpiGPIOOptionsFlowHandler(config_entry)


class RpiGPIOOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle integration options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize integration options flow."""
        self.config_entry = config_entry
        self.configured_ports: list[str] = _get_list_of_configured_ports(
            config_entry.data
        )

    async def async_step_init(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_binary_sensor", "add_switch", "add_cover", "remove"],
        )

    async def async_step_add_binary_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a binary sensor entry."""

        if user_input is None:

            return self.async_show_form(
                step_id="add_binary_sensor",
                data_schema=_get_schema_with_available_ports(
                    Platform.BINARY_SENSOR, self.configured_ports
                ),
            )
        new_data = self.config_entry.data.copy()
        ports = user_input.pop(CONF_PORTS)
        new_data[CONF_BINARY_SENSORS] = {port: user_input for port in ports}

        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
        self.hass.async_create_task(
            self.hass.config_entries.async_reload(self.config_entry.entry_id)
        )

        return self.async_create_entry(title="", data={})

    async def async_step_add_switch(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a switch entry."""

        if user_input is None:
            return self.async_show_form(
                step_id="add_switch",
                data_schema=_get_schema_with_available_ports(
                    Platform.SWITCH, self.configured_ports
                ),
            )
        new_data = self.config_entry.data.copy()
        ports = user_input.pop(CONF_PORTS)
        new_data[CONF_SWITCHES] = {port: user_input for port in ports}
        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
        self.hass.async_create_task(
            self.hass.config_entries.async_reload(self.config_entry.entry_id)
        )
        return self.async_create_entry(title="", data={})

    async def async_step_add_cover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a cover entry."""

        if user_input is None:
            return self.async_show_form(
                step_id="add_cover",
                data_schema=_get_schema_with_available_ports(
                    Platform.COVER, self.configured_ports
                ),
            )

        if user_input[CONF_RELAY_PIN] == user_input[CONF_STATE_PIN]:
            return self.async_show_form(
                step_id="add_cover",
                data_schema=_get_schema_with_available_ports(
                    Platform.COVER, self.configured_ports
                ),
                errors={CONF_RELAY_PIN: "same_port", CONF_STATE_PIN: "same_port"},
            )

        new_data = self.config_entry.data.copy()
        new_data.setdefault(CONF_COVERS, {})[
            f"{user_input[CONF_RELAY_PIN]}-{user_input[CONF_STATE_PIN]}"
        ] = user_input

        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
        self.hass.async_create_task(
            self.hass.config_entries.async_reload(self.config_entry.entry_id)
        )
        return self.async_create_entry(title="", data={})

    async def async_step_remove(
        self, user_input: dict[str, list[str]] | None = None
    ) -> FlowResult:
        """Remove configured entity."""
        if user_input is None:
            return self.async_show_form(
                step_id="remove",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_ENTITIES, default=[]
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=_async_get_registered_entities(
                                    self.hass, self.config_entry.entry_id
                                ),
                                multiple=True,
                                mode=selector.SelectSelectorMode.DROPDOWN,
                            )
                        )
                    }
                ),
            )
        new_data: dict[str, dict[str, Any]] = self.config_entry.data.copy()
        for entity in user_input[CONF_ENTITIES]:
            platform, unique_id = entity.split("/")
            new_data[f"{platform}s"].pop(unique_id)
            async_dispatcher_send(self.hass, f"port_{unique_id}_removed")

        self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)

        return self.async_create_entry(title="", data={})
