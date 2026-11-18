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

    # UNIT_SEL = 0x06 기준 (모든 각도/각속도 단위를 라디안으로 통일):
    # Accel = m/s^2 (100 LSB), Mag = uT (16 LSB),
    # Gyro = rad/s (900 LSB), Euler = rad (900 LSB), Temp = Celsius
    _RAD_SCALE = 1.0 / 900.0

    _SCALE = {
        ACCELERATION: 0.01,
        MAGNETIC: 0.0625,
        GYROSCOPE: _RAD_SCALE,
        EULER: _RAD_SCALE,
        QUATERNION: 1.0 / (1 << 14),
        ACCEL_LINEAR: 0.01,
        ACCEL_GRAVITY: 0.01,
    }

    def __init__(self, i2c=None, addr=0x28, reset=False):
        self._i2c = i2c if i2c is not None else machine.I2C(1, freq=100000)
        self._addr = addr

        # 단일 8바이트 버퍼와 memoryview 슬라이스로 XBee RAM 절약
        self._buf8 = bytearray(8)
        mv = memoryview(self._buf8)
        self._buf1 = mv[:1]
        self._buf6 = mv[:6]

        self._init_sensor(_NDOF_MODE, reset)

    def _wait_ready(self, retries=40, delay_ms=25):
        for _ in range(retries):
            try:
                if self._read_byte(_CHIP_ID_ADDR) == _BNO055_ID:
                    return
            except OSError:
                pass
            utime.sleep_ms(delay_ms)
        raise RuntimeError("Failed to find BNO055 sensor")

    def _init_sensor(self, mode, reset):
        try:
            self._write_reg(_PAGE_ID_ADDR, 0x00)
        except OSError:
            pass

        self._wait_ready(retries=15, delay_ms=40)
        self.set_mode(_CONFIG_MODE)

        if reset:
            try:
                self._write_reg(_SYS_TRIGGER_ADDR, 0x20)
            except OSError:
                pass
            utime.sleep_ms(650)
            self._wait_ready(retries=25, delay_ms=20)

        self._write_reg(_PAGE_ID_ADDR, 0x00)
        self._write_reg(_PWR_MODE_ADDR, _POWER_NORMAL)
        utime.sleep_ms(10)

        # 0x06: Accel=m/s^2, Gyro=rad/s, Euler=rad, Temp=Celsius
        self._write_reg(_UNIT_SEL_ADDR, 0x06)
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
            raise ValueError("Invalid target")
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
