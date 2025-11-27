"""OPENWRT Entities"""
import logging
from homeassistant.helpers.update_coordinator import CoordinatorEntity  # type: ignore
from homeassistant.core import HomeAssistant                            # type: ignore
from homeassistant.config_entries import ConfigEntry                    # type: ignore

from .const import COORDINATOR, DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add bjtoon_health_code entities from a config_entry."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    sensors = []
    for sensor in SENSOR_TYPES:
        sensors.append(OPENWRTSensor(sensor, coordinator))

    async_add_entities(sensors, False)


class OPENWRTSensor(CoordinatorEntity):
    """Define an bjtoon_health_code entity."""
    _attr_has_entity_name = True

    def __init__(self, kind, coordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self.kind = kind
        self.coordinator = coordinator

    @property
    def name(self):
        """Return the name."""
        return f"{SENSOR_TYPES[self.kind]['name']}"

    @property
    def unique_id(self):
        return f"{DOMAIN}_{self.kind}_{self.coordinator.host}"

    @property
    def device_info(self):
        """Return the device info."""
        # 确保 data 不为 None，使用空字典作为默认值
        data = self.coordinator.data or {}
        return {
            "identifiers": {(DOMAIN, self.coordinator.host)},
            "name": data.get("device_name", "OpenWrt Device"),  # 提供默认值
            "manufacturer": "OpenWrt",
            "model": data.get("model", "Unknown Model"),        # 提供默认值
            "sw_version": data.get("sw_version", "Unknown"),    # 提供默认值
        }

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def available(self):
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    @property
    def state(self):
        """Return the state."""
        # 检查coordinator.data是否为None，避免NoneType错误
        if self.coordinator.data is None:
            return None
        # 使用get方法安全获取数据，不存在时返回None
        return self.coordinator.data.get(self.kind)

    @property
    def icon(self):
        """Return the icon."""
        return SENSOR_TYPES[self.kind]["icon"]

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement."""
        if SENSOR_TYPES[self.kind].get("unit_of_measurement"):
            return SENSOR_TYPES[self.kind]["unit_of_measurement"]

    @property
    def device_class(self):
        """Return the unit_of_measurement."""
        if SENSOR_TYPES[self.kind].get("device_class"):
            return SENSOR_TYPES[self.kind]["device_class"]

    @property
    def state_attributes(self):
        attrs = {}
        data = self.coordinator.data  # 先获取数据引用
        # 检查数据是否为None，避免空指针错误
        if data is not None:
            # 安全获取属性数据
            if data.get(self.kind + "_attrs"):
                attrs = data[self.kind + "_attrs"]
            # 安全获取querytime（即使不存在也不会报错）
            if "querytime" in data:
                attrs["querytime"] = data["querytime"]
        return attrs

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Bjtoon health code entity."""
        # await self.coordinator.async_request_refresh()
