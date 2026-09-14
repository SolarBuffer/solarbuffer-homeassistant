"""Sensoren: netvermogen, zon, accu, gas, prijs en per apparaat."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SolarBufferConfigEntry
from .const import ruw_naar_zichtbaar
from .coordinator import SolarBufferCoordinator
from .entity import (
    SolarBufferAccessoryEntity,
    SolarBufferDeviceEntity,
    SolarBufferEntity,
)


@dataclass(frozen=True, kw_only=True)
class SolarBufferSensorDescription(SensorEntityDescription):
    """Sensorbeschrijving met een eigen uitleesfunctie."""

    waarde: Callable[[dict[str, Any]], Any]
    aanwezig: Callable[[dict[str, Any]], bool] = lambda _d: True


def _accu(data: dict[str, Any], veld: str) -> Any:
    accu = data.get("battery") or {}
    return accu.get(veld)


HUB_SENSOREN: tuple[SolarBufferSensorDescription, ...] = (
    SolarBufferSensorDescription(
        key="net_power",
        translation_key="net_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        waarde=lambda d: d.get("power"),
    ),
    SolarBufferSensorDescription(
        key="system_status",
        translation_key="system_status",
        waarde=lambda d: d.get("system_status"),
    ),
    SolarBufferSensorDescription(
        key="solar_power",
        translation_key="solar_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        waarde=lambda d: d.get("inverter_power"),
        aanwezig=lambda d: bool(d.get("inverter_enabled")),
    ),
    SolarBufferSensorDescription(
        key="gas_today",
        translation_key="gas_today",
        device_class=SensorDeviceClass.GAS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        waarde=lambda d: d.get("gas_today_m3"),
        aanwezig=lambda d: bool(d.get("gas_enabled")),
    ),
    SolarBufferSensorDescription(
        key="energy_price",
        translation_key="energy_price",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="ct/kWh",
        waarde=lambda d: d.get("current_price_ct"),
        aanwezig=lambda d: bool(d.get("dynamic_pricing_enabled")),
    ),
    SolarBufferSensorDescription(
        key="battery_soc",
        translation_key="battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        waarde=lambda d: _accu(d, "soc"),
        aanwezig=lambda d: bool(d.get("battery_enabled")),
    ),
    SolarBufferSensorDescription(
        key="battery_power",
        translation_key="battery_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        waarde=lambda d: _accu(d, "power_w"),
        aanwezig=lambda d: bool(d.get("battery_enabled")),
    ),
    SolarBufferSensorDescription(
        key="battery_charged_today",
        translation_key="battery_charged_today",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        waarde=lambda d: _accu(d, "charge_today_kwh"),
        aanwezig=lambda d: bool(d.get("battery_enabled")),
    ),
    SolarBufferSensorDescription(
        key="battery_discharged_today",
        translation_key="battery_discharged_today",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        waarde=lambda d: _accu(d, "discharge_today_kwh"),
        aanwezig=lambda d: bool(d.get("battery_enabled")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SolarBufferConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    data = coordinator.data or {}

    entiteiten: list[SensorEntity] = [
        SolarBufferHubSensor(coordinator, beschrijving)
        for beschrijving in HUB_SENSOREN
        if beschrijving.aanwezig(data)
    ]

    for apparaat in coordinator.devices:
        ip = apparaat.get("ip")
        if not ip:
            continue
        entiteiten.append(SolarBufferDeviceStatus(coordinator, ip))
        entiteiten.append(SolarBufferDevicePower(coordinator, ip))
        entiteiten.append(SolarBufferDeviceEnergy(coordinator, ip))
        entiteiten.append(SolarBufferDeviceBrightness(coordinator, ip))
        if apparaat.get("chip_temp") is not None:
            entiteiten.append(SolarBufferDeviceChipTemp(coordinator, ip))

    for acc in coordinator.accessories:
        acc_id = acc.get("id")
        if not acc_id:
            continue
        if acc.get("acc_type") == "temperature":
            entiteiten.append(SolarBufferAccessoryTemperature(coordinator, acc_id))
        else:
            entiteiten.append(SolarBufferAccessoryPower(coordinator, acc_id))
            entiteiten.append(SolarBufferAccessoryEnergy(coordinator, acc_id))

    async_add_entities(entiteiten)


class SolarBufferHubSensor(SolarBufferEntity, SensorEntity):
    """Een sensor die bij de hub zelf hoort."""

    entity_description: SolarBufferSensorDescription

    def __init__(
        self,
        coordinator: SolarBufferCoordinator,
        beschrijving: SolarBufferSensorDescription,
    ) -> None:
        super().__init__(coordinator, beschrijving.key)
        self.entity_description = beschrijving

    @property
    def native_value(self) -> Any:
        return self.entity_description.waarde(self.coordinator.data or {})


class SolarBufferDeviceStatus(SolarBufferDeviceEntity, SensorEntity):
    """De toestand van één SolarBuffer in één woord, zoals de hub die noemt."""

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "device_status")

    @property
    def native_value(self) -> Any:
        return self._device.get("status")


class SolarBufferDevicePower(SolarBufferDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "device_power")

    @property
    def native_value(self) -> Any:
        return self._device.get("power")


class SolarBufferDeviceEnergy(SolarBufferDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "device_energy_today")

    @property
    def native_value(self) -> Any:
        return self._device.get("energy_today_kwh")


class SolarBufferDeviceBrightness(SolarBufferDeviceEntity, SensorEntity):
    """De stand van de boiler, op dezelfde schaal als de webinterface toont.

    De hub rekent intern met een waarde tussen 30 en 100 en met decimalen, want
    dat is de uitkomst van de regelaar. Die decimalen bereiken de dimmer nooit,
    dus ze horen ook niet in een weergave thuis.
    """

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "device_brightness")

    @property
    def native_value(self) -> Any:
        if not self._device.get("on"):
            return 0
        return ruw_naar_zichtbaar(self._device.get("brightness"))


class SolarBufferDeviceChipTemp(SolarBufferDeviceEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: SolarBufferCoordinator, ip: str) -> None:
        super().__init__(coordinator, ip, "device_chip_temperature")

    @property
    def native_value(self) -> Any:
        return self._device.get("chip_temp")


class SolarBufferAccessoryPower(SolarBufferAccessoryEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator: SolarBufferCoordinator, acc_id: str) -> None:
        super().__init__(coordinator, acc_id, "accessory_power")

    @property
    def native_value(self) -> Any:
        return self._accessory.get("power")


class SolarBufferAccessoryEnergy(SolarBufferAccessoryEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: SolarBufferCoordinator, acc_id: str) -> None:
        super().__init__(coordinator, acc_id, "accessory_energy_today")

    @property
    def native_value(self) -> Any:
        return self._accessory.get("energy_today_kwh")


class SolarBufferAccessoryTemperature(SolarBufferAccessoryEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: SolarBufferCoordinator, acc_id: str) -> None:
        super().__init__(coordinator, acc_id, "accessory_temperature")

    @property
    def native_value(self) -> Any:
        return self._accessory.get("temperature")
