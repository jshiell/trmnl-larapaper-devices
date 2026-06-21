"""LaraPaper API client."""
from aiohttp import ClientError, ClientResponseError, ClientSession


class LaraPaperAuthError(Exception):
    """Raised on 401/403 responses."""


class LaraPaperApiError(Exception):
    """Raised on other API failures."""


class LaraPaperApiClient:
    def __init__(self, server_url: str, bearer_token: str, session: ClientSession) -> None:
        self._url = server_url.rstrip("/")
        self._headers = {"Authorization": f"Bearer {bearer_token}"}
        self._session = session

    async def get_devices(self) -> list[dict]:
        data = await self._request(
            lambda: self._session.get(
                f"{self._url}/api/devices", headers=self._headers
            )
        )
        return data["data"]

    async def get_device_status(self, device_id: int) -> dict:
        return await self._request(
            lambda: self._session.post(
                f"{self._url}/api/display/status?device_id={device_id}",
                headers=self._headers,
            )
        )

    async def _request(self, make_request) -> dict:
        try:
            async with make_request() as resp:
                resp.raise_for_status()
                return await resp.json()
        except ClientResponseError as err:
            if err.status in (401, 403):
                raise LaraPaperAuthError from err
            raise LaraPaperApiError from err
        except ClientError as err:
            raise LaraPaperApiError from err
