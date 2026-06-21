"""Tests for LaraPaperApiClient."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientConnectionError, ClientResponseError, RequestInfo
from yarl import URL

from custom_components.larapaper.api import (
    LaraPaperApiClient,
    LaraPaperAuthError,
    LaraPaperApiError,
)


@pytest.fixture
def mock_session():
    session = MagicMock()
    return session


def make_response(status, json_data=None, raise_for_status=None):
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data or {})
    if raise_for_status:
        resp.raise_for_status = MagicMock(side_effect=raise_for_status)
    else:
        resp.raise_for_status = MagicMock()
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


class TestGetDevices:
    async def test_returns_device_list(self, mock_session):
        devices = [{"id": 8, "name": "My TRMNL"}]
        resp = make_response(200, {"data": devices})
        mock_session.get = MagicMock(return_value=resp)

        client = LaraPaperApiClient("http://server", "token", mock_session)
        result = await client.get_devices()

        assert result == devices

    async def test_raises_auth_error_on_401(self, mock_session):
        req_info = RequestInfo(URL("http://server/api/devices"), "GET", {}, URL("http://server/api/devices"))
        err = ClientResponseError(req_info, (), status=401)
        resp = make_response(401, raise_for_status=err)
        mock_session.get = MagicMock(return_value=resp)

        client = LaraPaperApiClient("http://server", "token", mock_session)
        with pytest.raises(LaraPaperAuthError):
            await client.get_devices()

    async def test_raises_auth_error_on_403(self, mock_session):
        req_info = RequestInfo(URL("http://server/api/devices"), "GET", {}, URL("http://server/api/devices"))
        err = ClientResponseError(req_info, (), status=403)
        resp = make_response(403, raise_for_status=err)
        mock_session.get = MagicMock(return_value=resp)

        client = LaraPaperApiClient("http://server", "token", mock_session)
        with pytest.raises(LaraPaperAuthError):
            await client.get_devices()

    async def test_raises_api_error_on_500(self, mock_session):
        req_info = RequestInfo(URL("http://server/api/devices"), "GET", {}, URL("http://server/api/devices"))
        err = ClientResponseError(req_info, (), status=500)
        resp = make_response(500, raise_for_status=err)
        mock_session.get = MagicMock(return_value=resp)

        client = LaraPaperApiClient("http://server", "token", mock_session)
        with pytest.raises(LaraPaperApiError):
            await client.get_devices()

    async def test_raises_api_error_on_connection_error(self, mock_session):
        mock_session.get = MagicMock(side_effect=ClientConnectionError())

        client = LaraPaperApiClient("http://server", "token", mock_session)
        with pytest.raises(LaraPaperApiError):
            await client.get_devices()


class TestGetDeviceStatus:
    async def test_returns_status_dict(self, mock_session):
        status = {"id": 8, "battery_percent": 29}
        resp = make_response(200, status)
        mock_session.post = MagicMock(return_value=resp)

        client = LaraPaperApiClient("http://server", "token", mock_session)
        result = await client.get_device_status(8)

        assert result == status
        mock_session.post.assert_called_once()
        call_url = mock_session.post.call_args[0][0]
        assert "device_id=8" in call_url

    async def test_raises_auth_error_on_401(self, mock_session):
        req_info = RequestInfo(URL("http://server/api/display/status"), "POST", {}, URL("http://server/api/display/status"))
        err = ClientResponseError(req_info, (), status=401)
        resp = make_response(401, raise_for_status=err)
        mock_session.post = MagicMock(return_value=resp)

        client = LaraPaperApiClient("http://server", "token", mock_session)
        with pytest.raises(LaraPaperAuthError):
            await client.get_device_status(8)
