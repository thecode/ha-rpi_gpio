# HomeAssistant HACS custom RPI GPIO integration

This HACS integration is used to address GPIO (especially and only tested for RaspberryPi) using libgpiod and python gpiod >=v2

**This is very very early stuff, don't use in your setup in any way**

[python gpiod examples](https://github.com/brgl/libgpiod/tree/master/bindings/python/examples)


## Sample config for the raspberry pi berryclip hat

Aiming for config_flow configuration, but nevertheless:

```yaml
ha-gpiod:
  chip: '/dev/gpiochip0'
  switches:
    - name: "Led 1 red"
      line_offset: 4
    - name: "Led 2 red"
      line_offset: 17
    - name: "Led 3 yellow"
      line_offset: 22
    - name: "Led 4 yellow"
      line_offset: 10
    - name: "Led 5 green"
      line_offset: 9
    - name: "Led 6 green"
      line_offset: 11
    - name: "Buzzer"
      line_offset: 8
  buttons:
    - name: "Button"
      line_offset: 7
  invert_logic: false
```

## Add Debug info
```yaml
logger:
  default: info
  logs:
    custom_components.ha-gpiod: debug
```
