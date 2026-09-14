"""Gedeelde basis voor alle SolarBuffer-entiteiten."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolarBufferCoordinator


class SolarBufferEntity(CoordinatorEntity[SolarBufferCoordinator]):
    """Entiteit die bij de hub zelf hoort."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SolarBufferCoordinator, sleutel: str) -> None:
        super().__init__(coordinator)
        self._entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{self._entry_id}_{sleutel}"
        self._attr_translation_key = sleutel

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="SolarBuffer",
            manufacturer="SolarBuffer",
            model="Hub",
            configuration_url=self.coordinator.client.base_url,
        )


class SolarBufferDeviceEntity(CoordinatorEntity[SolarBufferCoordinator]):
    """Entiteit die bij één aangesloten SolarBuffer hoort.

    Het IP is de sleutel waarmee de hub zijn apparaten adresseert, dus daar
    hangen we het unieke id aan op. Wijzigt het IP door een nieuwe DHCP-lease,
    dan komt het apparaat als nieuw binnen; dat is een bekend nadeel van deze
    API en iets om later met het MAC-adres op te lossen.
    """

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SolarBufferCoordinator, ip: str, sleutel: str
    ) -> None:
        super().__init__(coordinator)
        self._ip = ip
        self._entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{self._entry_id}_{ip}_{sleutel}"
        self._attr_translation_key = sleutel

    @property
    def _device(self) -> dict[str, Any]:
        return self.coordinator.device_by_ip(self._ip) or {}

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.device_by_ip(self._ip) is not None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry_id}_{self._ip}")},
            name=self._device.get("name") or self._ip,
            manufacturer="SolarBuffer",
            model="SolarBuffer",
            via_device=(DOMAIN, self._entry_id),
            configuration_url=f"http://{self._ip}",
        )


class SolarBufferAccessoryEntity(CoordinatorEntity[SolarBufferCoordinator]):
    """Entiteit voor een losse verbruiker of temperatuursensor."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SolarBufferCoordinator, acc_id: str, sleutel: str
    ) -> None:
        super().__init__(coordinator)
        self._acc_id = acc_id
        self._entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{self._entry_id}_{acc_id}_{sleutel}"
        self._attr_translation_key = sleutel

    @property
    def _accessory(self) -> dict[str, Any]:
        return self.coordinator.accessory_by_id(self._acc_id) or {}

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.accessory_by_id(self._acc_id) is not None
        )

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry_id}_{self._acc_id}")},
            name=self._accessory.get("name") or self._acc_id,
            manufacturer="SolarBuffer",
            model="Accessoire",
            via_device=(DOMAIN, self._entry_id),
        )
