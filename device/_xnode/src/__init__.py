# @package: xnode
# @version: 1.4.1
# @type: device-specific
# @category: board
# @interface: GPIO, I2C
# @depends: termviz, termio
# @platforms: xbee
# @tags: xbee, zigbee, xnode, digi

import gc
import umachine as machine
from micropython import const

XNODE_LED_PIN = 'D9'
XNODE_SUPPLY_VOLTAGE_PIN = 'D2'
XNODE_I2C_ID1_SCL_PIN = 'D1'
XNODE_I2C_ID1_SDA_PIN = 'D11'

class Din:
    LOW = 0
    HIGH = 1
    PULL_DOWN = machine.Pin.PULL_DOWN
    PULL_UP = machine.Pin.PULL_UP

    def __init__(self, pin, *, pull=None, active_low=True):
        self._pin = machine.Pin(pin, machine.Pin.IN, pull=pull)
        self._active_low = active_low

    def value(self):
        v = self._pin.value()
        return (0 if v else 1) if self._active_low else (1 if v else 0)

    def raw_value(self):
        return self._pin.value()

    def is_active(self):
        return self.value() == 1

    @property
    def pin(self):
        return self._pin

class Dout:
    LOW = 0
    HIGH = 1
    PULL_DOWN = machine.Pin.PULL_DOWN
    PULL_UP = machine.Pin.PULL_UP

    def __init__(self, pin, *, pull=None, value=LOW, active_low=False):
        self._active_low = active_low
        init_hw = (0 if value else 1) if active_low else (1 if value else 0)
        self._pin = machine.Pin(pin, machine.Pin.OUT, pull=pull, value=init_hw)

    def value(self, n=None):
        if n is None:
            v = self._pin.value()
            return (0 if v else 1) if self._active_low else (1 if v else 0)
        hw = (0 if n else 1) if self._active_low else (1 if n else 0)
        self._pin.value(hw)

    def raw_value(self, n=None):
        if n is None:
            return self._pin.value()
        self._pin.value(1 if n else 0)

    def on(self):
        self._pin.value(0 if self._active_low else 1)

    def off(self):
        self._pin.value(1 if self._active_low else 0)

    def toggle(self):
        self._pin.toggle()

    @property
    def pin(self):
        return self._pin

def Wdt(timeout):
    return machine.WDT(0, timeout)

class I2c:
    def __init__(self, addr, freq=400000):
        self._addr = addr
        self._i2c = machine.I2C(1, freq=freq)
        self._buf1 = bytearray(1)
        self._buf2 = bytearray(2)

    @property
    def address(self):
        return self._addr

    def read_u8(self, reg):
        self._i2c.readfrom_mem_into(self._addr, reg, self._buf1)
        return self._buf1[0]

    def read_s8(self, reg):
        self._i2c.readfrom_mem_into(self._addr, reg, self._buf1)
        v = self._buf1[0]
        return v - 256 if v > 127 else v

    def read_u16(self, reg, *, little_endian=True):
        self._i2c.readfrom_mem_into(self._addr, reg, self._buf2)
        if little_endian:
            return self._buf2[0] | (self._buf2[1] << 8)
        return (self._buf2[0] << 8) | self._buf2[1]

    def read_s16(self, reg, *, little_endian=True):
        v = self.read_u16(reg, little_endian=little_endian)
        return v - 65536 if v > 32767 else v

    def write_u8(self, reg, val):
        self._buf1[0] = val & 0xFF
        self._i2c.writeto_mem(self._addr, reg, self._buf1)

    def write_u16(self, reg, val, *, little_endian=True):
        if little_endian:
            self._buf2[0] = val & 0xFF
            self._buf2[1] = (val >> 8) & 0xFF
        else:
            self._buf2[0] = (val >> 8) & 0xFF
            self._buf2[1] = val & 0xFF
        self._i2c.writeto_mem(self._addr, reg, self._buf2)

    def readfrom(self, nbytes, *, stop=True):
        return self._i2c.readfrom(self._addr, nbytes, stop)

    def readinto(self, buf, *, stop=True):
        return self._i2c.readinto(self._addr, buf, stop)

    def readfrom_mem(self, reg, nbytes, *, addrsize=8):
        return self._i2c.readfrom_mem(self._addr, reg, nbytes, addrsize=addrsize)

    def readfrom_mem_into(self, reg, buf, *, addrsize=8):
        return self._i2c.readfrom_mem_into(self._addr, reg, buf, addrsize=addrsize)

    def writeto(self, buf, *, stop=True):
        return self._i2c.writeto(self._addr, buf, stop)

    def writeto_mem(self, reg, buf, *, addrsize=8):
        return self._i2c.writeto_mem(self._addr, reg, buf, addrsize=addrsize)

class Led:
    def __init__(self):
        self._led = Dout(XNODE_LED_PIN, value=Dout.LOW, active_low=True)

    def on(self):
        self._led.on()

    def off(self):
        self._led.off()

    def toggle(self):
        self._led.toggle()

    def value(self, n=None):
        return self._led.value(n)

class SupplyVoltage(machine.ADC):
    def __init__(self):
        super().__init__(XNODE_SUPPLY_VOLTAGE_PIN)

    def read_raw(self):
        return super().read()

    def read(self):
        return round((super().read() * (3.3 / 4095.0)) * 1.6, 1)

# --- Lazy Proxy Wrappers (Compatible with both MicroPython v1.12 and v1.20) ---

def get_sys_info():
    from .diag import get_sys_info as _fn
    return _fn()

def get_mem_info():
    from .diag import get_mem_info as _fn
    return _fn()

def get_fs_info(path='/'):
    from .diag import get_fs_info as _fn
    return _fn(path)

def i2cdetect(show=False):
    from .diag import i2cdetect as _fn
    return _fn(show)

def ReplSerial(timeout=None, *, bufsize=128):
    from termio import ReplSerial as _cls
    return _cls(timeout=timeout, bufsize=bufsize)

class _IlluminanceProxy:
    BH1750_ADDR = const(0x23)
    POWER_OFF = const(0x00)
    POWER_ON = const(0x01)
    POWER_RESET = const(0x07)
    CONT_HIGH_RES = const(0x10)
    CONT_HIGH_RES_2 = const(0x11)
    CONT_LOW_RES = const(0x13)
    ONE_TIME_HIGH_RES = const(0x20)
    ONE_TIME_HIGH_RES_2 = const(0x21)
    ONE_TIME_LOW_RES = const(0x23)

    def __call__(self, *, mode=0x10):
        from .env import Illuminance as _cls
        return _cls(mode=mode)

Illuminance = _IlluminanceProxy()

class _TphgProxy:
    BME680_ADDR = const(0x77)
    FORCED_MODE = const(0x01)
    SLEEP_MODE = const(0x00)

    def __call__(self, *args, **kwargs):
        from .env import Tphg as _cls
        return _cls(*args, **kwargs)

Tphg = _TphgProxy()

gc.collect()
