"""Tests for LaraPaper config flow."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.larapaper.api import LaraPaperAuthError, LaraPaperApiError
from custom_components.larapaper.const import CONF_BEARER_TOKEN, CONF_SERVER_URL, DOMAIN

VALID_INPUT = {
    CONF_SERVER_URL: "http://server.local",
    CONF_BEARER_TOKEN: "mytoken",
}


@pytest.fixture(autouse=True)
def mock_client():
    with patch("custom_components.larapaper.config_flow.LaraPaperApiClient") as mock:
        instance = MagicMock()
        instance.get_devices = AsyncMock(return_value=[{"id": 8}])
        mock.return_value = instance
        yield mock


class TestUserFlow:
    async def test_shows_form(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_creates_entry_on_valid_input(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_SERVER_URL] == "http://server.local"
        assert result["data"][CONF_BEARER_TOKEN] == "mytoken"

    async def test_invalid_auth_shows_error(self, hass, mock_client):
        mock_client.return_value.get_devices.side_effect = LaraPaperAuthError

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        assert result["type"] == FlowResultType.FORM
        assert "invalid_auth" in result["errors"].values()

    async def test_cannot_connect_shows_error(self, hass, mock_client):
        mock_client.return_value.get_devices.side_effect = LaraPaperApiError

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_INPUT
        )
        assert result["type"] == FlowResultType.FORM
        assert "cannot_connect" in result["errors"].values()

    async def test_duplicate_aborts(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(result["flow_id"], VALID_INPUT)

        result2 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], VALID_INPUT
        )
        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "already_configured"


class TestValidationLogging:
    async def test_logs_auth_error(self, hass, mock_client, caplog):
        import logging
        mock_client.return_value.get_devices.side_effect = LaraPaperAuthError("bad token")

        with caplog.at_level(logging.WARNING, logger="custom_components.larapaper.config_flow"):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            await hass.config_entries.flow.async_configure(result["flow_id"], VALID_INPUT)

        assert any("auth" in r.message.lower() for r in caplog.records)

    async def test_logs_api_error(self, hass, mock_client, caplog):
        import logging
        mock_client.return_value.get_devices.side_effect = LaraPaperApiError("timeout")

        with caplog.at_level(logging.ERROR, logger="custom_components.larapaper.config_flow"):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            await hass.config_entries.flow.async_configure(result["flow_id"], VALID_INPUT)

        assert any("connect" in r.message.lower() for r in caplog.records)

    async def test_logs_unknown_error(self, hass, mock_client, caplog):
        import logging
        mock_client.return_value.get_devices.side_effect = RuntimeError("unexpected")

        with caplog.at_level(logging.ERROR, logger="custom_components.larapaper.config_flow"):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            await hass.config_entries.flow.async_configure(result["flow_id"], VALID_INPUT)

        assert any("unexpected" in r.message.lower() for r in caplog.records)


class TestReauthFlow:
    async def test_reauth_confirm_updates_token(self, hass, mock_client):
        entry_result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(entry_result["flow_id"], VALID_INPUT)
        await hass.async_block_till_done()

        entry = hass.config_entries.async_entries(DOMAIN)[0]

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_REAUTH, "entry_id": entry.entry_id},
            data=entry.data,
        )
        assert result["step_id"] == "reauth_confirm"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_BEARER_TOKEN: "newtoken"}
        )
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.data[CONF_BEARER_TOKEN] == "newtoken"
