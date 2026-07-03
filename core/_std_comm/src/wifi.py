# @package: wifi
# @version: 2.0.0
# @type: core
# @category: communication
# @interface: WiFi
# @depends: none
# @platforms: rp2, esp32
# @tags: wifi, network, wireless, sta, ap, connect
# @author: PlanXLab Development Team

import network
import time

_sta = None
_ap = None

def _get_pm_const(name):
    try:
        return getattr(network.WLAN, name)
    except AttributeError:
        return None

class Wifi:
    
    AUTH_OPEN = 0
    AUTH_WEP = 1
    AUTH_WPA_PSK = 2
    AUTH_WPA2_PSK = 3
    AUTH_WPA_WPA2_PSK = 4

    PM_NONE = _get_pm_const('PM_NONE')
    PM_PERFORMANCE = _get_pm_const('PM_PERFORMANCE')
    PM_POWERSAVE = _get_pm_const('PM_POWERSAVE')

    @staticmethod
    def _sta():
        global _sta
        if _sta is None:
            _sta = network.WLAN(network.STA_IF)
        if not _sta.active():
            _sta.active(True)
        return _sta

    @staticmethod
    def _ap_if():
        global _ap
        if _ap is None:
            _ap = network.WLAN(network.AP_IF)
        return _ap

    @staticmethod
    def scan() -> list[tuple]:
        return Wifi._sta().scan()

    @staticmethod
    def ssids() -> list[str]:
        aps = Wifi._sta().scan()
        seen = set()
        result = []
        for ap in aps:
            ssid = ap[0].decode('utf-8', 'ignore')
            if ssid and ssid not in seen:
                seen.add(ssid)
                result.append(ssid)
        return result

    @staticmethod
    def connect(ssid: str, password: str = "", *, timeout_s: float = 20.0, pm: int = None) -> bool:
        sta = Wifi._sta()
        if sta.isconnected():
            if sta.config('essid') == ssid:
                return True
            sta.disconnect()
            time.sleep_ms(100)

        sta.connect(ssid, password)
        deadline = time.ticks_add(time.ticks_ms(), int(timeout_s * 1000))
        
        while not sta.isconnected():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return False
            time.sleep_ms(100)
        
        if pm is not None:
            try:
                sta.config(pm=pm)
            except Exception:
                pass
        
        return True

    @staticmethod
    def disconnect() -> None:
        sta = Wifi._sta()
        if sta.isconnected():
            sta.disconnect()
            time.sleep_ms(100)

    @staticmethod
    def is_connected() -> bool:
        return Wifi._sta().isconnected()

    @staticmethod
    def ifconfig() -> tuple | None:
        sta = Wifi._sta()
        if not sta.isconnected():
            return None
        return sta.ifconfig()

    @staticmethod
    def ip() -> str | None:
        cfg = Wifi.ifconfig()
        return cfg[0] if cfg else None

    @staticmethod
    def gateway() -> str | None:
        cfg = Wifi.ifconfig()
        return cfg[2] if cfg else None

    @staticmethod
    def dns() -> str | None:
        cfg = Wifi.ifconfig()
        return cfg[3] if cfg else None

    @staticmethod
    def netmask() -> str | None:
        cfg = Wifi.ifconfig()
        return cfg[1] if cfg else None

    @staticmethod
    def mac() -> str:
        mac_bytes = Wifi._sta().config('mac')
        return ':'.join(f'{b:02X}' for b in mac_bytes)

    @staticmethod
    def rssi() -> int | None:
        sta = Wifi._sta()
        if not sta.isconnected():
            return None
        try:
            return sta.status('rssi')
        except Exception:
            return None

    @staticmethod
    def ssid() -> str | None:
        sta = Wifi._sta()
        if not sta.isconnected():
            return None
        try:
            return sta.config('essid')
        except Exception:
            return None

    @staticmethod
    def hostname(name: str = None) -> str:
        sta = Wifi._sta()
        if name is not None:
            try:
                sta.config(dhcp_hostname=name)
            except Exception:
                try:
                    network.hostname(name)
                except Exception:
                    pass
        try:
            return sta.config('dhcp_hostname')
        except Exception:
            try:
                return network.hostname()
            except Exception:
                return ""

    @staticmethod
    def status() -> dict:
        sta = Wifi._sta()
        connected = sta.isconnected()
        return {
            "connected": connected,
            "ssid": Wifi.ssid() if connected else None,
            "ip": Wifi.ip() if connected else None,
            "rssi": Wifi.rssi() if connected else None,
            "mac": Wifi.mac(),
        }

    @staticmethod
    def connect_multi(networks: list[tuple[str, str]], *, timeout_s: float = 10.0) -> str | None:
        for ssid, password in networks:
            if Wifi.connect(ssid, password, timeout_s=timeout_s):
                return ssid
        return None

    @staticmethod
    def wait_connected(timeout_s: float = 30.0) -> bool:
        deadline = time.ticks_add(time.ticks_ms(), int(timeout_s * 1000))
        while not Wifi.is_connected():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return False
            time.sleep_ms(100)
        return True

    @staticmethod
    def deactivate() -> None:
        global _sta
        if _sta is not None:
            try:
                _sta.active(False)
            except Exception:
                pass
            _sta = None
