"""Switch entities – Q outputs, M memory coils, V flag bits, NQ virtual outputs."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, COORDINATOR,
    CONF_OUTPUT_COUNT, CONF_M_COUNT, CONF_V_COUNT, CONF_ENABLE_NQ,
    Q_MODBUS_START, M_MODBUS_START, V_MODBUS_START,
    NQ_COUNT,
)
from .coordinator import SiemensLogoCoordinator


def _device_info(entry_id: str) -> dict:
    return {
        "identifiers": {(DOMAIN, entry_id)},
        "name": "Siemens Logo",
        "manufacturer": "Siemens",
        "model": "Logo! 8.4",
    }


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SiemensLogoCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    cfg = dict(entry.data)
    cfg.update(entry.options)

    entities: list[SwitchEntity] = []

    # Q – Digital Outputs
    for idx in range(cfg[CONF_OUTPUT_COUNT]):
        entities.append(LogoCoilSwitch(
            coordinator, entry, "Q", idx, Q_MODBUS_START + idx))

    # M – Memory Coils
    for idx in range(cfg.get(CONF_M_COUNT, 0)):
        entities.append(LogoCoilSwitch(
            coordinator, entry, "M", idx, M_MODBUS_START + idx))

    # V – Flag Bits (named V<byte>.<bit>)
    for idx in range(cfg.get(CONF_V_COUNT, 0)):
        entities.append(LogoCoilSwitch(
            coordinator, entry, "V", idx, V_MODBUS_START + idx,
            name_override=f"V{idx // 8}.{idx % 8}"))

    # NQ – Virtual outputs derived from AQ1/AQ2 bit decomposition
    if cfg.get(CONF_ENABLE_NQ, False):
        for idx in range(NQ_COUNT):
            entities.append(LogoNQSwitch(coordinator, entry, idx))

    if entities:
        async_add_entities(entities)


class LogoCoilSwitch(CoordinatorEntity[SiemensLogoCoordinator], SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, addr_type, index, modbus_addr,
                 name_override: str | None = None):
        super().__init__(coordinator)
        self._addr_type   = addr_type
        self._index       = index
        self._modbus_addr = modbus_addr
        self._attr_unique_id   = f"{entry.entry_id}_{addr_type}_{index}"
        self._attr_name        = name_override or f"{addr_type}{index + 1}"
        self._attr_device_info = _device_info(entry.entry_id)

    @property
    def is_on(self) -> bool | None:
        bits: list[bool] = (self.coordinator.data or {}).get(self._addr_type, [])
        return bits[self._index] if self._index < len(bits) else None

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_coil(self._modbus_addr, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_coil(self._modbus_addr, False)


class LogoNQSwitch(CoordinatorEntity[SiemensLogoCoordinator], SwitchEntity):
    """Virtual output NQ1-NQ16: each bit of AQ1 (NQ1-8) or AQ2 (NQ9-16)."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, index: int):
        super().__init__(coordinator)
        self._index = index
        self._attr_unique_id   = f"{entry.entry_id}_NQ_{index + 1}"
        self._attr_name        = f"NQ{index + 1}"
        self._attr_device_info = _device_info(entry.entry_id)

    @property
    def is_on(self) -> bool | None:
        nq: list[bool] = (self.coordinator.data or {}).get("NQ", [])
        return nq[self._index] if self._index < len(nq) else None

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_write_nq(self._index, True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_write_nq(self._index, False)
