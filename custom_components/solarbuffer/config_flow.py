"""Instellen via de interface van Home Assistant."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SolarBufferAuthError, SolarBufferClient, SolarBufferError
from .const import DEFAULT_HOST, DEFAULT_PORT, DOMAIN

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class SolarBufferConfigFlow(ConfigFlow, domain=DOMAIN):
    """Vraagt om adres en inloggegevens en controleert of ze werken."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = int(user_input.get(CONF_PORT) or DEFAULT_PORT)

            # Eén hub per adres, anders krijg je dubbele entiteiten.
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            client = SolarBufferClient(
                async_get_clientsession(self.hass),
                host,
                port,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                await client.async_login()
                await client.async_get_status()
            except SolarBufferAuthError:
                errors["base"] = "invalid_auth"
            except SolarBufferError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"SolarBuffer ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """De hub verloor zijn tokens, of het wachtwoord is gewijzigd."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            client = SolarBufferClient(
                async_get_clientsession(self.hass),
                entry.data[CONF_HOST],
                entry.data[CONF_PORT],
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                await client.async_login()
            except SolarBufferAuthError:
                errors["base"] = "invalid_auth"
            except SolarBufferError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates=dict(user_input)
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=errors,
        )
