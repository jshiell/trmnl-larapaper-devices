"""Tests for LaraPaper sensor entities."""
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from homeassistant.components.sensor import SensorDeviceClass

from custom_components.larapaper.sensor import LaraPaperSensor, SENSOR_DESCRIPTIONS
from custom_components.larapaper.coordinator import LaraPaperCoordinator


DEVICE = {"id": 8, "name": "My TRMNL", "mac_address": "AA:BB:CC:DD:EE:FF"}
STATUS = {
    "id": 8,
    "battery_percent": 29,
    "last_battery_voltage": 3.35,
    "last_rssi_level": -76,
    "wifi_strength": 2,
    "last_firmware_version": "1.7.4",
    "updated_at": "2024-01-01T12:00:00+00:00",
    "default_refresh_interval": 900,
    "sleep_mode_enabled": False,
    "current_screen_image": "http://example.com/img.png",
}
COORDINATOR_DATA = {8: {"device": DEVICE, "status": STATUS}}


@pytest.fixture
def coordinator(hass):
    coord = MagicMock(spec=LaraPaperCoordinator)
    coord.data = COORDINATOR_DATA
    coord.hass = hass
    return coord


def get_sensor(coordinator, key):
    desc = next(d for d in SENSOR_DESCRIPTIONS if d.key == key)
    return LaraPaperSensor(coordinator, 8, desc)


class TestSensorValues:
    def test_battery_percent(self, coordinator):
        sensor = get_sensor(coordinator, "battery_percent")
        assert sensor.native_value == 29

    def test_battery_voltage(self, coordinator):
        sensor = get_sensor(coordinator, "battery_voltage")
        assert sensor.native_value == 3.35

    def test_rssi(self, coordinator):
        sensor = get_sensor(coordinator, "rssi")
        assert sensor.native_value == -76

    def test_wifi_strength(self, coordinator):
        sensor = get_sensor(coordinator, "wifi_strength")
        assert sensor.native_value == 2

    def test_firmware_version(self, coordinator):
        sensor = get_sensor(coordinator, "firmware_version")
        assert sensor.native_value == "1.7.4"

    def test_updated_at_returns_aware_datetime(self, coordinator):
        sensor = get_sensor(coordinator, "updated_at")
        result = sensor.native_value
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_refresh_interval(self, coordinator):
        sensor = get_sensor(coordinator, "refresh_interval")
        assert sensor.native_value == 900


class TestUniqueIds:
    def test_unique_id_format(self, coordinator):
        sensor = get_sensor(coordinator, "battery_percent")
        assert sensor.unique_id == "larapaper_8_battery_percent"


class TestDeviceClasses:
    def test_battery_has_battery_device_class(self, coordinator):
        sensor = get_sensor(coordinator, "battery_percent")
        assert sensor.device_class == SensorDeviceClass.BATTERY

    def test_updated_at_has_timestamp_device_class(self, coordinator):
        sensor = get_sensor(coordinator, "updated_at")
        assert sensor.device_class == SensorDeviceClass.TIMESTAMP
