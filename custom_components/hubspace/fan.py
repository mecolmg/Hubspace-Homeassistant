"""Platform for fan integration."""
from typing import Any

from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)
from .const import TOGGLE_DISABLED, TOGGLE_ENABLED, FunctionClass
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from . import DOMAIN, hubspace
from homeassistant.components.fan import (
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
    FanEntity,
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType or None = None,
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.

    domain_data = hass.data[DOMAIN]
    fans = [
        HubspaceFanEntity(
            child, domain_data["account_id"], domain_data["refresh_token"]
        )
        for child in domain_data["children"]
        if child.get("semanticDescriptionKey", None) == "fan"
    ]
    add_entities(fans, True)


class HubspaceFanFunction(hubspace.HubspaceFunction):
    def _value_key(self, value: Any) -> Any:
        if self.function_class == FunctionClass.FAN_SPEED:
            # Sorts fan speeds which have a format "fan-speed-025"
            return int(value[-3:])
        return value


class HubspaceFanEntity(FanEntity, hubspace.HubspaceEntity):
    """Representation of a Hubspace Fan."""

    _function_class = HubspaceFanFunction
    _attr_supported_features = SUPPORT_SET_SPEED

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        supported_features = 0
        if FunctionClass.FAN_SPEED in self.functions:
            supported_features |= SUPPORT_SET_SPEED
        if self.preset_modes:
            supported_features |= SUPPORT_PRESET_MODE
        return supported_features

    @property
    def is_on(self) -> bool or None:
        """Return whether the fan is on."""
        return self._get_state_value(FunctionClass.POWER, STATE_OFF) == STATE_ON

    @property
    def _fan_speed_values(self) -> list[str] or None:
        fan_speed_values = self._get_function_values(FunctionClass.FAN_SPEED)
        if fan_speed_values:
            # Remove off state from list of values.
            return fan_speed_values[1:]
        return None

    @property
    def percentage(self) -> int or None:
        """Return the current speed percentage."""
        return (
            ordered_list_item_to_percentage(
                self._fan_speed_values,
                self._get_state_value(FunctionClass.FAN_SPEED),
            )
            if self._fan_speed_values
            else None
        )

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return (
            len(self._fan_speed_values)
            if self._fan_speed_values
            else super().speed_count
        )

    @property
    def preset_mode(self) -> str or None:
        """Return the current preset mode, e.g., auto, smart, interval, favorite.

        Requires SUPPORT_SET_SPEED.
        """
        for [function_class, function] in self.states.items():
            for [function_instance, state] in function.items():
                if (
                    function_class == FunctionClass.TOGGLE
                    and function_instance is not None
                    and state.hubspace_value() == "enabled"
                ):
                    return function_instance
        return "auto"

    @property
    def preset_modes(self) -> list[str] or None:
        """Return a list of available preset modes.

        Requires SUPPORT_SET_SPEED.
        """
        preset_modes = []
        for function in self.functions.values():
            preset_modes.extend(
                [
                    function_instance
                    for function_instance in function.keys()
                    if function_instance is not None
                ]
            )
        if preset_modes:
            preset_modes.insert(0, "auto")
        return preset_modes

    def turn_on(
        self,
        percentage: int or None = None,
        preset_mode: str or None = None,
        **kwargs,
    ) -> None:
        """Instruct the light to turn on."""
        self._set_state_value(FunctionClass.POWER, STATE_ON)
        if percentage is not None:
            self._set_state_value(
                FunctionClass.FAN_SPEED,
                percentage_to_ordered_list_item(self._fan_speed_values, percentage),
            )
        if preset_mode is not None:
            self._set_state_value((FunctionClass.TOGGLE, preset_mode), TOGGLE_ENABLED)
        self._push_state()

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        self._set_state_value(
            FunctionClass.FAN_SPEED,
            percentage_to_ordered_list_item(self._fan_speed_values, percentage),
        )
        self._push_state()

    def set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == "auto":
            for mode in self.preset_modes:
                self._set_state_value((FunctionClass.TOGGLE, mode), TOGGLE_DISABLED)
        else:
            self._set_state_value((FunctionClass.TOGGLE, preset_mode), TOGGLE_ENABLED)
        self._push_state()

    def turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        self._set_state_value(FunctionClass.POWER, STATE_OFF)
        self._push_state()
