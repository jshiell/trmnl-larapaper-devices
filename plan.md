# LaraPaper Home Assistant Integration

## Context

Create a custom Home Assistant integration that polls a LaraPaper server for device information and exposes each device as a set of HA entities (sensors, a binary sensor, and an image). The integration is configured via UI config flow with a server URL and bearer token, and supports reauth when the token is rejected.

## API Contract (verified live)

**GET /api/devices** → `{ "data": [{ "id": 8, "name": "...", "friendly_id": "JFxEKV", "mac_address": "08:F9:E0:DF:E0:04", "battery_voltage": 3.35, "rssi": -76 }] }`

**POST /api/display/status?device_id=8** → `{ "id", "mac_address", "name", "friendly_id", "last_rssi_level", "last_battery_voltage", "last_firmware_version", "battery_percent", "wifi_strength", "current_screen_image", "default_refresh_interval", "sleep_mode_enabled", "sleep_mode_from", "sleep_mode_to", "special_function", "pause_until", "updated_at" }`

## Directory Structure

```
custom_components/
└── larapaper/
    ├── __init__.py
    ├── manifest.json
    ├── const.py
    ├── api.py
    ├── coordinator.py
    ├── entity.py
    ├── sensor.py
    ├── binary_sensor.py
    ├── image.py
    ├── config_flow.py
    ├── strings.json
    └── translations/
        └── en.json
```

## Implementation Plan

### Step 1 — `manifest.json`

```json
{
  "domain": "larapaper",
  "name": "LaraPaper",
  "codeowners": ["@jamesshiell"],
  "config_flow": true,
  "documentation": "https://github.com/jamesshiell/trmnl-larapaper-devices",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "version": "1.0.0"
}
```

- `codeowners` and `documentation` are **required** by `hassfest` — the
  integration warns/fails validation without them.
- `integration_type: "hub"` — the server fronts multiple devices.
- Key order matters: `domain`, `name` first, then the rest alphabetically.
- `aiohttp` is bundled with HA core, so `requirements` is omitted; `dependencies`
  is omitted rather than set to `[]`.

### Step 2 — `const.py`

```python
from homeassistant.const import Platform

DOMAIN = "larapaper"
CONF_SERVER_URL = "server_url"
CONF_BEARER_TOKEN = "bearer_token"
DEFAULT_POLL_INTERVAL = 900
MIN_POLL_INTERVAL = 60
MANUFACTURER = "LaraPaper"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.IMAGE]
```

### Step 3 — `api.py`

**`LaraPaperApiClient(server_url, bearer_token, session)`**

- `async get_devices() -> list[dict]` — GET `/api/devices`, returns `data` list
- `async get_device_status(device_id: int) -> dict` — POST `/api/display/status?device_id={id}`
- Raises `LaraPaperAuthError` on 401/403, `LaraPaperApiError` on other failures

### Step 4 — `coordinator.py`

Define a typed config-entry alias (used throughout the integration):
```python
type LaraPaperConfigEntry = ConfigEntry[LaraPaperCoordinator]
```

**`LaraPaperCoordinator(DataUpdateCoordinator[dict[int, dict]])`**

Pass `config_entry` to the constructor (recent HA logs a deprecation warning
without it):
```python
super().__init__(hass, _LOGGER, name=DOMAIN, config_entry=entry,
                 update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL))
```

`coordinator.data` shape:
```python
{
    8: {
        "device": { ...from GET /api/devices... },
        "status": { ...from POST /api/display/status... }
    }
}
```

`_async_update_data()`:
1. `get_devices()` to list all device IDs
2. `asyncio.gather(*[get_device_status(id) for each])` concurrently
3. Build result dict keyed by `device_id`
4. Update the poll interval from the devices' reported refresh intervals, with an
   empty-list guard and a floor so a misconfigured device can't hammer the server:
   ```python
   intervals = [s["default_refresh_interval"] for s in statuses if s.get("default_refresh_interval")]
   if intervals:
       self.update_interval = timedelta(seconds=max(min(intervals), MIN_POLL_INTERVAL))
   ```
