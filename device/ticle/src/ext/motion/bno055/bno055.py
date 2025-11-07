import math
import utime
import ustruct
from ticle import I2CMaster

__version__ = "1.0.0"
__author__  = "PlanX Lab Development Team"


class BNO055:
    # Registers
    _REG_CHIP_ID         = 0x00
    _REG_PAGE_ID         = 0x07
    _REG_UNIT_SEL        = 0x3B
    _REG_OPR_MODE        = 0x3D
    _REG_PWR_MODE        = 0x3E
    _REG_SYS_TRIG        = 0x3F
    _REG_CALIB_STAT      = 0x35
    _REG_SYS_STAT        = 0x39
    _REG_SYS_ERR         = 0x3A
    _REG_AXIS_MAP_CONFIG = 0x41
    _REG_AXIS_MAP_SIGN   = 0x42

    # Data blocks (page 0)
    _ACCELERATION        = 0x08
    _MAGNETIC            = 0x0E
    _GYROSCOPE           = 0x14
    _EULER               = 0x1A  # heading, roll, pitch (Note: Euler calculations are done directly with quaternions here)
    _QUATERNION          = 0x20
    _ACCEL_LINEAR        = 0x28
    _ACCEL_GRAVITY       = 0x2E
    _TEMPERATURE         = 0x34

    # Offsets
    _REG_OFFSETS_START   = 0x55
    _OFFSETS_LEN         = 22
    _ACC_OFF_X_LSB       = 0x55
    _ACC_OFF_Y_LSB       = 0x57
    _ACC_OFF_Z_LSB       = 0x59
    _ACC_RADIUS_LSB      = 0x67

    # Modes / Units
    _MODE_CONFIG         = 0x00
    _MODE_ACCONLY        = 0x01
    _MODE_IMU            = 0x08
    _MODE_NDOF           = 0x0C
    _PWR_NORMAL          = 0x00
    _UNITS_SI            = 0x07  # ACC=m/s^2, GYR=rad/s, EULER=rad, TEMP=°C

    # Fixed scales with UNIT_SEL=_UNITS_SI
    _SCALE_ACC_MS2       = 1.0/100.0   # accel, linear, gravity
    _SCALE_GYR_RADS      = 1.0/900.0   # rad/s
    _SCALE_QUAT          = 1.0/(1<<14)

    READ_TYPE_ACCEL   = (1 << 0)
    READ_TYPE_GYRO    = (1 << 1)
    READ_TYPE_MAG     = (1 << 2)
    READ_TYPE_QUAT    = (1 << 3)
    READ_TYPE_EULER   = (1 << 4)
    READ_TYPE_LINEAR  = (1 << 5)
    READ_TYPE_GRAVITY = (1 << 6)
    READ_TYPE_ALL     = (READ_TYPE_ACCEL | READ_TYPE_GYRO | READ_TYPE_MAG |
                         READ_TYPE_QUAT  | READ_TYPE_EULER |
                         READ_TYPE_LINEAR| READ_TYPE_GRAVITY)

    CAL_FILE_NAME = "lib/ticle/bno055.cal"

    @staticmethod
    def run_calibration_wizard(sda, scl, *, addr=0x28, accel_samples=200, settle_ms=500, savefile=CAL_FILE_NAME):
        def _wait_fusion_running(i2c, timeout_ms=3000):
            t0 = utime.ticks_ms()
            while utime.ticks_diff(utime.ticks_ms(), t0) < timeout_ms:
                err = i2c.readfrom_mem(addr, BNO055._REG_SYS_ERR, 1)[0]
                if err:
                    raise RuntimeError("BNO055 system error: %d" % err)
                stat = i2c.readfrom_mem(addr, BNO055._REG_SYS_STAT, 1)[0]
                if stat == 5:
                    return True
                utime.sleep_ms(50)
            return False

        def _wait_sys3(i2c, timeout_s=60):
            print("  Step 4/4 System: Slowly rotate around all three axes (include slow yaw).")
            t0 = utime.ticks_ms()
            hinted = False
            while True:
                d = i2c.readfrom_mem(addr, BNO055._REG_CALIB_STAT, 1)[0]
                sys_ = (d >> 6) & 3
                if sys_ == 3:
                    print("    System OK")
                    return True
                if utime.ticks_diff(utime.ticks_ms(), t0) > timeout_s*1000:
                    return False
                if not hinted and utime.ticks_diff(utime.ticks_ms(), t0) > 5000:
                    print("    Hint: make slow 360° rotations on yaw, then pitch/roll.")
                    hinted = True
                utime.sleep_ms(150)

        i2c = I2CMaster(scl=scl, sda=sda)
        i2c.writeto_mem(addr, BNO055._REG_PAGE_ID, b'\x00')   # Page 0

        def _read_cal():
            d = i2c.readfrom_mem(addr, BNO055._REG_CALIB_STAT, 1)[0]
            return (d >> 6) & 3, (d >> 4) & 3, (d >> 2) & 3, d & 3  # sys, gyro, accel, mag

        mode = i2c.readfrom_mem(addr, BNO055._REG_OPR_MODE, 1)[0]
        if mode != BNO055._MODE_NDOF:
            if mode != BNO055._MODE_CONFIG:
                i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([BNO055._MODE_CONFIG]))
                utime.sleep_ms(20)
            i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([BNO055._MODE_NDOF]))
            utime.sleep_ms(200)
            _wait_fusion_running(i2c)

        print("[BNO055] Interactive calibration started.")

        print("  Step 1/3 Gyro: Place on flat surface and hold.")
        while True:
            sys_, gyr, acc, mag = _read_cal()
            if gyr == 3:
                print("    Gyro OK")
                break
            utime.sleep_ms(150)

        print("  Step 2/3 Accel(6-face): ±X/±Y/±Z slowly.")
        bx, by, bz, radius = BNO055._calibrate_accel_6face(i2c, addr, samples=accel_samples, settle_ms=settle_ms)
        print("    Accel offsets set (LSB): bx=%d, by=%d, bz=%d, radius=%d" % (bx, by, bz, radius))

        t0 = utime.ticks_ms()
        while True:
            sys_, gyr, acc, mag = _read_cal()
            if acc == 3:
                print("    Accel OK")
                break
            if utime.ticks_diff(utime.ticks_ms(), t0) > 5000:
                print("    Accel: timeout waiting for cal=3 (offsets written).")
                break
            utime.sleep_ms(150)
        _wait_fusion_running(i2c)

        print("  Step 3/3 Mag: free space, figure-eight.")
        while True:
            sys_, gyr, acc, mag = _read_cal()
            if mag == 3:
                print("    Mag OK")
                break
            utime.sleep_ms(150)

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

    def __init__(self, scl, sda, *, addr=0x28, calfile=CAL_FILE_NAME):
        self._i2c  = I2CMaster(scl=scl, sda=sda)
        self._addr = int(addr)

        self._buf6 = bytearray(6)
        self._buf8 = bytearray(8)

        if not self._wait_chip_id_ready(1000):
            raise RuntimeError("BNO055 not found or not ready")

        self._set_mode(self._MODE_CONFIG)
        self._i2c.writeto_mem(self._addr, self._REG_SYS_TRIG, bytes([0x20]))  # RST
        utime.sleep_ms(650)
        self._i2c.writeto_mem(self._addr, self._REG_PWR_MODE, bytes([self._PWR_NORMAL]))
        self._i2c.writeto_mem(self._addr, self._REG_PAGE_ID, bytes([0x00]))
        self._i2c.writeto_mem(self._addr, self._REG_SYS_TRIG, bytes([0x80]))  # External crystal
        self._i2c.writeto_mem(self._addr, self._REG_SYS_TRIG, bytes([0x00]))
        utime.sleep_ms(10)
        self._i2c.writeto_mem(self._addr, self._REG_UNIT_SEL, bytes([self._UNITS_SI]))
        self._set_mode(self._MODE_NDOF)

        BNO055._load_calibration_from_file(self._i2c, self._addr, calfile)

    def deinit(self):
        self._set_mode(self._MODE_CONFIG)
        self._i2c.writeto_mem(self._addr, self._REG_PWR_MODE, bytes([0x02]))  # SUSPEND
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

        self._set_mode(self._MODE_CONFIG)
        self._i2c.writeto_mem(self._addr, self._REG_AXIS_MAP_CONFIG, bytes([cfg]))
        self._i2c.writeto_mem(self._addr, self._REG_AXIS_MAP_SIGN,   bytes([sign]))
        self._set_mode(self._MODE_NDOF)

    def wait_ready(self, timeout_s=15):
        t0 = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), t0) < timeout_s*1000:
            d = self._i2c.readfrom_mem(self._addr, self._REG_CALIB_STAT, 1)[0]
            sys_ = (d>>6)&3; gyr=(d>>4)&3; acc=(d>>2)&3; mag=d&3
            if gyr==3 and acc==3 and mag==3 and sys_==3:
                return True
            utime.sleep_ms(150)
        return False

    def read(self):
        return self.accel, self.gyro, self.magnetic, self.quat, self.euler, self.linear, self.gravity, self.temp

    @property
    def diagnostics(self):
        d = self._i2c.readfrom_mem(self._addr, self._REG_CALIB_STAT, 1)[0]
        return {
            "chip_id": self._i2c.readfrom_mem(self._addr, self._REG_CHIP_ID, 1)[0],
            "sys_stat": self._i2c.readfrom_mem(self._addr, self._REG_SYS_STAT, 1)[0],
            "sys_err": self._i2c.readfrom_mem(self._addr, self._REG_SYS_ERR, 1)[0],
            "calib": ((d >> 6) & 3, (d >> 4) & 3, (d >> 2) & 3, d & 3)  # sys, gyro, accel, mag
        }

    @property
    def accel(self):
        self._i2c.readfrom_mem_into(self._addr, self._ACCELERATION, self._buf6)
        x, y, z = ustruct.unpack_from('<hhh', self._buf6, 0)
        s = self._SCALE_ACC_MS2
        return x*s, y*s, z*s

    @property
    def gyro(self):
        self._i2c.readfrom_mem_into(self._addr, self._GYROSCOPE, self._buf6)
        x, y, z = ustruct.unpack_from('<hhh', self._buf6, 0)
        s = self._SCALE_GYR_RADS
        return x*s, y*s, z*s

    @property
    def magnetic(self):
        self._i2c.readfrom_mem_into(self._addr, self._MAGNETIC, self._buf6)
        x, y, z = ustruct.unpack_from('<hhh', self._buf6, 0)
        return x/16.0, y/16.0, z/16.0  # μT

    @property
    def euler(self):
        """Calculate Euler angles (roll, pitch, yaw) from quaternion."""
        w, x, y, z = self.quat
        roll = math.atan2(2*(w*x + y*z), 1 - 2*(x*x + y*y))
        sp = 2*(w*y - z*x)
        sp = -1.0 if sp < -1.0 else (1.0 if sp > 1.0 else sp)
        pitch = math.asin(sp)
        yaw = math.atan2(2*(w*z + x*y), 1 - 2*(y*y + z*z))
        return roll, pitch, yaw

    @property
    def quat(self):
        self._i2c.readfrom_mem_into(self._addr, self._QUATERNION, self._buf8)
        w, x, y, z = ustruct.unpack_from('<hhhh', self._buf8, 0)
        s = self._SCALE_QUAT
        return w*s, x*s, y*s, z*s

    @property
    def linear(self):
        self._i2c.readfrom_mem_into(self._addr, self._ACCEL_LINEAR, self._buf6)
        x, y, z = ustruct.unpack_from('<hhh', self._buf6, 0)
        s = self._SCALE_ACC_MS2
        return x*s, y*s, z*s

    @property
    def gravity(self):
        self._i2c.readfrom_mem_into(self._addr, self._ACCEL_GRAVITY, self._buf6)
        x, y, z = ustruct.unpack_from('<hhh', self._buf6, 0)
        s = self._SCALE_ACC_MS2
        return x*s, y*s, z*s

    @property
    def temp(self):
        t = self._i2c.readfrom_mem(self._addr, self._TEMPERATURE, 1)[0]
        return t - 256 if t > 127 else t

    def _wait_chip_id_ready(self, timeout_ms=1000):
        t0 = utime.ticks_ms()
        while utime.ticks_diff(utime.ticks_ms(), t0) < timeout_ms:
            if self._i2c.readfrom_mem(self._addr, self._REG_CHIP_ID, 1)[0] == 0xA0:
                return True
            utime.sleep_ms(10)
        return False

    def _set_mode(self, mode):
        cur = self._i2c.readfrom_mem(self._addr, self._REG_OPR_MODE, 1)[0]
        if cur == mode:
            return
        if mode == self._MODE_CONFIG or cur != self._MODE_CONFIG:
            self._i2c.writeto_mem(self._addr, self._REG_OPR_MODE, bytes([self._MODE_CONFIG]))
            utime.sleep_ms(20)
        if mode != self._MODE_CONFIG:
            self._i2c.writeto_mem(self._addr, self._REG_OPR_MODE, bytes([mode]))
            utime.sleep_ms(200 if mode == self._MODE_NDOF else 50)

    @staticmethod
    def _load_calibration_from_file(i2c, addr, filename):
        try:
            with open(filename, "rb") as f:
                data = f.read()
        except OSError:
            return False
        if len(data) != BNO055._OFFSETS_LEN:
            return False

        cur = i2c.readfrom_mem(addr, BNO055._REG_OPR_MODE, 1)[0]
        if cur != BNO055._MODE_CONFIG:
            i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([BNO055._MODE_CONFIG]))
            utime.sleep_ms(20)

        i2c.writeto_mem(addr, BNO055._REG_PAGE_ID, bytes([0x00]))
        i2c.writeto_mem(addr, BNO055._REG_OFFSETS_START, data)

        if cur != BNO055._MODE_CONFIG:
            i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([cur]))
            utime.sleep_ms(200 if cur == BNO055._MODE_NDOF else 50)
        return True

    @staticmethod
    def _save_calibration_to_file(i2c, addr, filename):
        cur = i2c.readfrom_mem(addr, BNO055._REG_OPR_MODE, 1)[0]
        if cur != BNO055._MODE_CONFIG:
            i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([BNO055._MODE_CONFIG]))
            utime.sleep_ms(20)

        i2c.writeto_mem(addr, BNO055._REG_PAGE_ID, bytes([0x00]))
        blob = i2c.readfrom_mem(addr, BNO055._REG_OFFSETS_START, BNO055._OFFSETS_LEN)
        try:
            with open(filename, "wb") as f:
                f.write(bytes(blob))
        finally:
            if cur != BNO055._MODE_CONFIG:
                i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([cur]))
                utime.sleep_ms(200 if cur == BNO055._MODE_NDOF else 50)
        return True

    @staticmethod
    def _calibrate_accel_6face(i2c, addr, samples=200, settle_ms=500, timeout_s=120, confirm=False):
        orig = i2c.readfrom_mem(addr, BNO055._REG_OPR_MODE, 1)[0]
        if orig != BNO055._MODE_CONFIG:
            i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([BNO055._MODE_CONFIG]))
            utime.sleep_ms(20)

        i2c.writeto_mem(addr, BNO055._REG_PAGE_ID, bytes([0x00]))
        i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([BNO055._MODE_ACCONLY]))
        utime.sleep_ms(50)

        G = 981  # 1g in LSB (accel LSB=0.01 m/s^2 -> 9.81 m/s^2 = 981 LSB)
        MAIN = int(0.85 * G)
        ORTH = int(0.20 * G)
        STABLE_WIN = 40
        start_ms = utime.ticks_ms()

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
                i2c.readfrom_mem_into(addr, BNO055._ACCELERATION, b)
                x, y, z = ustruct.unpack_from('<hhh', b, 0)
                sx += x; sy += y; sz += z
                utime.sleep_ms(2)
            inv = 1.0/n
            return sx*inv, sy*inv, sz*inv

        def capture_face(tag):
            if confirm:
                print("    Make %s and press Enter…" % tag)
                try: input()
                except Exception: pass

            while True:
                xs = []; ys = []; zs = []
                b = bytearray(6)
                for _ in range(32):
                    i2c.readfrom_mem_into(addr, BNO055._ACCELERATION, b)
                    x, y, z = ustruct.unpack_from('<hhh', b, 0)
                    xs.append(x); ys.append(y); zs.append(z)
                    utime.sleep_ms(5)

                ax = sum(xs)/32; ay = sum(ys)/32; az = sum(zs)/32
                if (max(xs)-min(xs) <= STABLE_WIN and
                    max(ys)-min(ys) <= STABLE_WIN and
                    max(zs)-min(zs) <= STABLE_WIN):
                    got = classify(ax, ay, az)
                    if got == tag:
                        utime.sleep_ms(settle_ms)
                        return avg_vec(samples)

                if utime.ticks_diff(utime.ticks_ms(), start_ms) > timeout_s*1000:
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

        i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([BNO055._MODE_CONFIG]))
        utime.sleep_ms(20)
        i2c.writeto_mem(addr, BNO055._REG_PAGE_ID, bytes([0x00]))

        def w16(reg_lsb, val_s16):
            i2c.writeto_mem(addr, reg_lsb, ustruct.pack('<h', int(val_s16)))

        w16(BNO055._ACC_OFF_X_LSB, bx)
        w16(BNO055._ACC_OFF_Y_LSB, by)
        w16(BNO055._ACC_OFF_Z_LSB, bz)
        w16(BNO055._ACC_RADIUS_LSB, acc_radius)

        i2c.writeto_mem(addr, BNO055._REG_OPR_MODE, bytes([orig]))
        utime.sleep_ms(200 if orig == BNO055._MODE_NDOF else 50)
        return bx, by, bz, acc_radius
