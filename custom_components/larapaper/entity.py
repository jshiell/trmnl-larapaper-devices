"""Base entity for LaraPaper integration."""
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import LaraPaperCoordinator


class LaraPaperEntity(CoordinatorEntity[LaraPaperCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: LaraPaperCoordinator, device_id: int) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def _device_data(self) -> dict:
        return self.coordinator.data[self._device_id]

    @property
    def device_info(self) -> DeviceInfo:
        d = self._device_data
        status = d["status"]
        device = d["device"]
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._device_id))},
            name=device["name"],
            manufacturer=MANUFACTURER,
            model="TRMNL",
            sw_version=status.get("last_firmware_version"),
            connections={(CONNECTION_NETWORK_MAC, device["mac_address"])},
        )
