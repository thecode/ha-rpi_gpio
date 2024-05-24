# HomeAssistant HACS custom RPI GPIOD integration

This HACS integration is used to address GPIO (especially and only tested for RaspberryPi) using libgpiod and python gpiod >=v2.02 since RPI.gpio is no longer supported. I created this for my own use, and to understand a custom integration, but since it is working on Raspberry pi feel free to use.

**This is working in my homeassistant environment, that's it. Shared for testing and usage at your own risk!**

This is a rewrite of [ha-rpi_gpio](https://github.com/thecode/ha-rpi_gpio) adapted in [ha-gpio](https://codeberg.org/raboof/ha-gpio) and rewritten by me ..

# Installation
Via HACS: add as custom repository from github using this github https://github.com/jdeneef/ha_gpiod/ (HACS => integrations => 3-dots menu => custom repositories, go back to hacs, install gpiod component, reboot, add config, reboot)
I have no plans to make this a HACS integration adding all tests and other stuff but you are free to use this anyway. 

# Usage
The `gpiod` platform should be initialized using the path to the gpio chip. When path is not added in the config `/dev/gpiochip[0-5]` are tested for being a gpiodevice having `pinctrl`, in sequence `[0,4,1,2,3,5]`. So with a raspberry pi you should be OK to leave the path empty.

Raspberry Pi | GPIO Device
--- | ---
RPi3, RPi4 | `/dev/gpiochip0`
RPi5 | `/dev/gpiochip4`


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

cover:
  - platform: gpiod
    covers:
      - relay_pin: 4
        name: Cover blue
        state_pin: 7
        relay_time: 1200
 ```

## Platform

Key | Required | Default | Type | Description
-- | -- | -- | -- | --
`gpiod` | only for path| | | `gpiod` platform config and initialization, only required when you need to specify a specific gpiodevice path (see path)
`path` | no | discovered | string | path to gpio device, if not set autodiscovered

## Binary Sensor

The `gpiod` binary sensor platform allows you to read sensor values of the GPIOs of your device.

### Configuration options

Key | Required | Default | Type | Description
-- | -- | -- | -- | --
`sensors` | yes | | list | List of sensor IO ports ([Raspberry Pi BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png))
`name` | yes | | string  | The name for the binary sensor entity
`port` | yes | | integer | the GPIO port to be used
`unique_id` | no | generated | string  | An ID that uniquely identifies the sensor. Set this to a unique value to allow customization through the UI, auto generated when not set manually in config
`debounce` | no | `50` | integer | The time in milliseconds for port debouncing
`invert_logic` | no | `false` | boolean | If `true`, inverts the output logic to ACTIVE LOW
`pull_mode` | no | `UP` | string  | Type of internal pull resistor to use: `UP` - pull-up resistor, `DOWN` - pull-down resistor


## Switch

The `gpiod` switch platform allows you to control the GPIOs of your device.


### Options

Key | Required | Default | Type | Description
-- | -- | -- | -- | --
`switches` | yes | | list | List of switch IO ports ([Raspberry Pi BCM mode pin numbers](https://pinout.xyz/resources/raspberry-pi-pinout.png))
`name` | yes | | string | The name for the switch entity
`port` | yes | | integer | the GPIO port to be used
`unique_id` | no | generated | string | An ID that uniquely identifies the switch. Set this to a unique value to allow customization through the UI, auto generated when not set manually in config
`invert_logic` | no | `false` | boolean | If true, inverts the output logic to ACTIVE LOW

## Cover

The `gpiod` cover platform allows you to control GPIOs to open/close covers; note that I have only verified cover functionality simulating with switches and buttons, so logic could be off on some points ..

### Options

Key | Required | Default | Type | Description
-- | -- | -- | -- | --
`name` | yes | | string | The name for the cover entity
`relay_pin`|yes| |integer|Relay switch pin switching cover motor
`relay_time`|no|`200` |integer|Time in milliseconds relay switch will be switched to open/close cover
`invert_relay`|no | `false`| boolean| invert logic for relay pin
`state_pin`|yes| | integer|State pin sharing opened/closed status of cover
`state_pull_mode`|no|`UP`|string|pull_mode for state trigger
`invert_state`|no|`true`|boolean|invert logic for state pin
`unique_id` | no | generated | string | An ID that uniquely identifies the switch. Set this to a unique value to allow customization through the UI, auto generated when not set manually in config
    
## Add Debug info
```yaml
logger:
  default: info
  logs:
    custom_components.gpiod: debug
```

