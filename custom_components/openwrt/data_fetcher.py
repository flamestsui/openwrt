"""
get openwrt info by token and sysauth
"""

import logging
import requests
import re
import asyncio
import json
import time
import datetime
from urllib import parse

from async_timeout import timeout                                           # type: ignore
from aiohttp.client_exceptions import ClientConnectorError
from homeassistant.helpers.aiohttp_client import async_create_clientsession # type: ignore
from homeassistant.core import HomeAssistant                                # type: ignore
from homeassistant.helpers.update_coordinator import UpdateFailed           # type: ignore

from .const import (
    DO_URL,
    UBUS_URL,
    SWITCH_TYPES,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class DataFetcher:
    """fetch the openwrt data"""

    def __init__(self, hass: HomeAssistant, host: str, username: str, passwd: str) -> None:
        self._host = host
        self._username = username
        self._passwd = passwd
        self._hass = hass
        self._session_client = async_create_clientsession(hass)
        self._data = {}
        self._token_ = ""
        self._session_ = ""

    def requestget_data(self, url, headerstr):
        responsedata = requests.get(url, headers=headerstr)  # pylint: disable=missing-timeout
        if responsedata.status_code != 200:
            return responsedata.status_code
        json_text = responsedata.content.decode('utf-8')
        resdata = json.loads(json_text)
        return resdata

    def requestpost_data(self, url, headerstr, datastr):
        responsedata = requests.post(url, headers=headerstr, data=datastr, verify=False)  # pylint: disable=missing-timeout
        if responsedata.status_code != 200:
            return responsedata.status_code
        json_text = responsedata.content.decode('utf-8')
        resdata = json.loads(json_text)
        return resdata

    def requestget_data_text(self, url, headerstr, datastr):
        responsedata = requests.post(url, headers=headerstr, verify=False)  # pylint: disable=missing-timeout
        if responsedata.status_code != 200:
            return responsedata.status_code
        resdata = responsedata.content.decode('utf-8')
        return resdata

    def requestpost_json(self, url, headerstr, json_body):
        responsedata = requests.post(url, headers=headerstr, json=json_body, verify=False)  # pylint: disable=missing-timeout
        if responsedata.status_code != 200:
            return responsedata.status_code
        json_text = responsedata.content.decode('utf-8')
        resdata = json.loads(json_text)
        return resdata

    def requestpost_json2(self, url, headerstr, json_body):
        responsedata = requests.post(url, headers=headerstr, data=json_body, verify=False)  # pylint: disable=missing-timeout
        if responsedata.status_code != 200:
            return responsedata.status_code
        json_text = responsedata.content.decode('utf-8')
        resdata = json.loads(json_text)
        return resdata

    def requestpost_cookies(self, url, headerstr, body):
        responsedata = requests.get(url, headers=headerstr, data=body, verify=False)  # pylint: disable=missing-timeout
        if responsedata.status_code == 403:
            return 403
        if responsedata.status_code != 200 and responsedata.status_code != 302:
            return responsedata.status_code

        result = responsedata.text
        res = re.compile(r'"sessionid": "(.*?)", "token": "(.*?)"')
        b = re.search(res, result)
        if b is None:
            return 9999
        else:
            self._token_ = b.group(2)
            self._session_ = b.group(1)
            _LOGGER.info("token:" + self._token_)
            _LOGGER.info("session:" + self._session_)
        return [self._session_, self._token_, self._session_]

    def seconds_to_dhms(self, seconds):
        if isinstance(seconds, str):
            return seconds.replace("\n%", "")
        days = seconds // (3600 * 24)
        hours = (seconds // 3600) % 24
        minutes = (seconds // 60) % 60
        seconds = seconds % 60
        if days > 0:
            return ("{0}天{1}小时{2}分钟".format(days, hours, minutes))
        if hours > 0:
            return ("{0}小时{1}分钟".format(hours, minutes))
        if minutes > 0:
            return ("{0}分钟{1}秒".format(minutes, seconds))
        return ("{0}秒".format(seconds))

    def hum_convert(self, value):
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        size = 1024.0
        for i in range(len(units)):  # pylint: disable=consider-using-enumerate
            if (value / size) < 1:
                return "%.2f%s" % (value, units[i])
            value = value / size

    def hum_convert_nounit(self, value):
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        size = 1024.0
        for i in range(len(units)):
            if (value / size) < 1:
                return "%.2f" % (value)
            value = value / size

    def speed_convert(self,  value):
        value = value/8
        units = ["B/s", "KB/s", "MB/s", "GB/s", "TB/s", "PB/s"]
        size = 1024.0
        for i in range(len(units)):  # pylint: disable=consider-using-enumerate
            if (value / size) < 1:
                return "%.2f%s" % (value, units[i])
            value = value / size

    def speed_convert_nounit(self,  value):
        units = ["B/s", "KB/s", "MB/s", "GB/s", "TB/s", "PB/s"]
        size = 1024.0
        for i in range(len(units)):
            if (value / size) < 1:
                return "%.2f" % (value)
            value = value / size

    async def login_openwrt(self):
        hass = self._hass
        host = self._host
        username = self._username
        passwd = self._passwd
        header = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        body = "luci_username=" + username + "&luci_password=" + passwd
        url = host + DO_URL
        _LOGGER.debug("Requests remaining: %s", url)
        try:
            async with timeout(REQUEST_TIMEOUT):
                resdata = await self._hass.async_add_executor_job(self.requestpost_cookies, url, header, body)
                _LOGGER.debug("login_openwrt resdata: %s", resdata)
                if resdata[0] == 403:
                    _LOGGER.debug("OPENWRT Username or Password is wrong，please reconfig!")
                    return resdata
                elif resdata[0] == 9999:
                    _LOGGER.debug("OPENWRT Step 2 is wrong!")
                    return resdata
                else:
                    _LOGGER.debug("login_successfully for OPENWRT")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching openwrt_login data (timeout=%ds)", REQUEST_TIMEOUT)
            resdata = [403, "", ""]
        except (ClientConnectorError) as error:
            _LOGGER.error("Error fetching openwrt_login data: %s", error)
            raise UpdateFailed(error)
        return resdata

    async def _check_openwrt_passwall(self, sysauth):
        header = {
            "Content-Type": "application/json",
            "Cookie": "sysauth_http=" + sysauth
        }
        postJson = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": ["" + self._session_ + "", "uci", "get", {"config": "passwall", "section": "@global[0]", "option": "enabled"}]
        }

        url = self._host + UBUS_URL

        try:
            async with timeout(REQUEST_TIMEOUT):
                resdata = await self._hass.async_add_executor_job(self.requestpost_json, url, header, postJson)
                _LOGGER.debug("check_openwrt_passwall resdata: %s", resdata)
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching _check_openwrt_passwall data (timeout=%ds)", REQUEST_TIMEOUT)
            return
        except (ClientConnectorError) as error:
            _LOGGER.error("Error fetching _check_openwrt_passwall data: %s", error)
            raise UpdateFailed(error)

        if resdata["result"][1]["value"] == "1":
            return True
        else:
            return False

    async def _get_openwrt_passwall(self, sysauth):
        self._data["openwrt_passwall_ip"] = ""
        self._data["openwrt_passwall_country"] = ""
        self._data["querytime"] = ""

        header = {
            "Cookie": "sysauth_http=" + sysauth
        }
        
        parameter = "admin/services/passwall/ip"

        url = self._host + DO_URL + parameter

        _LOGGER.debug("_get_openwrt_passwall Url = " + url)

        try:
            async with timeout(REQUEST_TIMEOUT):
                resdata = await self._hass.async_add_executor_job(self.requestget_data, url, header)
                _LOGGER.debug("_get_openwrt_passwall resdata = %s", resdata)
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching openwrt_passwall data (timeout=%ds)", REQUEST_TIMEOUT)
            return
        except (ClientConnectorError) as error:
            _LOGGER.error("Error fetching openwrt_passwall data: %s", error)
            raise UpdateFailed(error)

        if resdata == 401 or resdata == 403:
            self._data = 401
            return

        if resdata == 502:
            self._data = 502
            return

        if isinstance(resdata, dict):
            self._data["openwrt_passwall_ip"] = resdata.get("outboard")
            self._data["openwrt_passwall_country"] = resdata.get("outboardip").get("country")

            querytime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._data["querytime"] = querytime

        return

    async def _get_openwrt_status(self, sysauth):
        postData = '[{"jsonrpc": "2.0", "id": 1, "method": "call", "params": ["' + sysauth + '", "system", "info", {}]},' + \
            '{"jsonrpc": "2.0", "id": 2, "method": "call", "params": ["' + sysauth + '", "luci", "getCPUInfo", {}]},' + \
            '{"jsonrpc": "2.0", "id": 3, "method": "call", "params": ["' + sysauth + '", "luci", "getCPUUsage", {}]},' +\
            '{"jsonrpc": "2.0", "id": 4, "method": "call", "params": ["' + sysauth + '", "luci", "getTempInfo", {}]},' +\
            '{"jsonrpc": "2.0", "id": 5, "method": "call", "params": ["' + sysauth + '", "file", "read", {"path": "/proc/sys/net/netfilter/nf_conntrack_count"}]},' +\
            '{"jsonrpc": "2.0", "id": 6, "method": "call", "params": ["' + sysauth + '", "luci", "getOnlineUsers", {}]},' +\
            '{"jsonrpc": "2.0", "id": 7, "method": "call", "params": ["' + sysauth + '", "uci", "get", {"config": "network"}]},' +\
            '{"jsonrpc": "2.0", "id": 8, "method": "call", "params": ["' + sysauth+'", "network.interface", "dump",{}]},' +\
            '{"jsonrpc": "2.0", "id": 9, "method": "call", "params": ["' + sysauth+'", "luci-rpc", "getNetworkDevices",{}]},' +\
            '{"jsonrpc": "2.0", "id": 10, "method": "call", "params": ["' + sysauth + '", "luci", "getRealtimeStats",{"mode":"interface","device":"br-lan"}]}]'

        # postData = json.dumps(json.loads(postData), sort_keys=True, indent=4, separators=(',', ': '))
        postData = json.dumps(json.loads(postData))

        header = {
            "Content-Type": "application/json",
            "Content-Length": str(len(postData))
        }

        url = self._host + "/ubus/"

        try:
            async with timeout(REQUEST_TIMEOUT):
                resdatas = await self._hass.async_add_executor_job(self.requestpost_json2, url, header, postData)
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching openwrt_status data (timeout=%ds)", REQUEST_TIMEOUT)
            return
        except (ClientConnectorError) as error:
            _LOGGER.error("Error fetching openwrt_status data: %s", error)
            raise UpdateFailed(error)

        _LOGGER.debug("Requests remaining: %s", url)

        if resdatas == 401 or resdatas == 403:
            self._data = 401
            _LOGGER.debug("_get_openwrt_status requestpost_json2: %s", self._data)
            return

        self._data = {}

        for resdata in resdatas:
            if resdata["id"] == 1:
                # _LOGGER.debug("Id 1 - Start")
                self._data["openwrt_uptime"] = self.seconds_to_dhms(resdata["result"][1]["uptime"])

                self._data["openwrt_memory"] = round((1 - resdata["result"][1]["memory"]["available"]/resdata["result"][1]["memory"]["total"])*100, 0)
                self._data["openwrt_memory_attrs"] = resdata["result"][1]["memory"]

                self._data["openwrt_memory_total"] = resdata["result"][1]["memory"]["total"]
                self._data["openwrt_memory_free"] = resdata["result"][1]["memory"]["free"]
                self._data["openwrt_memory_shared"] = resdata["result"][1]["memory"]["shared"]
                self._data["openwrt_memory_buffered"] = resdata["result"][1]["memory"]["buffered"]
                self._data["openwrt_memory_available"] = resdata["result"][1]["memory"]["available"]
                self._data["openwrt_memory_cached"] = resdata["result"][1]["memory"]["cached"]

                self._data["openwrt_memory_total_gb"] = round(resdata["result"][1]["memory"]["total"]/1024/1024/1024, 3)
                self._data["openwrt_memory_free_gb"] = round(resdata["result"][1]["memory"]["free"]/1024/1024/1024, 3)
                self._data["openwrt_memory_shared_gb"] = round(resdata["result"][1]["memory"]["shared"]/1024/1024/1024, 3)
                self._data["openwrt_memory_buffered_gb"] = round(resdata["result"][1]["memory"]["buffered"]/1024/1024/1024, 3)
                self._data["openwrt_memory_available_gb"] = round(resdata["result"][1]["memory"]["available"]/1024/1024/1024, 3)
                self._data["openwrt_memory_cached_gb"] = round(resdata["result"][1]["memory"]["cached"]/1024/1024/1024, 3)
                # _LOGGER.debug("Id 1 - End")

            elif resdata["id"] == 2:
                # _LOGGER.debug("Id 2 - Start")
                cpuinfo = resdata["result"][1]["cpuinfo"]
                self._data["openwrt_cputemp"] = 0
                # _LOGGER.debug("Id 2 - End")

            elif resdata["id"] == 3:
                # _LOGGER.debug("Id 3 - Start")
                self._data["openwrt_cpu"] = resdata["result"][1]["cpuusage"].replace("%", "")
                # _LOGGER.debug("Id 3 - End")

            elif resdata["id"] == 5:
                # _LOGGER.debug("Id 5 - Start")
                self._data["openwrt_conncount"] = resdata["result"][1]["data"].replace("\n", "")
                # _LOGGER.debug("Id 5 - End")

            elif resdata["id"] == 6:
                # _LOGGER.debug("Id 6- Start")
                self._data["openwrt_user_online"] = resdata["result"][1]["onlineusers"]
                # _LOGGER.debug("Id 6 - End")

            elif resdata["id"] == 7:
                # _LOGGER.debug("Id 7 - Start")
                if resdata["result"][1].get("wan"):
                    self._data["openwrt_wan_ip"] = resdata["result"][1]["wan"]["ipaddr"]
                    self._data["openwrt_wan_ip_attrs"] = resdata["result"][1]["wan"]
                    try:
                        self._data["openwrt_wan_uptime"] = self.seconds_to_dhms(resdata["result"][1]["wan"]["uptime"])
                    except Exception:  # pylint: disable=broad-exception-caught
                        self._data["openwrt_wan_uptime"] = resdata["result"][1]["wan"]["uptime"]
                else:
                    self._data["openwrt_wan_ip"] = ""
                    self._data["openwrt_wan_uptime"] = ""

                if resdata["result"][1].get("wan6"):
                    self._data["openwrt_wan6_ip"] = resdata["result"][1]["wan6"]["ipaddr"]
                    self._data["openwrt_wan6_ip_attrs"] = resdata["result"][1]["wan6"]
                    try:
                        self._data["openwrt_wan6_uptime"] = self.seconds_to_dhms(resdata["result"][1]["wan6"]["uptime"])
                    except Exception:  # pylint: disable=broad-exception-caught
                        self._data["openwrt_wan6_uptime"] = resdata["result"][1]["wan6"]["uptime"]

                else:
                    self._data["openwrt_wan6_ip"] = ""
                    self._data["openwrt_wan6_uptime"] = ""
                # _LOGGER.debug("Id 7 - End")

            elif resdata["id"] == 8:
                # _LOGGER.debug("Id 8 - Start")
                if self._data["openwrt_wan_ip"] == "":
                    for ress in resdata["result"][1]["interface"]:
                        if ress["interface"] == "lan":
                            self._data["openwrt_wan_ip"] = ress["ipv4-address"][0]["address"]
                            self._data["openwrt_wan_uptime"] = self.seconds_to_dhms(ress["uptime"])
                # _LOGGER.debug("Id 8 - End")

            elif resdata["id"] == 9:
                # _LOGGER.debug("Id 9 - Start")
                self._data["openwrt_rx"] = self.hum_convert_nounit(resdata["result"][1]["br-lan"]["stats"]["rx_bytes"])
                self._data["openwrt_tx"] = self.hum_convert_nounit(resdata["result"][1]["br-lan"]["stats"]["tx_bytes"])
                # self._data["openwrt_rx_packets"] = self.speed_convert_nounit(resdata["result"][1]["br-lan"]["stats"]["rx_packets"])
                # self._data["openwrt_tx_packets"] = self.speed_convert_nounit(resdata["result"][1]["br-lan"]["stats"]["tx_packets"])
                # _LOGGER.debug("Id 9 - End")

            elif resdata["id"] == 10:
                # _LOGGER.debug("Id 10 - Start")
                jsonTmp = resdata["result"][1]["result"]
                self._data["openwrt_rx_packets"] = self.speed_convert_nounit((jsonTmp[1][1] - jsonTmp[0][1])/(jsonTmp[1][0] - jsonTmp[0][0]))
                self._data["openwrt_tx_packets"] = self.speed_convert_nounit((jsonTmp[1][3] - jsonTmp[0][1])/(jsonTmp[1][3] - jsonTmp[0][0]))
                # _LOGGER.debug("Id 10 - End")

        querytime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._data["querytime"] = querytime

        # _LOGGER.debug(querytime)

        return

    async def get_openwrt_version(self, sysauth):
        body = '[{"jsonrpc": "2.0", "id": 41, "method": "call", "params": ["' + sysauth + '", "system", "board", {}]}]'

        header = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body))
        }

        url = self._host + "/ubus/"
        try:
            async with timeout(REQUEST_TIMEOUT):
                resdata = await self._hass.async_add_executor_job(self.requestpost_json2, url, header, body)
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching openwrt_version data (timeout=%ds)", REQUEST_TIMEOUT)
            return
        except (ClientConnectorError) as error:
            _LOGGER.error("Error fetching openwrt_version data: %s", error)
            raise UpdateFailed(error)
        
        _LOGGER.debug("Requests remaining: %s", url)
        
        if resdata == 401 or resdata == 403:
            self._data = 401
            _LOGGER.debug("get_openwrt_version requestpost_json2: %s", self._data)
            return
        
        openwrtinfo = {}
        try:
            # 提取核心数据节点，减少重复嵌套访问
            system_core_info = resdata[0]["result"][1]
        except (IndexError, KeyError, TypeError):
            # 索引/键不存在、类型错误时，初始化空字典避免后续报错
            system_core_info = {}

        # 赋值 OpenWRT 信息（get 方法容错，键不存在返回空字符串）
        openwrtinfo["sw_version"] = system_core_info.get("kernel", "")
        openwrtinfo["device_name"] = system_core_info.get("hostname", "")
        openwrtinfo["model"] = system_core_info.get("release", {}).get("description", "").replace("'", "")

        return openwrtinfo

    async def _get_ikuai_switch(self, sysauth, name):
        resdata = await self._check_openwrt_passwall(sysauth)

        if resdata == True:
            self._data["switch"].append({"name": name, "onoff": "on"})
        else:
            self._data["switch"].append({"name": name, "onoff": "off"})
        return

    async def get_data(self, sysauth):
        tasks = [
            asyncio.create_task(self._get_openwrt_status(sysauth)),
            asyncio.create_task(self._get_openwrt_passwall(sysauth)),
        ]
        await asyncio.gather(*tasks)

        self._data["switch"] = []
        tasks = []
        for switch in SWITCH_TYPES:  # pylint: disable=consider-using-dict-items
            tasks = [
                asyncio.create_task(self._get_ikuai_switch(sysauth, SWITCH_TYPES[switch]["name"],)),
            ]
            await asyncio.gather(*tasks)

        return self._data


class GetDataError(Exception):
    """request error or response data is unexpected"""
