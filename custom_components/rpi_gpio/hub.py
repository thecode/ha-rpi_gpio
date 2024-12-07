from __future__ import annotations

from . import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

from homeassistant.core import HomeAssistant
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, EVENT_HOMEASSISTANT_START
from homeassistant.exceptions import HomeAssistantError

from typing import Dict
from datetime import timedelta
import gpiod

from gpiod.line import Direction, Value, Bias, Drive, Edge, Clock
EventType = gpiod.EdgeEvent.Type

BIAS = { 
    "UP": Bias.PULL_UP, 
    "DOWN": Bias.PULL_DOWN,
    "DISABLED": Bias.DISABLED,
    "AS_IS": Bias.AS_IS,
}
DRIVE = { 
    "OPEN_DRAIN": Drive.OPEN_DRAIN, 
    "OPEN_SOURCE": Drive.OPEN_SOURCE, 
    "PUSH_PULL": Drive.PUSH_PULL, 
} 

class Hub:

    def __init__(self, hass: HomeAssistant, path: str) -> None:
        """GPIOD Hub"""

        self._path = path
        self._chip :  gpiod.Chip
        self._name = path
        self._id = path
        self._hass = hass
        self._online = False

        if path:
            # use config
            _LOGGER.debug(f"trying to use configured device: {path}")
            if self.verify_gpiochip(path):
                self._online = True
                self._path = path
        else:
            # discover
            _LOGGER.debug(f"auto discovering gpio device")
            for d in [0,4,1,2,3,5]:
                # rpi3,4 using 0. rpi5 using 4
                path = f"/dev/gpiochip{d}"
                if self.verify_gpiochip(path):
                    self._online = True
                    self._path = path
                    break

        self.verify_online()
        _LOGGER.debug(f"using gpio_device: {self._path}")

    def verify_online(self):
        if not self._online:
            _LOGGER.error("No gpio device detected, bailing out")
            raise HomeAssistantError("No gpio device detected")

    def verify_gpiochip(self, path):
        if not gpiod.is_gpiochip_device(path):
            _LOGGER.debug(f"verify_gpiochip: {path} not a gpiochip_device")
            return False

        _LOGGER.debug(f"verify_gpiochip: {path} is a gpiochip_device")
        self._chip = gpiod.Chip(path)
        info = self._chip.get_info()
        if not "pinctrl" in info.label:
            _LOGGER.debug(f"verify_gpiochip: {path} no pinctrl {info.label}")
            return False

        _LOGGER.debug(f"verify_gpiochip gpiodevice: {path} has pinctrl")
        return True

    def verify_port_ready(self, port: int):
        info = self._chip.get_line_info(port)
        _LOGGER.debug(f"original port info: {info}")
        if info.used and info.consumer != DOMAIN:
            _LOGGER.error(f"Port {port} already in use by {info.consumer}")
            raise HomeAssistantError(f"Port {port} already in use by {info.consumer}")

    @property
    def hub_id(self) -> str:
        """ID for hub"""
        return self._id

    def add_switch(self, entity, port, active_low, bias, drive_mode, init_output_value = True) -> gpiod.LineRequest:
        _LOGGER.debug(f"add_switch - port: {port}, active_low: {active_low}, bias: {bias}, drive_mode: {drive_mode}, init_output_value: {init_output_value}")
        self.verify_online()
        self.verify_port_ready(port)

        line_request = self._chip.request_lines(
            consumer=DOMAIN,
            config={port: gpiod.LineSettings(
            direction = Direction.OUTPUT,
            bias = BIAS[bias],
            drive = DRIVE[drive_mode],
            active_low = active_low,
            output_value = Value.ACTIVE if init_output_value and entity.is_on else Value.INACTIVE)})
        _LOGGER.debug(f"add_switch line_request: {line_request}")
        return line_request

    def turn_on(self, line, port) -> None:
        _LOGGER.debug(f"in turn_on {port}")
        self.verify_online()
        line.set_value(port, Value.ACTIVE)

    def turn_off(self, line, port) -> None:
        _LOGGER.debug(f"in turn_off {port}")
        self.verify_online()
        line.set_value(port, Value.INACTIVE)

    def add_sensor(self, entity, port, active_low, bias, debounce) -> gpiod.LineRequest:
        _LOGGER.debug(f"add_sensor - port: {port}, active_low: {active_low}, bias: {bias}, debounce: {debounce}")
        self.verify_online()
        self.verify_port_ready(port)

        line_request = self._chip.request_lines(
            consumer=DOMAIN,
            config={port: gpiod.LineSettings(
                direction = Direction.INPUT,
                edge_detection = Edge.BOTH,
                bias = BIAS[bias],
                active_low = active_low,
                debounce_period = timedelta(milliseconds=debounce),
                event_clock = Clock.REALTIME)})

        entity.is_on = True if line_request.get_value(port) == Value.ACTIVE else False
        _LOGGER.debug(f"add_sensor line_request: {line_request}. current state: {entity.is_on}")
        return line_request

    def add_cover(self, entity, relay_port, relay_active_low, relay_bias, relay_drive, 
                  state_port, state_bias, state_active_low):
        _LOGGER.debug(f"add_cover - relay_port: {relay_port}, state_port: {state_port}")
        relay_line = self.add_switch(entity, relay_port, relay_active_low, relay_bias, relay_drive, init_output_value = False)
        state_line = self.add_sensor(entity, state_port, state_active_low, state_bias, 50)
        return relay_line, state_line

