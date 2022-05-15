"""Platform for light integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_COLOR_TEMP,
    LightEntity,
)
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

# Import the device class from the component that you want to support
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util.color import (
    color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin,
)
from homeassistant.util.percentage import percentage_to_ordered_list_item

from . import DOMAIN
from .const import FunctionClass
from .hubspace import HubspaceEntity, HubspaceFunction, HubspaceStateValue

SCAN_INTERVAL = timedelta(seconds=30)
BASE_INTERVAL = timedelta(seconds=30)


def _brightness_to_hass(value):
    return int(value * 255) // 100


def _brightness_to_hubspace(value):
    return value * 100 // 255


def _color_temp_to_hass(value) -> int:
    return color_temperature_kelvin_to_mired(float(value[:-1]))


def _color_temp_to_hubspace(value) -> str:
    return f"{color_temperature_mired_to_kelvin(value)}K"


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.

    domain_data = hass.data[DOMAIN]
    lights = [
        HubspaceLight(child, domain_data["account_id"], domain_data["refresh_token"])
        for child in domain_data["children"]
        if child.get("semanticDescriptionKey", None) == "light"
    ]
    add_entities(lights, True)


class HubspaceLightFunction(HubspaceFunction):
    def _value_key(self, value: Any) -> Any:
        if self.function_class == FunctionClass.COLOR_TEMPERATURE:
            return _color_temp_to_hass(value)
        return value


class HubspaceLightStateValue(HubspaceStateValue):
    def hass_value(self) -> Any or None:
        if self.function_class == FunctionClass.BRIGHTNESS:
            return _brightness_to_hass(self.hubspace_value())
        return super().hass_value()

    def set_hass_value(self, value):
        if self.function_class == FunctionClass.BRIGHTNESS:
            self.set_hubspace_value(_brightness_to_hubspace(value))
        else:
            super().set_hubspace_value(value)


class HubspaceLight(LightEntity, HubspaceEntity):
    """Representation of a Hubspace Light."""

    _function_class = HubspaceLightFunction
    _state_value_class = HubspaceLightStateValue

    @property
    def supported_color_modes(self) -> set[str] or None:
        """Flag supported color modes."""
        color_modes = set()
        if FunctionClass.BRIGHTNESS in self.functions:
            color_modes.add(COLOR_MODE_BRIGHTNESS)
        if FunctionClass.COLOR_TEMPERATURE in self.functions:
            color_modes.add(COLOR_MODE_COLOR_TEMP)
        return color_modes

    @property
    def is_on(self) -> bool or None:
        """Return whether the light is on, or if multiple all the lights are on."""
        return self._get_state_value(FunctionClass.POWER, STATE_OFF) == STATE_ON

    @property
    def brightness(self) -> int or None:
        """Return the brightness of this light between 0..255."""
        return self._get_state_value(FunctionClass.BRIGHTNESS)

    @property
    def color_temp(self) -> int or None:
        """Return the CT color value in mireds."""
        value = self._get_state_value(FunctionClass.COLOR_TEMPERATURE)
        if not value:
            return None
        return _color_temp_to_hass(value)

    @property
    def min_mireds(self) -> int:
        """Return the coldest color_temp that this light supports."""
        hubspace_values = self._get_function_values(FunctionClass.COLOR_TEMPERATURE)
        if not hubspace_values:
            return super().min_mireds
        return _color_temp_to_hass(hubspace_values[0])

    @property
    def max_mireds(self) -> int:
        """Return the warmest color_temp that this light supports."""
        hubspace_values = self._get_function_values(FunctionClass.COLOR_TEMPERATURE)
        if not hubspace_values:
            return super().min_mireds
        return _color_temp_to_hass(hubspace_values[-1])

    def turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""

        self._set_state_value(FunctionClass.POWER, STATE_ON)
        if ATTR_BRIGHTNESS in kwargs:
            self._set_state_value(FunctionClass.BRIGHTNESS, kwargs[ATTR_BRIGHTNESS])
        if ATTR_COLOR_TEMP in kwargs:
            self._set_state_value(
                FunctionClass.COLOR_TEMPERATURE,
                percentage_to_ordered_list_item(
                    self._get_function_values(
                        FunctionClass.COLOR_TEMPERATURE, default=[]
                    ),
                    (kwargs[ATTR_COLOR_TEMP] - self.min_mireds)
                    / (self.max_mireds - self.min_mireds)
                    * 100,
                ),
            )
        self._push_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._set_state_value(FunctionClass.POWER, STATE_OFF)
        self._push_state()