5. Wrap `LaraPaperApiError` → `UpdateFailed`; `LaraPaperAuthError` →
   `ConfigEntryAuthFailed` (this automatically triggers the reauth flow — see Step 8)

### Step 5 — `entity.py`

**`LaraPaperEntity(CoordinatorEntity[LaraPaperCoordinator])`**

- `_attr_has_entity_name = True` — so entity names compose under the device name
  (HA standard); the description `name` becomes the suffix.
- `_device_data` property → `coordinator.data[device_id]`
- `device_info` property → `DeviceInfo(identifiers={(DOMAIN, str(device_id))}, name=..., manufacturer=MANUFACTURER, model="TRMNL", sw_version=status["last_firmware_version"], connections={(CONNECTION_NETWORK_MAC, mac_address)})`

### Step 6 — `sensor.py`

**`LaraPaperSensorEntityDescription`** — extends `SensorEntityDescription` with `value_fn: Callable[[dict], Any]`

**`LaraPaperSensor(LaraPaperEntity, SensorEntity)`**
- `unique_id` = `f"{DOMAIN}_{device_id}_{description.key}"`
- `native_value` = `description.value_fn(self._device_data)`

**Sensors per device** (all except `battery_percent` get
`entity_category = EntityCategory.DIAGNOSTIC`):

| key | name | value_fn | device_class | unit |
|-----|------|----------|--------------|------|
| `battery_percent` | Battery | `d["status"]["battery_percent"]` | BATTERY | % |
| `battery_voltage` | Battery Voltage | `d["status"]["last_battery_voltage"]` | VOLTAGE | V |
| `rssi` | Signal Strength | `d["status"]["last_rssi_level"]` | SIGNAL_STRENGTH | dBm |
| `wifi_strength` | WiFi Bars | `d["status"]["wifi_strength"]` | — | — |
| `firmware_version` | Firmware | `d["status"]["last_firmware_version"]` | — | — |
| `updated_at` | Last Updated | `_parse_ts(d["status"]["updated_at"])` | TIMESTAMP | — |
| `refresh_interval` | Refresh Interval | `d["status"]["default_refresh_interval"]` | DURATION | s |

`_parse_ts` helper: `TIMESTAMP` requires a **timezone-aware** `datetime`. Use
`dt_util.parse_datetime(value)` and return it only if it parsed and is tz-aware,
else `None`:
```python
def _parse_ts(value: str | None) -> datetime | None:
    dt = dt_util.parse_datetime(value) if value else None
    return dt if dt and dt.tzinfo else None
```

**`current_screen_image` is not a sensor.** It's a URL/path/data value that will
exceed the 255-character state limit (HA drops over-long states with a warning).
Expose it instead via the `image` platform — see Step 6b.

### Step 7 — `binary_sensor.py`

**`LaraPaperBinarySensor(LaraPaperEntity, BinarySensorEntity)`**
- `unique_id` = `f"{DOMAIN}_{device_id}_{description.key}"`
- `is_on` = `description.value_fn(self._device_data)`

Single descriptor: `sleep_mode` → `d["status"]["sleep_mode_enabled"]`

### Step 7b — `image.py`

**`LaraPaperImage(LaraPaperEntity, ImageEntity)`** — one per device, exposing
`current_screen_image` (keeps the long value off a capped sensor state).

- `unique_id` = `f"{DOMAIN}_{device_id}_current_screen"`
- `ImageEntity.__init__` needs `hass` passed through.
- `image_url` property → `d["status"]["current_screen_image"]` (absolute URL).
  Track the last URL and bump `self._attr_image_last_updated` (from
  `updated_at`) when it changes so HA re-fetches.
- `entity_category = EntityCategory.DIAGNOSTIC`.

### Step 8 — `config_flow.py`

**`LaraPaperConfigFlow(ConfigFlow, domain=DOMAIN)`**

`async_step_user`:
1. Present form: `server_url` (str), `bearer_token` (str)
2. On submit: create `LaraPaperApiClient` with `async_get_clientsession(hass)`
3. Call `get_devices()` to validate — catch `LaraPaperAuthError` →
   `"invalid_auth"`, `LaraPaperApiError` → `"cannot_connect"`, bare `Exception` →
   `"unknown"`
