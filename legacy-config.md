# Legacy binary sensor and switch configuration

**This configuration is used for backward compatibility and should not be used for new installations.**

## Binary Sensor

The `rpi_gpio` binary sensor platform allows you to read sensor values of the GPIOs of your [Raspberry Pi](https://www.raspberrypi.org/).

### Configuration

To use your Raspberry Pi's GPIO in your installation, add the following to your `configuration.yaml` file:

```yaml
# Basic configuration.yaml entry
binary_sensor:
  - platform: rpi_gpio
    ports:
      11: PIR Office
      12: PIR Bedroom
```

```yaml
# Full configuration.yaml entry
binary_sensor:
  - platform: rpi_gpio
    bouncetime: 80
    invert_logic: true
    pull_mode: "DOWN"
    ports:
      11: PIR Office
      12: PIR Bedroom
```

### Options

| Key            | Required | Default               | Type    | Description                                                                |
| -------------- | -------- | --------------------- | --------|------------------------------------------------------------------ |
| `bouncetime`   | no       | `50`                  | integer | The time in milliseconds for port debouncing                                                |
| `invert_logic` | no       | `false` (ACTIVE HIGH) | boolean | If `true`, inverts the output logic to ACTIVE LOW                                           |
| `pull_mode`    | no       | `UP`                  | string  | Type of internal pull resistor to use: `UP` - pull-up resistor, `DOWN` - pull-down resistor |
| `ports`        | yes      |                       | list    | List of used ports ([BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png)) and corresponding names |

For more details about the GPIO layout, visit the Wikipedia [article](https://en.wikipedia.org/wiki/Raspberry_Pi#General_purpose_input-output_(GPIO)_connector) about the Raspberry Pi.

## Switch

The `rpi_gpio` switch platform allows you to control the GPIOs of your [Raspberry Pi](https://www.raspberrypi.org/).

### Configuration

To use your Raspberry Pi's GPIO in your installation, add the following to your `configuration.yaml` file:

```yaml
# Basic configuration.yaml entry
switch:
  - platform: rpi_gpio
    ports:
      11: Fan Office
      12: Light Desk
```

```yaml
# Full configuration.yaml entry
switch:
  - platform: rpi_gpio
    invert_logic: true
    ports:
      11: Fan Office
      12: Light Desk
```

### Options

| Key            | Required | Default | Type            | Description                                         |
| -------------- | -------- | ------- | --------------- | --------------------------------------------------- |
| `invert_logic` | no       | `false` | boolean         | If true, inverts the output logic to ACTIVE LOW     |
| `ports`        | yes      |                       | list    | List of used ports ([BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png)) and corresponding names |

For more details about the GPIO layout, visit the Wikipedia [article](https://en.wikipedia.org/wiki/Raspberry_Pi#General_purpose_input-output_(GPIO)_connector) about the Raspberry Pi.

**Note that a pin managed by Home Assistant is expected to be exclusive to Home Assistant.**

A common question is what does Port refer to, this number is the actual GPIO #, not the pin #.
For example, if you have a relay connected to pin 11 its GPIO # is 17.

```yaml
# Basic configuration.yaml entry
switch:
  - platform: rpi_gpio
    ports:
      17: Speaker Relay
```
