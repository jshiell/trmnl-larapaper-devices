"""LaraPaper binary sensor platform."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import LaraPaperConfigEntry, LaraPaperCoordinator
from .entity import LaraPaperEntity
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class LaraPaperBinarySensorEntityDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict], Any]


BINARY_SENSOR_DESCRIPTIONS: tuple[LaraPaperBinarySensorEntityDescription, ...] = (
    LaraPaperBinarySensorEntityDescription(
        key="sleep_mode",
        name="Sleep Mode",
        value_fn=lambda d: d["status"]["sleep_mode_enabled"],
    ),
)


class LaraPaperBinarySensor(LaraPaperEntity, BinarySensorEntity):
    entity_description: LaraPaperBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: LaraPaperCoordinator,
        device_id: int,
        description: LaraPaperBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator, device_id)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{device_id}_{description.key}"

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self._device_data)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LaraPaperConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        LaraPaperBinarySensor(coordinator, device_id, description)
        for device_id in coordinator.data
        for description in BINARY_SENSOR_DESCRIPTIONS
    )
