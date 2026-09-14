"""De SolarBuffer-integratie voor Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolarBufferAuthError, SolarBufferClient, SolarBufferError
from .coordinator import SolarBufferCoordinator

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.NUMBER,
]

type SolarBufferConfigEntry = ConfigEntry[SolarBufferCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SolarBufferConfigEntry) -> bool:
    """Zet de verbinding op en laad de platforms."""
    client = SolarBufferClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    try:
        await client.async_login()
    except SolarBufferAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except SolarBufferError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = SolarBufferCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SolarBufferConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: SolarBufferConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
