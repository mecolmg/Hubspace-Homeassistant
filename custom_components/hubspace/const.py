"""Hubspace constant variables."""

from typing import Final

# JSON Keys
DEVICE_ID: Final = "id"
DEVICE_DESCRIPTION: Final = "description"
DEVICE_STATE: Final = "state"
STATE_VALUES: Final = "values"
FUNCTION_CLASS: Final = "functionClass"
FUNCTION_INSTANCE: Final = "functionInstance"
TOGGLE_DISABLED: Final = "disabled"
TOGGLE_ENABLED: Final = "enabled"

# Function Classes
class FunctionClass:
    UNSUPPORTED = "unsupported"
    POWER = "power"
    BRIGHTNESS = "brightness"
    FAN_SPEED = "fan-speed"
    AVAILABLE = "available"
    TOGGLE = "toggle"
    COLOR_TEMPERATURE = "color-temperature"


# List of function classes that can be set by home assistant.
SETTABLE_FUNCTION_CLASSES: Final = [
    FunctionClass.POWER,
    FunctionClass.BRIGHTNESS,
    FunctionClass.FAN_SPEED,
    FunctionClass.TOGGLE,
    FunctionClass.COLOR_TEMPERATURE,
]

# Function Instances
class FunctionInstance:
    LIGHT_POWER = "light-power"
    FAN_POWER = "fan-power"
    FAN_SPEED = "fan-speed"
    COMFORT_BREEZE = "comfort-breeze"


# Function Key.
FunctionKey = str or tuple(str, str or None)
