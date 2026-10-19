"""Binaire sensoren: de stand van de legionellabeveiliging per boiler."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SolarBufferConfigEntry
from .coordinator import SolarBufferCoordinator
from .entity import SolarBufferDeviceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBufferConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data

    entiteiten: list[BinarySensorEntity] = []
    for apparaat in coordinator.devices:
        ip = apparaat.get("ip")
        if not ip:
            continue
        # Deze velden bestaan op elke hub die legionellabeveiliging kent. Zijn ze
        # er niet, dan is het een oudere hub en maken we niets aan.
        if "legionella_active" in apparaat:
            entiteiten.append(SolarBufferLegionellaActive(coordinator, ip))
        if "legionella_required" in apparaat:
            entiteiten.append(SolarBufferLegionellaRequired(coordinator, ip))

    async_add_entities(entiteiten)


class SolarBufferLegionellaActive(SolarBufferDeviceEntity, BinarySensorEntity):
    """Aan zolang er een legionellaronde loopt.

    Tijdens zo'n ronde draait de boiler op vol vermogen en telt de zon niet mee,
    dus dit is het moment waarop er stroom van het net gebruikt kan worden. Met
    deze sensor kan iemand daar een melding aan hangen.
    """

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "legionella_active")

    @property
    def is_on(self) -> bool | None:
        waarde = self._device.get("legionella_active")
        return None if waarde is None else bool(waarde)


class SolarBufferLegionellaRequired(SolarBufferDeviceEntity, BinarySensorEntity):
    """Aan als een ronde nodig is maar nog wacht op zijn moment.

    Bij de stand Handmatig wacht de hub op een ingestelde trigger en bij Laag
    tarief op een goedkoop uur. In die tussentijd staat deze sensor aan.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "legionella_required")

    @property
    def is_on(self) -> bool | None:
        waarde = self._device.get("legionella_required")
        return None if waarde is None else bool(waarde)
