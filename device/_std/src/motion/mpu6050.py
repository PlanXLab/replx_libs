# @package: mpu6050
# @version: 3.0
# @type: device-std
# @category: motion
# @sensor_type: D
# @interface: I2C
# @depends: i2c
# @platforms: *
# @tags: imu, 6dof, accelerometer, gyroscope, dmp, quaternion, euler, tilt, mpu6050
# @author: PlanXLab Development Team

import math
import time
from micropython import const
from i2c import I2CController

# Register addresses
_RA_XA_OFFS_H       = const(0x06)
_RA_YA_OFFS_H       = const(0x08)
_RA_ZA_OFFS_H       = const(0x0A)
_RA_SMPLRT_DIV      = const(0x19)
_RA_XG_OFFS_USRH    = const(0x13)
_RA_YG_OFFS_USRH    = const(0x15)
_RA_ZG_OFFS_USRH    = const(0x17)
_RA_CONFIG          = const(0x1A)
_RA_GYRO_CONFIG     = const(0x1B)
_RA_ACCEL_CONFIG    = const(0x1C)
_RA_FIFO_EN         = const(0x23)
_RA_INT_ENABLE      = const(0x38)
_RA_INT_STATUS      = const(0x3A)
_RA_ACCEL_XOUT_H    = const(0x3B)
_RA_GYRO_XOUT_H     = const(0x43)
_RA_SIGNAL_PATH_RST = const(0x68)
_RA_USER_CTRL       = const(0x6A)
_RA_PWR_MGMT_1      = const(0x6B)
_RA_PWR_MGMT_2      = const(0x6C)
_RA_BANK_SEL        = const(0x6D)
_RA_MEM_START_ADDR  = const(0x6E)
_RA_MEM_R_W         = const(0x6F)
_RA_DMP_CFG_1       = const(0x70)
_RA_DMP_CFG_2       = const(0x71)
_RA_FIFO_COUNTH     = const(0x72)
_RA_FIFO_R_W        = const(0x74)
_RA_WHO_AM_I        = const(0x75)

# Bit positions
_BIT_DMP_EN         = const(7)
_BIT_FIFO_EN        = const(6)
_BIT_DMP_RST        = const(3)
_BIT_FIFO_RST       = const(2)

# Conversion constants
_ACC_LSB_PER_G      = 4096.0  
_DMP_ACC_LSB_PER_G  = 2048.0
_G0                 = 9.80665
_GYR_LSB_PER_DPS    = 16.4
_DPS_TO_RAD_S       = 0.017453292519943295
_DMP_PACKET_SIZE    = const(42)
_FIFO_CAPACITY      = const(1024)
_QUAT_NORM_MIN      = 0.25
_QUAT_NORM_MAX      = 2.25
_QUAT_JUMP_DOT_MIN  = 0.65
_TILT_ACCEL_MIN     = _G0 * 0.25
_TILT_ACCEL_MAX     = _G0 * 2.25
_ANGLE_ZERO_EPS     = 1.0e-3
_YAW_GYRO_DEADBAND  = 2.5 * _DPS_TO_RAD_S
_ACCEL_OFFSET_TEST_DELTA = const(256)
_ACCEL_OFFSET_SAMPLES = const(64)
_ACCEL_OFFSET_DELAY_MS = const(2)
_ACCEL_OFFSET_SETTLE_MS = const(50)
_ACCEL_OFFSET_MIN_COUNTS = 128.0
_ACCEL_OFFSET_SCALE_MIN = 512.0
_ACCEL_OFFSET_SCALE_MAX = 8192.0
_ACCEL_OFFSET_REG_SETS = (
    (_RA_XA_OFFS_H, _RA_YA_OFFS_H, _RA_ZA_OFFS_H),
    (0x77, 0x7A, 0x7D),
)

