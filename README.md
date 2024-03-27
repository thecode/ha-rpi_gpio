# HomeAssistant HACS custom RPI GPIOD integration

This HACS integration is used to address GPIO (especially and only tested for RaspberryPi) using libgpiod and python gpiod >=v2.02 since RPI.gpio is no longer supported. I created this for my own use, and to understand a custom integration, but since it is working on Raspberry pi feel free to use.

**This is early stuff, working in my homeassistant environment. Test and use at your own risk!**

This is a rewrite of [ha-rpi_gpio](https://github.com/thecode/ha-rpi_gpio) adapted in [ha-gpio](https://codeberg.org/raboof/ha-gpio) and completely rewritten here ..

Currently supports `binary_sensor` and `switch`; `cover` planned to be inline with the originla ha-rpi_gpio.

# Installation
Via HACS: add as custom repository from github using this github url (HACS => integrations => 3-dots menu => custom repositories)
I have no plans to make this a HACS integration adding all tests and other stuff but you are free to use this anyway. 

# Usage
The `gpiod` platform should be initialized using the path to the gpio chip. Default is `/dev/gpiochip0`. Add the following to your `configuration.yaml` file:


## Sample config for the raspberry pi berryclip hat

See also configuraton-example.yaml

```yaml
gpiod:
  path: '/dev/gpiochip0'

switch:
  - platform: gpiod
    switches:
      - name: "Led 1 red"
        port: 4
      - name: "Led 2 red"
        port: 17
        unique_id: "gpio_led_red_2"
      - name: "Led 3 yellow"
        port: 22
        invert_logic: true
      - name: "Led 4 yellow"
        port: 10
      - name: "Led 5 green"
        port: 9
      - name: "Led 6 green"
        port: 11
      - name: "Buzzer"
        port: 8

binary_sensor:
  - platform: gpiod
    sensors:
    - name: "Button"
      port: 7
```

## Platform

Key | Required | Default | Type | Description
-- | -- | -- | -- | --
`gpiod:` | yes | | | `gpiod` platform config and initialization
`path` | no | /dev/gpiochip0 | string | path to gpio device

## Binary Sensor

The `gpiod` binary sensor platform allows you to read sensor values of the GPIOs of your device.

### Configuration options

Key | Required | Default | Type | Description
-- | -- | -- | -- | --
`sensors` | yes | | list | List of sensor IO ports ([Raspberry Pi BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png))
`name` | yes | | string  | The name for the binary sensor entity
`port` | yes | | integer | the GPIO port to be used
`unique_id` | no | | string  | An ID that uniquely identifies the sensor. Set this to a unique value to allow customization through the UI
`bouncetime` | no | `50` | integer | The time in milliseconds for port debouncing
`invert_logic` | no | `false` (ACTIVE HIGH) | boolean | If `true`, inverts the output logic to ACTIVE LOW
`pull_mode` | no | `UP` | string  | Type of internal pull resistor to use: `UP` - pull-up resistor, `DOWN` - pull-down resistor


## Switch

The `gpiod` switch platform allows you to control the GPIOs of your device.


### Options

Key | Required | Default | Type | Description
-- | -- | -- | -- | --
`switches` | yes | | list | List of switch IO ports ([Raspberry Pi BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png))
`name` | yes | | string | The name for the switch entity
`port` | yes | | integer | the GPIO port to be used
`unique_id` | no | | string | An ID that uniquely identifies the switch. Set this to a unique value to allow customization through the UI
`invert_logic` | no | `false` | boolean | If true, inverts the output logic to ACTIVE LOW

## Add Debug info
```yaml
logger:
  default: info
  logs:
    custom_components.gpiod: debug
```


