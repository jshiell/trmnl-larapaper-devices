"""LaraPaper image platform."""
from __future__ import annotations

from homeassistant.components.image import ImageEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import LaraPaperConfigEntry, LaraPaperCoordinator
from .entity import LaraPaperEntity
from .const import DOMAIN


class LaraPaperImage(LaraPaperEntity, ImageEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Current Screen"

    def __init__(self, coordinator: LaraPaperCoordinator, device_id: int) -> None:
        LaraPaperEntity.__init__(self, coordinator, device_id)
        ImageEntity.__init__(self, coordinator.hass)
        self._attr_unique_id = f"{DOMAIN}_{device_id}_current_screen"
        self._last_url: str | None = None

    @property
    def image_url(self) -> str | None:
        return self._device_data["status"].get("current_screen_image")

    @callback
    def _handle_coordinator_update(self) -> None:
        current_url = self._device_data["status"].get("current_screen_image")
        if current_url != self._last_url:
            self._last_url = current_url
            updated_at = self._device_data["status"].get("updated_at")
            self._attr_image_last_updated = (
                dt_util.parse_datetime(updated_at) if updated_at else dt_util.utcnow()
            )
        super()._handle_coordinator_update()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LaraPaperConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        LaraPaperImage(coordinator, device_id) for device_id in coordinator.data
    )
