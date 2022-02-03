# Home Assistant Raspberry Pi GPIO custom integration

**This is a spin-off from the original Home Assistant integration which was marked as deprecated and will be removed in Home Assistant Core 2022.6.**

The `rpi_gpio` integration supports the following platforms: `Binary Sensor`, `Cover`, `Switch`

## Binary Sensor

The `rpi_gpio` binary sensor platform allows you to read sensor values of the GPIOs of your [Raspberry Pi](https://www.raspberrypi.org/).

### Configuration

To use your Raspberry Pi's GPIO in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
binary_sensor:
  - platform: rpi_gpio
    ports:
      11: PIR Office
      12: PIR Bedroom
```

For more details about the GPIO layout, visit the Wikipedia [article](https://en.wikipedia.org/wiki/Raspberry_Pi#GPIO_connector) about the Raspberry Pi.

## Cover

The `rpi_gpio` cover platform allows you to use a Raspberry Pi to control your cover such as Garage doors.

It uses two pins on the Raspberry Pi.

- The `state_pin` will detect if the cover is closed, and
- the `relay_pin` will trigger the cover to open or close.

Although you do not need Andrews Hilliday's software controller when you run Home Assistant, he has written clear instructions on how to hook your garage door and sensors up to your Raspberry Pi, which can be found [here](https://github.com/andrewshilliday/garage-door-controller#hardware-setup).

### Configuration

To enable Raspberry Pi Covers in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
cover:
  - platform: rpi_gpio
    covers:
      - relay_pin: 10
        state_pin: 11
```

### Full example

```yaml
# Example configuration.yaml entry
cover:
  - platform: rpi_gpio
    relay_time: 0.2
    invert_relay: false
    state_pull_mode: "UP"
    invert_state: true
    covers:
      - relay_pin: 10
        state_pin: 11
      - relay_pin: 12
        state_pin: 13
        name: "Right door"
```

### Remote Raspberry Pi Cover

If you don't have Home Assistant running on your Raspberry Pi and you want to use it as a remote cover instead, there is a project called [GarageQTPi](https://github.com/Jerrkawz/GarageQTPi) that will work remotely with the [MQTT Cover Component](/integrations/cover.mqtt/). Follow the GitHub instructions to install and configure GarageQTPi and once configured follow the Home Assistant instructions to configure the MQTT Cover.

## Switch

The `rpi_gpio` switch platform allows you to control the GPIOs of your [Raspberry Pi](https://www.raspberrypi.org/).

### Configuration

To use your Raspberry Pi's GPIO in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
switch:
  - platform: rpi_gpio
    ports:
      11: Fan Office
      12: Light Desk
```

For more details about the GPIO layout, visit the Wikipedia [article](https://en.wikipedia.org/wiki/Raspberry_Pi#General_purpose_input-output_(GPIO)_connector) about the Raspberry Pi.

**Note that a pin managed by Home Assistant is expected to be exclusive to Home Assistant.**

A common question is what does Port refer to, this number is the actual GPIO #, not the pin #.
For example, if you have a relay connected to pin 11 its GPIO # is 17.

```yaml
# Example configuration.yaml entry
switch:
  - platform: rpi_gpio
    ports:
      17: Speaker Relay
```
