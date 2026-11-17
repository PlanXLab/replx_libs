# @package: thermometer
# @version: 1.3.0
# @type: device-specific
# @category: board
# @interface: I2C
# @depends: none
# @platforms: xbee
# @tags: thermometer, ir, sensor

import gc
import machine
from micropython import const

MLX90614_ADDR = const(0x5A)
EEPROM_TOMAX = const(0x00)
EEPROM_TOMIN = const(0x01)
EEPROM_PWMCTRL = const(0x02)
EEPROM_TARANGE = const(0x03)
EEPROM_EMISSIVITY = const(0x04)
EEPROM_CONFIG_REGISTER1 = const(0x05)
_REG_TA = const(0x06)
_REG_TOBJ1 = const(0x07)
_REG_TOBJ2 = const(0x08)

class Thermometer:
    def __init__(self):
        self._i2c = machine.I2C(1, freq=50000)
        self._buf2 = bytearray(2)

    def read_raw(self, is_object=True, eeprom=False, *, object=None):
        if object is not None:
            is_object = object
        reg = _REG_TOBJ1 if is_object else _REG_TA
        if eeprom:
            reg |= 0x20
        self._i2c.readfrom_mem_into(MLX90614_ADDR, reg, self._buf2)
        return self._buf2[0] | (self._buf2[1] << 8)

    read = read_raw

    def ambient(self):
        return round(self.read_raw(False) * 0.02 - 273.15, 1)

    def object(self):
        return round(self.read_raw(True) * 0.02 - 273.15, 1)

    def object2(self):
        self._i2c.readfrom_mem_into(MLX90614_ADDR, _REG_TOBJ2, self._buf2)
        raw = self._buf2[0] | (self._buf2[1] << 8)
        return round(raw * 0.02 - 273.15, 1)

    @property
    def emissivity(self):
        self._i2c.readfrom_mem_into(MLX90614_ADDR, 0x20 | EEPROM_EMISSIVITY, self._buf2)
        raw = self._buf2[0] | (self._buf2[1] << 8)
        return round(raw / 65535.0, 3)

gc.collect()
