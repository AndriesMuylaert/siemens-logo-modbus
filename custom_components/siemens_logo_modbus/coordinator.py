"""DataUpdateCoordinator for Siemens Logo Modbus."""
from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import timedelta
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_MODBUS_HOST, CONF_MODBUS_PORT, CONF_REFRESH_INTERVAL,
    CONF_INPUT_COUNT, CONF_OUTPUT_COUNT,
    CONF_M_COUNT, CONF_V_COUNT,
    CONF_AI_COUNT, CONF_AQ_COUNT, CONF_VW_COUNT, CONF_AM_COUNT,
    CONF_ENABLE_NQ, CONF_ENABLE_M_SELECTOR,
    I_MODBUS_START, Q_MODBUS_START, M_MODBUS_START, V_MODBUS_START,
    AI_MODBUS_START, AQ_MODBUS_START, VW_MODBUS_START, AM_MODBUS_START,
    NQ_AQ1_MODBUS_ADDR, NQ_AQ2_MODBUS_ADDR,
    M_MODBUS_START as M_BASE,
    M_SELECTOR_START, M_SELECTOR_COUNT, M_SELECTOR_RESET_S,
)

_LOGGER = logging.getLogger(__name__)

LOGO_SLAVE  = 1
_COIL_CHUNK = 2000
_REG_CHUNK  = 125


def _slave_kwarg_name() -> str:
    try:
        from pymodbus.client.mixin import ModbusClientMixin  # noqa: PLC0415
        sig = inspect.signature(ModbusClientMixin.read_discrete_inputs)
        if "device_id" in sig.parameters:
            return "device_id"
        if "slave" in sig.parameters:
            return "slave"
    except Exception as exc:  # noqa: BLE001
        _LOGGER.warning("Could not detect pymodbus slave kwarg: %s", exc)
    return "slave"


_SLAVE_KW: str = _slave_kwarg_name()