# DMP firmware (InvenSense DMP 6.12)
_DMP_FW_BYTES = bytes([
        0xFB, 0x00, 0x00, 0x3E, 0x00, 0x0B, 0x00, 0x36, 0x00, 0x01, 0x00, 0x02, 0x00, 0x03, 0x00, 0x00,
        0x00, 0x65, 0x00, 0x54, 0xFF, 0xEF, 0x00, 0x00, 0xFA, 0x80, 0x00, 0x0B, 0x12, 0x82, 0x00, 0x01,
        0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x28, 0x00, 0x00, 0xFF, 0xFF, 0x45, 0x81, 0xFF, 0xFF, 0xFA, 0x72, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x03, 0xE8, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x7F, 0xFF, 0xFF, 0xFE, 0x80, 0x01,
        0x00, 0x1B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x3E, 0x03, 0x30, 0x40, 0x00, 0x00, 0x00, 0x02, 0xCA, 0xE3, 0x09, 0x3E, 0x80, 0x00, 0x00,
        0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x60, 0x00, 0x00, 0x00,
        0x41, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x0B, 0x2A, 0x00, 0x00, 0x16, 0x55, 0x00, 0x00, 0x21, 0x82,
        0xFD, 0x87, 0x26, 0x50, 0xFD, 0x80, 0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00, 0x05, 0x80, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00,
        0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x6F, 0x00, 0x02, 0x65, 0x32, 0x00, 0x00, 0x5E, 0xC0,
        0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0xFB, 0x8C, 0x6F, 0x5D, 0xFD, 0x5D, 0x08, 0xD9, 0x00, 0x7C, 0x73, 0x3B, 0x00, 0x6C, 0x12, 0xCC,
        0x32, 0x00, 0x13, 0x9D, 0x32, 0x00, 0xD0, 0xD6, 0x32, 0x00, 0x08, 0x00, 0x40, 0x00, 0x01, 0xF4,
        0xFF, 0xE6, 0x80, 0x79, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xD0, 0xD6, 0x00, 0x00, 0x27, 0x10,

        0xFB, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x00,
        0x00, 0x00, 0xFA, 0x36, 0xFF, 0xBC, 0x30, 0x8E, 0x00, 0x05, 0xFB, 0xF0, 0xFF, 0xD9, 0x5B, 0xC8,
        0xFF, 0xD0, 0x9A, 0xBE, 0x00, 0x00, 0x10, 0xA9, 0xFF, 0xF4, 0x1E, 0xB2, 0x00, 0xCE, 0xBB, 0xF7,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x04, 0x00, 0x02, 0x00, 0x02, 0x02, 0x00, 0x00, 0x0C,
        0xFF, 0xC2, 0x80, 0x00, 0x00, 0x01, 0x80, 0x00, 0x00, 0xCF, 0x80, 0x00, 0x40, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x00, 0x14,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x03, 0x3F, 0x68, 0xB6, 0x79, 0x35, 0x28, 0xBC, 0xC6, 0x7E, 0xD1, 0x6C,
        0x80, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0xB2, 0x6A, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3F, 0xF0, 0x00, 0x00, 0x00, 0x30,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x25, 0x4D, 0x00, 0x2F, 0x70, 0x6D, 0x00, 0x00, 0x05, 0xAE, 0x00, 0x0C, 0x02, 0xD0,

        0x00, 0x00, 0x00, 0x00, 0x00, 0x65, 0x00, 0x54, 0xFF, 0xEF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x01, 0x00, 0x00, 0x44, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x00, 0x00, 0x00, 0x01, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x65, 0x00, 0x00, 0x00, 0x54, 0x00, 0x00, 0xFF, 0xEF, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x1B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00,
        0x00, 0x1B, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

        0xD8, 0xDC, 0xBA, 0xA2, 0xF1, 0xDE, 0xB2, 0xB8, 0xB4, 0xA8, 0x81, 0x91, 0xF7, 0x4A, 0x90, 0x7F,
        0x91, 0x6A, 0xF3, 0xF9, 0xDB, 0xA8, 0xF9, 0xB0, 0xBA, 0xA0, 0x80, 0xF2, 0xCE, 0x81, 0xF3, 0xC2,
        0xF1, 0xC1, 0xF2, 0xC3, 0xF3, 0xCC, 0xA2, 0xB2, 0x80, 0xF1, 0xC6, 0xD8, 0x80, 0xBA, 0xA7, 0xDF,
        0xDF, 0xDF, 0xF2, 0xA7, 0xC3, 0xCB, 0xC5, 0xB6, 0xF0, 0x87, 0xA2, 0x94, 0x24, 0x48, 0x70, 0x3C,
        0x95, 0x40, 0x68, 0x34, 0x58, 0x9B, 0x78, 0xA2, 0xF1, 0x83, 0x92, 0x2D, 0x55, 0x7D, 0xD8, 0xB1,
        0xB4, 0xB8, 0xA1, 0xD0, 0x91, 0x80, 0xF2, 0x70, 0xF3, 0x70, 0xF2, 0x7C, 0x80, 0xA8, 0xF1, 0x01,
        0xB0, 0x98, 0x87, 0xD9, 0x43, 0xD8, 0x86, 0xC9, 0x88, 0xBA, 0xA1, 0xF2, 0x0E, 0xB8, 0x97, 0x80,
        0xF1, 0xA9, 0xDF, 0xDF, 0xDF, 0xAA, 0xDF, 0xDF, 0xDF, 0xF2, 0xAA, 0xC5, 0xCD, 0xC7, 0xA9, 0x0C,
        0xC9, 0x2C, 0x97, 0x97, 0x97, 0x97, 0xF1, 0xA9, 0x89, 0x26, 0x46, 0x66, 0xB0, 0xB4, 0xBA, 0x80,
        0xAC, 0xDE, 0xF2, 0xCA, 0xF1, 0xB2, 0x8C, 0x02, 0xA9, 0xB6, 0x98, 0x00, 0x89, 0x0E, 0x16, 0x1E,
        0xB8, 0xA9, 0xB4, 0x99, 0x2C, 0x54, 0x7C, 0xB0, 0x8A, 0xA8, 0x96, 0x36, 0x56, 0x76, 0xF1, 0xB9,
        0xAF, 0xB4, 0xB0, 0x83, 0xC0, 0xB8, 0xA8, 0x97, 0x11, 0xB1, 0x8F, 0x98, 0xB9, 0xAF, 0xF0, 0x24,
        0x08, 0x44, 0x10, 0x64, 0x18, 0xF1, 0xA3, 0x29, 0x55, 0x7D, 0xAF, 0x83, 0xB5, 0x93, 0xAF, 0xF0,
        0x00, 0x28, 0x50, 0xF1, 0xA3, 0x86, 0x9F, 0x61, 0xA6, 0xDA, 0xDE, 0xDF, 0xD9, 0xFA, 0xA3, 0x86,
        0x96, 0xDB, 0x31, 0xA6, 0xD9, 0xF8, 0xDF, 0xBA, 0xA6, 0x8F, 0xC2, 0xC5, 0xC7, 0xB2, 0x8C, 0xC1,
        0xB8, 0xA2, 0xDF, 0xDF, 0xDF, 0xA3, 0xDF, 0xDF, 0xDF, 0xD8, 0xD8, 0xF1, 0xB8, 0xA8, 0xB2, 0x86,

        0xB4, 0x98, 0x0D, 0x35, 0x5D, 0xB8, 0xAA, 0x98, 0xB0, 0x87, 0x2D, 0x35, 0x3D, 0xB2, 0xB6, 0xBA,
        0xAF, 0x8C, 0x96, 0x19, 0x8F, 0x9F, 0xA7, 0x0E, 0x16, 0x1E, 0xB4, 0x9A, 0xB8, 0xAA, 0x87, 0x2C,
        0x54, 0x7C, 0xB9, 0xA3, 0xDE, 0xDF, 0xDF, 0xA3, 0xB1, 0x80, 0xF2, 0xC4, 0xCD, 0xC9, 0xF1, 0xB8,
        0xA9, 0xB4, 0x99, 0x83, 0x0D, 0x35, 0x5D, 0x89, 0xB9, 0xA3, 0x2D, 0x55, 0x7D, 0xB5, 0x93, 0xA3,
        0x0E, 0x16, 0x1E, 0xA9, 0x2C, 0x54, 0x7C, 0xB8, 0xB4, 0xB0, 0xF1, 0x97, 0x83, 0xA8, 0x11, 0x84,
        0xA5, 0x09, 0x98, 0xA3, 0x83, 0xF0, 0xDA, 0x24, 0x08, 0x44, 0x10, 0x64, 0x18, 0xD8, 0xF1, 0xA5,
        0x29, 0x55, 0x7D, 0xA5, 0x85, 0x95, 0x02, 0x1A, 0x2E, 0x3A, 0x56, 0x5A, 0x40, 0x48, 0xF9, 0xF3,
        0xA3, 0xD9, 0xF8, 0xF0, 0x98, 0x83, 0x24, 0x08, 0x44, 0x10, 0x64, 0x18, 0x97, 0x82, 0xA8, 0xF1,
        0x11, 0xF0, 0x98, 0xA2, 0x24, 0x08, 0x44, 0x10, 0x64, 0x18, 0xDA, 0xF3, 0xDE, 0xD8, 0x83, 0xA5,
        0x94, 0x01, 0xD9, 0xA3, 0x02, 0xF1, 0xA2, 0xC3, 0xC5, 0xC7, 0xD8, 0xF1, 0x84, 0x92, 0xA2, 0x4D,
        0xDA, 0x2A, 0xD8, 0x48, 0x69, 0xD9, 0x2A, 0xD8, 0x68, 0x55, 0xDA, 0x32, 0xD8, 0x50, 0x71, 0xD9,
        0x32, 0xD8, 0x70, 0x5D, 0xDA, 0x3A, 0xD8, 0x58, 0x79, 0xD9, 0x3A, 0xD8, 0x78, 0x93, 0xA3, 0x4D,
        0xDA, 0x2A, 0xD8, 0x48, 0x69, 0xD9, 0x2A, 0xD8, 0x68, 0x55, 0xDA, 0x32, 0xD8, 0x50, 0x71, 0xD9,
        0x32, 0xD8, 0x70, 0x5D, 0xDA, 0x3A, 0xD8, 0x58, 0x79, 0xD9, 0x3A, 0xD8, 0x78, 0xA8, 0x8A, 0x9A,
        0xF0, 0x28, 0x50, 0x78, 0x9E, 0xF3, 0x88, 0x18, 0xF1, 0x9F, 0x1D, 0x98, 0xA8, 0xD9, 0x08, 0xD8,
        0xC8, 0x9F, 0x12, 0x9E, 0xF3, 0x15, 0xA8, 0xDA, 0x12, 0x10, 0xD8, 0xF1, 0xAF, 0xC8, 0x97, 0x87,

        0x34, 0xB5, 0xB9, 0x94, 0xA4, 0x21, 0xF3, 0xD9, 0x22, 0xD8, 0xF2, 0x2D, 0xF3, 0xD9, 0x2A, 0xD8,
        0xF2, 0x35, 0xF3, 0xD9, 0x32, 0xD8, 0x81, 0xA4, 0x60, 0x60, 0x61, 0xD9, 0x61, 0xD8, 0x6C, 0x68,
        0x69, 0xD9, 0x69, 0xD8, 0x74, 0x70, 0x71, 0xD9, 0x71, 0xD8, 0xB1, 0xA3, 0x84, 0x19, 0x3D, 0x5D,
        0xA3, 0x83, 0x1A, 0x3E, 0x5E, 0x93, 0x10, 0x30, 0x81, 0x10, 0x11, 0xB8, 0xB0, 0xAF, 0x8F, 0x94,
        0xF2, 0xDA, 0x3E, 0xD8, 0xB4, 0x9A, 0xA8, 0x87, 0x29, 0xDA, 0xF8, 0xD8, 0x87, 0x9A, 0x35, 0xDA,
        0xF8, 0xD8, 0x87, 0x9A, 0x3D, 0xDA, 0xF8, 0xD8, 0xB1, 0xB9, 0xA4, 0x98, 0x85, 0x02, 0x2E, 0x56,
        0xA5, 0x81, 0x00, 0x0C, 0x14, 0xA3, 0x97, 0xB0, 0x8A, 0xF1, 0x2D, 0xD9, 0x28, 0xD8, 0x4D, 0xD9,
        0x48, 0xD8, 0x6D, 0xD9, 0x68, 0xD8, 0xB1, 0x84, 0x0D, 0xDA, 0x0E, 0xD8, 0xA3, 0x29, 0x83, 0xDA,
        0x2C, 0x0E, 0xD8, 0xA3, 0x84, 0x49, 0x83, 0xDA, 0x2C, 0x4C, 0x0E, 0xD8, 0xB8, 0xB0, 0xA8, 0x8A,
        0x9A, 0xF5, 0x20, 0xAA, 0xDA, 0xDF, 0xD8, 0xA8, 0x40, 0xAA, 0xD0, 0xDA, 0xDE, 0xD8, 0xA8, 0x60,
        0xAA, 0xDA, 0xD0, 0xDF, 0xD8, 0xF1, 0x97, 0x86, 0xA8, 0x31, 0x9B, 0x06, 0x99, 0x07, 0xAB, 0x97,
        0x28, 0x88, 0x9B, 0xF0, 0x0C, 0x20, 0x14, 0x40, 0xB8, 0xB0, 0xB4, 0xA8, 0x8C, 0x9C, 0xF0, 0x04,
        0x28, 0x51, 0x79, 0x1D, 0x30, 0x14, 0x38, 0xB2, 0x82, 0xAB, 0xD0, 0x98, 0x2C, 0x50, 0x50, 0x78,
        0x78, 0x9B, 0xF1, 0x1A, 0xB0, 0xF0, 0x8A, 0x9C, 0xA8, 0x29, 0x51, 0x79, 0x8B, 0x29, 0x51, 0x79,
        0x8A, 0x24, 0x70, 0x59, 0x8B, 0x20, 0x58, 0x71, 0x8A, 0x44, 0x69, 0x38, 0x8B, 0x39, 0x40, 0x68,
        0x8A, 0x64, 0x48, 0x31, 0x8B, 0x30, 0x49, 0x60, 0xA5, 0x88, 0x20, 0x09, 0x71, 0x58, 0x44, 0x68,

        0x11, 0x39, 0x64, 0x49, 0x30, 0x19, 0xF1, 0xAC, 0x00, 0x2C, 0x54, 0x7C, 0xF0, 0x8C, 0xA8, 0x04,
        0x28, 0x50, 0x78, 0xF1, 0x88, 0x97, 0x26, 0xA8, 0x59, 0x98, 0xAC, 0x8C, 0x02, 0x26, 0x46, 0x66,
        0xF0, 0x89, 0x9C, 0xA8, 0x29, 0x51, 0x79, 0x24, 0x70, 0x59, 0x44, 0x69, 0x38, 0x64, 0x48, 0x31,
        0xA9, 0x88, 0x09, 0x20, 0x59, 0x70, 0xAB, 0x11, 0x38, 0x40, 0x69, 0xA8, 0x19, 0x31, 0x48, 0x60,
        0x8C, 0xA8, 0x3C, 0x41, 0x5C, 0x20, 0x7C, 0x00, 0xF1, 0x87, 0x98, 0x19, 0x86, 0xA8, 0x6E, 0x76,
        0x7E, 0xA9, 0x99, 0x88, 0x2D, 0x55, 0x7D, 0x9E, 0xB9, 0xA3, 0x8A, 0x22, 0x8A, 0x6E, 0x8A, 0x56,
        0x8A, 0x5E, 0x9F, 0xB1, 0x83, 0x06, 0x26, 0x46, 0x66, 0x0E, 0x2E, 0x4E, 0x6E, 0x9D, 0xB8, 0xAD,
        0x00, 0x2C, 0x54, 0x7C, 0xF2, 0xB1, 0x8C, 0xB4, 0x99, 0xB9, 0xA3, 0x2D, 0x55, 0x7D, 0x81, 0x91,
        0xAC, 0x38, 0xAD, 0x3A, 0xB5, 0x83, 0x91, 0xAC, 0x2D, 0xD9, 0x28, 0xD8, 0x4D, 0xD9, 0x48, 0xD8,
        0x6D, 0xD9, 0x68, 0xD8, 0x8C, 0x9D, 0xAE, 0x29, 0xD9, 0x04, 0xAE, 0xD8, 0x51, 0xD9, 0x04, 0xAE,
        0xD8, 0x79, 0xD9, 0x04, 0xD8, 0x81, 0xF3, 0x9D, 0xAD, 0x00, 0x8D, 0xAE, 0x19, 0x81, 0xAD, 0xD9,
        0x01, 0xD8, 0xF2, 0xAE, 0xDA, 0x26, 0xD8, 0x8E, 0x91, 0x29, 0x83, 0xA7, 0xD9, 0xAD, 0xAD, 0xAD,
        0xAD, 0xF3, 0x2A, 0xD8, 0xD8, 0xF1, 0xB0, 0xAC, 0x89, 0x91, 0x3E, 0x5E, 0x76, 0xF3, 0xAC, 0x2E,
        0x2E, 0xF1, 0xB1, 0x8C, 0x5A, 0x9C, 0xAC, 0x2C, 0x28, 0x28, 0x28, 0x9C, 0xAC, 0x30, 0x18, 0xA8,
        0x98, 0x81, 0x28, 0x34, 0x3C, 0x97, 0x24, 0xA7, 0x28, 0x34, 0x3C, 0x9C, 0x24, 0xF2, 0xB0, 0x89,
        0xAC, 0x91, 0x2C, 0x4C, 0x6C, 0x8A, 0x9B, 0x2D, 0xD9, 0xD8, 0xD8, 0x51, 0xD9, 0xD8, 0xD8, 0x79,

        0xD9, 0xD8, 0xD8, 0xF1, 0x9E, 0x88, 0xA3, 0x31, 0xDA, 0xD8, 0xD8, 0x91, 0x2D, 0xD9, 0x28, 0xD8,
        0x4D, 0xD9, 0x48, 0xD8, 0x6D, 0xD9, 0x68, 0xD8, 0xB1, 0x83, 0x93, 0x35, 0x3D, 0x80, 0x25, 0xDA,
        0xD8, 0xD8, 0x85, 0x69, 0xDA, 0xD8, 0xD8, 0xB4, 0x93, 0x81, 0xA3, 0x28, 0x34, 0x3C, 0xF3, 0xAB,
        0x8B, 0xF8, 0xA3, 0x91, 0xB6, 0x09, 0xB4, 0xD9, 0xAB, 0xDE, 0xFA, 0xB0, 0x87, 0x9C, 0xB9, 0xA3,
        0xDD, 0xF1, 0xA3, 0xA3, 0xA3, 0xA3, 0x95, 0xF1, 0xA3, 0xA3, 0xA3, 0x9D, 0xF1, 0xA3, 0xA3, 0xA3,
        0xA3, 0xF2, 0xA3, 0xB4, 0x90, 0x80, 0xF2, 0xA3, 0xA3, 0xA3, 0xA3, 0xA3, 0xA3, 0xA3, 0xA3, 0xA3,
        0xA3, 0xB2, 0xA3, 0xA3, 0xA3, 0xA3, 0xA3, 0xA3, 0xB0, 0x87, 0xB5, 0x99, 0xF1, 0xA3, 0xA3, 0xA3,
        0x98, 0xF1, 0xA3, 0xA3, 0xA3, 0xA3, 0x97, 0xA3, 0xA3, 0xA3, 0xA3, 0xF3, 0x9B, 0xA3, 0xA3, 0xDC,
        0xB9, 0xA7, 0xF1, 0x26, 0x26, 0x26, 0xD8, 0xD8, 0xFF
])