4. Set unique ID = normalised `server_url`; call `_abort_if_unique_id_already_configured()`
5. `async_create_entry(title="LaraPaper", data={CONF_SERVER_URL: ..., CONF_BEARER_TOKEN: ...})`

`async_step_reauth` / `async_step_reauth_confirm`: the coordinator's
`ConfigEntryAuthFailed` (Step 4) auto-starts a reauth flow, so the flow must
handle it:
1. `async_step_reauth(entry_data)` → forward to `async_step_reauth_confirm`
2. `async_step_reauth_confirm`: re-prompt for `bearer_token`, validate via
   `get_devices()` (same error mapping as above), then
   `async_update_reload_and_abort(self._get_reauth_entry(), data_updates={CONF_BEARER_TOKEN: ...})`

### Step 9 — `__init__.py`

Signature: `async_setup_entry(hass, entry: LaraPaperConfigEntry)`.

1. Build `LaraPaperApiClient` from `entry.data` with `async_get_clientsession(hass)`
2. Create `LaraPaperCoordinator(hass, entry, client)` and call
   `async_config_entry_first_refresh()`
3. Store on the typed entry: `entry.runtime_data = coordinator` (no
   `hass.data[DOMAIN]` — current HA runtime-data pattern)
4. Forward to platforms: `await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)`

`async_unload_entry`:
`return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)` —
nothing to pop, since `runtime_data` is cleared with the entry.

### Step 10 — `strings.json` + `translations/en.json`

**Custom components load config-flow UI text from `translations/en.json`, not
`strings.json`** — shipping only `strings.json` shows raw keys in the UI. Keep
`strings.json` as the canonical source and ship an identical `translations/en.json`.

Both contain config-flow `step` text for `user` and `reauth_confirm`, error keys
(`invalid_auth`, `cannot_connect`, `unknown`) and abort keys
(`already_configured`, `reauth_successful`).

## Unique ID Scheme

| Scope | Unique ID |
|-------|-----------|
| Config entry | normalised `server_url` |
| HA device | `(DOMAIN, str(device_id))` |
| Sensor entity | `f"larapaper_{device_id}_{key}"` e.g. `larapaper_8_battery_percent` |
| Binary sensor | `f"larapaper_{device_id}_{key}"` e.g. `larapaper_8_sleep_mode` |
| Image entity | `f"larapaper_{device_id}_current_screen"` e.g. `larapaper_8_current_screen` |

## TDD Approach

Write tests in the repo-root `tests/` directory (not `tests/components/larapaper/`,
which is for in-tree HA core development) using pytest +
`pytest-homeassistant-custom-component`. Add a `tests/conftest.py` that enables
the `enable_custom_integrations` fixture so the custom component loads.

1. `test_api.py` — mock `aiohttp` responses, verify `LaraPaperApiClient` methods and error raising
2. `test_coordinator.py` — verify data shape, poll-interval calculation (incl. floor + empty-list guard)
3. `test_config_flow.py` — verify user flow, error handling, duplicate prevention, **and reauth flow**
4. `test_sensor.py` / `test_binary_sensor.py` / `test_image.py` — verify entity values after coordinator update

## Verification

1. Copy `custom_components/larapaper/` into an HA instance's `custom_components/` directory
2. Restart HA; navigate to Settings → Integrations → Add Integration → "LaraPaper"
3. Enter `https://trmnl.local.infernus.org` and the bearer token
4. Confirm a device "James Shiell's TRMNL" appears with 7 sensors (battery %,
   voltage, RSSI, WiFi bars, firmware, last updated, refresh interval), 1 binary
   sensor (sleep mode), and 1 image entity (current screen)
5. Check values match the API response (e.g. battery = 29%, RSSI = -76 dBm, firmware = 1.7.4)
6. Confirm the reauth flow: invalidate/rotate the token, reload the entry, and
   verify HA prompts for a new token rather than silently failing
