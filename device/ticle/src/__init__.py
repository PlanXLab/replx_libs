import sys
import micropython

try:
    micropython.alloc_emergency_exception_buf(128)
except Exception:
    pass

from ._utils import get_sys_info, get_mem_info, get_fs_info

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"

_lazy_map = {
    "KeyReader":           (".keyreader", "KeyReader"),
    "input":               (".repl", "input"),
    "ReplSerial":          (".repl", "ReplSerial"),
    "WifiManager":         (".wifi", "WifiManager"),
    "BLEBroker":           (".ble", "BLEBroker"),
    "Led":                 (".basic", "Led"),
    "Button":              (".basic", "Button"),
    "LOW":                 (".io", "LOW"),
    "HIGH":                (".io", "HIGH"),
    "Din":                 (".io", "Din"),
    "Dout":                (".io", "Dout"),
    "Adc":                 (".adc", "Adc"),
    "Pwm":                 (".pwm", "Pwm"),
    "STAT_OK":             (".bus_lock", "STAT_OK"),
    "STAT_TIMEOUT":        (".bus_lock", "STAT_TIMEOUT"),
    "STAT_BUS_ERR":        (".bus_lock", "STAT_BUS_ERR"),
    "STAT_NO_DEVICE":      (".bus_lock", "STAT_NO_DEVICE"),
    "I2C0_SPINLOCK_ID":    (".bus_lock", "I2C0_SPINLOCK_ID"),
    "I2C1_SPINLOCK_ID":    (".bus_lock", "I2C1_SPINLOCK_ID"),
    "SPI0_SPINLOCK_ID":    (".bus_lock", "SPI0_SPINLOCK_ID"),
    "SPI1_SPINLOCK_ID":    (".bus_lock", "SPI1_SPINLOCK_ID"),
    "SpinLock":            (".bus_lock", "SpinLock"),
    "i2cdetect":           (".i2c", "i2cdetect"),
    "I2CMaster":           (".i2c", "I2CMaster"),
    "Spi":                 (".spi", "Spi"),
}

__all__ = [
    "__version__", "__author__",
    "get_sys_info", "get_mem_info", "get_fs_info",
    "KeyReader", "input", "ReplSerial",
    "WifiManager", "BLEBroker",
    "Led", "Button",
    "LOW", "HIGH", "Din", "Dout", "Adc", "Pwm",
    "STAT_OK", "STAT_TIMEOUT", "STAT_BUS_ERR", "STAT_NO_DEVICE",
    "I2C0_SPINLOCK_ID", "I2C1_SPINLOCK_ID",
    "SPI0_SPINLOCK_ID", "SPI1_SPINLOCK_ID",
    "SpinLock", "i2cdetect", "I2CMaster", "Spi",
]

def __getattr__(name):
    try:
        rel_mod, attr = _lazy_map[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    
    fullname = __name__ + rel_mod
    __import__(fullname)
    mod = sys.modules[fullname]
    
    obj = getattr(mod, attr)
    globals()[name] = obj
    return obj

def __dir__():
    return sorted(list(globals().keys()) + list(_lazy_map.keys()))
