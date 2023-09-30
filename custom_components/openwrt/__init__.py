"""The openwrt integration."""
from __future__ import annotations
from async_timeout import timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, Config
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .data_fetcher import DataFetcher
from .const import (
    DOMAIN,
    CONF_USERNAME,
    CONF_PASSWD,
    CONF_HOST,
    CONF_UPDATE_INTERVAL,
    COORDINATOR,
    UNDO_UPDATE_LISTENER,
)
from homeassistant.exceptions import ConfigEntryNotReady

import time
import datetime
import logging
import asyncio


_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.SWITCH,
]


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up configured openwrt."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up openwrt from a config entry."""
    host = entry.data[CONF_HOST]
    username = entry.data[CONF_USERNAME]
    passwd = entry.data[CONF_PASSWD]
    update_interval_seconds = entry.options.get(CONF_UPDATE_INTERVAL, 10)
    coordinator = OPENWRTDataUpdateCoordinator(hass, host, username, passwd, update_interval_seconds)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = entry.add_update_listener(update_listener)

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )

    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)


class OPENWRTDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching OPENWRT data."""

    def __init__(self, hass: HomeAssistant, host: str, username: str, passwd: str, update_interval_seconds: int) -> None:
        """Initialize."""
        update_interval = datetime.timedelta(seconds=update_interval_seconds)
        _LOGGER.debug("%s Data will be update every %s", host, update_interval)
        self._token = ""
        self._token_expire_time = 0
        self._allow_login = True
        self._sw_version = "1.0"
        self._device_name = "OpenWrt"
        self._model = "OpenWrt Router"

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

        self._fetcher = DataFetcher(hass, host, username, passwd)
        self.host = host

    async def get_access_token(self):
        if time.time() < self._token_expire_time:
            return self._token
        else:
            if self._allow_login == True:
                self._token = await self._fetcher.login_openwrt()
                self._token = self._token[0]
                if self._token == 403:
                    self._allow_login = False
                self._token_expire_time = time.time() + 60*60*2
                return self._token

    async def _async_update_data(self):
        """Update data via DataFetcher."""
        _LOGGER.debug("token_expire_time=%s", self._token_expire_time)

        if self._allow_login == True:
            sysauth = await self.get_access_token()
            sysauth = str(sysauth)
            _LOGGER.debug("sysauth - " + sysauth)

            if self._sw_version == "1.0":
                openwrtinfodata = await self._fetcher.get_openwrt_version(sysauth)
                self._sw_version = openwrtinfodata["sw_version"]
                self._device_name = openwrtinfodata["device_name"]
                self._model = openwrtinfodata["model"]
                _LOGGER.info(f"Current Functioin is _async_update_data1, self._sw_version: %s" % self._sw_version)
                _LOGGER.info(f"Current Functioin is _async_update_data1, self._device_name: %s" % self._device_name)
                _LOGGER.info(f"Current Functioin is _async_update_data1, self._sw_version: %s" % self._model)
            try:
                async with timeout(10):
                    data = await self._fetcher.get_data(sysauth)
                    _LOGGER.info(f"Current Functioin is _async_update_data1, data: %s" % data)
                    if data == 401:
                        self._token_expire_time = 0
                        return
                    if not data:
                        _LOGGER.error("failed in getting data")
                        raise UpdateFailed("failed in getting data")
                    data["sw_version"] = self._sw_version
                    data["device_name"] = self._device_name
                    data["model"] = self._model
                    _LOGGER.info(f"Current Functioin is _async_update_data2, self._sw_version: %s" % self._sw_version)
                    _LOGGER.info(f"Current Functioin is _async_update_data2, self._device_name: %s" % self._device_name)
                    _LOGGER.info(f"Current Functioin is _async_update_data2, self._sw_version: %s" % self._model)
                    return data
            except Exception as error:
                raise UpdateFailed(error) from error
