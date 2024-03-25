from __future__ import annotations

from . import DOMAIN
import asyncio
import threading
from time import sleep
LISTENER_LOOP=1

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant, callback

from collections import defaultdict
from datetime import timedelta
import gpiod

from gpiod.line import Direction, Value, Bias, Edge, Clock

class Hub:

    manufacturer = "ha_gpiod"

    def __init__(self, hass: HomeAssistant, path: str) -> None:
        """GPIOD Hub"""

        _LOGGER.debug(f"in hub.__init__ {path}")

        self._path = path
        self._name = path
        self._id = path
        self._hass = hass
        self._config = defaultdict(gpiod.LineSettings)
        self._lines = None
        self._online = False
        self._edge_events = False
        self._listening = False
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


    @property
    def hub_id(self) -> str:
        """ID for hub"""
        return self._id

    def cleanup(self) -> None:
        _LOGGER.debug("hub.cleanup")
        self._listening = False
        # wait for loop time, give wait_edge_eventns time to timeout
        sleep(LISTENER_LOOP)
        if self._config:
            self._config.clear()
        if self._lines:
            self._lines.release()
        self._online = False

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

    def edge_detect(self):
        _LOGGER.debug("in hub.edge_detect")
        if not self._edge_events:
            return
        self._listener = threading.Thread(target=self.listener,daemon=True).start()
        # self._listener = self._hass.create_task(self.listen())
        # self._listener = asyncio.create_task(self.listen())
        # self._listener = hass.async_create_background_task(self.listen(), "listener_task_gpiod")
        # _LOGGER.debug(f"listener: {self._listener}")

    def listener(self):
        self._listening = True
        # wait some time to allow other entities to startup
        sleep(5)
        while self._listening:
            if self._lines.wait_edge_events(timedelta(seconds=LISTENER_LOOP)):
                events = self._lines.read_edge_events()
                for event in events:
                    _LOGGER.debug(f"Event: {event}")
            else:
                _LOGGER.debug(f"no event, rewhile: {self._listening}")
        _LOGGER.debug("listener stopped")

    def add_switch(self, entity, port, invert_logic) -> None:
        _LOGGER.debug(f"in add_switch {port}")
        self._entities[port] = entity
        self._config[port].direction = Direction.OUTPUT
        self._config[port].output_value = Value.INACTIVE
        self._config[port].active_low = invert_logic
        self.update_lines()

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
        self.update_lines()

    def update(self, **kwargs):
        return self._lines.get_value(port) == Value.ACTIVE
