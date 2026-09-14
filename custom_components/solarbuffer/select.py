"""Keuzelijst voor de accustand: automatisch, handmatig of uit."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SolarBufferConfigEntry
from .const import BATTERY_DIRECTIONS, BATTERY_MODES
from .coordinator import SolarBufferCoordinator
from .entity import SolarBufferEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBufferConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    # De hub weigert deze endpoints als er geen Zendure hangt, dus dan maken we
    # de entiteiten ook niet aan.
    if not coordinator.has_zendure:
        return
    async_add_entities(
        [
            SolarBufferBatteryModeSelect(coordinator),
            SolarBufferBatteryDirectionSelect(coordinator),
        ]
    )


class SolarBufferBatteryModeSelect(SolarBufferEntity, SelectEntity):
    """Automaat laat SolarBuffer regelen, handmatig volgt jouw setpoint, uit is standby."""

    _attr_options = BATTERY_MODES
    _attr_icon = "mdi:home-battery"

    def __init__(self, coordinator: SolarBufferCoordinator) -> None:
        super().__init__(coordinator, "battery_mode")

    @property
    def current_option(self) -> str | None:
        return (self.coordinator.data or {}).get("battery_control_mode")

    async def async_select_option(self, option: str) -> None:
        d = self.coordinator.data or {}
        await self.coordinator.client.async_set_battery_mode(
            option,
            direction=d.get("battery_manual_direction"),
            power=d.get("battery_manual_power"),
        )
        await self.coordinator.async_refresh_soon()


class SolarBufferBatteryDirectionSelect(SolarBufferEntity, SelectEntity):
    """Laden of ontladen, telt alleen mee in de handmatige stand."""

    _attr_options = BATTERY_DIRECTIONS
    _attr_icon = "mdi:swap-vertical"

    def __init__(self, coordinator: SolarBufferCoordinator) -> None:
        super().__init__(coordinator, "battery_direction")

    @property
    def current_option(self) -> str | None:
        return (self.coordinator.data or {}).get("battery_manual_direction")

    async def async_select_option(self, option: str) -> None:
        d = self.coordinator.data or {}
        await self.coordinator.client.async_set_battery_mode(
            d.get("battery_control_mode") or "manual",
            direction=option,
            power=d.get("battery_manual_power"),
        )
        await self.coordinator.async_refresh_soon()
