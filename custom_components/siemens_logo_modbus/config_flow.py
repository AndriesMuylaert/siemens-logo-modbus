"""Config flow for Siemens Logo Modbus integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback

from .const import (
    DOMAIN,
    CONF_MODBUS_HOST, CONF_MODBUS_PORT, CONF_REFRESH_INTERVAL,
    CONF_INPUT_COUNT, CONF_OUTPUT_COUNT,
    CONF_M_COUNT, CONF_V_COUNT,
    CONF_AI_COUNT, CONF_AQ_COUNT, CONF_VW_COUNT, CONF_AM_COUNT,
    CONF_ENABLE_NQ, CONF_ENABLE_M_SELECTOR,
    DEFAULT_HOST, DEFAULT_PORT, DEFAULT_REFRESH_INTERVAL,
    DEFAULT_INPUT_COUNT, DEFAULT_OUTPUT_COUNT,
    DEFAULT_M_COUNT, DEFAULT_V_COUNT,
    DEFAULT_AI_COUNT, DEFAULT_AQ_COUNT, DEFAULT_VW_COUNT, DEFAULT_AM_COUNT,
    DEFAULT_ENABLE_NQ, DEFAULT_ENABLE_M_SELECTOR,
    MIN_REFRESH_INTERVAL, MAX_REFRESH_INTERVAL,
    I_MAX_COUNT, Q_MAX_COUNT, M_MAX_COUNT, V_MAX_COUNT,
    AI_MAX_COUNT, AQ_MAX_COUNT, VW_MAX_COUNT, AM_MAX_COUNT,
)

_LOGGER = logging.getLogger(__name__)


def _build_schema(defaults: dict) -> vol.Schema:
    def _int(key, default, mn, mx):
        return vol.Required(key, default=defaults.get(key, default)), \
               vol.All(vol.Coerce(int), vol.Range(min=mn, max=mx))

    return vol.Schema({
        # ── Connection ────────────────────────────────────────────────
        vol.Required(CONF_MODBUS_HOST,
            default=defaults.get(CONF_MODBUS_HOST, DEFAULT_HOST)): str,
        vol.Required(CONF_MODBUS_PORT,
            default=defaults.get(CONF_MODBUS_PORT, DEFAULT_PORT)):
            vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
        vol.Required(CONF_REFRESH_INTERVAL,
            default=defaults.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL)):
            vol.All(vol.Coerce(int), vol.Range(min=MIN_REFRESH_INTERVAL, max=MAX_REFRESH_INTERVAL)),

        # ── Digital I/O ───────────────────────────────────────────────
        vol.Required(CONF_INPUT_COUNT,
            default=defaults.get(CONF_INPUT_COUNT, DEFAULT_INPUT_COUNT)):
            vol.All(vol.Coerce(int), vol.Range(min=1, max=I_MAX_COUNT)),
        vol.Required(CONF_OUTPUT_COUNT,
            default=defaults.get(CONF_OUTPUT_COUNT, DEFAULT_OUTPUT_COUNT)):
            vol.All(vol.Coerce(int), vol.Range(min=1, max=Q_MAX_COUNT)),

        # ── Bit memories (0 = disabled) ───────────────────────────────
        vol.Required(CONF_M_COUNT,
            default=defaults.get(CONF_M_COUNT, DEFAULT_M_COUNT)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=M_MAX_COUNT)),
        vol.Required(CONF_V_COUNT,
            default=defaults.get(CONF_V_COUNT, DEFAULT_V_COUNT)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=V_MAX_COUNT)),

        # ── Analog I/O (0 = disabled) ─────────────────────────────────
        vol.Required(CONF_AI_COUNT,
            default=defaults.get(CONF_AI_COUNT, DEFAULT_AI_COUNT)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=AI_MAX_COUNT)),
        vol.Required(CONF_AQ_COUNT,
            default=defaults.get(CONF_AQ_COUNT, DEFAULT_AQ_COUNT)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=AQ_MAX_COUNT)),

        # ── Analog memories (0 = disabled) ────────────────────────────
        vol.Required(CONF_VW_COUNT,
            default=defaults.get(CONF_VW_COUNT, DEFAULT_VW_COUNT)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=VW_MAX_COUNT)),
        vol.Required(CONF_AM_COUNT,
            default=defaults.get(CONF_AM_COUNT, DEFAULT_AM_COUNT)):
            vol.All(vol.Coerce(int), vol.Range(min=0, max=AM_MAX_COUNT)),

        # ── Special features ──────────────────────────────────────────
        vol.Required(CONF_ENABLE_NQ,
            default=defaults.get(CONF_ENABLE_NQ, DEFAULT_ENABLE_NQ)): bool,
        vol.Required(CONF_ENABLE_M_SELECTOR,
            default=defaults.get(CONF_ENABLE_M_SELECTOR, DEFAULT_ENABLE_M_SELECTOR)): bool,
    })


async def _async_validate_connection(hass: HomeAssistant, data: dict) -> dict[str, str]:
    errors: dict[str, str] = {}
    try:
        from pymodbus.client import AsyncModbusTcpClient  # noqa: PLC0415
        client = AsyncModbusTcpClient(host=data[CONF_MODBUS_HOST], port=data[CONF_MODBUS_PORT])
        try:
            if not await client.connect():
                errors["base"] = "cannot_connect"
        finally:
            client.close()
    except ImportError:
        _LOGGER.warning("pymodbus not available during config flow; skipping connection test")
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Unexpected error connecting to Logo")
        errors["base"] = "cannot_connect"
    return errors


class SiemensLogoModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await _async_validate_connection(self.hass, user_input)
            if not errors:
                title = f"Siemens Logo @ {user_input[CONF_MODBUS_HOST]}:{user_input[CONF_MODBUS_PORT]}"
                return self.async_create_entry(title=title, data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input or {}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> SiemensLogoOptionsFlow:
        return SiemensLogoOptionsFlow()


class SiemensLogoOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        current: dict[str, Any] = dict(self.config_entry.data)
        current.update(self.config_entry.options)
        if user_input is not None:
            errors = await _async_validate_connection(self.hass, user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(user_input or current),
            errors=errors,
        )