_DMP_CFG_BYTES = bytes([
        0x03, 0x7B, 0x03, 0x4C, 0xCD, 0x6C,
        0x03, 0xAB, 0x03, 0x36, 0x56, 0x76,
        0x00, 0x68, 0x04, 0x02, 0xCB, 0x47, 0xA2,
        0x02, 0x18, 0x04, 0x00, 0x05, 0x8B, 0xC1,
        0x01, 0x0C, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x03, 0x7F, 0x06, 0x0C, 0xC9, 0x2C, 0x97, 0x97, 0x97,
        0x03, 0x89, 0x03, 0x26, 0x46, 0x66,
        0x00, 0x6C, 0x02, 0x20, 0x00,
        0x02, 0x40, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x02, 0x44, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x02, 0x48, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x02, 0x4C, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x02, 0x50, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x02, 0x54, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x02, 0x58, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x02, 0x5C, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x02, 0xBC, 0x04, 0x00, 0x00, 0x00, 0x00,
        0x01, 0xEC, 0x04, 0x00, 0x00, 0x40, 0x00,
        0x03, 0x7F, 0x06, 0x0C, 0xC9, 0x2C, 0x97, 0x97, 0x97,
        0x04, 0x02, 0x03, 0x0D, 0x35, 0x5D,
        0x04, 0x09, 0x04, 0x87, 0x2D, 0x35, 0x3D,
        0x00, 0xA3, 0x01, 0x00,

        0x00, 0x00, 0x00, 0x01,

        0x07, 0x86, 0x01, 0xFE,
        0x07, 0x41, 0x05, 0xF1, 0x20, 0x28, 0x30, 0x38,
        0x07, 0x7E, 0x01, 0x30,
        0x07, 0x46, 0x01, 0x9A,
        0x07, 0x47, 0x04, 0xF1, 0x28, 0x30, 0x38,
        0x07, 0x6C, 0x04, 0xF1, 0x28, 0x30, 0x38,
        0x02, 0x16, 0x02, 0x00, 0x01
])

