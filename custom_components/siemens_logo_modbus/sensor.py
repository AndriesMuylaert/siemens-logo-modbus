"""Sensor entities – read-only word addresses: AI (analog inputs)."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, COORDINATOR, CONF_AI_COUNT
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
    count = cfg.get(CONF_AI_COUNT, 0)
    if count == 0:
        return

    async_add_entities([
        LogoAnalogSensor(coordinator, entry, idx)
        for idx in range(count)
    ])


class LogoAnalogSensor(CoordinatorEntity[SiemensLogoCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, index):
        super().__init__(coordinator)
        self._index = index
        self._attr_unique_id   = f"{entry.entry_id}_AI_{index + 1}"
        self._attr_name        = f"AI{index + 1}"
        self._attr_device_info = _DEVICE_INFO(entry.entry_id)

    @property
    def native_value(self) -> int | None:
        words: list[int] = (self.coordinator.data or {}).get("AI", [])
        return words[self._index] if self._index < len(words) else None
