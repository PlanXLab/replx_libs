# @package: imu
# @version: 1.1.0
# @type: device-specific
# @category: board
# @interface: I2C
# @depends: none
# @platforms: xbee
# @tags: imu, bno055, sensor

import time
import struct
import machine
from micropython import const


BNO055_ADDR = const(0x28)
ACCELERATION = const(0x08)
MAGNETIC = const(0x0E)
GYROSCOPE = const(0x14)
EULER = const(0x1A)
QUATERNION = const(0x20)
ACCEL_LINEAR = const(0x28)
ACCEL_GRAVITY = const(0x2E)
TEMPERATURE = const(0x34)

class IMU:
    def __init__(self):
        self.__i2c = machine.I2C(1)
        self.__scale = {
            ACCELERATION: 1 / 100,
            MAGNETIC: 1 / 16,
            GYROSCOPE: 0.001090830782496456,
            EULER: 1 / 16,
            QUATERNION: 1 / (1 << 14),
            ACCEL_LINEAR: 1 / 100,
            ACCEL_GRAVITY: 1 / 100,
        }
        self.__call = {
            ACCELERATION: self.__read_other,
            MAGNETIC: self.__read_other,
            GYROSCOPE: self.__read_other,
            EULER: self.__read_other,
            QUATERNION: self.__read_quaternion,
            ACCEL_LINEAR: self.__read_other,
            ACCEL_GRAVITY: self.__read_other,
            TEMPERATURE: self.__read_temperature,
        }

        self.__i2c.writeto_mem(BNO055_ADDR, 0x3D, bytes([0x00]))
        time.sleep_ms(20)
        self.__i2c.writeto_mem(BNO055_ADDR, 0x3F, bytes([0x20]))
        time.sleep_ms(650)
        self.__i2c.writeto_mem(BNO055_ADDR, 0x3E, bytes([0x00]))
        self.__i2c.writeto_mem(BNO055_ADDR, 0x07, bytes([0x00]))
        self.__i2c.writeto_mem(BNO055_ADDR, 0x3F, bytes([0x80]))
        self.__i2c.writeto_mem(BNO055_ADDR, 0x3F, bytes([0x00]))
        time.sleep_ms(10)
        self.__i2c.writeto_mem(BNO055_ADDR, 0x3D, bytes([0x0C]))
        time.sleep_ms(200)

    def __read_temperature(self, addr):
        t = self.__i2c.readfrom_mem(BNO055_ADDR, addr, 1)[0]
        return t - 256 if t > 127 else t

    def __read_quaternion(self, addr):
        t = self.__i2c.readfrom_mem(BNO055_ADDR, addr, 8)
        return tuple(
            v * self.__scale[QUATERNION] for v in struct.unpack("hhhh", t)
        )

    def __read_other(self, addr):
        if addr not in self.__scale:
            raise ValueError(f"Address {addr} not in scale mapping")
        t = self.__i2c.readfrom_mem(BNO055_ADDR, addr, 6)
        return tuple(v * self.__scale[addr] for v in struct.unpack("hhh", t))

    def calibration(self):
        data = self.__i2c.readfrom_mem(BNO055_ADDR, 0x35, 1)[0]
        return (data >> 6) & 0x03, (data >> 4) & 0x03, (data >> 2) & 0x03, data & 0x03

    def read(self, addr):
        return self.__call[addr](addr)
