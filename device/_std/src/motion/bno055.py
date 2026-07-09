# @package: bno055
# @version: 1.0.0
# @type: device-std
# @category: motion
# @sensor_type: D
# @interface: I2C
# @depends: i2c
# @platforms: *
# @tags: imu, 9dof, accelerometer, gyroscope, magnetometer, quaternion, euler, bno055
# @author: PlanXLab Development Team

import math
import time
import struct
from micropython import const
from i2c import I2CController

_REG_CHIP_ID         = const(0x00)
_REG_PAGE_ID         = const(0x07)
_REG_UNIT_SEL        = const(0x3B)
_REG_OPR_MODE        = const(0x3D)
_REG_PWR_MODE        = const(0x3E)
_REG_SYS_TRIG        = const(0x3F)
_REG_CALIB_STAT      = const(0x35)
_REG_SYS_STAT        = const(0x39)
_REG_SYS_ERR         = const(0x3A)
_REG_AXIS_MAP_CONFIG = const(0x41)
_REG_AXIS_MAP_SIGN   = const(0x42)

_ACCELERATION        = const(0x08)
_MAGNETIC            = const(0x0E)
_GYROSCOPE           = const(0x14)
_QUATERNION          = const(0x20)
_ACCEL_LINEAR        = const(0x28)
_ACCEL_GRAVITY       = const(0x2E)
_TEMPERATURE         = const(0x34)

_REG_OFFSETS_START   = const(0x55)
_OFFSETS_LEN         = const(22)
_ACC_OFF_X_LSB       = const(0x55)
_ACC_OFF_Y_LSB       = const(0x57)
_ACC_OFF_Z_LSB       = const(0x59)
_ACC_RADIUS_LSB      = const(0x67)

_MODE_CONFIG         = const(0x00)
_MODE_ACCONLY        = const(0x01)
_MODE_IMU            = const(0x08)
_MODE_NDOF           = const(0x0C)
_PWR_NORMAL          = const(0x00)
_UNITS_SI            = const(0x07)

_READ_TYPE_ACCEL     = const(1 << 0)
_READ_TYPE_GYRO      = const(1 << 1)
_READ_TYPE_MAG       = const(1 << 2)
_READ_TYPE_QUAT      = const(1 << 3)
_READ_TYPE_EULER     = const(1 << 4)
_READ_TYPE_LINEAR    = const(1 << 5)
_READ_TYPE_GRAVITY   = const(1 << 6)
_READ_TYPE_ALL       = const(_READ_TYPE_ACCEL | _READ_TYPE_GYRO | _READ_TYPE_MAG |
                             _READ_TYPE_QUAT | _READ_TYPE_EULER |
                             _READ_TYPE_LINEAR | _READ_TYPE_GRAVITY)

_SCALE_ACC_MS2       = 1.0 / 100.0
_SCALE_GYR_RADS      = 1.0 / 900.0
_SCALE_QUAT          = 1.0 / (1 << 14)

_B_PAGE0       = b'\x00'
_B_CONFIG      = b'\x00'
_B_NDOF        = b'\x0C'
_B_ACCONLY     = b'\x01'
_B_PWR_NORMAL  = b'\x00'
_B_PWR_SUSPEND = b'\x02'
_B_RST         = b'\x20'
_B_EXT_CLK_ON  = b'\x80'
_B_EXT_CLK_OFF = b'\x00'
_B_UNITS_SI    = b'\x07'


