# Home Assistant Raspberry Pi GPIO custom integration

**This is a spin-off from the original Home Assistant integration, which was removed in Home Assistant Core version 2022.6.**

The `rpi_gpio` integration supports the following platforms: `Binary Sensor`, `Cover`, `Switch`

# Installation

### HACS

The recommend way to install `rpi_gpio` is through [HACS](https://hacs.xyz/).

### Manual installation

Copy the `rpi_gpio` folder and all of its contents into your Home Assistant's `custom_components` folder. This folder is usually inside your `/config` folder. If you are running Hass.io, use SAMBA to copy the folder over. You may need to create the `custom_components` folder and then copy the `rpi_gpio` folder and all of its contents into it.

# Usage

## Binary Sensor

The `rpi_gpio` binary sensor platform allows you to read sensor values of the GPIOs of your [Raspberry Pi](https://www.raspberrypi.org/).

### Configuration

[Legacy binary sensor configuration](https://github.com/thecode/ha-rpi_gpio/blob/main/legacy-config.md#binary-sensor)

To use your Raspberry Pi's GPIO in your installation, add the following to your `configuration.yaml` file:

```yaml
# Basic configuration.yaml entry
binary_sensor:
  - platform: rpi_gpio
    sensors:
      - port: 11
        name: "PIR Office"
      - port: 12
        name: "PIR Bedroom"
```

```yaml
# Full configuration.yaml entry
binary_sensor:
  - platform: rpi_gpio
    sensors:
      - port: 11
        name: "PIR Office"
        unique_id: "pir_office_sensor_port_11"
        bouncetime: 80
        invert_logic: true
        pull_mode: "DOWN"
      - port: 12
        name: "PIR Bedroom"
        unique_id: "pir_bedroom_sensor_port_12"
```

### Options

| Key            | Required | Default               | Type    | Description                                                                                                 |
| -------------- | -------- | --------------------- | --------|------------------------------------------------------------------------------------------------------------ |
| `sensors`      | yes      |                       | list    | List of sensor IO ports ([BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png))      |
| `name`         | yes      |                       | string  | The name for the binary sensor entity                                                                       |
| `unique_id`    | no       |                       | string  | An ID that uniquely identifies the sensor. Set this to a unique value to allow customization through the UI |
| `bouncetime`   | no       | `50`                  | integer | The time in milliseconds for port debouncing                                                                |
| `invert_logic` | no       | `false` (ACTIVE HIGH) | boolean | If `true`, inverts the output logic to ACTIVE LOW                                                           |
| `pull_mode`    | no       | `UP`                  | string  | Type of internal pull resistor to use: `UP` - pull-up resistor, `DOWN` - pull-down resistor                 |

For more details about the GPIO layout, visit the Wikipedia [article](https://en.wikipedia.org/wiki/Raspberry_Pi#General_purpose_input-output_(GPIO)_connector) about the Raspberry Pi.

## Cover

The `rpi_gpio` cover platform allows you to use a Raspberry Pi to control your cover such as Garage doors.

It uses two pins on the Raspberry Pi.

- The `state_pin` will detect if the cover is closed, and
- the `relay_pin` will trigger the cover to open or close.

Although you do not need Andrews Hilliday's software controller when you run Home Assistant, he has written clear instructions on how to hook your garage door and sensors up to your Raspberry Pi, which can be found [here](https://github.com/andrewshilliday/garage-door-controller#hardware-setup).

### Configuration

To enable Raspberry Pi Covers in your installation, add the following to your `configuration.yaml` file:

```yaml
# Basic configuration.yaml entry
cover:
  - platform: rpi_gpio
    covers:
      - relay_pin: 10
        state_pin: 11
```

```yaml
# Full configuration.yaml entry
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
        unique_id: "right_door_cover_port_13"
```

### Options

| Key               | Required | Default | Type    | Description                                                                                                |
| ----------------- | -------- | ------- | ------- | ---------------------------------------------------------------------------------------------------------- |
| `relay_time`      | no       | `0.2`   | float   | The time that the relay will be on for in seconds                                                          |
| `invert_relay`    | no       | `false` | boolean | Invert the relay pin output so that it is active-high (True)                                               |
| `state_pull_mode` | no       | `UP`    | string  | The direction the State pin is pulling. It can be `UP` or `DOWN`                                           |
| `invert_state`    | no       | `false` | boolean | Invert the value of the State pin so that 0 means closed                                                   |
| `covers`          | yes      |         | list    | List of covers                                                                                             |
| `relay_pin`       | yes      |         | integer | The pin of your Raspberry Pi where the relay is connected                                                  |
| `state_pin`       | yes      |         | integer | The pin of your Raspberry Pi to retrieve the state                                                         |
| `name`            | no       |         | string  | The name for the cover entity                                                                              |
| `unique_id`       | no       |         | string  | An ID that uniquely identifies the cover. Set this to a unique value to allow customization through the UI |

### Remote Raspberry Pi Cover

If you don't have Home Assistant running on your Raspberry Pi and you want to use it as a remote cover instead, there is a project called [GarageQTPi](https://github.com/Jerrkawz/GarageQTPi) that will work remotely with the [MQTT Cover Component](/integrations/cover.mqtt/). Follow the GitHub instructions to install and configure GarageQTPi and once configured follow the Home Assistant instructions to configure the MQTT Cover.

## Switch

The `rpi_gpio` switch platform allows you to control the GPIOs of your [Raspberry Pi](https://www.raspberrypi.org/).

### Configuration

[Legacy switch configuration](https://github.com/thecode/ha-rpi_gpio/blob/main/legacy-config.md#switch)

To use your Raspberry Pi's GPIO in your installation, add the following to your `configuration.yaml` file:

```yaml
# Basic configuration.yaml entry
switch:
  - platform: rpi_gpio
    switches:
      - port: 11
        name: "Fan Office"
      - port: 12
        name: "Light Desk"
```

```yaml
# Full configuration.yaml entry
switch:
  - platform: rpi_gpio
    switches:
      - port: 11
        name: "Fan Office"
        unique_id: "fan_office_switch_port_11"
        persistent: true
      - port: 12
        name: "Light Desk"
        unique_id: "light_desk_switch_port_12"
        invert_logic: true
```

### Options

| Key            | Required | Default | Type    | Description                                                                                                 |
| -------------- | -------- | ------- | --------| ----------------------------------------------------------------------------------------------------------- |
| `switches`     | yes      |         | list    | List of switch IO ports ([BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png))      |
| `name`         | yes      |         | string  | The name for the switch entity                                                                              |
| `unique_id`    | no       |         | string  | An ID that uniquely identifies the switch. Set this to a unique value to allow customization through the UI |
| `invert_logic` | no       | `false` | boolean | If true, inverts the output logic to ACTIVE LOW                                                             |
| `persistent`   | no       | `false` | boolean | If true, the switch state will be persistent in HA and will be restored if HA restart / crash               |

For more details about the GPIO layout, visit the Wikipedia [article](https://en.wikipedia.org/wiki/Raspberry_Pi#General_purpose_input-output_(GPIO)_connector) about the Raspberry Pi.

A common question is what does Port refer to, this number is the actual GPIO #, not the pin #.
For example, if you have a relay connected to pin 11 its GPIO # is 17.

```yaml
# Basic configuration.yaml entry
switch:
  - platform: rpi_gpio
    switches:
      - port: 17
        name: "Speaker Relay"
```
