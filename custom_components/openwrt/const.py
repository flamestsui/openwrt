"""Constants for the openwrt health code integration."""

DOMAIN = "openwrt"

# CONF KEY
CONF_USERNAME = "username"
CONF_PASSWD = "passwd"
CONF_HOST = "host"
CONF_TOKEN_EXPIRE_TIME = "token_expire_time"
COORDINATOR = "coordinator"
CONF_UPDATE_INTERVAL = "update_interval_seconds"

UNDO_UPDATE_LISTENER = "undo_update_listener"

REQUEST_TIMEOUT = 10
# OPENWRT URL
DO_URL = "/cgi-bin/luci/"
UBUS_URL = "/ubus/"

# Sensor Configuration
SENSOR_TYPES = {
    "openwrt_uptime": {
        "icon": "mdi:clock-time-eight",
        "label": "OpenWrt启动时长",
        "name": "uptime",
    },
    "openwrt_cpu": {
        "icon": "mdi:cpu-64-bit",
        "label": "CPU占用",
        "name": "CPU",
        "unit_of_measurement": "%",
    },
    "openwrt_cputemp": {
        "icon": "mdi:thermometer",
        "label": "CPU温度",
        "name": "CPU_temperature",
        "unit_of_measurement": "°C",
        "device_class": "temperature",
    },
    "openwrt_memory": {
        "icon": "mdi:memory",
        "label": "内存占用",
        "name": "Memory",
        "unit_of_measurement": "%",
    },
    "openwrt_memory_total": {
        "icon": "mdi:memory",
        "label": "内存总数",
        "name": "Memory_Total",
        "unit_of_measurement": "B",
    },
    "openwrt_memory_total_gb": {
        "icon": "mdi:memory",
        "label": "内存总数",
        "name": "Memory_Total_GB",
        "unit_of_measurement": "GiB",
    },
    "openwrt_memory_free": {
        "icon": "mdi:memory",
        "label": "空闲内存",
        "name": "Memory_Free",
        "unit_of_measurement": "B",
    },
    "openwrt_memory_free_gb": {
        "icon": "mdi:memory",
        "label": "空闲内存",
        "name": "Memory_Free_GB",
        "unit_of_measurement": "GiB",
    },
    "openwrt_memory_shared": {
        "icon": "mdi:memory",
        "label": "共享内存",
        "name": "Memory_Share",
        "unit_of_measurement": "B",
    },
    "openwrt_memory_shared_gb": {
        "icon": "mdi:memory",
        "label": "共享内存",
        "name": "Memory_Share_GB",
        "unit_of_measurement": "GiB",
    },
    "openwrt_memory_buffered": {
        "icon": "mdi:memory",
        "label": "缓冲内存",
        "name": "Memory_Buffered",
        "unit_of_measurement": "B",
    },
    "openwrt_memory_buffered_gb": {
        "icon": "mdi:memory",
        "label": "缓冲内存",
        "name": "Memory_Buffered_GB",
        "unit_of_measurement": "GiB",
    },
    "openwrt_memory_available": {
        "icon": "mdi:memory",
        "label": "可用内存",
        "name": "Memory_Available",
        "unit_of_measurement": "B",
    },
    "openwrt_memory_available_gb": {
        "icon": "mdi:memory",
        "label": "可用内存",
        "name": "Memory_Available_GB",
        "unit_of_measurement": "GiB",
    },
    "openwrt_memory_cached": {
        "icon": "mdi:memory",
        "label": "缓存内存",
        "name": "Memory_Cached",
        "unit_of_measurement": "B",
    },
    "openwrt_memory_cached_gb": {
        "icon": "mdi:memory",
        "label": "缓存内存",
        "name": "Memory_Cached_GB",
        "unit_of_measurement": "GiB",
    },
    "openwrt_wan_ip": {
        "icon": "mdi:wan",
        "label": "WAN IP",
        "name": "Wan_ip",
    },
    "openwrt_wan_uptime": {
        "icon": "mdi:timer-sync-outline",
        "label": "WAN Uptime",
        "name": "Wan_uptime",
    },
    "openwrt_wan6_ip": {
        "icon": "mdi:wan",
        "label": "WAN IP6",
        "name": "Wan6_ip",
    },
    "openwrt_wan6_uptime": {
        "icon": "mdi:timer-sync-outline",
        "label": "WAN IP6 Uptime",
        "name": "Wan6_uptime",
    },
    "openwrt_user_online": {
        "icon": "mdi:account-multiple",
        "label": "在线用户数",
        "name": "user_online",
    },
    "openwrt_conncount": {
        "icon": "mdi:lan-connect",
        "label": "活动连接",
        "name": "conncount",
    },
    "openwrt_tx": {
        "icon": "mdi:upload-network",
        "label": "上传总量",
        "name": "tx",
        "unit_of_measurement": "GB",
    },
    "openwrt_tx_packets": {
        "icon": "mdi:upload-network",
        "label": "上传速度",
        "name": "tx_packets",
        "unit_of_measurement": "KB/s",
    },
    "openwrt_rx": {
        "icon": "mdi:download-network",
        "label": "下载总量",
        "name": "rx",
        "unit_of_measurement": "GB",
    },
    "openwrt_rx_packets": {
        "icon": "mdi:download-network",
        "label": "下载速度",
        "name": "rx_packets",
        "unit_of_measurement": "KB/s",
    },
    "openwrt_passwall_ip": {
        "icon": "mdi:ip-network-outline",
        "label": "PassWall IP",
        "name": "passwall_ip",
    },
    "openwrt_passwall_country": {
        "icon": "mdi:lan-connect",
        "label": "PassWall节点",
        "name": "passwall_country",
    },
}

