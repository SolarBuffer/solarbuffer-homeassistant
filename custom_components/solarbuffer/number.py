"""Instelbaar vermogen voor de handmatige accustand."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SolarBufferConfigEntry
from .const import MAX_MANUAL_POWER_W
from .coordinator import SolarBufferCoordinator
from .entity import SolarBufferEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBufferConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    if not coordinator.has_zendure:
        return
    async_add_entities([SolarBufferManualPowerNumber(coordinator)])


class SolarBufferManualPowerNumber(SolarBufferEntity, NumberEntity):
    """Vermogen voor de handmatige stand.

    De hub topt dit zelf af op de ingestelde maximale laad- of ontlaadwaarde
    van de accu, dus een ruimere bovengrens hier kan geen kwaad.
    """

    _attr_native_min_value = 0
    _attr_native_max_value = MAX_MANUAL_POWER_W
    _attr_native_step = 50
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: SolarBufferCoordinator) -> None:
        super().__init__(coordinator, "battery_manual_power")

    @property
    def native_value(self) -> float | None:
        waarde = (self.coordinator.data or {}).get("battery_manual_power")
        return float(waarde) if waarde is not None else None

    async def async_set_native_value(self, value: float) -> None:
        d = self.coordinator.data or {}
        await self.coordinator.client.async_set_battery_mode(
            d.get("battery_control_mode") or "manual",
            direction=d.get("battery_manual_direction"),
            power=int(value),
        )
        await self.coordinator.async_refresh_soon()
