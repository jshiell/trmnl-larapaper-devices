# LaraPaper for Home Assistant

A Home Assistant integration for [LaraPaper](https://github.com/jamesshiell/larapaper) — a self-hosted server that manages [TRMNL](https://usetrmnl.com) e-ink display devices.

Each device on your LaraPaper server is exposed in Home Assistant as a device with sensors, a binary sensor, and an image entity.

## Entities

For each device:

| Entity | Type | Description |
|--------|------|-------------|
| Battery | Sensor | Battery level (%) |
| Battery Voltage | Sensor (diagnostic) | Raw battery voltage (V) |
| Signal Strength | Sensor (diagnostic) | Wi-Fi RSSI (dBm) |
| WiFi Bars | Sensor (diagnostic) | Wi-Fi signal bars |
| Firmware | Sensor (diagnostic) | Firmware version string |
| Last Updated | Sensor (diagnostic) | Timestamp of last device check-in |
| Refresh Interval | Sensor (diagnostic) | Configured poll interval (s) |
| Sleep Mode | Binary sensor | Whether sleep mode is active |
| Current Screen | Image (diagnostic) | The image currently displayed on the device |

## Requirements

- A running [LaraPaper](https://github.com/jamesshiell/larapaper) server
- A bearer token from your LaraPaper instance
- Home Assistant 2024.1 or later

## Installation

### Via HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** → click the three-dot menu → **Custom repositories**.
3. Add `https://github.com/jamesshiell/trmnl-larapaper-devices` with category **Integration**.
4. Search for **LaraPaper** in HACS and install it.
5. Restart Home Assistant.

### Manual

1. Download or clone this repository.
2. Copy the `custom_components/larapaper` directory into your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **LaraPaper**.
3. Enter your LaraPaper server URL (e.g. `https://larapaper.example.com`) and bearer token.

The integration polls each device at the interval configured on the LaraPaper server (defaulting to 15 minutes). If the bearer token is revoked, Home Assistant will prompt you to re-authenticate without removing the integration.
