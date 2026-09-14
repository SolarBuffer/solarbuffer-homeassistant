"""Instellen via de interface van Home Assistant."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
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

    _ontdekt_host: str = ""
    _ontdekt_port: int = DEFAULT_PORT

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = int(user_input.get(CONF_PORT) or DEFAULT_PORT)

            client = SolarBufferClient(
                async_get_clientsession(self.hass),
                host,
                port,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                await client.async_login()
                status = await client.async_get_status()
            except SolarBufferAuthError:
                errors["base"] = "invalid_auth"
            except SolarBufferError:
                errors["base"] = "cannot_connect"
            else:
                # Herken de hub aan zijn eigen vaste aanduiding, zodat een
                # nieuwe DHCP-lease hem niet in een tweede hub verandert.
                # Oudere hubs melden die nog niet; dan valt het terug op het
                # adres, zoals het hiervoor altijd ging.
                await self.async_set_unique_id(
                    status.get("hub_id") or f"{host}:{port}"
                )
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: host, CONF_PORT: port}
                )
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

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Een hub die zichzelf op het netwerk aankondigt.

        We vragen alleen nog om de inloggegevens; adres en poort komen uit de
        aankondiging. Staat de hub al ingesteld, dan werken we hooguit zijn
        adres bij, bijvoorbeeld na een nieuwe DHCP-lease.
        """
        host = discovery_info.host
        port = discovery_info.port or DEFAULT_PORT
        gevonden_id = (discovery_info.properties or {}).get("id")

        await self.async_set_unique_id(gevonden_id or f"{host}:{port}")
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: host, CONF_PORT: port}
        )

        self._ontdekt_host = host
        self._ontdekt_port = port
        self.context["title_placeholders"] = {"host": host}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            client = SolarBufferClient(
                async_get_clientsession(self.hass),
                self._ontdekt_host,
                self._ontdekt_port,
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
                    title=f"SolarBuffer ({self._ontdekt_host})",
                    data={
                        CONF_HOST: self._ontdekt_host,
                        CONF_PORT: self._ontdekt_port,
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            description_placeholders={"host": self._ontdekt_host},
            errors=errors,
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
