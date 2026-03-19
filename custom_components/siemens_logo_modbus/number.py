"""Number entities – AQ, VW, AM analog R/W words and M10-M14 decimal selector."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, COORDINATOR,
    CONF_AQ_COUNT, CONF_VW_COUNT, CONF_AM_COUNT, CONF_ENABLE_M_SELECTOR,
    AQ_MODBUS_START, VW_MODBUS_START, AM_MODBUS_START,
    M_SELECTOR_MIN, M_SELECTOR_MAX,
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

    entities: list[NumberEntity] = []

    for idx in range(cfg.get(CONF_AQ_COUNT, 0)):
        entities.append(LogoWordNumber(coordinator, entry, "AQ", idx, AQ_MODBUS_START + idx))

    for idx in range(cfg.get(CONF_VW_COUNT, 0)):
        entities.append(LogoWordNumber(coordinator, entry, "VW", idx, VW_MODBUS_START + idx))

    for idx in range(cfg.get(CONF_AM_COUNT, 0)):
        entities.append(LogoWordNumber(coordinator, entry, "AM", idx, AM_MODBUS_START + idx))

    if cfg.get(CONF_ENABLE_M_SELECTOR, False):
        entities.append(LogoMSelectorNumber(coordinator, entry))

    if entities:
        async_add_entities(entities)


class LogoWordNumber(CoordinatorEntity[SiemensLogoCoordinator], NumberEntity):
    _attr_has_entity_name    = True
    _attr_mode               = NumberMode.BOX
    _attr_native_min_value   = 0
    _attr_native_max_value   = 65535
    _attr_native_step        = 1

    def __init__(self, coordinator, entry, addr_type, index, modbus_addr):
        super().__init__(coordinator)
        self._addr_type   = addr_type
        self._index       = index
        self._modbus_addr = modbus_addr
        self._attr_unique_id   = f"{entry.entry_id}_{addr_type}_{index + 1}"
        self._attr_name        = f"{addr_type}{index + 1}"
        self._attr_device_info = _device_info(entry.entry_id)

    @property
    def native_value(self) -> float | None:
        words: list[int] = (self.coordinator.data or {}).get(self._addr_type, [])
        return float(words[self._index]) if self._index < len(words) else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_register(self._modbus_addr, int(value))


class LogoMSelectorNumber(CoordinatorEntity[SiemensLogoCoordinator], NumberEntity):
    """Decimal selector 0-31 that writes M10-M14 as individual coils.

    The value is automatically reset to 0 after 1 second, making it a
    one-shot trigger suitable for driving a slave Logo in the background.
    """
    _attr_has_entity_name  = True
    _attr_mode             = NumberMode.BOX
    _attr_native_min_value = float(M_SELECTOR_MIN)
    _attr_native_max_value = float(M_SELECTOR_MAX)
    _attr_native_step      = 1
    _attr_icon             = "mdi:code-braces"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id   = f"{entry.entry_id}_M_SELECTOR"
        self._attr_name        = "M10-M14 Selector"
        self._attr_device_info = _device_info(entry.entry_id)

    @property
    def native_value(self) -> float:
        val = (self.coordinator.data or {}).get("M_SELECTOR", 0)
        return float(val)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_m_selector(int(value))