BUTTON_TYPES = {
    "openwrt_restart": {
        "label": "OpenWrt重启",
        "name": "Restart",
        "device_class": "restart",
        "action": "restart",
    },
    "openwrt_restart_reconnect_wan": {
        "label": "OpenWrt重连wan网络",
        "name": "Reconnect_wan",
        "device_class": "restart",
        "action": "reconnect_iface",
        "iface": "wan",
    },
    "openwrt_restart_reconnect_wan6": {
        "label": "OpenWrt重连wan6网络",
        "name": "Reconnect_wan6",
        "device_class": "restart",
        "action": "reconnect_iface",
        "iface": "wan6",
    },
    "openwrt_restart_reconnect_gw": {
        "label": "OpenWrt重连GW网络",
        "name": "Reconnect_gw",  # 实体名称
        "device_class": "restart",
        "action": "reconnect_iface",
        "iface": "gw",  # 网络接口
    },
    "openwrt_restart_reconnect_docker": {
        "label": "OpenWrt重连docker网络",
        "name": "Reconnect_docker",
        "device_class": "restart",
        "action": "reconnect_iface",
        "iface": "docker",
    },
    "openwrt_node_subscribe": {
        "label": "OpenWrt重新订阅fq节点",
        "name": "Node_subscribe",
        "device_class": "restart",
        "action": "submit_data",
        "parameter1": "admin/services/passwall/node_subscribe",
        "parameter2": "admin/services/passwall/node_subscribe",
        "body": {
            "token": "{{action_token}}",
            "cbi.submit": "1",  # 以下 cfg08b7d7 需要在浏览器工具中抓包获取，每个路由器值不一样。
            "cbi.cbe.passwall.cfg08b7d7.subscribe_proxy": "1",
            "cbid.passwall.cfg08b7d7.filter_keyword_mode": "1",
            "cbid.passwall.cfg08b7d7.filter_discard_list": "s801",
            "cbid.passwall.cfg08b7d7.filter_discard_list": "剩余流量",
            "cbid.passwall.cfg08b7d7.filter_discard_list": "QQ群",
            "cbid.passwall.cfg08b7d7.filter_discard_list": "官网",
            "cbid.passwall.cfg08b7d7.filter_keep_list": "",
            "cbid.passwall.cfg08b7d7.ss_aead_type": "xray",
            "cbid.passwall.cfg08b7d7.trojan_type": "trojan-plus",
            "cbi.sts.passwall.subscribe_list": "",
            "cbid.passwall.cfg108b02.remark": "SS",
            "cbid.passwall.cfg108b02.url": "https://xxxxxxxxxxxxxxxxxxxx",
            "cbid.passwall.cfg108b02._update": "手动订阅"
        }
    },
}

SWITCH_TYPES = {
    "passwall": {
        "icon": "mdi:account-lock",
        "label": "PassWall开关",
        "name": "passwall",
        "turn_on_body": "1",
        "turn_off_body": "0",
    },
}
