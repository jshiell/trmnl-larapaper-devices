"""LaraPaper data update coordinator."""
import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import LaraPaperApiClient, LaraPaperApiError, LaraPaperAuthError
from .const import DEFAULT_POLL_INTERVAL, DOMAIN, MIN_POLL_INTERVAL

_LOGGER = logging.getLogger(__name__)

type LaraPaperConfigEntry = ConfigEntry["LaraPaperCoordinator"]


class LaraPaperCoordinator(DataUpdateCoordinator[dict[int, dict]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: LaraPaperApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )
        self._client = client

    async def _async_update_data(self) -> dict[int, dict]:
        try:
            devices = await self._client.get_devices()
            statuses = await asyncio.gather(
                *[self._client.get_device_status(d["id"]) for d in devices]
            )
        except LaraPaperAuthError as err:
            raise ConfigEntryAuthFailed from err
        except LaraPaperApiError as err:
            raise UpdateFailed from err

        intervals = [
            s["default_refresh_interval"]
            for s in statuses
            if s.get("default_refresh_interval")
        ]
        if intervals:
            self.update_interval = timedelta(seconds=max(min(intervals), MIN_POLL_INTERVAL))

        return {
            d["id"]: {"device": d, "status": s}
            for d, s in zip(devices, statuses)
        }
