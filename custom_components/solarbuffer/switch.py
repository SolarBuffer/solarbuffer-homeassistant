"""Schakelaars: de regeling, schema's, anti-legionella, vakantie en per apparaat."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SolarBufferConfigEntry
from .coordinator import SolarBufferCoordinator
from .entity import SolarBufferDeviceEntity, SolarBufferEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBufferConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data

    entiteiten: list[SwitchEntity] = [
        SolarBufferRegulationSwitch(coordinator),
        SolarBufferSchedulesSwitch(coordinator),
        SolarBufferLegionellaSwitch(coordinator),
        SolarBufferVacationSwitch(coordinator),
    ]
    entiteiten += [
        SolarBufferDeviceSwitch(coordinator, apparaat["ip"])
        for apparaat in coordinator.devices
        if apparaat.get("ip")
    ]
    async_add_entities(entiteiten)


class _ToggleSwitch(SolarBufferEntity, SwitchEntity):
    """Basis voor de schakelaars die de hub als 'omschakelen' aanbiedt.

    De hub heeft geen 'zet aan' en 'zet uit', alleen een omschakel-endpoint.
    We kijken daarom eerst naar de huidige stand en schakelen alleen als die
    afwijkt, anders zou aanzetten van iets dat al aan staat het juist uitzetten.
    """

    _veld: str

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get(self._veld))

    async def _async_toggle(self) -> None:
        raise NotImplementedError

    async def async_turn_on(self, **kwargs: Any) -> None:
        if not self.is_on:
            await self._async_toggle()
            await self.coordinator.async_refresh_soon()

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self.is_on:
            await self._async_toggle()
            await self.coordinator.async_refresh_soon()


class SolarBufferRegulationSwitch(_ToggleSwitch):
    _veld = "enabled"
    _attr_icon = "mdi:solar-power"

    def __init__(self, coordinator: SolarBufferCoordinator) -> None:
        super().__init__(coordinator, "regulation")

    async def _async_toggle(self) -> None:
        await self.coordinator.client.async_toggle_regulation()


class SolarBufferSchedulesSwitch(_ToggleSwitch):
    _veld = "schedules_enabled"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: SolarBufferCoordinator) -> None:
        super().__init__(coordinator, "schedules")

    async def _async_toggle(self) -> None:
        await self.coordinator.client.async_toggle_schedules()


class SolarBufferLegionellaSwitch(_ToggleSwitch):
    _veld = "anti_legionella_enabled"
    _attr_icon = "mdi:water-boiler"

    def __init__(self, coordinator: SolarBufferCoordinator) -> None:
        super().__init__(coordinator, "anti_legionella")

    async def _async_toggle(self) -> None:
        await self.coordinator.client.async_toggle_anti_legionella()


class SolarBufferVacationSwitch(SolarBufferEntity, SwitchEntity):
    """Vakantiestand. Deze heeft wel een echte aan/uit, geen omschakelaar."""

    _attr_icon = "mdi:palm-tree"

    def __init__(self, coordinator: SolarBufferCoordinator) -> None:
        super().__init__(coordinator, "vacation")

    @property
    def is_on(self) -> bool:
        return bool((self.coordinator.data or {}).get("vacation_mode"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        huidig = bool((self.coordinator.data or {}).get("vacation_legionella"))
        await self.coordinator.client.async_set_vacation(True, huidig)
        await self.coordinator.async_refresh_soon()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.async_set_vacation(False)
        await self.coordinator.async_refresh_soon()


class SolarBufferDeviceSwitch(SolarBufferDeviceEntity, SwitchEntity):
    """Handmatig aan- of uitzetten van één SolarBuffer."""

    _attr_name = None  # draagt de naam van het apparaat zelf

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "device")
        # De basisklasse zet een vertaalsleutel, maar deze entiteit is de
        # hoofdentiteit van zijn apparaat en leent daar zijn naam van.
        self._attr_translation_key = None

    @property
    def is_on(self) -> bool:
        return bool(self._device.get("on"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        d = self._device
        return {
            "brightness": d.get("brightness"),
            "priority": d.get("priority"),
            "online": d.get("online"),
            "started": d.get("started"),
            "boost_until": d.get("boost_until"),
        }

    async def _async_toggle(self) -> None:
        await self.coordinator.client.async_toggle_device(self._ip)
        await self.coordinator.async_refresh_soon()

    async def async_turn_on(self, **kwargs: Any) -> None:
        if not self.is_on:
            await self._async_toggle()

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self.is_on:
            await self._async_toggle()
