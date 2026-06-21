"""Tests for LaraPaper image entity."""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from custom_components.larapaper.image import LaraPaperImage
from custom_components.larapaper.coordinator import LaraPaperCoordinator


DEVICE = {"id": 8, "name": "My TRMNL", "mac_address": "AA:BB:CC:DD:EE:FF"}
STATUS = {
    "current_screen_image": "http://example.com/screen.png",
    "updated_at": "2024-01-01T12:00:00+00:00",
    "last_firmware_version": "1.7.4",
}
COORDINATOR_DATA = {8: {"device": DEVICE, "status": STATUS}}


@pytest.fixture
def coordinator(hass):
    coord = MagicMock(spec=LaraPaperCoordinator)
    coord.data = COORDINATOR_DATA
    coord.hass = hass
    return coord


class TestImageEntity:
    def test_unique_id(self, hass, coordinator):
        image = LaraPaperImage(coordinator, 8)
        image.hass = hass
        assert image.unique_id == "larapaper_8_current_screen"

    def test_image_url(self, hass, coordinator):
        image = LaraPaperImage(coordinator, 8)
        image.hass = hass
        assert image.image_url == "http://example.com/screen.png"

    def test_last_updated_bumped_when_image_changes(self, hass, coordinator):
        image = LaraPaperImage(coordinator, 8)
        image.hass = hass
        image.async_write_ha_state = MagicMock()
        image._handle_coordinator_update()
        first_updated = image._attr_image_last_updated

        coordinator.data = {
            8: {
                "device": DEVICE,
                "status": {
                    **STATUS,
                    "current_screen_image": "http://example.com/new.png",
                    "updated_at": "2024-01-02T12:00:00+00:00",
                },
            }
        }
        image._handle_coordinator_update()

        assert image._attr_image_last_updated != first_updated

    def test_last_updated_not_bumped_when_image_unchanged(self, hass, coordinator):
        image = LaraPaperImage(coordinator, 8)
        image.hass = hass
        image.async_write_ha_state = MagicMock()
        image._handle_coordinator_update()
        first_updated = image._attr_image_last_updated

        image._handle_coordinator_update()

        assert image._attr_image_last_updated == first_updated
