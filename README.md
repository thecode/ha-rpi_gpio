# HomeAssistant HACS custom RPI GPIOD integration

This HACS integration is used to address GPIO (especially and only tested for RaspberryPi) using libgpiod and python gpiod >=v2.02

**This is very very early stuff, don't use in your setup in any way**


## Sample config for the raspberry pi berryclip hat

Aiming for config_flow configuration, but nevertheless:

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

## Add Debug info
```yaml
logger:
  default: info
  logs:
    custom_components.gpiod: debug
```