_DMP_UPD_BYTES = bytes([
        0x01, 0xB2, 0x02, 0xFF, 0xFF,
        0x01, 0x90, 0x04, 0x09, 0x23, 0xA1, 0x35,
        0x01, 0x6A, 0x02, 0x06, 0x00,
        0x01, 0x60, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x60, 0x04, 0x40, 0x00, 0x00, 0x00,
        0x01, 0x62, 0x02, 0x00, 0x00,
        0x00, 0x60, 0x04, 0x00, 0x40, 0x00, 0x00
])


class MPU6050:
    DLPF_DIV8K_256HZ       = 0
    DLPF_DIV1K_98HZ        = 2
    DLPF_DIV1K_42HZ        = 3
    SIMPLERT_DIV8K_1KHz    = 7
    SIMPLERT_DIV1K_200Hz   = 4
    SIMPLERT_DIV1K_100Hz   = 9

    class Mode:
        DMP_STABLE   = "dmp_stable"
        DMP_FAST     = "dmp_fast"
        RAW_BALANCED = "raw_balanced"
        RAW_FAST     = "raw_fast"

    _MODE_PRESETS = {
        Mode.DMP_STABLE:   (DLPF_DIV1K_42HZ,  SIMPLERT_DIV1K_100Hz, True),
        Mode.DMP_FAST:     (DLPF_DIV1K_98HZ,  SIMPLERT_DIV1K_200Hz, True),
        Mode.RAW_BALANCED: (DLPF_DIV1K_42HZ,  SIMPLERT_DIV1K_200Hz, False),
        Mode.RAW_FAST:     (DLPF_DIV8K_256HZ, SIMPLERT_DIV8K_1KHz,  False),
    }

    _IDENTITY_MATRIX = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    _DEFAULT_REMAPS = {
        'raw': 'xyz',
        'enu': 'xyz',
        'flu': 'y-xz',
        'ned': 'yx-z',
    }

    def __init__(self, i2c, *, addr=0x68, mode=Mode.RAW_BALANCED, coord='flu', remap='-z-xy'):
        self._i2c  = i2c
        self._i2c.set_retry_policy(retries=3, delay_us=1000)
        self._addr = int(addr)
        self._pkt_size = _DMP_PACKET_SIZE
        self._yaw = 0.0
        self._yaw_last_us = time.ticks_us()
        coord = coord.lower()
        if coord not in self._DEFAULT_REMAPS:
            raise ValueError("coord must be 'raw', 'enu', 'flu', or 'ned'")
        self._coord = coord
        self._remap = remap
        coord_matrix = self._parse_axis_remap(self._DEFAULT_REMAPS[coord])
        self._remap_matrix = self._IDENTITY_MATRIX if remap is None else self._parse_axis_remap(remap)
        self._body_matrix = self._mat_mul(coord_matrix, self._remap_matrix)
        self._body_matrix_t = self._mat_transpose(self._body_matrix)
        self._gravity_world = (0.0, 0.0, -_G0 if coord == 'ned' else _G0)

        self._ensure_i2c_device()

        self._write_u8_checked(_RA_PWR_MGMT_1, 0x80, 'reset')
        time.sleep_ms(100)
        self._write_u8_checked(_RA_SIGNAL_PATH_RST, 0x07, 'signal path reset')
        time.sleep_ms(10)
        self._write_u8_checked(_RA_PWR_MGMT_1, 0x01, 'wake')
        self._write_u8_checked(_RA_PWR_MGMT_2, 0x00, 'enable axes')
        time.sleep_ms(10)

        who = self._read_u8_checked(_RA_WHO_AM_I, 'identity check')
        if who not in (0x68, 0x69, 0x70):
            raise RuntimeError("MPU6050 not found (WHO_AM_I=0x%02X)" % who)
        self._who_am_i = who

        if mode not in self._MODE_PRESETS:
            raise ValueError("Unknown mode: %r" % (mode,))
        dlpf, smplrt_div, use_dmp = self._MODE_PRESETS[mode]
        self._use_dmp = bool(use_dmp)

        self._write_u8_checked(_RA_CONFIG, dlpf, 'configure DLPF')
        cur = self._read_u8_checked(_RA_GYRO_CONFIG, 'read gyro range')
        self._write_u8_checked(_RA_GYRO_CONFIG, (cur & ~0x18) | (3 << 3), 'configure gyro range')   # ±2000 dps
        cur = self._read_u8_checked(_RA_ACCEL_CONFIG, 'read accel range')
        self._write_u8_checked(_RA_ACCEL_CONFIG, (cur & ~0x18) | (2 << 3), 'configure accel range')  # ±8 g
        self._write_u8_checked(_RA_SMPLRT_DIV, smplrt_div, 'configure sample rate')

        self._write_u8_checked(_RA_INT_ENABLE, 0x00, 'disable interrupts')
        self._write_u8_checked(_RA_USER_CTRL, 0x00, 'disable FIFO and DMP')
        self._write_u8_checked(_RA_FIFO_EN, 0x00, 'disable FIFO sensors')

        self._acc_bias = [0.0, 0.0, 0.0] 
        self._gyr_bias = [0.0, 0.0, 0.0] 
        self._gyr_raw_bias = [0.0, 0.0, 0.0]
        self._dmp_accel = (0.0, 0.0, 0.0) 
        self._last_raw_quat = (1.0, 0.0, 0.0, 0.0)
        self._last_quat = (1.0, 0.0, 0.0, 0.0)
        self._last_tilt = (0.0, 0.0)
        self._quat_ready = False
        self._accel_offset_regs = None
        self._accel_offset_scales = None
        self._buf6 = bytearray(6)
        self._buf14 = bytearray(14)
        self._buf42 = bytearray(self._pkt_size)

        if self._use_dmp:
            self._accel_offset_regs, self._accel_offset_scales = self._measure_accel_offset_scale()

        self._quick_bias()

        if self._use_dmp:
            self._apply_gyro_offsets()
            self._apply_accel_offsets()
            self._quick_gyro_bias()
            self._load_dmp_firmware()
            self._flush_fifo()
            self._wait_for_dmp_packet()
            self.zero_heading()

    def _ensure_i2c_device(self):
        try:
            devices = self._i2c.scan()
        except OSError as err:
            raise RuntimeError(
                "MPU6050 I2C scan failed on SDA=%d SCL=%d freq=%d: %r"
                % (self._sda, self._scl, self._freq, err)
            )

        if self._addr not in devices:
            raise RuntimeError(
                "MPU6050 not found at 0x%02X on SDA=%d SCL=%d; I2C scan found: %s"
                % (self._addr, self._sda, self._scl, self._format_i2c_devices(devices))
            )

        who = self._read_u8_checked(_RA_WHO_AM_I, 'identity check before reset')
        if who not in (0x68, 0x69, 0x70):
            raise RuntimeError(
                "MPU6050 not found at 0x%02X (WHO_AM_I=0x%02X)"
                % (self._addr, who)
            )

    def _write_u8_checked(self, reg, value, phase):
        try:
            self._i2c.write_u8(self._addr, reg, value)
        except OSError as err:
            raise RuntimeError(
                "MPU6050 I2C write failed during %s at addr=0x%02X reg=0x%02X "
                "on SDA=%d SCL=%d freq=%d: %r"
                % (phase, self._addr, reg, self._sda, self._scl, self._freq, err)
            )

    def _read_u8_checked(self, reg, phase):
        try:
            return self._i2c.read_u8(self._addr, reg)
        except OSError as err:
            raise RuntimeError(
                "MPU6050 I2C read failed during %s at addr=0x%02X reg=0x%02X "
                "on SDA=%d SCL=%d freq=%d: %r"
                % (phase, self._addr, reg, self._sda, self._scl, self._freq, err)
            )

    @staticmethod
    def _format_i2c_devices(devices):
        if not devices:
            return 'none'
        return ', '.join('0x%02X' % int(addr) for addr in devices)

    def deinit(self):
        self._i2c.write_u8(self._addr, _RA_INT_ENABLE, 0x00)
        self._i2c.write_u8(self._addr, _RA_USER_CTRL, 0x00)
        self._i2c.write_u8(self._addr, _RA_FIFO_EN, 0x00)
        time.sleep_ms(10)
        self._i2c.write_u8(self._addr, _RA_PWR_MGMT_1, 0x40)
        try: 
            self._i2c.deinit()
        except Exception: 
            pass

    @property
    def accel(self):
        x, y, z = self._read_accel_pcb()
        return self._apply_body_transform(x, y, z)

    @property
    def raw_accel(self):
        return self._read_accel_pcb()

    @property
    def gyro(self):
        x, y, z = self._read_gyro_pcb()
        return self._apply_body_transform(x, y, z)

    @property
    def raw_gyro(self):
        return self._read_gyro_pcb()

    def _read_accel_pcb(self):
        self._i2c.readfrom_mem_into(self._addr, _RA_ACCEL_XOUT_H, self._buf6)
        b = self._buf6
        ax = self._twos16(b[0],b[1])
        ay = self._twos16(b[2],b[3])
        az = self._twos16(b[4],b[5])
        ax_ms2 = (ax / _ACC_LSB_PER_G) * _G0
        ay_ms2 = (ay / _ACC_LSB_PER_G) * _G0
        az_ms2 = (az / _ACC_LSB_PER_G) * _G0
        x = ax_ms2 - self._acc_bias[0]
        y = ay_ms2 - self._acc_bias[1]
        z = az_ms2 - self._acc_bias[2]
        return (x, y, z)

    def _read_gyro_pcb(self):
        self._i2c.readfrom_mem_into(self._addr, _RA_GYRO_XOUT_H, self._buf6)
        b = self._buf6
        gx = self._twos16(b[0],b[1])
        gy = self._twos16(b[2],b[3])
        gz = self._twos16(b[4],b[5])
        gxd = (gx / _GYR_LSB_PER_DPS) * _DPS_TO_RAD_S
        gyd = (gy / _GYR_LSB_PER_DPS) * _DPS_TO_RAD_S
        gzd = (gz / _GYR_LSB_PER_DPS) * _DPS_TO_RAD_S
        x = gxd - self._gyr_bias[0]
        y = gyd - self._gyr_bias[1]
        z = gzd - self._gyr_bias[2]
        return (x, y, z)

    @property
    def quat(self):
        if not self._use_dmp:
            return (1.0, 0.0, 0.0, 0.0)

        pkt = self._read_dmp_packet()
        if pkt is None:
            self._restart_dmp_stream()
            pkt = self._read_dmp_packet(timeout_ms=300)
            if pkt is None:
                return self._last_quat

        q0 = self._twos32(pkt[0], pkt[1], pkt[2], pkt[3])
        q1 = self._twos32(pkt[4], pkt[5], pkt[6], pkt[7])
        q2 = self._twos32(pkt[8], pkt[9], pkt[10], pkt[11])
        q3 = self._twos32(pkt[12], pkt[13], pkt[14], pkt[15])
        
        dmp_ax = self._twos16(pkt[28], pkt[29])
        dmp_ay = self._twos16(pkt[32], pkt[33])
        dmp_az = self._twos16(pkt[36], pkt[37])
        dmp_accel = (
            (dmp_ax / _DMP_ACC_LSB_PER_G) * _G0,
            (dmp_ay / _DMP_ACC_LSB_PER_G) * _G0,
            (dmp_az / _DMP_ACC_LSB_PER_G) * _G0
        )
        
        if not (q0 | q1 | q2 | q3):
            return self._last_quat

        s = 1.0 / (1 << 30)
        q_raw = (q0*s, q1*s, q2*s, q3*s)
        n2 = q_raw[0]*q_raw[0] + q_raw[1]*q_raw[1] + q_raw[2]*q_raw[2] + q_raw[3]*q_raw[3]
        if n2 < _QUAT_NORM_MIN or n2 > _QUAT_NORM_MAX:
            self._restart_dmp_stream()
            return self._last_quat

        q_raw = self._q_normalize(q_raw)
        if self._quat_ready:
            lq = self._last_raw_quat
            dot = abs(q_raw[0]*lq[0] + q_raw[1]*lq[1] + q_raw[2]*lq[2] + q_raw[3]*lq[3])
            if dot < _QUAT_JUMP_DOT_MIN:
                return self._last_quat

        q = self._transform_quat(q_raw)
        if self._quat_ready:
            lq = self._last_quat
            if q[0]*lq[0] + q[1]*lq[1] + q[2]*lq[2] + q[3]*lq[3] < 0.0:
                q = (-q[0], -q[1], -q[2], -q[3])

        self._last_raw_quat = q_raw
        self._last_quat = q
        self._dmp_accel = dmp_accel
        self._update_yaw_from_gyro()
        self._quat_ready = True
        return self._last_quat

    @property
    def tilt(self):
        if self._use_dmp:
            _ = self.quat
            return self._tilt_from_accel(self._dmp_accel)

        return self._tilt_from_accel(self._read_accel_pcb())

    @property
    def euler(self):
        if not self._use_dmp:
            return (0.0, 0.0, 0.0)

        return self._euler_from_quat(self.quat)

    @property
    def linear(self):
        if not self._use_dmp:
            return (0.0, 0.0, 0.0)
        
        q = self.quat  
        return self._linear_from_quat(q, self._dmp_accel)

    def _linear_from_quat(self, q, accel):
        w, x, y, z = q
        ax, ay, az = self._apply_body_transform(accel[0], accel[1], accel[2])
        xx, yy, zz = x*x, y*y, z*z
        wx, wy, wz = w*x, w*y, w*z
        xy, xz, yz = x*y, x*z, y*z
        axw = (1-2*(yy+zz))*ax + 2*(xy+wz)*ay + 2*(xz-wy)*az
        ayw = 2*(xy-wz)*ax + (1-2*(xx+zz))*ay + 2*(yz+wx)*az
        azw = 2*(xz+wy)*ax + 2*(yz-wx)*ay + (1-2*(xx+yy))*az
        gxw, gyw, gzw = self._gravity_world
        return (axw - gxw, ayw - gyw, azw - gzw)

    def _euler_from_quat(self, q):
        roll, pitch = self._tilt_from_accel(self._dmp_accel)
        return (roll, pitch, self._clean_angle(self._yaw))

    def zero_heading(self):
        if self._use_dmp:
            _ = self.quat
        self._yaw = 0.0
        self._yaw_last_us = time.ticks_us()

    def _update_yaw_from_gyro(self):
        now = time.ticks_us()
        dt = time.ticks_diff(now, self._yaw_last_us) / 1000000.0
        self._yaw_last_us = now
        if dt <= 0.0 or dt > 0.5:
            return
        _, _, gz = self.gyro
        if -_YAW_GYRO_DEADBAND < gz < _YAW_GYRO_DEADBAND:
            return
        self._yaw = self._wrap_angle_raw(self._yaw + gz * dt)

    def _flush_fifo(self):
        user = self._i2c.read_u8(self._addr, _RA_USER_CTRL)
        self._i2c.write_u8(self._addr, _RA_USER_CTRL, user | (1 << _BIT_FIFO_RST))
        time.sleep_ms(2)

    def _restart_dmp_stream(self):
        user = self._i2c.read_u8(self._addr, _RA_USER_CTRL)
        self._i2c.write_u8(self._addr, _RA_USER_CTRL, user | (1 << _BIT_DMP_RST) | (1 << _BIT_FIFO_RST))
        time.sleep_ms(5)
        user = self._i2c.read_u8(self._addr, _RA_USER_CTRL)
        self._i2c.write_u8(self._addr, _RA_USER_CTRL, user | (1 << _BIT_DMP_EN) | (1 << _BIT_FIFO_EN))
        self._i2c.write_u8(self._addr, _RA_FIFO_EN, 0x00)
        time.sleep_ms(2)

    def _apply_gyro_offsets(self):
        offsets = (
            (_RA_XG_OFFS_USRH, self._gyr_raw_bias[0]),
            (_RA_YG_OFFS_USRH, self._gyr_raw_bias[1]),
            (_RA_ZG_OFFS_USRH, self._gyr_raw_bias[2]),
        )
        for reg, bias in offsets:
            self._write_i16(reg, self._clamp_i16(-int(round(bias))))
        self._gyr_bias = [0.0, 0.0, 0.0]

    def _measure_accel_offset_scale(self):
        for regs in _ACCEL_OFFSET_REG_SETS:
            try:
                scales = self._measure_accel_offset_scale_for_regs(regs)
            except OSError:
                scales = None
            if scales is not None:
                return regs, scales
        raise RuntimeError("MPU6050 accel offset registers are not responsive")

    def _measure_accel_offset_scale_for_regs(self, regs):
        originals = tuple(self._read_i16(reg) for reg in regs)
        scales = []
        try:
            base = self._average_accel_counts()
            for axis in range(3):
                reg = regs[axis]
                self._write_i16(reg, self._clamp_i16(originals[axis] + _ACCEL_OFFSET_TEST_DELTA))
                time.sleep_ms(_ACCEL_OFFSET_SETTLE_MS)
                changed = self._average_accel_counts()
                self._write_i16(reg, originals[axis])
                time.sleep_ms(_ACCEL_OFFSET_SETTLE_MS)

                delta = changed[axis] - base[axis]
                if -_ACCEL_OFFSET_MIN_COUNTS < delta < _ACCEL_OFFSET_MIN_COUNTS:
                    return None

                scale = abs((_ACCEL_OFFSET_TEST_DELTA * _ACC_LSB_PER_G) / delta)
                if scale < _ACCEL_OFFSET_SCALE_MIN or scale > _ACCEL_OFFSET_SCALE_MAX:
                    return None
                scales.append(scale)
        finally:
            for reg, original in zip(regs, originals):
                self._write_i16(reg, original)
        return (scales[0], scales[1], scales[2])

    def _average_accel_counts(self, n=_ACCEL_OFFSET_SAMPLES, delay_ms=_ACCEL_OFFSET_DELAY_MS):
        sx = sy = sz = 0.0
        b = self._buf6
        for _ in range(n):
            self._i2c.readfrom_mem_into(self._addr, _RA_ACCEL_XOUT_H, b)
            sx += self._twos16(b[0], b[1])
            sy += self._twos16(b[2], b[3])
            sz += self._twos16(b[4], b[5])
            time.sleep_ms(delay_ms)
        inv = 1.0 / n
        return (sx * inv, sy * inv, sz * inv)

    def _apply_accel_offsets(self):
        regs = self._accel_offset_regs
        scales = self._accel_offset_scales
        if regs is None or scales is None:
            return

        for axis in range(3):
            bias_g = self._acc_bias[axis] / _G0
            delta = -int(round(bias_g * scales[axis]))
            value = self._read_i16(regs[axis]) + delta
            self._write_i16(regs[axis], self._clamp_i16(value))
        self._acc_bias = [0.0, 0.0, 0.0]

    def _apply_body_transform(self, x, y, z):
        return self._apply_matrix(self._body_matrix, x, y, z)

    def _transform_quat(self, q):
        r = self._quat_to_matrix(q)
        r = self._mat_mul(r, self._body_matrix_t)
        return self._matrix_to_quat(r)

    def _tilt_from_gravity(self, gravity):
        x, y, z = gravity
        mag = math.sqrt(x*x + y*y + z*z)
        if mag < _TILT_ACCEL_MIN or mag > _TILT_ACCEL_MAX:
            return self._last_tilt

        self._last_tilt = (
            self._clean_angle(math.atan2(y, z)),
            self._clean_angle(math.atan2(-x, z)),
        )
        return self._last_tilt

    def _tilt_from_accel(self, accel):
        x, y, z = self._apply_body_transform(accel[0], accel[1], accel[2])
        return self._tilt_from_gravity((x, y, z))

    def _read_dmp_packet(self, timeout_ms=150):
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            st = self._i2c.read_u8(self._addr, _RA_INT_STATUS)
            cnt = self._fifo_count_direct()

            if (st & 0x10) or cnt >= _FIFO_CAPACITY:
                self._restart_dmp_stream()
                t0 = time.ticks_ms()
                continue

            if cnt >= self._pkt_size:
                rem = cnt % self._pkt_size
                if rem:
                    self._restart_dmp_stream()
                    t0 = time.ticks_ms()
                    continue
                while cnt > self._pkt_size:
                    _ = self._fifo_read_direct(self._pkt_size)
                    cnt -= self._pkt_size
                return self._fifo_read_direct(self._pkt_size)

            time.sleep_ms(1)
        return None

    def _wait_for_dmp_packet(self, timeout_ms=150):
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            if self._fifo_count_direct() >= self._pkt_size:
                return True
            time.sleep_ms(1)
        return False

    def _load_dmp_firmware(self, fw=None, cfg=None, upd=None):
        fw  = fw if fw  is not None else _DMP_FW_BYTES
        cfg = cfg if cfg is not None else _DMP_CFG_BYTES
        upd = upd if upd is not None else _DMP_UPD_BYTES

        self._i2c.write_u8(self._addr, _RA_USER_CTRL, (1<<_BIT_DMP_RST) | (1<<_BIT_FIFO_RST))
        time.sleep_ms(10)

        self._write_memory_block_direct(fw, bank=0, address=0)
        self._write_config_set_direct(cfg)
        self._write_config_set_direct(upd)

        self._i2c.write_u8(self._addr, _RA_DMP_CFG_1, 0x03)
        self._i2c.write_u8(self._addr, _RA_DMP_CFG_2, 0x00)

        user = self._i2c.read_u8(self._addr, _RA_USER_CTRL)
        self._i2c.write_u8(self._addr, _RA_USER_CTRL, user | (1<<_BIT_FIFO_RST))
        time.sleep_ms(5)

        user |= (1<<_BIT_DMP_EN) | (1<<_BIT_FIFO_EN)
        self._i2c.write_u8(self._addr, _RA_USER_CTRL, user)
        self._i2c.write_u8(self._addr, _RA_FIFO_EN, 0x00)

        self._pkt_size = _DMP_PACKET_SIZE
        return True

    def _select_bank_direct(self, bank):
        self._i2c.write_u8(self._addr, _RA_BANK_SEL, bank & 0x1F)

    def _set_mem_addr_direct(self, addr):
        self._i2c.write_u8(self._addr, _RA_MEM_START_ADDR, addr & 0xFF)

    def _write_memory_block_direct(self, data: bytes, bank=0, address=0, chunk=16):
        i = 0
        L = len(data)
        while i < L:
            self._select_bank_direct(bank)
            self._set_mem_addr_direct(address)
            space = 256 - address
            this = min(chunk, space, L - i)
            self._i2c.writeto_mem(self._addr, _RA_MEM_R_W, data[i:i+this])
            i += this
            address += this
            if address == 256:
                bank += 1
                address = 0

    def _write_config_set_direct(self, cfg: bytes):
        i, L = 0, len(cfg)
        while i < L:
            if i + 3 > L:
                raise ValueError("Malformed DMP config (truncated header)")
            
            bank = cfg[i]; offset = cfg[i+1]
            length = cfg[i+2]; i += 3

            if length == 0:
                if i >= L:
                    raise ValueError("Malformed DMP config (missing special code)")
                
                special = cfg[i]
                i += 1
                if special == 0x01:
                    self._i2c.write_u8(self._addr, _RA_INT_ENABLE, 0x02)  # DMP INT
                continue

            if i + length > L:
                raise ValueError("Malformed DMP config (length overflow)")
            
            self._write_memory_block_direct(cfg[i:i+length], bank=bank, address=offset)
            i += length

    def _fifo_count_direct(self):
        b = self._i2c.readfrom_mem(self._addr, _RA_FIFO_COUNTH, 2)
        return (b[0] << 8) | b[1]

    def _fifo_read_direct(self, n):
        mv = memoryview(self._buf42)[:n]
        self._i2c.readfrom_mem_into(self._addr, _RA_FIFO_R_W, mv)
        return mv

    def _quick_bias(self, n=200, delay_ms=2):
        # throw away first readings
        for _ in range(20):
            self._i2c.readfrom_mem_into(self._addr, _RA_ACCEL_XOUT_H, self._buf14)
            time.sleep_ms(1)

        ax = ay = az = gx = gy = gz = 0.0
        b = self._buf14
        for _ in range(n):
            self._i2c.readfrom_mem_into(self._addr, _RA_ACCEL_XOUT_H, b)
            ax += self._twos16(b[0],b[1])
            ay += self._twos16(b[2],b[3])
            az += self._twos16(b[4],b[5])
            gx += self._twos16(b[8],b[9])
            gy += self._twos16(b[10],b[11])
            gz += self._twos16(b[12],b[13])
            time.sleep_ms(delay_ms)

        inv = 1.0/n
        axg, ayg, azg = (ax*inv)/_ACC_LSB_PER_G, (ay*inv)/_ACC_LSB_PER_G, (az*inv)/_ACC_LSB_PER_G

        vals = (axg, ayg, azg)
        dom = max(range(3), key=lambda i: abs(vals[i]))
        g_corr = [0.0, 0.0, 0.0]
        g_corr[dom] = 1.0 if vals[dom] >= 0 else -1.0
        self._acc_bias = [
            (axg - g_corr[0]) * _G0,
            (ayg - g_corr[1]) * _G0,
            (azg - g_corr[2]) * _G0,
        ]

        self._gyr_raw_bias = [gx*inv, gy*inv, gz*inv]
        gxd = self._gyr_raw_bias[0] / _GYR_LSB_PER_DPS * _DPS_TO_RAD_S
        gyd = self._gyr_raw_bias[1] / _GYR_LSB_PER_DPS * _DPS_TO_RAD_S
        gzd = self._gyr_raw_bias[2] / _GYR_LSB_PER_DPS * _DPS_TO_RAD_S
        self._gyr_bias = [gxd, gyd, gzd]

    def _quick_gyro_bias(self, n=128, delay_ms=2):
        for _ in range(10):
            self._i2c.readfrom_mem_into(self._addr, _RA_GYRO_XOUT_H, self._buf6)
            time.sleep_ms(1)

        gx = gy = gz = 0.0
        b = self._buf6
        for _ in range(n):
            self._i2c.readfrom_mem_into(self._addr, _RA_GYRO_XOUT_H, b)
            gx += self._twos16(b[0], b[1])
            gy += self._twos16(b[2], b[3])
            gz += self._twos16(b[4], b[5])
            time.sleep_ms(delay_ms)

        inv = 1.0 / n
        self._gyr_bias = [
            ((gx * inv) / _GYR_LSB_PER_DPS) * _DPS_TO_RAD_S,
            ((gy * inv) / _GYR_LSB_PER_DPS) * _DPS_TO_RAD_S,
            ((gz * inv) / _GYR_LSB_PER_DPS) * _DPS_TO_RAD_S,
        ]

    def _write_i16(self, reg, value):
        if value < 0:
            value += 0x10000
        self._i2c.write_u8(self._addr, reg, (value >> 8) & 0xFF)
        self._i2c.write_u8(self._addr, reg + 1, value & 0xFF)

    def _read_i16(self, reg):
        b = self._i2c.readfrom_mem(self._addr, reg, 2)
        return self._twos16(b[0], b[1])

    @staticmethod
    def _clamp_i16(value):
        if value < -32768:
            return -32768
        if value > 32767:
            return 32767
        return value

    @staticmethod
    def _parse_axis_remap(remap):
        text = str(remap).lower().replace(' ', '')
        axes = 'xyz'
        rows = []
        used = [False, False, False]
        i = 0
        while i < len(text):
            sign = 1
            ch = text[i]
            if ch == '-' or ch == '+':
                sign = -1 if ch == '-' else 1
                i += 1
                if i >= len(text):
                    raise ValueError("remap must use x, y, z exactly once")
                ch = text[i]
            idx = axes.find(ch)
            if idx < 0 or used[idx]:
                raise ValueError("remap must use x, y, z exactly once")
            used[idx] = True
            row = [0, 0, 0]
            row[idx] = sign
            rows.append((row[0], row[1], row[2]))
            i += 1

        if len(rows) != 3 or not (used[0] and used[1] and used[2]):
            raise ValueError("remap must use x, y, z exactly once")

        matrix = (rows[0], rows[1], rows[2])
        if MPU6050._mat_det(matrix) != 1:
            raise ValueError("remap must preserve a right-handed coordinate frame")
        return matrix

    @staticmethod
    def _apply_matrix(m, x, y, z):
        return (
            m[0][0]*x + m[0][1]*y + m[0][2]*z,
            m[1][0]*x + m[1][1]*y + m[1][2]*z,
            m[2][0]*x + m[2][1]*y + m[2][2]*z,
        )

    @staticmethod
    def _mat_transpose(m):
        return (
            (m[0][0], m[1][0], m[2][0]),
            (m[0][1], m[1][1], m[2][1]),
            (m[0][2], m[1][2], m[2][2]),
        )

    @staticmethod
    def _mat_mul(a, b):
        return (
            (
                a[0][0]*b[0][0] + a[0][1]*b[1][0] + a[0][2]*b[2][0],
                a[0][0]*b[0][1] + a[0][1]*b[1][1] + a[0][2]*b[2][1],
                a[0][0]*b[0][2] + a[0][1]*b[1][2] + a[0][2]*b[2][2],
            ),
            (
                a[1][0]*b[0][0] + a[1][1]*b[1][0] + a[1][2]*b[2][0],
                a[1][0]*b[0][1] + a[1][1]*b[1][1] + a[1][2]*b[2][1],
                a[1][0]*b[0][2] + a[1][1]*b[1][2] + a[1][2]*b[2][2],
            ),
            (
                a[2][0]*b[0][0] + a[2][1]*b[1][0] + a[2][2]*b[2][0],
                a[2][0]*b[0][1] + a[2][1]*b[1][1] + a[2][2]*b[2][1],
                a[2][0]*b[0][2] + a[2][1]*b[1][2] + a[2][2]*b[2][2],
            ),
        )

    @staticmethod
    def _mat_det(m):
        return (
            m[0][0] * (m[1][1]*m[2][2] - m[1][2]*m[2][1])
            - m[0][1] * (m[1][0]*m[2][2] - m[1][2]*m[2][0])
            + m[0][2] * (m[1][0]*m[2][1] - m[1][1]*m[2][0])
        )

    @staticmethod
    def _quat_to_matrix(q):
        w, x, y, z = q
        xx, yy, zz = x*x, y*y, z*z
        wx, wy, wz = w*x, w*y, w*z
        xy, xz, yz = x*y, x*z, y*z
        return (
            (1 - 2*(yy + zz), 2*(xy - wz),     2*(xz + wy)),
            (2*(xy + wz),     1 - 2*(xx + zz), 2*(yz - wx)),
            (2*(xz - wy),     2*(yz + wx),     1 - 2*(xx + yy)),
        )

    @staticmethod
    def _matrix_to_quat(m):
        trace = m[0][0] + m[1][1] + m[2][2]
        if trace > 0.0:
            s = math.sqrt(trace + 1.0) * 2.0
            q = (
                0.25 * s,
                (m[2][1] - m[1][2]) / s,
                (m[0][2] - m[2][0]) / s,
                (m[1][0] - m[0][1]) / s,
            )
        elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
            s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
            q = (
                (m[2][1] - m[1][2]) / s,
                0.25 * s,
                (m[0][1] + m[1][0]) / s,
                (m[0][2] + m[2][0]) / s,
            )
        elif m[1][1] > m[2][2]:
            s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
            q = (
                (m[0][2] - m[2][0]) / s,
                (m[0][1] + m[1][0]) / s,
                0.25 * s,
                (m[1][2] + m[2][1]) / s,
            )
        else:
            s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
            q = (
                (m[1][0] - m[0][1]) / s,
                (m[0][2] + m[2][0]) / s,
                (m[1][2] + m[2][1]) / s,
                0.25 * s,
            )
        return MPU6050._q_normalize(q)

    @staticmethod
    def _wrap_angle(angle):
        return MPU6050._clean_angle(MPU6050._wrap_angle_raw(angle))

    @staticmethod
    def _wrap_angle_raw(angle):
        if angle > math.pi:
            angle -= 2 * math.pi
        elif angle < -math.pi:
            angle += 2 * math.pi
        return angle

    @staticmethod
    def _clean_angle(angle):
        if -_ANGLE_ZERO_EPS < angle < _ANGLE_ZERO_EPS:
            return 0.0
        return angle

    @staticmethod
    def _quat_to_euler(q):
        w, x, y, z = q
        raw_roll = math.atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
        sp = 2*(w*y - z*x)
        sp = -1.0 if sp < -1.0 else (1.0 if sp > 1.0 else sp)
        raw_pitch = math.asin(sp)
        raw_yaw = math.atan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
        return MPU6050._clean_angle(raw_roll), MPU6050._clean_angle(raw_pitch), MPU6050._wrap_angle(raw_yaw)

    @staticmethod
    def _q_normalize(q):
        w, x, y, z = q
        n2 = w*w + x*x + y*y + z*z
        if n2 <= 0.0:
            return (1.0, 0.0, 0.0, 0.0)
        
        n = math.sqrt(n2)
        return (w/n, x/n, y/n, z/n)

    @staticmethod
    def _twos16(h, l):
        v = (h << 8) | l
        return v - 0x10000 if v & 0x8000 else v

    @staticmethod
    def _twos32(b0, b1, b2, b3):
        v = (b0 << 24) | (b1 << 16) | (b2 << 8) | b3
        if v & 0x80000000:
            v = -((~v & 0xFFFFFFFF) + 1)
        return v
