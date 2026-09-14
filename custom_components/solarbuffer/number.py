"""Instelbaar vermogen voor de handmatige accustand."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SolarBufferConfigEntry
from .const import MAX_MANUAL_POWER_W, ruw_naar_zichtbaar, zichtbaar_naar_ruw
from .coordinator import SolarBufferCoordinator
from .entity import SolarBufferDeviceEntity, SolarBufferEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBufferConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data

    entiteiten: list[NumberEntity] = [
        SolarBufferDeviceSetpoint(coordinator, apparaat["ip"])
        for apparaat in coordinator.devices
        if apparaat.get("ip")
    ]
    if coordinator.has_zendure:
        entiteiten.append(SolarBufferManualPowerNumber(coordinator))
    async_add_entities(entiteiten)


class SolarBufferDeviceSetpoint(SolarBufferDeviceEntity, NumberEntity):
    """Handmatige stand voor één SolarBuffer.

    Alleen zinvol met de automatische besturing uit. Staat die aan, dan rekent
    de hub binnen een paar seconden zelf een nieuwe stand uit en is hier niets
    meer van over. De schakelaar Regeling zet je die besturing uit.

    Nul betekent uitzetten. Daarboven geldt het bereik waarin de dimmer
    betrouwbaar werkt; de hub begrenst een te lage of te hoge waarde zelf.
    """

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 0
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:tune-vertical"

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "device_setpoint")

    @property
    def native_value(self) -> float | None:
        if not self._device.get("on"):
            return 0
        return ruw_naar_zichtbaar(self._device.get("brightness"))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            # Zo is in Home Assistant te zien of een ingestelde stand blijft
            # staan, zonder dat je het op de hub hoeft te controleren.
            "regulation_enabled": (self.coordinator.data or {}).get("enabled"),
        }

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.async_set_device_brightness(
            self._ip, zichtbaar_naar_ruw(value)
        )
        await self.coordinator.async_refresh_soon()


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
