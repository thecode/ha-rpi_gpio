# My dev environment howto ..

## Set up dev environment

Create virtual env anywhere, but most likely in project directory /venv
```bash
python -m venv venv

```

Add `homeassistant` and `gpiod` to the environement

```bash
. ./venv/bin/activate
(venv) ha_gpiod$ pip install homeassitant
(venv) ha_gpiod$ pip install gpiod
```

## Edit code in dev environment

Using `neovim` and related LSPs for python

```bash
. ./venv/bin/activate
(venv) ha_gpiod$ nvimt &
```

## Test runs
For testing I use a separate `rpi3`, copying code to the rpi3:
```bash
scp -r custom_components/gpiod rpi3:
```

and start homeassistant docker a bash script `./test`:

```bash
#!/bin/sh

rm -rf custom_components/*gpio*/
cp -r ~user/*gpio* custom_components/
chmod a+rX custom_components/*gpio*
docker-compose up homeassistant

echo ## Last bits of log
tail home-assistant.log

```

## Documentation
Pushing to github to verify the markdown was a bit tiresome, [mmark](https://mmark.miek.nl/) helps out, really nice cli markdown renderer.

```bash
# render to html
mmark -html README.md > /tmp/mmark.html
# or with styling
mmark -css ~/Projects/markdown.css -html README.md > /tmp/mmark.html
# open in default browser
xdg-open /tmp/mmark.html
```
