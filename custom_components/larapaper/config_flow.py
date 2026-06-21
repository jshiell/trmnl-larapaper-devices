"""Config flow for LaraPaper integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import LaraPaperApiClient, LaraPaperAuthError, LaraPaperApiError
from .const import CONF_BEARER_TOKEN, CONF_SERVER_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class LaraPaperConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            errors = await self._validate(user_input[CONF_SERVER_URL], user_input[CONF_BEARER_TOKEN])
            if not errors:
                await self.async_set_unique_id(user_input[CONF_SERVER_URL].rstrip("/"))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="LaraPaper", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_SERVER_URL): str,
                vol.Required(CONF_BEARER_TOKEN): str,
            }),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        reauth_entry = self._get_reauth_entry()

        if user_input is not None:
            errors = await self._validate(
                reauth_entry.data[CONF_SERVER_URL], user_input[CONF_BEARER_TOKEN]
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={CONF_BEARER_TOKEN: user_input[CONF_BEARER_TOKEN]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_BEARER_TOKEN): str}),
            errors=errors,
        )

    async def _validate(self, server_url: str, bearer_token: str) -> dict[str, str]:
        session = async_get_clientsession(self.hass)
        client = LaraPaperApiClient(server_url, bearer_token, session)
        try:
            await client.get_devices()
        except LaraPaperAuthError as err:
            _LOGGER.warning("Authentication failed for %s: %s", server_url, err)
            return {"base": "invalid_auth"}
        except LaraPaperApiError as err:
            _LOGGER.error("Cannot connect to %s: %s", server_url, err)
            return {"base": "cannot_connect"}
        except Exception as err:
            _LOGGER.exception("Unexpected error during validation for %s: %s", server_url, err)
            return {"base": "unknown"}
        return {}
