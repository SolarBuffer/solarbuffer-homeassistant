"""Toont of er nieuwe hub-software klaarstaat en kan die installeren."""

from __future__ import annotations

from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SolarBufferConfigEntry
from .coordinator import SolarBufferCoordinator
from .entity import SolarBufferEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBufferConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    # Oudere hubs melden hier niets over; dan heeft de entiteit geen zin.
    if "update_available" not in (coordinator.data or {}):
        return
    async_add_entities([SolarBufferUpdate(coordinator)])


class SolarBufferUpdate(SolarBufferEntity, UpdateEntity):
    """Bijwerken van de hub-software.

    De hub vergelijkt bij het updaten commits en geen versienummers, dus dat is
    ook wat je hier ziet. Zolang beide gelijk zijn draait de hub de nieuwste
    code; lopen ze uiteen, dan staat er iets klaar.

    Installeren betekent dat de hub zijn code ophaalt en zichzelf herstart. De
    verbinding valt daarbij kort weg, wat Home Assistant vanzelf opvangt bij de
    volgende opvraging.
    """

    _attr_supported_features = UpdateEntityFeature.INSTALL
    _attr_title = "SolarBuffer Hub"

    def __init__(self, coordinator: SolarBufferCoordinator) -> None:
        super().__init__(coordinator, "hub_update")

    @property
    def installed_version(self) -> str | None:
        return (self.coordinator.data or {}).get("version_installed")

    @property
    def latest_version(self) -> str | None:
        data = self.coordinator.data or {}
        # Staat er niets klaar, dan is de nieuwste versie de draaiende versie.
        # Home Assistant toont dan geen update, en dat klopt.
        if not data.get("update_available"):
            return data.get("version_installed")
        return data.get("version_latest") or data.get("version_installed")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"status": (self.coordinator.data or {}).get("system_status")}

    async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        await self.coordinator.client.async_run_update()
