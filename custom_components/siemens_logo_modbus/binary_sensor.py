"""Binary sensors – read-only bit addresses: I (digital inputs)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, COORDINATOR, CONF_INPUT_COUNT
from .coordinator import SiemensLogoCoordinator

_DEVICE_INFO = lambda entry_id: {
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

    async_add_entities([
        LogoBinarySensor(coordinator, entry, idx)
        for idx in range(cfg[CONF_INPUT_COUNT])
    ])


class LogoBinarySensor(CoordinatorEntity[SiemensLogoCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, index):
        super().__init__(coordinator)
        self._index = index
        self._attr_unique_id   = f"{entry.entry_id}_I_{index + 1}"
        self._attr_name        = f"I{index + 1}"
        self._attr_device_info = _DEVICE_INFO(entry.entry_id)

    @property
    def is_on(self) -> bool | None:
        bits: list[bool] = (self.coordinator.data or {}).get("I", [])
        return bits[self._index] if self._index < len(bits) else None
