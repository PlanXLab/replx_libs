# @package: imu
# @version: 1.1.0
# @type: device-specific
# @category: board
# @interface: I2C
# @depends: none
# @platforms: xbee
# @tags: thermometer, ir, sensor

import struct
import machine
from micropython import const


MLX90614_ADDR = const(0x5A)
EEPROM_PWMCTRL = const(0x02)
EEPROM_CONFIG_REGISTER1 = const(0x05)


class Thermometer:

    def __init__(self):
        self.__i2c = machine.I2C(1, freq=50000) #The maximum frequency of the MLX90614 is 100 KHz and the minimum is 10 KHz. 

    def read(self, object=True, eeprom=False):
        reg = const(0x07) if object else const(0x06)
        if eeprom:
            reg = 0x20 | reg
            
        data = self.__i2c.readfrom_mem(MLX90614_ADDR, reg, 2)
        return struct.unpack('<H', data)[0]

    def ambient(self):
        data = self.read(False)
        return round(data * 0.02 - 273.15, 1)

    def object(self):
        data = self.read()
        return round(data * 0.02 - 273.15, 1)
