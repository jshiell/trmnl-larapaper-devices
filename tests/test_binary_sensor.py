"""Tests for LaraPaper binary sensor entities."""
import pytest
from unittest.mock import MagicMock

from custom_components.larapaper.binary_sensor import LaraPaperBinarySensor, BINARY_SENSOR_DESCRIPTIONS
from custom_components.larapaper.coordinator import LaraPaperCoordinator


DEVICE = {"id": 8, "name": "My TRMNL", "mac_address": "AA:BB:CC:DD:EE:FF"}
STATUS = {"sleep_mode_enabled": True}
COORDINATOR_DATA = {8: {"device": DEVICE, "status": STATUS}}


@pytest.fixture
def coordinator(hass):
    coord = MagicMock(spec=LaraPaperCoordinator)
    coord.data = COORDINATOR_DATA
    coord.hass = hass
    return coord


class TestSleepModeBinarySensor:
    def test_is_on_when_sleep_enabled(self, coordinator):
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "sleep_mode")
        sensor = LaraPaperBinarySensor(coordinator, 8, desc)
        assert sensor.is_on is True

    def test_is_off_when_sleep_disabled(self, coordinator):
        coordinator.data = {8: {"device": DEVICE, "status": {"sleep_mode_enabled": False}}}
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "sleep_mode")
        sensor = LaraPaperBinarySensor(coordinator, 8, desc)
        assert sensor.is_on is False

    def test_unique_id(self, coordinator):
        desc = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "sleep_mode")
        sensor = LaraPaperBinarySensor(coordinator, 8, desc)
        assert sensor.unique_id == "larapaper_8_sleep_mode"
