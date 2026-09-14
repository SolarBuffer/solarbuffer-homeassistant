"""Praten met de SolarBuffer-hub over zijn eigen REST-API."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import STATUS_PATH, TOKEN_PATH

_LOGGER = logging.getLogger(__name__)


class SolarBufferError(Exception):
    """Er ging iets mis in het verkeer met de hub."""


class SolarBufferAuthError(SolarBufferError):
    """Gebruikersnaam of wachtwoord klopt niet."""


class SolarBufferNotFound(SolarBufferError):
    """De hub kent dit endpoint niet, of het gevraagde apparaat bestaat niet."""


class SolarBufferClient:
    """Kleine client rond de endpoints die de hub al heeft.

    De hub accepteert op elk beveiligd endpoint een Bearer-token, dus zowel
    lezen als schakelen gaat via dezelfde weg. Tokens overleven geen herstart
    van de hub, daarom halen we bij een 401 eenmalig een nieuw token en doen we
    het verzoek opnieuw. Dat maakt een reboot van de hub onzichtbaar voor Home
    Assistant.
    """

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"
        self._username = username
        self._password = password
        self._token: str | None = None
        self._login_lock = asyncio.Lock()

    @property
    def base_url(self) -> str:
        return self._base

    async def async_login(self) -> None:
        """Haalt een nieuw token op. Gooit SolarBufferAuthError bij verkeerde gegevens."""
        async with self._login_lock:
            try:
                async with self._session.post(
                    f"{self._base}{TOKEN_PATH}",
                    json={"username": self._username, "password": self._password},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        raise SolarBufferAuthError("Gebruikersnaam of wachtwoord onjuist")
                    resp.raise_for_status()
                    data = await resp.json()
            except SolarBufferAuthError:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                raise SolarBufferError(f"Hub niet bereikbaar: {err}") from err

            token = data.get("token")
            if not token:
                raise SolarBufferError("Hub gaf geen token terug")
            self._token = token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        _opnieuw: bool = True,
    ) -> Any:
        if self._token is None:
            await self.async_login()

        try:
            async with self._session.request(
                method,
                f"{self._base}{path}",
                json=json_body,
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 401 and _opnieuw:
                    # Hub herstart, token weg. Eenmalig opnieuw inloggen.
                    self._token = None
                    return await self._request(
                        method, path, json_body=json_body, _opnieuw=False
                    )
                if resp.status == 401:
                    raise SolarBufferAuthError("Token geweigerd na opnieuw inloggen")
                if resp.status == 404:
                    raise SolarBufferNotFound(path)
                if resp.status == 403:
                    raise SolarBufferError(
                        f"Geen rechten voor {path}; deze actie vraagt een beheerdersaccount"
                    )
                resp.raise_for_status()
                if resp.content_type == "application/json":
                    return await resp.json()
                return await resp.text()
        except SolarBufferError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise SolarBufferError(f"Verzoek {path} mislukt: {err}") from err

    async def async_get_status(self) -> dict[str, Any]:
        """De volledige toestand van de hub in één keer."""
        data = await self._request("GET", STATUS_PATH)
        if not isinstance(data, dict):
            raise SolarBufferError("Onverwacht antwoord van /status_json")
        return data

    # --- schakelen -------------------------------------------------------

    async def _zet(self, pad: str, body: dict[str, Any], omschakelpad: str) -> None:
        """Zet een stand, en val terug op omschakelen bij een oudere hub.

        Nieuwere hubs hebben endpoints die een gevraagde stand aannemen. Kent de
        hub die nog niet, dan is er alleen een omschakelaar; die gebruiken we dan
        alsnog. De aanroeper heeft in dat geval al vastgesteld dat de stand
        werkelijk moet wijzigen.
        """
        try:
            await self._request("POST", pad, json_body=body)
        except SolarBufferNotFound:
            await self._request("GET", omschakelpad)

    async def async_set_regulation(self, aan: bool) -> None:
        await self._zet("/api/regulation", {"enabled": aan}, "/toggle_pid")

    async def async_set_schedules(self, aan: bool) -> None:
        await self._zet("/api/schedules", {"enabled": aan}, "/toggle_schedules")

    async def async_set_anti_legionella(self, aan: bool) -> None:
        await self._zet(
            "/api/anti_legionella", {"enabled": aan}, "/toggle_anti_legionella"
        )

    async def async_set_device_power(self, ip: str, aan: bool) -> None:
        await self._zet(
            f"/api/device/{ip}/power", {"on": aan}, f"/toggle_shelly/{ip}"
        )

    async def async_set_device_brightness(self, ip: str, stand: int) -> None:
        """Zet een SolarBuffer op een vaste stand.

        Blijft alleen staan met de automatische besturing uit; anders rekent de
        hub binnen een paar seconden een nieuwe stand uit.
        """
        await self._request(
            "POST", f"/set_brightness/{ip}", json_body={"brightness": stand}
        )

    async def async_run_update(self) -> None:
        await self._request("POST", "/api/update")

    async def async_boost_device(self, ip: str) -> None:
        await self._request("POST", f"/boost/{ip}")

    async def async_set_vacation(self, active: bool, legionella: bool = False) -> None:
        await self._request(
            "POST", "/vacation", json_body={"active": active, "legionella": legionella}
        )

    async def async_set_battery_mode(
        self, mode: str, direction: str | None = None, power: int | None = None
    ) -> None:
        body: dict[str, Any] = {"mode": mode}
        if direction is not None:
            body["direction"] = direction
        if power is not None:
            body["power"] = power
        await self._request("POST", "/api/battery/control_mode", json_body=body)
