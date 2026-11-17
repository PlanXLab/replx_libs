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

BNO055_ADDR = const(0x28)
ACCELERATION = const(0x08)
MAGNETIC = const(0x0E)
GYROSCOPE = const(0x14)
EULER = const(0x1A)
QUATERNION = const(0x20)
ACCEL_LINEAR = const(0x28)
ACCEL_GRAVITY = const(0x2E)
TEMPERATURE = const(0x34)

MODE_CONFIG = const(0x00)
MODE_IMU = const(0x08)
MODE_COMPASS = const(0x09)
MODE_M4G = const(0x0A)
MODE_NDOF_FMC_OFF = const(0x0B)
MODE_NDOF = const(0x0C)

class IMU:
    ACCELERATION = ACCELERATION
    MAGNETIC = MAGNETIC
    GYROSCOPE = GYROSCOPE
    EULER = EULER
    QUATERNION = QUATERNION
    ACCEL_LINEAR = ACCEL_LINEAR
    ACCEL_GRAVITY = ACCEL_GRAVITY
    TEMPERATURE = TEMPERATURE

    MODE_CONFIG = MODE_CONFIG
    MODE_IMU = MODE_IMU
    MODE_COMPASS = MODE_COMPASS
    MODE_M4G = MODE_M4G
    MODE_NDOF_FMC_OFF = MODE_NDOF_FMC_OFF
    MODE_NDOF = MODE_NDOF

    _SCALE = {
        ACCELERATION: 0.01,
        MAGNETIC: 0.0625,
        GYROSCOPE: 0.001090830782496456,
        EULER: 0.0625,
        QUATERNION: 1.0 / (1 << 14),
        ACCEL_LINEAR: 0.01,
        ACCEL_GRAVITY: 0.01,
    }

    def __init__(self, mode=MODE_NDOF):
        self._i2c = machine.I2C(1)
        self._buf1 = bytearray(1)
        self._buf6 = bytearray(6)
        self._buf8 = bytearray(8)
        self._mode = mode

        self._write_reg(0x3D, MODE_CONFIG)
        utime.sleep_ms(20)
        self._write_reg(0x3F, 0x20)
        utime.sleep_ms(650)
        self._write_reg(0x3E, 0x00)
        self._write_reg(0x07, 0x00)
        self._write_reg(0x3F, 0x80)
        self._write_reg(0x3F, 0x00)
        utime.sleep_ms(10)
        self.set_mode(mode)

    def _write_reg(self, reg, val):
        self._buf1[0] = val & 0xFF
        self._i2c.writeto_mem(BNO055_ADDR, reg, self._buf1)

    def set_mode(self, mode):
        self._mode = mode
        self._write_reg(0x3D, mode)
        utime.sleep_ms(200)

    def reset(self):
        self.__init__(mode=self._mode)

    def _read_temperature(self, target):
        self._i2c.readfrom_mem_into(BNO055_ADDR, target, self._buf1)
        t = self._buf1[0]
        return t - 256 if t > 127 else t

    def _read_quaternion(self, target):
        self._i2c.readfrom_mem_into(BNO055_ADDR, target, self._buf8)
        s = self._SCALE[QUATERNION]
        w, x, y, z = ustruct.unpack("<hhhh", self._buf8)
        return w * s, x * s, y * s, z * s

    def _read_vector(self, target):
        s = self._SCALE.get(target)
        if s is None:
            raise ValueError("Invalid sensor target: {}".format(target))
        self._i2c.readfrom_mem_into(BNO055_ADDR, target, self._buf6)
        x, y, z = ustruct.unpack("<hhh", self._buf6)
        return x * s, y * s, z * s

    def calibration(self):
        self._i2c.readfrom_mem_into(BNO055_ADDR, 0x35, self._buf1)
        data = self._buf1[0]
        return (data >> 6) & 0x03, (data >> 4) & 0x03, (data >> 2) & 0x03, data & 0x03

    def is_calibrated(self):
        sys_cal, gyro, accel, mag = self.calibration()
        return sys_cal == 3 and gyro == 3 and accel == 3 and mag == 3

    def read(self, target=EULER):
        if target == TEMPERATURE:
            return self._read_temperature(target)
        if target == QUATERNION:
            return self._read_quaternion(target)
        return self._read_vector(target)

    @property
    def euler(self):
        return self._read_vector(EULER)

    @property
    def quaternion(self):
        return self._read_quaternion(QUATERNION)

    @property
    def acceleration(self):
        return self._read_vector(ACCELERATION)

    @property
    def magnetic(self):
        return self._read_vector(MAGNETIC)

    @property
    def gyroscope(self):
        return self._read_vector(GYROSCOPE)

    @property
    def linear_acceleration(self):
        return self._read_vector(ACCEL_LINEAR)

    @property
    def gravity(self):
        return self._read_vector(ACCEL_GRAVITY)

    @property
    def temperature(self):
        return self._read_temperature(TEMPERATURE)

gc.collect()
