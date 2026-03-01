"""OPENWRT Entities"""
import logging
import time
import datetime
import json
import requests
from async_timeout import timeout
from aiohttp.client_exceptions import ClientConnectorError
import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import UpdateFailed

from .data_fetcher import DataFetcher

from .const import (
    COORDINATOR,
    DOMAIN,
    CONF_HOST,
    CONF_USERNAME,
    CONF_PASSWD,
    DO_URL,
    SWITCH_TYPES,
    UBUS_URL,
    REQUEST_TIMEOUT,
)


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities):
    """Add Switchentities from a config_entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    host = config_entry.data[CONF_HOST]
    username = config_entry.data[CONF_USERNAME]
    passwd = config_entry.data[CONF_PASSWD]
    
    # 等待协调器首次数据加载完成，避免初始化时数据为None
    await coordinator.async_config_entry_first_refresh()
    
    switchs = []

    if SWITCH_TYPES:
        _LOGGER.debug("setup switchs")
        for switch in SWITCH_TYPES:
            switchs.append(IKUAISwitch(hass, switch, coordinator, host, username, passwd))
            _LOGGER.debug(SWITCH_TYPES[switch]["name"])
        async_add_entities(switchs, False)


class IKUAISwitch(SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, kind: str, coordinator, host: str, username: str, passwd: str) -> None:
        """Initialize."""
        super().__init__()
        self.kind = kind
        self.coordinator = coordinator
        self._state = None
        coordinator_data = self.coordinator.data or {}  # 空值时赋值为空字典
        # _LOGGER.debug("coordinator_data %s", coordinator_data)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self.coordinator.host)},
            "name": coordinator_data.get("device_name", host),  
            "manufacturer": "OpenWrt",
            "model": self.coordinator.data["model"],
            "sw_version": self.coordinator.data["sw_version"],
        }
        self._attr_icon = SWITCH_TYPES[self.kind]['icon']
        self._attr_device_class = "switch"
        self._attr_entity_registry_enabled_default = True
        self._hass = hass
        self._token = ""
        self._token_expire_time = 0
        self._allow_login = True
        self._fetcher = DataFetcher(hass, host, username, passwd)
        self._host = host
        self._name = SWITCH_TYPES[self.kind]['name']
        self._turn_on_body = SWITCH_TYPES[self.kind]['turn_on_body']
        self._turn_off_body = SWITCH_TYPES[self.kind]['turn_off_body']
        self._change = True
        self._switchonoff = None
        
        self._isold = coordinator_data.get("openwrt_isold", False)

        self._token_ = ""
        self._session_ = ""
        self._sysauth_ = ""
        self._token_task_ = ""

        listswitch = self.coordinator.data.get("switch")

        for switchdata in listswitch:
            if switchdata["name"] == self._name:
                self._switchonoff = switchdata["onoff"]

        self._is_on = self._switchonoff == "on"
        self._state = "on" if self._is_on == True else "off"

    @property
    def name(self):
        """Return the name."""
        return f"{self._name}"

    @property
    def unique_id(self):
        return f"{DOMAIN}_switch_{self.coordinator.host}_{self._name}"

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def is_on(self):
        """Check if switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Turn switch on."""
        self._is_on = True
        self._change = False
        json_body = self._turn_on_body
        await self._switch(json_body)
        self._switchonoff = "on"

    async def async_turn_off(self, **kwargs):
        """Turn switch off."""
        self._is_on = False
        self._change = False
        json_body = self._turn_off_body
        await self._switch(json_body)
        self._switchonoff = "off"

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    async def async_update(self):
        """Update entity."""
        await self.coordinator.async_request_refresh()

        listswitch = self.coordinator.data.get("switch")

        for switchdata in listswitch:
            if switchdata["name"] == self._name:
                self._switchonoff = switchdata["onoff"]

        self._is_on = self._switchonoff == "on"
        self._state = "on" if self._is_on == True else "off"
        self._change = True

    def requestpost_json(self, url, json_body):
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Cookie": "sysauth_http=" + self._sysauth_
        }
        responsedata = requests.post(url,  headers=header, json=json_body)
        if responsedata.status_code != 200:
            return responsedata.status_code
        json_text = responsedata.content.decode('utf-8')
        resdata = json.loads(json_text)
        return resdata

    def requestpost_token(self, url, data_body):
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Cookie": "sysauth_http=" + self._sysauth_,
            "Content-Length": str(len(data_body))
        }
        responsedata = requests.post(url, data=data_body, headers=header)
        if responsedata.status_code == 403:
            _LOGGER.error(f"Current function requestpost_token, error code %s" % str(responsedata.status_code))
            _LOGGER.error(f"Current function requestpost_token, url: %s" % url)
            _LOGGER.error(f"Current function requestpost_token, data_body: %s" % data_body)
            _LOGGER.error(f"Current function requestpost_token, header: %s" % header)
        if responsedata.status_code != 200:
            return responsedata.status_code
        json_text = responsedata.content.decode('utf-8')

        resdata = json.loads(json_text)
        self._token_task_ = resdata["token"]

        _LOGGER.info(type(resdata))
        _LOGGER.info(f"requestpost_token resdata : %s" % resdata)
        _LOGGER.info(f"requestpost_token self._token_ : %ss" % self._token_)
        return resdata

    def requestpost_confirm(self, url, data_body):
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Cookie": "sysauth_http=" + self._sysauth_,
            "Content-Length": str(len(data_body))
        }
        responsedata = requests.post(url, data=data_body, headers=header)
        if responsedata.status_code == 403:
            _LOGGER.error(url)
            _LOGGER.error(data_body)
            _LOGGER.error(header)
        if responsedata.status_code != 200:
            return responsedata.status_code
        responsedata = responsedata.content.decode('utf-8')

        if responsedata == "OK":
            return True
        return False

    async def get_access_token(self):
        if time.time() < self._token_expire_time:
            return self._token
        else:
            if self._allow_login == True:
                self._token = await self._fetcher.login_openwrt()
                
                self._sysauth_ = self._token[0]
                self._token_ = self._token[1]
                self._session_ = self._token[2]
                
                if self._sysauth_ == 403 or self._sysauth_ == 9999:
                    self._allow_login = False
                
                if self._token == 10001:
                    self._allow_login = False
                    
                self._token_expire_time = time.time() + 60*60*2
                return self._token
            else:
                return
            
            return False

    async def passwall_check(self):
        postJson = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": ["" + self._session_ + "", "uci", "get", {"config": "passwall", "section": "@global[0]", "option": "enabled"}]
        }
        
        url = self._host + UBUS_URL
        _LOGGER.debug(f"Current funtion passwall_check , _session_ : %s" % self._session_)
        _LOGGER.debug(f"Current funtion passwall_check , _token_ : %s" % self._token_)
        
        # _LOGGER.debug(f"Current funtion SWITCH_TYPES[isold] : %s" % SWITCH_TYPES["isold"])
        # _LOGGER.debug(f"Current funtion SWITCH_TYPES[openwrt_isold] : %s" % self.coordinator.data["openwrt_isold"])
        # _LOGGER.debug(f"Current funtion self.coordinator.data : %s" % self.coordinator.data)
        
        if self.coordinator.data["openwrt_isold"]:
            raise UpdateFailed("无法连接到服务器！！！")
        
        if not self._allow_login:
            _LOGGER.error("Current function passwall_check, _allow_login is False")
            return False

        try:
            async with timeout(REQUEST_TIMEOUT):
                resdata = await self._hass.async_add_executor_job(self.requestpost_json, url, postJson)
                
        except (ClientConnectorError) as error:
            raise UpdateFailed(error)
        
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching passwall_check data (timeout=%ds)", REQUEST_TIMEOUT)
            return False

        if resdata["result"][1]["value"] == "1":
            return "on"
        else:
            return "off"

    async def passwall_ischange(self):
        postJson = {"jsonrpc": "2.0", "id": 1, "method": "call", "params": ["" + self._session_ + "", "uci", "changes", {}]}

        url = self._host + UBUS_URL
        _LOGGER.debug(f"Current funtion passwall_ischange , _session_ : %s" % self._session_)
        _LOGGER.debug(f"Current funtion passwall_ischange , _token_ : %s" % self._token_)
        
        if not self._allow_login:
            _LOGGER.error("Current function passwall_ischange, _allow_login is False")
            return False

        try:
            async with timeout(REQUEST_TIMEOUT):
                resdata = await self._hass.async_add_executor_job(self.requestpost_json, url, postJson)
                
        except (ClientConnectorError) as error:
            raise UpdateFailed(error)
        
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching passwall_ischange data (timeout=%ds)", REQUEST_TIMEOUT)
            return False

        if resdata["result"][1]["changes"] == {}:
            return False
        else:
            return True

    async def passwall_action(self, action_body):
        postJson = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": ["" + self._session_ + "", "uci", "set", {"config": "passwall", "section": "@global[0]", "values": {"enabled": "" + str(action_body)+""}}]
        }
        
        if not self._allow_login:
            _LOGGER.error("Current function passwall_action, _allow_login is False")
            return False

        url = self._host + UBUS_URL
        _LOGGER.debug(f"Current funtion passwall_action , _session_ : %s" % self._session_)
        _LOGGER.debug(f"Current funtion passwall_action , _token_ : %s" % self._token_)

        try:
            async with timeout(REQUEST_TIMEOUT):
                resdata = await self._hass.async_add_executor_job(self.requestpost_json, url, postJson)
                
        except (ClientConnectorError) as error:
            raise UpdateFailed(error)
        
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching passwall_action data (timeout=%ds)", REQUEST_TIMEOUT)
            return False

        _LOGGER.debug("Requests remaining: %s", url)
        _LOGGER.debug(resdata)

        if resdata["result"][0] == 0:
            _LOGGER.info(True)
            return True

        _LOGGER.info(False)
        return False

    async def passwall_submit(self):
        postData = "sid=" + self._session_ + "&token=" + self._token_

        url = self._host + "/cgi-bin/luci/admin/uci/apply_rollback"
        _LOGGER.debug(f"Current funtion passwall_submit , _session_ : %s" % self._session_)
        _LOGGER.debug(f"Current funtion passwall_submit , _token_ : %s" % self._token_)
        
        if not self._allow_login:
            _LOGGER.error("Current function passwall_submit, _allow_login is False")
            return False

        try:
            async with timeout(REQUEST_TIMEOUT):
                resdata = await self._hass.async_add_executor_job(self.requestpost_token, url, postData)
                
        except (ClientConnectorError) as error:
            raise UpdateFailed(error)
        
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching passwall_submit data (timeout=%ds)", REQUEST_TIMEOUT)
            return False

        if resdata == 403:
            return False

        if resdata["token"] != "":
            return True
        else:
            return False

    async def passwall_confrim(self):
        postData = "token=" + self._token_task_

        url = self._host + "/cgi-bin/luci/admin/uci/confirm"
        _LOGGER.debug(f"Current funtion passwall_confrim , _session_ : %s" % self._session_)
        _LOGGER.debug(f"Current funtion passwall_confrim , _token_ : %s" % self._token_)
        
        if not self._allow_login:
            _LOGGER.error("Current function passwall_confrim, _allow_login is False")
            return False

        try:
            async with timeout(REQUEST_TIMEOUT):
                resdata = await self._hass.async_add_executor_job(self.requestpost_confirm, url, postData)
                
        except (ClientConnectorError) as error:
            raise UpdateFailed(error)
        
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching passwall_confrim data (timeout=%ds)", REQUEST_TIMEOUT)
            return False

        if resdata == "OK":
            return True
        else:
            return False

    async def _switch(self, action_body):
        # if self._isold:
        #     raise UpdateFailed("无法连接到服务器")
        #     return
        
        if self._allow_login == True:
            await self.get_access_token()
            resdata = await self.passwall_check()
            _LOGGER.error(f"Currert Switch Status : %s" % resdata)
            
            retdata = await self.passwall_action(action_body)
            retdata = await self.passwall_ischange()
            
            if retdata:
                retdata = await self.passwall_submit()
                retdata = await self.passwall_confrim()

            _LOGGER.info("操作openwrt switch: %s, 结果: %s" % (action_body, retdata))

        return "OK"
