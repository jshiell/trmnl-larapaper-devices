"""Tests for LaraPaperCoordinator."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import timedelta

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.larapaper.api import LaraPaperAuthError, LaraPaperApiError
from custom_components.larapaper.coordinator import LaraPaperCoordinator
from custom_components.larapaper.const import MIN_POLL_INTERVAL


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


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get_devices = AsyncMock(return_value=[DEVICE])
    client.get_device_status = AsyncMock(return_value=STATUS)
    return client


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry"
    return entry


class TestCoordinatorDataShape:
    async def test_data_keyed_by_device_id(self, hass, mock_client, mock_entry):
        coordinator = LaraPaperCoordinator(hass, mock_entry, mock_client)
        data = await coordinator._async_update_data()

        assert 8 in data
        assert data[8]["device"] == DEVICE
        assert data[8]["status"] == STATUS

    async def test_fetches_status_for_each_device(self, hass, mock_client, mock_entry):
        second_device = {**DEVICE, "id": 9}
        mock_client.get_devices.return_value = [DEVICE, second_device]
        mock_client.get_device_status.return_value = STATUS

        coordinator = LaraPaperCoordinator(hass, mock_entry, mock_client)
        await coordinator._async_update_data()

        assert mock_client.get_device_status.call_count == 2


class TestPollIntervalUpdate:
    async def test_updates_interval_from_device_refresh_interval(self, hass, mock_client, mock_entry):
        coordinator = LaraPaperCoordinator(hass, mock_entry, mock_client)
        await coordinator._async_update_data()

        assert coordinator.update_interval == timedelta(seconds=900)

    async def test_enforces_minimum_poll_interval(self, hass, mock_client, mock_entry):
        mock_client.get_device_status.return_value = {**STATUS, "default_refresh_interval": 10}

        coordinator = LaraPaperCoordinator(hass, mock_entry, mock_client)
        await coordinator._async_update_data()

        assert coordinator.update_interval == timedelta(seconds=MIN_POLL_INTERVAL)

    async def test_skips_interval_update_when_no_devices(self, hass, mock_client, mock_entry):
        mock_client.get_devices.return_value = []

        coordinator = LaraPaperCoordinator(hass, mock_entry, mock_client)
        original_interval = coordinator.update_interval
        await coordinator._async_update_data()

        assert coordinator.update_interval == original_interval


class TestErrorHandling:
    async def test_auth_error_raises_config_entry_auth_failed(self, hass, mock_client, mock_entry):
        mock_client.get_devices.side_effect = LaraPaperAuthError

        coordinator = LaraPaperCoordinator(hass, mock_entry, mock_client)
        with pytest.raises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()

    async def test_api_error_raises_update_failed(self, hass, mock_client, mock_entry):
        mock_client.get_devices.side_effect = LaraPaperApiError

        coordinator = LaraPaperCoordinator(hass, mock_entry, mock_client)
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
