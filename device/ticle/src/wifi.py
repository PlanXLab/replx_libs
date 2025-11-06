import network
import utime

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


_wifi_iface = None

class WifiManager:
    @staticmethod
    def _ensure_initialized():
        global _wifi_iface
        if _wifi_iface is None:
            _wifi_iface = network.WLAN(network.STA_IF)
            if not _wifi_iface.active():
                _wifi_iface.active(True)

    @staticmethod
    def scan() -> list[tuple[str,int,int,int]]:
        WifiManager._ensure_initialized()
        return _wifi_iface.scan()

    @staticmethod
    def available_ssids() -> list[str]:
        WifiManager._ensure_initialized()
        aps = _wifi_iface.scan()
        ssids = set()
        for ap in aps:
            ssid = ap[0].decode('utf-8', 'ignore')
            if ssid:
                ssids.add(ssid)
        return list(ssids)

    @staticmethod
    def connect(ssid: str, password: str, timeout: float = 20.0) -> bool:
        WifiManager._ensure_initialized()
        if _wifi_iface.isconnected():
            return True

        _wifi_iface.connect(ssid, password)
        start = utime.ticks_ms()
        while not _wifi_iface.isconnected():
            if utime.ticks_diff(utime.ticks_ms(), start) > int(timeout * 1000):
                return False
            utime.sleep_ms(200)
        return True

    @staticmethod
    def disconnect() -> None:
        WifiManager._ensure_initialized()
        if _wifi_iface.isconnected():
            _wifi_iface.disconnect()
            utime.sleep_ms(100)
    
    @staticmethod
    def ifconfig() -> tuple | None:
        if not WifiManager.is_connected():
            return None
        return _wifi_iface.ifconfig()

    @staticmethod
    def is_connected() -> bool:
        WifiManager._ensure_initialized()
        return _wifi_iface.isconnected()

    @staticmethod
    def ip() -> str | None:
        if not WifiManager.is_connected():
            return None
        return _wifi_iface.ifconfig()[0]
