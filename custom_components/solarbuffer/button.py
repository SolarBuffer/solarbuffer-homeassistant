"""Knoppen: boost per SolarBuffer."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    async_add_entities(
        SolarBufferBoostButton(coordinator, apparaat["ip"])
        for apparaat in coordinator.devices
        if apparaat.get("ip")
    )


class SolarBufferBoostButton(SolarBufferDeviceEntity, ButtonEntity):
    """Zet de boiler tijdelijk op vol vermogen.

    De hub gebruikt hiervoor een omschakel-endpoint: nogmaals indrukken breekt
    een lopende boost af. De resterende tijd staat als attribuut op de
    schakelaar van hetzelfde apparaat.
    """

    _attr_icon = "mdi:flash"

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "boost")

    async def async_press(self) -> None:
        await self.coordinator.client.async_boost_device(self._ip)
        await self.coordinator.async_refresh_soon()
