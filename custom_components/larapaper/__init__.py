"""LaraPaper Home Assistant integration."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LaraPaperApiClient
from .const import CONF_BEARER_TOKEN, CONF_SERVER_URL, PLATFORMS
from .coordinator import LaraPaperConfigEntry, LaraPaperCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: LaraPaperConfigEntry) -> bool:
    client = LaraPaperApiClient(
        entry.data[CONF_SERVER_URL],
        entry.data[CONF_BEARER_TOKEN],
        async_get_clientsession(hass),
    )
    coordinator = LaraPaperCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LaraPaperConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
