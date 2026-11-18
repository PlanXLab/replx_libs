# @package: imu
# @version: 1.3.0
# @type: device-specific
# @category: board
# @interface: I2C
# @depends: none
# @platforms: xbee
# @tags: imu, bno055, sensor

import utime
import ustruct
import gc
import machine
from micropython import const


_CHIP_ID_ADDR = const(0x00)
_BNO055_ID = const(0xA0)

_PAGE_ID_ADDR = const(0x07)
_UNIT_SEL_ADDR = const(0x3B)
_OPR_MODE_ADDR = const(0x3D)
_PWR_MODE_ADDR = const(0x3E)
_SYS_TRIGGER_ADDR = const(0x3F)
_CALIB_STAT_ADDR = const(0x35)

_CONFIG_MODE = const(0x00)
_NDOF_MODE = const(0x0C)
_POWER_NORMAL = const(0x00)


class IMU:
    ACCELERATION = const(0x08)
    MAGNETIC = const(0x0E)
    GYROSCOPE = const(0x14)
    EULER = const(0x1A)
    QUATERNION = const(0x20)
    ACCEL_LINEAR = const(0x28)
    ACCEL_GRAVITY = const(0x2E)
    TEMPERATURE = const(0x34)

    # UNIT_SEL = 0x06 (m/s^2, uT, rad/s, deg, celsius)
    _SCALE = {
        ACCELERATION: 0.01,
        MAGNETIC: 0.0625,
        GYROSCOPE: 0.001090830782496456,  # 1 / 900 (rad/s)
        EULER: 0.0625,                    # 1 / 16 (deg)
        QUATERNION: 1.0 / (1 << 14),
        ACCEL_LINEAR: 0.01,
        ACCEL_GRAVITY: 0.01,
    }

    def __init__(self, addr=0x28):
        self._i2c = machine.I2C(1, freq=100000)
        self._addr = addr
        
        self._buf1 = bytearray(1)
        self._buf6 = bytearray(6)
        self._buf8 = bytearray(8)
        self._init_sensor(_NDOF_MODE)

    def _init_sensor(self, mode):
        for _ in range(10):
            try:
                if self._read_byte(_CHIP_ID_ADDR) == _BNO055_ID:
                    break
            except OSError:
                pass
            utime.sleep_ms(50)
        else:
            raise RuntimeError("Failed to find BNO055 sensor")

        self.set_mode(_CONFIG_MODE)
        self._write_reg(_SYS_TRIGGER_ADDR, 0x20)
        utime.sleep_ms(700)
        while True:
            try:
                if self._read_byte(_CHIP_ID_ADDR) == _BNO055_ID:
                    break
            except OSError:
                pass
            utime.sleep_ms(20)

        self._write_reg(_PWR_MODE_ADDR, _POWER_NORMAL)
        utime.sleep_ms(10)
        self._write_reg(_PAGE_ID_ADDR, 0x00)
        self._write_reg(_UNIT_SEL_ADDR, 0x06) # UNIT_SEL = 0x06
        self._write_reg(_SYS_TRIGGER_ADDR, 0x00)
        utime.sleep_ms(10)
        self.set_mode(mode)

    def set_mode(self, mode):
        self._write_reg(_OPR_MODE_ADDR, mode)
        utime.sleep_ms(30)

    def _write_reg(self, reg, val):
        self._buf1[0] = val & 0xFF
        self._i2c.writeto_mem(self._addr, reg, self._buf1)

    def _read_byte(self, reg):
        self._i2c.readfrom_mem_into(self._addr, reg, self._buf1)
        return self._buf1[0]

    def _read_temperature(self):
        t = self._read_byte(self.TEMPERATURE)
        return t - 256 if t > 127 else t

    def _read_quaternion(self):
        self._i2c.readfrom_mem_into(self._addr, self.QUATERNION, self._buf8)
        s = self._SCALE[self.QUATERNION]
        w, x, y, z = ustruct.unpack("<hhhh", self._buf8)
        return w * s, x * s, y * s, z * s

    def _read_vector(self, target):
        s = self._SCALE.get(target)
        if s is None:
            raise ValueError("Invalid sensor target: {}".format(target))
        self._i2c.readfrom_mem_into(self._addr, target, self._buf6)
        x, y, z = ustruct.unpack("<hhh", self._buf6)
        return x * s, y * s, z * s

    def calibration(self):
        data = self._read_byte(_CALIB_STAT_ADDR)
        return (data >> 6) & 0x03, (data >> 4) & 0x03, (data >> 2) & 0x03, data & 0x03

    def read(self, target=EULER):
        if target == self.TEMPERATURE:
            return self._read_temperature()
        if target == self.QUATERNION:
            return self._read_quaternion()
        return self._read_vector(target)

    @property
    def euler(self):
        return self._read_vector(self.EULER)

    @property
    def quaternion(self):
        return self._read_quaternion()

    @property
    def acceleration(self):
        return self._read_vector(self.ACCELERATION)

    @property
    def magnetic(self):
        return self._read_vector(self.MAGNETIC)

    @property
    def gyroscope(self):
        return self._read_vector(self.GYROSCOPE)

    @property
    def linear_acceleration(self):
        return self._read_vector(self.ACCEL_LINEAR)

    @property
    def gravity(self):
        return self._read_vector(self.ACCEL_GRAVITY)

    @property
    def temperature(self):
        return self._read_temperature()


gc.collect()