class SiemensLogoCoordinator(DataUpdateCoordinator[dict[str, Any]]):

    def __init__(self, hass: HomeAssistant, entry_data: dict) -> None:
        self._host:              str  = entry_data[CONF_MODBUS_HOST]
        self._port:              int  = entry_data[CONF_MODBUS_PORT]
        self._input_count:       int  = entry_data[CONF_INPUT_COUNT]
        self._output_count:      int  = entry_data[CONF_OUTPUT_COUNT]
        self._m_count:           int  = entry_data.get(CONF_M_COUNT, 0)
        self._v_count:           int  = entry_data.get(CONF_V_COUNT, 0)
        self._ai_count:          int  = entry_data.get(CONF_AI_COUNT, 0)
        self._aq_count:          int  = entry_data.get(CONF_AQ_COUNT, 0)
        self._vw_count:          int  = entry_data.get(CONF_VW_COUNT, 0)
        self._am_count:          int  = entry_data.get(CONF_AM_COUNT, 0)
        self._enable_nq:         bool = entry_data.get(CONF_ENABLE_NQ, False)
        self._enable_m_selector: bool = entry_data.get(CONF_ENABLE_M_SELECTOR, False)

        super().__init__(
            hass, _LOGGER, name=DOMAIN,
            update_interval=timedelta(seconds=entry_data[CONF_REFRESH_INTERVAL]),
        )
        self._client = AsyncModbusTcpClient(host=self._host, port=self._port)
        self._m_selector_reset_task: asyncio.Task | None = None

    # ── Connection ────────────────────────────────────────────────────────────

    async def _ensure_connected(self) -> None:
        if not self._client.connected:
            if not await self._client.connect():
                raise UpdateFailed(f"Cannot connect to Logo at {self._host}:{self._port}")

    def _skw(self) -> dict:
        return {_SLAVE_KW: LOGO_SLAVE}

    # ── Read helpers ──────────────────────────────────────────────────────────

    async def _read_coils(self, start: int, count: int) -> list[bool]:
        r = await self._client.read_coils(address=start, count=count, **self._skw())
        if r.isError():
            raise ModbusException(f"read_coils error at {start}")
        return list(r.bits[:count])

    async def _read_discrete_inputs(self, start: int, count: int) -> list[bool]:
        r = await self._client.read_discrete_inputs(address=start, count=count, **self._skw())
        if r.isError():
            raise ModbusException(f"read_discrete_inputs error at {start}")
        return list(r.bits[:count])

    async def _read_input_registers(self, start: int, count: int) -> list[int]:
        r = await self._client.read_input_registers(address=start, count=count, **self._skw())
        if r.isError():
            raise ModbusException(f"read_input_registers error at {start}")
        return list(r.registers)

    async def _read_holding_registers(self, start: int, count: int) -> list[int]:
        r = await self._client.read_holding_registers(address=start, count=count, **self._skw())
        if r.isError():
            raise ModbusException(f"read_holding_registers error at {start}")
        return list(r.registers)

    async def _read_coils_chunked(self, start: int, count: int) -> list[bool]:
        bits: list[bool] = []
        offset = 0
        while offset < count:
            chunk = min(_COIL_CHUNK, count - offset)
            bits.extend(await self._read_coils(start + offset, chunk))
            offset += chunk
        return bits

    async def _read_holding_registers_chunked(self, start: int, count: int) -> list[int]:
        regs: list[int] = []
        offset = 0
        while offset < count:
            chunk = min(_REG_CHUNK, count - offset)
            regs.extend(await self._read_holding_registers(start + offset, chunk))
            offset += chunk
        return regs

    # ── Write helpers ─────────────────────────────────────────────────────────

    async def async_write_coil(self, address: int, value: bool) -> None:
        await self._ensure_connected()
        r = await self._client.write_coil(address=address, value=value, **self._skw())
        if r.isError():
            raise ModbusException(f"write_coil error at {address}")
        await self.async_request_refresh()

    async def async_write_register(self, address: int, value: int) -> None:
        await self._ensure_connected()
        r = await self._client.write_register(address=address, value=value, **self._skw())
        if r.isError():
            raise ModbusException(f"write_register error at {address}")
        await self.async_request_refresh()

    # ── NQ virtual output write ───────────────────────────────────────────────

    async def async_write_nq(self, nq_index: int, value: bool) -> None:
        """Write a single NQ bit (0-based index 0-15) by read-modify-write on AQ register."""
        await self._ensure_connected()
        if nq_index < 8:
            reg_addr = NQ_AQ1_MODBUS_ADDR
            bit_pos  = nq_index
        else:
            reg_addr = NQ_AQ2_MODBUS_ADDR
            bit_pos  = nq_index - 8

        regs = await self._read_holding_registers(reg_addr, 1)
        current = regs[0] if regs else 0
        if value:
            new_val = current | (1 << bit_pos)
        else:
            new_val = current & ~(1 << bit_pos)
        await self.async_write_register(reg_addr, new_val)

    # ── M10-M14 selector write ────────────────────────────────────────────────

    async def async_write_m_selector(self, decimal_value: int) -> None:
        """Write decimal_value (0-31) into M10-M14 as individual coils, then reset after 1 s."""
        await self._ensure_connected()
        for bit_pos in range(M_SELECTOR_COUNT):
            # M14=LSB, M10=MSB: coil offset 0→M10=bit4, offset 4→M14=bit0
            decimal_bit = (M_SELECTOR_COUNT - 1 - bit_pos)
            bit_val = bool((decimal_value >> decimal_bit) & 1)
            coil_addr = M_BASE + M_SELECTOR_START + bit_pos
            r = await self._client.write_coil(address=coil_addr, value=bit_val, **self._skw())
            if r.isError():
                raise ModbusException(f"write_coil error for M selector bit {bit_pos}")

        await self.async_request_refresh()

        # Cancel any pending reset task and schedule a new one
        if self._m_selector_reset_task and not self._m_selector_reset_task.done():
            self._m_selector_reset_task.cancel()

        self._m_selector_reset_task = self.hass.async_create_task(
            self._reset_m_selector_after_delay()
        )

    async def _reset_m_selector_after_delay(self) -> None:
        await asyncio.sleep(M_SELECTOR_RESET_S)
        try:
            await self._ensure_connected()
            for bit_pos in range(M_SELECTOR_COUNT):
                coil_addr = M_BASE + M_SELECTOR_START + bit_pos
                await self._client.write_coil(address=coil_addr, value=False, **self._skw())
            await self.async_request_refresh()
        except Exception as exc:  # noqa: BLE001
            _LOGGER.warning("M selector auto-reset failed: %s", exc)

    # ── Core poll ─────────────────────────────────────────────────────────────

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            await self._ensure_connected()
            data: dict[str, Any] = {}

            data["I"] = await self._read_discrete_inputs(I_MODBUS_START, self._input_count)
            data["Q"] = await self._read_coils(Q_MODBUS_START, self._output_count)

            data["M"]  = await self._read_coils(M_MODBUS_START, self._m_count) \
                         if self._m_count > 0 else []
            data["V"]  = await self._read_coils_chunked(V_MODBUS_START, self._v_count) \
                         if self._v_count > 0 else []
            data["AI"] = await self._read_input_registers(AI_MODBUS_START, self._ai_count) \
                         if self._ai_count > 0 else []
            data["AQ"] = await self._read_holding_registers(AQ_MODBUS_START, self._aq_count) \
                         if self._aq_count > 0 else []
            data["VW"] = await self._read_holding_registers_chunked(VW_MODBUS_START, self._vw_count) \
                         if self._vw_count > 0 else []
            data["AM"] = await self._read_holding_registers(AM_MODBUS_START, self._am_count) \
                         if self._am_count > 0 else []

            # NQ virtual outputs: derive from AQ1 and AQ2 register bits
            if self._enable_nq:
                aq_regs = await self._read_holding_registers(NQ_AQ1_MODBUS_ADDR, 2)
                aq1 = aq_regs[0] if len(aq_regs) > 0 else 0
                aq2 = aq_regs[1] if len(aq_regs) > 1 else 0
                nq_bits = []
                for bit in range(8):
                    nq_bits.append(bool((aq1 >> bit) & 1))
                for bit in range(8):
                    nq_bits.append(bool((aq2 >> bit) & 1))
                data["NQ"] = nq_bits

            # M selector: current decimal value of M10-M14
            if self._enable_m_selector and self._m_count >= (M_SELECTOR_START + M_SELECTOR_COUNT):
                m_bits = data.get("M", [])
                val = 0
                for bit_pos in range(M_SELECTOR_COUNT):
                    idx = M_SELECTOR_START + bit_pos
                    if idx < len(m_bits) and m_bits[idx]:
                        # M14=LSB, M10=MSB: coil offset 0→M10=bit4, offset 4→M14=bit0
                        decimal_bit = M_SELECTOR_COUNT - 1 - bit_pos
                        val |= (1 << decimal_bit)
                data["M_SELECTOR"] = val

            return data

        except ModbusException as exc:
            raise UpdateFailed(f"Modbus error: {exc}") from exc
        except UpdateFailed:
            raise
        except Exception as exc:
            raise UpdateFailed(f"Unexpected error: {exc}") from exc
