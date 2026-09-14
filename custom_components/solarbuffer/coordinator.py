"""Haalt periodiek de toestand op en deelt die met alle entiteiten."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SolarBufferAuthError, SolarBufferClient, SolarBufferError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SolarBufferCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Eén /status_json per interval, gedeeld door alle entiteiten.

    De hub geeft zijn hele toestand in één antwoord terug, dus er is geen reden
    om per entiteit te pollen. Bij een schakelactie vragen we meteen daarna een
    verse stand op, zodat de knop in Home Assistant niet even terugspringt.
    """

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, client: SolarBufferClient
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
            config_entry=entry,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_status()
        except SolarBufferAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except SolarBufferError as err:
            raise UpdateFailed(str(err)) from err

    # --- hulpjes waar de entiteiten op leunen ----------------------------

    @property
    def devices(self) -> list[dict[str, Any]]:
        """De SolarBuffers zelf."""
        return list((self.data or {}).get("devices") or [])

    @property
    def accessories(self) -> list[dict[str, Any]]:
        """Losse verbruikers en temperatuursensoren."""
        return list((self.data or {}).get("accessories") or [])

    def device_by_ip(self, ip: str) -> dict[str, Any] | None:
        return next((d for d in self.devices if d.get("ip") == ip), None)

    def accessory_by_id(self, acc_id: str) -> dict[str, Any] | None:
        return next((a for a in self.accessories if a.get("id") == acc_id), None)

    @property
    def has_zendure(self) -> bool:
        """Accubediening bestaat alleen bij een gekoppelde Zendure."""
        d = self.data or {}
        return bool(d.get("battery_enabled")) and d.get("battery_type") == "zendure"

    async def async_refresh_soon(self) -> None:
        """Na een schakelactie meteen de echte stand ophalen."""
        await self.async_request_refresh()
