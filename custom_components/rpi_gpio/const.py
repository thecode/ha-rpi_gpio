"""Constants for the Raspberry Pi GPIO integration."""

DOMAIN = "rpi_gpio"

CONF_BOUNCETIME = "bouncetime"
CONF_PULL_MODE = "pull_mode"
CONF_INVERT_LOGIC = "invert_logic"
CONF_PORTS = "ports"
CONF_RELAY_PIN = "relay_pin"
CONF_RELAY_TIME = "relay_time"
CONF_STATE_PIN = "state_pin"
CONF_STATE_PULL_MODE = "state_pull_mode"
CONF_INVERT_STATE = "invert_state"
CONF_INVERT_RELAY = "invert_relay"


DEFAULT_BOUNCETIME = 50
DEFAULT_INVERT_LOGIC = False
DEFAULT_PULL_MODE = "UP"
DEFAULT_RELAY_TIME = 0.2
DEFAULT_STATE_PULL_MODE = "UP"
DEFAULT_INVERT_STATE = False
DEFAULT_INVERT_RELAY = False

PUD_DOWN = "21"
PUD_UP = "22"

GPIO_PIN_MAP = {
    "0": "27",
    "1": "28",
    "2": "3",
    "3": "5",
    "4": "7",
    "5": "29",
    "6": "31",
    "7": "26",
    "8": "24",
    "9": "21",
    "10": "19",
    "11": "23",
    "12": "32",
    "13": "33",
    "14": "8",
    "15": "10",
    "16": "36",
    "17": "11",
    "18": "12",
    "19": "35",
    "20": "38",
    "21": "40",
    "22": "15",
    "23": "16",
    "24": "18",
    "25": "22",
    "26": "37",
    "27": "13",
}
