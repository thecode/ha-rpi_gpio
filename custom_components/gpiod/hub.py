from __future__ import annotations

from . import DOMAIN
from time import sleep
LISTENER_WINDOW = 5

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, EVENT_HOMEASSISTANT_START

from collections import defaultdict
from datetime import timedelta
import gpiod

from gpiod.line import Direction, Value, Bias, Edge, Clock
EventType = gpiod.EdgeEvent.Type

class Hub:

    manufacturer = "ha_gpiod"

    def __init__(self, hass: HomeAssistant, path: str) -> None:
        """GPIOD Hub"""

        _LOGGER.debug(f"in hub.__init__ {path}")

        self._path = path
        self._name = path
        self._id = path
        self._hass = hass
        self._online = False
        self._config = defaultdict(gpiod.LineSettings)
        self._lines = None
        self._edge_events = False
        self._listener = None
        self._entities = {}

        if not gpiod.is_gpiochip_device(path):
            _LOGGER.debug(f"initilization failed: {path} not a gpiochip_device")
            return
        with gpiod.Chip(path) as chip:
            info = chip.get_info()
            if not "pinctrl" in info.label:
                _LOGGER.debug(f"initialization failed: {path} no pinctrl")
                return

        self._online = True

        if self._online:
            _LOGGER.info(f"initialized: {path}")
        else:
            _LOGGER.warning(f"initialization failed: {path}")
    
        # startup and shutdown triggers of hass
        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, self.startup)
        self._hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.cleanup)

    def startup(self, _):
        """Stuff to do after starting."""
        _LOGGER.debug(f"startup {DOMAIN} hub")
        if not self._online:
            return

        self.update_lines()
        if not self._edge_events:
            return

        _LOGGER.debug("Start listener")
        self._listener = self._hass.create_task(self.listen())


    def cleanup(self, _):
        """Stuff to do before stopping."""
        _LOGGER.debug(f"cleanup {DOMAIN} hub")
        if self._listener:
            self._listener.cancel()
            # wait for loop time, give wait_edge_events some time
            sleep(LISTENER_WINDOW)
        if self._config:
            self._config.clear()
        if self._lines:
            self._lines.release()
        self._online = False

    @property
    def hub_id(self) -> str:
        """ID for hub"""
        return self._id

    def update_lines(self) -> None:
        if not self._online:
            _LOGGER.debug(f"gpiod hub not online {self._path}")
        if not self._config:
            _LOGGER.debug(f"gpiod config is empty")
        if self._lines:
            self._lines.release()

        _LOGGER.debug(f"updating lines: {self._config}")
        self._lines = gpiod.request_lines(
            self._path,
            consumer = self.manufacturer,
            config = self._config
        )

    async def listen(self):
        while True:
            _LOGGER.debug("Listener loop")
            events_available = await self._hass.async_add_executor_job(
                self._lines.wait_edge_events,timedelta(seconds=LISTENER_WINDOW))
            if events_available:
                events = await self._hass.async_add_executor_job(
                    self._lines.read_edge_events)
                for event in events:
                    _LOGGER.debug(f"Event: {event}")
                    self._entities[event.line_offset].set(
                       True if event.event_type == EventType.RISING_EDGE else False
                    )

    def add_switch(self, entity, port, invert_logic) -> None:
        _LOGGER.debug(f"in add_switch {port}")
        self._entities[port] = entity
        self._config[port].direction = Direction.OUTPUT
        self._config[port].output_value = Value.INACTIVE
        self._config[port].active_low = invert_logic

    def turn_on(self, port) -> None:
        _LOGGER.debug(f"in turn_on")
        self._lines.set_value(port, Value.ACTIVE)
        
    def turn_off(self, port) -> None:
        _LOGGER.debug(f"in turn_off")
        self._lines.set_value(port, Value.INACTIVE)

    def add_sensor(self, entity, port, invert_logic, pull_mode, debounce) -> None:
        _LOGGER.debug(f"in add_sensor {port}")
        self._entities[port] = entity
        self._config[port].direction = Direction.INPUT
        self._config[port].active_low = invert_logic
        self._config[port].bias = Bias.PULL_DOWN if pull_mode == "DOWN" else Bias.PULL_UP
        self._config[port].debounce_period = timedelta(milliseconds=debounce)
        self._config[port].edge_detection = Edge.BOTH
        self._config[port].event_clock = Clock.REALTIME
        self._edge_events = True

    def update(self, port, **kwargs):
        return self._lines.get_value(port) == Value.ACTIVE

    def add_cover(self, entity, relay_pin, invert_relay, 
                      state_pin, state_pull_mode, invert_state) -> None:
        _LOGGER.debug(f"in add_cover {relay_pin} {state_pin}")
        self.add_switch(entity, relay_pin, invert_relay)
        self.add_sensor(entity, state_pin, invert_state, state_pull_mode, 50)

