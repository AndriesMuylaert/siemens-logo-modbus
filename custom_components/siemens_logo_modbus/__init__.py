"""Siemens Logo Modbus integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    COORDINATOR,
    CONF_MODBUS_HOST,
    CONF_MODBUS_PORT,
    CONF_REFRESH_INTERVAL,
    CONF_INPUT_COUNT,
    CONF_OUTPUT_COUNT,
    PLATFORM_BINARY_SENSOR,
    PLATFORM_SWITCH,
    PLATFORM_SENSOR,
    PLATFORM_NUMBER,
)
from .coordinator import SiemensLogoCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    PLATFORM_BINARY_SENSOR,
    PLATFORM_SWITCH,
    PLATFORM_SENSOR,
    PLATFORM_NUMBER,
]


def _effective_data(entry: ConfigEntry) -> dict:
    """Merge config data with options (options override data after re-config)."""
    data = dict(entry.data)
    data.update(entry.options)
    return data


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Siemens Logo Modbus from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = SiemensLogoCoordinator(hass, _effective_data(entry))
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {COORDINATOR: coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
