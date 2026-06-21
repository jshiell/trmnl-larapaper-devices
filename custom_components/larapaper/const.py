from homeassistant.const import Platform

DOMAIN = "larapaper"
CONF_SERVER_URL = "server_url"
CONF_BEARER_TOKEN = "bearer_token"
DEFAULT_POLL_INTERVAL = 900
MIN_POLL_INTERVAL = 60
MANUFACTURER = "LaraPaper"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.IMAGE]
