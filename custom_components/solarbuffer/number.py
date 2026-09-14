"""Invulvelden: handmatige stand per SolarBuffer en het accuvermogen."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode, RestoreNumber
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SolarBufferConfigEntry
from .const import DOMAIN, MAX_MANUAL_POWER_W, zichtbaar_naar_ruw
from .coordinator import SolarBufferCoordinator
from .entity import SolarBufferDeviceEntity, SolarBufferEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBufferConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data

    entiteiten: list[NumberEntity] = [
        SolarBufferDeviceSetpoint(coordinator, apparaat["ip"])
        for apparaat in coordinator.devices
        if apparaat.get("ip")
    ]
    if coordinator.has_zendure:
        entiteiten.append(SolarBufferManualPowerNumber(coordinator))
    async_add_entities(entiteiten)


class SolarBufferDeviceSetpoint(SolarBufferDeviceEntity, RestoreNumber):
    """Invulveld voor een handmatige stand van één SolarBuffer.

    Dit veld houdt bewust vast wat jij hebt ingevuld en volgt niet de stand van
    de hub. Zou het wel meelopen, dan verandert het elke paar seconden zodra de
    regeling aan het werk is, en loopt de geschiedenis in Home Assistant vol met
    waarden die niemand heeft ingesteld. De gemeten stand staat al in een eigen
    sensor; dit is een bediening, geen meting.

    Instellen kan alleen met de automatische besturing uit. Staat die aan, dan
    zou de hub de waarde binnen een paar seconden overschrijven, en dan doet het
    veld alsof er iets gebeurt terwijl er niets gebeurt.

    Nul betekent uitzetten. De hub begrenst een te lage of te hoge waarde zelf.
    """

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:tune-vertical"

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "device_setpoint")
        self._ingevuld: float | None = None

    async def async_added_to_hass(self) -> None:
        """Haalt terug wat er voor de herstart was ingevuld."""
        await super().async_added_to_hass()
        vorige = await self.async_get_last_number_data()
        if vorige is not None and vorige.native_value is not None:
            self._ingevuld = vorige.native_value

    @property
    def native_value(self) -> float | None:
        return self._ingevuld

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            # Zo is af te lezen of het veld op dit moment iets kan doen.
            "regulation_enabled": (self.coordinator.data or {}).get("enabled"),
        }

    async def async_set_native_value(self, value: float) -> None:
        if (self.coordinator.data or {}).get("enabled"):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="regulation_is_on",
            )
        await self.coordinator.client.async_set_device_brightness(
            self._ip, zichtbaar_naar_ruw(value)
        )
        self._ingevuld = value
        self.async_write_ha_state()


class SolarBufferManualPowerNumber(SolarBufferEntity, NumberEntity):
    """Vermogen voor de handmatige stand.

    De hub topt dit zelf af op de ingestelde maximale laad- of ontlaadwaarde
    van de accu, dus een ruimere bovengrens hier kan geen kwaad.
    """

    _attr_native_min_value = 0
    _attr_native_max_value = MAX_MANUAL_POWER_W
    _attr_native_step = 50
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: SolarBufferCoordinator) -> None:
        super().__init__(coordinator, "battery_manual_power")

    @property
    def native_value(self) -> float | None:
        waarde = (self.coordinator.data or {}).get("battery_manual_power")
        return float(waarde) if waarde is not None else None

    async def async_set_native_value(self, value: float) -> None:
        d = self.coordinator.data or {}
        await self.coordinator.client.async_set_battery_mode(
            d.get("battery_control_mode") or "manual",
            direction=d.get("battery_manual_direction"),
            power=int(value),
        )
        await self.coordinator.async_refresh_soon()