class BNO055:
    READ_TYPE_ACCEL   = _READ_TYPE_ACCEL
    READ_TYPE_GYRO    = _READ_TYPE_GYRO
    READ_TYPE_MAG     = _READ_TYPE_MAG
    READ_TYPE_QUAT    = _READ_TYPE_QUAT
    READ_TYPE_EULER   = _READ_TYPE_EULER
    READ_TYPE_LINEAR  = _READ_TYPE_LINEAR
    READ_TYPE_GRAVITY = _READ_TYPE_GRAVITY
    READ_TYPE_ALL     = _READ_TYPE_ALL

    CAL_FILE_NAME = "lib/ticle/bno055.cal"

    @staticmethod
    def run_calibration_wizard(i2c, *, addr=0x28, accel_samples=200, settle_ms=500, savefile=CAL_FILE_NAME):
        def _wait_fusion_running(i2c, timeout_ms=3000):
            t0 = time.ticks_ms()
            while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
                err = i2c.readfrom_mem(addr, _REG_SYS_ERR, 1)[0]
                if err:
                    raise RuntimeError("BNO055 system error: %d" % err)
                stat = i2c.readfrom_mem(addr, _REG_SYS_STAT, 1)[0]
                if stat == 5:
                    return True
                time.sleep_ms(50)
            return False

        def _wait_sys3(i2c, timeout_s=60):
            print("  Step 4/4 System: Slowly rotate around all three axes (include slow yaw).")
            t0 = time.ticks_ms()
            hinted = False
            while True:
                d = i2c.readfrom_mem(addr, _REG_CALIB_STAT, 1)[0]
                sys_ = (d >> 6) & 3
                if sys_ == 3:
                    print("    System OK")
                    return True
                if time.ticks_diff(time.ticks_ms(), t0) > timeout_s*1000:
                    return False
                if not hinted and time.ticks_diff(time.ticks_ms(), t0) > 5000:
                    print("    Hint: make slow 360° rotations on yaw, then pitch/roll.")
                    hinted = True
                time.sleep_ms(150)

        i2c.writeto_mem(addr, _REG_PAGE_ID, _B_PAGE0)

        def _read_cal():
            d = i2c.readfrom_mem(addr, _REG_CALIB_STAT, 1)[0]
            return (d >> 6) & 3, (d >> 4) & 3, (d >> 2) & 3, d & 3  # sys, gyro, accel, mag

        mode = i2c.readfrom_mem(addr, _REG_OPR_MODE, 1)[0]
        if mode != _MODE_NDOF:
            if mode != _MODE_CONFIG:
                i2c.writeto_mem(addr, _REG_OPR_MODE, _B_CONFIG)
                time.sleep_ms(20)
            i2c.writeto_mem(addr, _REG_OPR_MODE, _B_NDOF)
            time.sleep_ms(200)
            _wait_fusion_running(i2c)

        print("[BNO055] Interactive calibration started.")

        print("  Step 1/3 Gyro: Place on flat surface and hold.")
        while True:
            sys_, gyr, acc, mag = _read_cal()
            if gyr == 3:
                print("    Gyro OK")
                break
            time.sleep_ms(150)

        print("  Step 2/3 Accel(6-face): ±X/±Y/±Z slowly.")
        bx, by, bz, radius = BNO055._calibrate_accel_6face(i2c, addr, samples=accel_samples, settle_ms=settle_ms)
        print("    Accel offsets set (LSB): bx=%d, by=%d, bz=%d, radius=%d" % (bx, by, bz, radius))

        t0 = time.ticks_ms()
        while True:
            sys_, gyr, acc, mag = _read_cal()
            if acc == 3:
                print("    Accel OK")
                break
            if time.ticks_diff(time.ticks_ms(), t0) > 5000:
                print("    Accel: timeout waiting for cal=3 (offsets written).")
                break
            time.sleep_ms(150)
        _wait_fusion_running(i2c)

        print("  Step 3/3 Mag: free space, figure-eight.")
        while True:
            sys_, gyr, acc, mag = _read_cal()
            if mag == 3:
                print("    Mag OK")
                break
            time.sleep_ms(150)

        if not _wait_sys3(i2c, timeout_s=90):
            raise RuntimeError("Calibration ended without System=3. Repeat slow all-axis rotations and ensure NDOF mode.")

        sys_, gyr, acc, mag = _read_cal()
        print("[BNO055] calibration status: sys=%d, gyro=%d, accel=%d, mag=%d" % (sys_, gyr, acc, mag))

        if savefile:
            try:
                BNO055._save_calibration_to_file(i2c, addr, savefile)
                print("[BNO055] Calibration saved to '%s'." % savefile)
            except Exception as e:
                print("[BNO055] Save failed:", e)

        _wait_fusion_running(i2c, timeout_ms=2000)
        sys_, gyr, acc, mag = _read_cal()
        print("[BNO055] Final calibration status: sys=%d, gyro=%d, accel=%d, mag=%d" % (sys_, gyr, acc, mag))
        print("[BNO055] Calibration done.")

    def __init__(self, i2c, *, addr=0x28, calfile=CAL_FILE_NAME):
        self._i2c  = i2c
        self._addr = int(addr)

        self._buf6 = bytearray(6)
        self._buf8 = bytearray(8)

        if not self._wait_chip_id_ready(1000):
            raise RuntimeError("BNO055 not found or not ready")

        self._set_mode(_MODE_CONFIG)
        self._i2c.writeto_mem(self._addr, _REG_SYS_TRIG, _B_RST)
        time.sleep_ms(650)
        self._i2c.writeto_mem(self._addr, _REG_PWR_MODE, _B_PWR_NORMAL)
        self._i2c.writeto_mem(self._addr, _REG_PAGE_ID, _B_PAGE0)
        self._i2c.writeto_mem(self._addr, _REG_SYS_TRIG, _B_EXT_CLK_ON)
        self._i2c.writeto_mem(self._addr, _REG_SYS_TRIG, _B_EXT_CLK_OFF)
        time.sleep_ms(10)
        self._i2c.writeto_mem(self._addr, _REG_UNIT_SEL, _B_UNITS_SI)

        BNO055._load_calibration_from_file(self._i2c, self._addr, calfile)
        self._set_mode(_MODE_NDOF)

    def deinit(self):
        self._set_mode(_MODE_CONFIG)
        self._i2c.writeto_mem(self._addr, _REG_PWR_MODE, _B_PWR_SUSPEND)
        self._i2c = None

    def set_axis_remap(self, x='X', y='Y', z='Z', sx=+1, sy=+1, sz=+1):
        x = x.upper()
        y = y.upper()
        z = z.upper()
        MAP = {'X':0, 'Y':1, 'Z':2}
        if x not in MAP or y not in MAP or z not in MAP or x==y or y==z or z==x:
            raise ValueError("Invalid axis remap")
        cfg  = (MAP[z] << 4) | (MAP[y] << 2) | MAP[x]
        sign = (0 if sx>0 else 1) | ((0 if sy>0 else 1)<<1) | ((0 if sz>0 else 1)<<2)

        self._set_mode(_MODE_CONFIG)
        self._i2c.writeto_mem(self._addr, _REG_AXIS_MAP_CONFIG, bytes([cfg]))
        self._i2c.writeto_mem(self._addr, _REG_AXIS_MAP_SIGN, bytes([sign]))
        self._set_mode(_MODE_NDOF)

    def wait_ready(self, timeout_s=15):
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_s*1000:
            d = self._i2c.readfrom_mem(self._addr, _REG_CALIB_STAT, 1)[0]
            sys_ = (d>>6)&3; gyr=(d>>4)&3; acc=(d>>2)&3; mag=d&3
            if gyr==3 and acc==3 and mag==3 and sys_==3:
                return True
            time.sleep_ms(150)
        return False

    def read(self):
        return self.accel, self.gyro, self.magnetic, self.quat, self.euler, self.linear, self.gravity, self.temp

    @property
    def diagnostics(self):
        d = self._i2c.readfrom_mem(self._addr, _REG_CALIB_STAT, 1)[0]
        return {
            "chip_id": self._i2c.readfrom_mem(self._addr, _REG_CHIP_ID, 1)[0],
            "sys_stat": self._i2c.readfrom_mem(self._addr, _REG_SYS_STAT, 1)[0],
            "sys_err": self._i2c.readfrom_mem(self._addr, _REG_SYS_ERR, 1)[0],
            "calib": ((d >> 6) & 3, (d >> 4) & 3, (d >> 2) & 3, d & 3)  # sys, gyro, accel, mag
        }

    @property
    def accel(self):
        self._i2c.readfrom_mem_into(self._addr, _ACCELERATION, self._buf6)
        x, y, z = struct.unpack_from('<hhh', self._buf6, 0)
        s = _SCALE_ACC_MS2
        return x*s, y*s, z*s

    @property
    def gyro(self):
        self._i2c.readfrom_mem_into(self._addr, _GYROSCOPE, self._buf6)
        x, y, z = struct.unpack_from('<hhh', self._buf6, 0)
        s = _SCALE_GYR_RADS
        return x*s, y*s, z*s

    @property
    def magnetic(self):
        self._i2c.readfrom_mem_into(self._addr, _MAGNETIC, self._buf6)
        x, y, z = struct.unpack_from('<hhh', self._buf6, 0)
        return x/16.0, y/16.0, z/16.0  # μT

    @property
    def euler(self):
        w, x, y, z = self.quat
        roll = math.atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
        sp = 2*(w*y - z*x)
        sp = -1.0 if sp < -1.0 else (1.0 if sp > 1.0 else sp)
        pitch = math.asin(sp)
        yaw = math.atan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
        return roll, pitch, yaw

    @property
    def quat(self):
        self._i2c.readfrom_mem_into(self._addr, _QUATERNION, self._buf8)
        w, x, y, z = struct.unpack_from('<hhhh', self._buf8, 0)
        s = _SCALE_QUAT
        return w*s, x*s, y*s, z*s

    @property
    def linear(self):
        self._i2c.readfrom_mem_into(self._addr, _ACCEL_LINEAR, self._buf6)
        x, y, z = struct.unpack_from('<hhh', self._buf6, 0)
        s = _SCALE_ACC_MS2
        return x*s, y*s, z*s

    @property
    def gravity(self):
        self._i2c.readfrom_mem_into(self._addr, _ACCEL_GRAVITY, self._buf6)
        x, y, z = struct.unpack_from('<hhh', self._buf6, 0)
        s = _SCALE_ACC_MS2
        return x*s, y*s, z*s

    @property
    def temp(self):
        t = self._i2c.readfrom_mem(self._addr, _TEMPERATURE, 1)[0]
        return t - 256 if t > 127 else t

    def _wait_chip_id_ready(self, timeout_ms=1000):
        t0 = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), t0) < timeout_ms:
            if self._i2c.readfrom_mem(self._addr, _REG_CHIP_ID, 1)[0] == 0xA0:
                return True
            time.sleep_ms(10)
        return False

    def _set_mode(self, mode):
        cur = self._i2c.readfrom_mem(self._addr, _REG_OPR_MODE, 1)[0]
        if cur == mode:
            return
        if mode == _MODE_CONFIG or cur != _MODE_CONFIG:
            self._i2c.writeto_mem(self._addr, _REG_OPR_MODE, _B_CONFIG)
            time.sleep_ms(20)
        if mode != _MODE_CONFIG:
            self._i2c.writeto_mem(self._addr, _REG_OPR_MODE, bytes([mode]))
            time.sleep_ms(200 if mode == _MODE_NDOF else 50)

    @staticmethod
    def _load_calibration_from_file(i2c, addr, filename):
        if not filename:
            return False
        try:
            with open(filename, "rb") as f:
                data = f.read()
        except OSError:
            return False
        if len(data) != _OFFSETS_LEN:
            return False

        cur = i2c.readfrom_mem(addr, _REG_OPR_MODE, 1)[0]
        if cur != _MODE_CONFIG:
            i2c.writeto_mem(addr, _REG_OPR_MODE, _B_CONFIG)
            time.sleep_ms(20)

        i2c.writeto_mem(addr, _REG_PAGE_ID, _B_PAGE0)
        i2c.writeto_mem(addr, _REG_OFFSETS_START, data)

        if cur != _MODE_CONFIG:
            i2c.writeto_mem(addr, _REG_OPR_MODE, bytes([cur]))
            time.sleep_ms(200 if cur == _MODE_NDOF else 50)
        return True

    @staticmethod
    def _save_calibration_to_file(i2c, addr, filename):
        cur = i2c.readfrom_mem(addr, _REG_OPR_MODE, 1)[0]
        if cur != _MODE_CONFIG:
            i2c.writeto_mem(addr, _REG_OPR_MODE, _B_CONFIG)
            time.sleep_ms(20)

        i2c.writeto_mem(addr, _REG_PAGE_ID, _B_PAGE0)
        blob = i2c.readfrom_mem(addr, _REG_OFFSETS_START, _OFFSETS_LEN)
        try:
            with open(filename, "wb") as f:
                f.write(bytes(blob))
            return True
        except OSError:
            return False
        finally:
            if cur != _MODE_CONFIG:
                i2c.writeto_mem(addr, _REG_OPR_MODE, bytes([cur]))
                time.sleep_ms(200 if cur == _MODE_NDOF else 50)

    @staticmethod
    def _calibrate_accel_6face(i2c, addr, samples=200, settle_ms=500, timeout_s=120, confirm=False):
        orig = i2c.readfrom_mem(addr, _REG_OPR_MODE, 1)[0]
        if orig != _MODE_CONFIG:
            i2c.writeto_mem(addr, _REG_OPR_MODE, _B_CONFIG)
            time.sleep_ms(20)

        i2c.writeto_mem(addr, _REG_PAGE_ID, _B_PAGE0)
        i2c.writeto_mem(addr, _REG_OPR_MODE, _B_ACCONLY)
        time.sleep_ms(50)

        G = 981  # 1g in LSB (accel LSB=0.01 m/s^2 -> 9.81 m/s^2 = 981 LSB)
        MAIN = int(0.85 * G)
        ORTH = int(0.20 * G)
        STABLE_WIN = 40
        start_ms = time.ticks_ms()

        def classify(ax, ay, az):
            if ax >  MAIN and abs(ay) < ORTH and abs(az) < ORTH: return "+X"
            if ax < -MAIN and abs(ay) < ORTH and abs(az) < ORTH: return "-X"
            if ay >  MAIN and abs(ax) < ORTH and abs(az) < ORTH: return "+Y"
            if ay < -MAIN and abs(ax) < ORTH and abs(az) < ORTH: return "-Y"
            if az >  MAIN and abs(ax) < ORTH and abs(ay) < ORTH: return "+Z"
            if az < -MAIN and abs(ax) < ORTH and abs(ay) < ORTH: return "-Z"
            return None

        def avg_vec(n):
            sx = sy = sz = 0
            b = bytearray(6)
            for _ in range(n):
                i2c.readfrom_mem_into(addr, _ACCELERATION, b)
                x, y, z = struct.unpack_from('<hhh', b, 0)
                sx += x; sy += y; sz += z
                time.sleep_ms(2)
            inv = 1.0/n
            return sx*inv, sy*inv, sz*inv

        def capture_face(tag):
            if confirm:
                print("    Make %s and press Enter…" % tag)
                try: input()
                except Exception: pass

            b = bytearray(6)
            while True:
                sx = sy = sz = 0
                min_x = min_y = min_z = 32767
                max_x = max_y = max_z = -32768
                for _ in range(32):
                    i2c.readfrom_mem_into(addr, _ACCELERATION, b)
                    x, y, z = struct.unpack_from('<hhh', b, 0)
                    sx += x; sy += y; sz += z
                    if x < min_x: min_x = x
                    if x > max_x: max_x = x
                    if y < min_y: min_y = y
                    if y > max_y: max_y = y
                    if z < min_z: min_z = z
                    if z > max_z: max_z = z
                    time.sleep_ms(5)

                ax = sx / 32; ay = sy / 32; az = sz / 32
                if (max_x - min_x <= STABLE_WIN and
                    max_y - min_y <= STABLE_WIN and
                    max_z - min_z <= STABLE_WIN):
                    got = classify(ax, ay, az)
                    if got == tag:
                        time.sleep_ms(settle_ms)
                        return avg_vec(samples)

                if time.ticks_diff(time.ticks_ms(), start_ms) > timeout_s*1000:
                    raise RuntimeError("Accel 6-face: timeout waiting for posture/stability")

        # 6 faces
        xp = capture_face("+X"); xm = capture_face("-X")
        yp = capture_face("+Y"); ym = capture_face("-Y")
        zp = capture_face("+Z"); zm = capture_face("-Z")

        bx = int(round((xp[0] + xm[0]) * 0.5))
        by = int(round((yp[1] + ym[1]) * 0.5))
        bz = int(round((zp[2] + zm[2]) * 0.5))
        gx = abs(xp[0] - xm[0]) * 0.5
        gy = abs(yp[1] - ym[1]) * 0.5
        gz = abs(zp[2] - zm[2]) * 0.5
        acc_radius = int(round((gx + gy + gz) / 3.0))

        if not (900 <= acc_radius <= 1050):
            raise RuntimeError("Accel 6-face: invalid radius (expected ~981 LSB), got %d" % acc_radius)

        i2c.writeto_mem(addr, _REG_OPR_MODE, _B_CONFIG)
        time.sleep_ms(20)
        i2c.writeto_mem(addr, _REG_PAGE_ID, _B_PAGE0)

        def w16(reg_lsb, val_s16):
            i2c.writeto_mem(addr, reg_lsb, struct.pack('<h', int(val_s16)))

        w16(_ACC_OFF_X_LSB, bx)
        w16(_ACC_OFF_Y_LSB, by)
        w16(_ACC_OFF_Z_LSB, bz)
        w16(_ACC_RADIUS_LSB, acc_radius)

        i2c.writeto_mem(addr, _REG_OPR_MODE, bytes([orig]))
        time.sleep_ms(200 if orig == _MODE_NDOF else 50)
        return bx, by, bz, acc_radius
