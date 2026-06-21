"""LaraPaper sensor platform."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import LaraPaperConfigEntry, LaraPaperCoordinator
from .entity import LaraPaperEntity
from .const import DOMAIN


def _parse_ts(value: str | None) -> datetime | None:
    dt = dt_util.parse_datetime(value) if value else None
    return dt if dt and dt.tzinfo else None


@dataclass(frozen=True, kw_only=True)
class LaraPaperSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any]


SENSOR_DESCRIPTIONS: tuple[LaraPaperSensorEntityDescription, ...] = (
    LaraPaperSensorEntityDescription(
        key="battery_percent",
        name="Battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda d: d["status"]["battery_percent"],
    ),
    LaraPaperSensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d["status"]["last_battery_voltage"],
    ),
    LaraPaperSensorEntityDescription(
        key="rssi",
        name="Signal Strength",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d["status"]["last_rssi_level"],
    ),
    LaraPaperSensorEntityDescription(
        key="wifi_strength",
        name="WiFi Bars",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d["status"]["wifi_strength"],
    ),
    LaraPaperSensorEntityDescription(
        key="firmware_version",
        name="Firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d["status"]["last_firmware_version"],
    ),
    LaraPaperSensorEntityDescription(
        key="updated_at",
        name="Last Updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _parse_ts(d["status"]["updated_at"]),
    ),
    LaraPaperSensorEntityDescription(
        key="refresh_interval",
        name="Refresh Interval",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d["status"]["default_refresh_interval"],
    ),
)


class LaraPaperSensor(LaraPaperEntity, SensorEntity):
    entity_description: LaraPaperSensorEntityDescription

    def __init__(
        self,
        coordinator: LaraPaperCoordinator,
        device_id: int,
        description: LaraPaperSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._device_data)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LaraPaperConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        LaraPaperSensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in SENSOR_DESCRIPTIONS
    )
