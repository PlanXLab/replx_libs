# @package: as5600
# @version: 1.0.2
# @type: device-std
# @category: orientation
# @sensor_type: D
# @interface: I2C
# @depends: i2c, ufilter
# @platforms: *
# @tags: encoder, magnetic, angle, rotation, position, velocity, as5600
# @author: PlanXLab Development Team

import math
import time
from micropython import const
from i2c import I2CController
from ufilter import AngleEMA, TauLowPass, SlewRateLimiter

_REG_CONF_H      = const(0x07)
_REG_CONF_L      = const(0x08)
_REG_STATUS      = const(0x0B)
_REG_RAW_ANGLE_H = const(0x0C)
_REG_AGC         = const(0x1A)
_REG_MAG_H       = const(0x1B)

_STATUS_MD = const(0x20)
_STATUS_ML = const(0x10)
_STATUS_MH = const(0x08)

_STATUS_NORMAL        = const(0)
_STATUS_NO_MAGNET     = const(1)
_STATUS_WEAK_MAGNET   = const(2)
_STATUS_STRONG_MAGNET = const(3)
_STATUS_FIELD_RANGE   = const(4)

_CALIB_MODE_FIXED    = const(0)
_CALIB_MODE_ADAPTIVE = const(1)

_TAU      = 2.0 * math.pi
_DEC2RAD  = _TAU / 4096.0
_DEC2DEG  = 360.0 / 4096.0

def to_deg(rad: float) -> float:
    deg = rad * 180.0 / math.pi
    return deg % 360.0

def to_deg_signed(rad: float) -> float:
    d = to_deg(rad)
    return d - 360.0 if d >= 180.0 else d

class AS5600:
    VELOCITY_UNIT_RAD_S_TO_RPM    = 60.0 / _TAU
    VELOCITY_UNIT_RAD_S_TO_RPS    = 1.0 / _TAU

    STATUS_NORMAL                 = _STATUS_NORMAL
    STATUS_NO_MAGNET              = _STATUS_NO_MAGNET
    STATUS_WEAK_MAGNET            = _STATUS_WEAK_MAGNET
    STATUS_STRONG_MAGNET          = _STATUS_STRONG_MAGNET
    STATUS_FIELD_RANGE            = _STATUS_FIELD_RANGE

    CALIB_SOFT_ZERO_MODE_FIXED    = _CALIB_MODE_FIXED
    CALIB_SOFT_ZERO_MODE_ADAPTIVE = _CALIB_MODE_ADAPTIVE

    DEFAULT_CAL_FILE = "lib/ticle/as5600_zero.cal"

    def __init__(self, sda: int, scl: int, *, addr=0x36,
                 ema_alpha=0.25,
                 vel_tau_s=0.02,
                 vel_slew_rise=1e9,
                 vel_slew_fall=1e9,
                 cal_file: str = None,
                 apply_conf: bool = True,
                 hysteresis: int = 1,
                 slow_filter: int = 3,
                 fast_filter_threshold: int = 4,
                 watchdog: int = 0,
                 cache_window_us=500  # Lazy cache window (recommended: 200~2000us)
                 ):
        self._i2c = I2CController(sda=sda, scl=scl)
        self._addr = int(addr)
        
        self._b1 = bytearray(1)
        self._b2 = bytearray(2)

        self._mt_accum = 0.0
        self._mt_path = 0.0
        self._mt_last = None
        self._mt_last_dec = None
        self._mt_residual_ticks = 0
        self._mt_streak_sign = 0
        self._mt_streak_len = 0
        self._mt_streak_sum = 0

        self._soft_z_raw  = 0

        self._v_last_dec = None
        self._v_last_ts = None
        self._v_rad_s = 0.0
        self._v_residual = 0
        self._v_last_emit_ts = None
        self._v_last_vel = 0.0

        self._angle_ema = AngleEMA(ema_alpha)
        self._vel_lp = TauLowPass(tau_s=vel_tau_s, initial=0.0)
        self._vel_slew = SlewRateLimiter(rise_per_s=vel_slew_rise, fall_per_s=vel_slew_fall)

        self._cache_window_us = int(cache_window_us)
        self._cache_ts_us = None
        self._cache_ticks = None
        self._cache_dec = None

        self._last_angle = 0.0
        self._last_vel = 0.0
        self._last_turn = (0.0, 0.0)
        self._last_ts_us = 0
        self._last_status = self.STATUS_NORMAL

        if apply_conf:
            self.set_conf(hysteresis=hysteresis, slow_filter=slow_filter, fast_filter_threshold=fast_filter_threshold, watchdog=watchdog)

        self._cal_file = cal_file or self.DEFAULT_CAL_FILE
        self._load_soft_zero_from_file(self._cal_file)

    def reset_cache(self):
        self._cache_ts_us = None
        self._cache_ticks = None
        self._cache_dec = None

    def _ensure_sample(self, now_us=None):
        now = time.ticks_us() if now_us is None else now_us
        if (self._cache_ts_us is not None and
            self._cache_ticks is not None and
            time.ticks_diff(now, self._cache_ts_us) <= self._cache_window_us):
            return self._cache_ticks, self._cache_dec, self._cache_ts_us

        dec = self._raw_angle_dec()
        ticks = (dec - self._soft_z_raw) & 0x0FFF

        self._cache_ts_us = now
        self._cache_ticks = ticks
        self._cache_dec = dec
        return ticks, dec, now

    def status(self) -> int:
        self._i2c.readfrom_mem_into(self._addr, _REG_STATUS, self._b1)
        s = self._b1[0]
        md = bool(s & _STATUS_MD)
        ml = bool(s & _STATUS_ML)
        mh = bool(s & _STATUS_MH)
        if not md:
            return _STATUS_NO_MAGNET
        if ml and mh:
            return _STATUS_FIELD_RANGE
        if ml:
            return _STATUS_WEAK_MAGNET
        if mh:
            return _STATUS_STRONG_MAGNET
        return _STATUS_NORMAL

    def health_ok(self) -> bool:
        return self.status() == self.STATUS_NORMAL

    def set_conf(self, *, hysteresis=1, slow_filter=3, fast_filter_threshold=4, watchdog=0):
        if not (0 <= hysteresis <= 3):
            raise ValueError("hysteresis 0..3")
        if not (0 <= slow_filter <= 3):
            raise ValueError("slow_filter 0..3")
        if not (0 <= fast_filter_threshold <= 6):
            raise ValueError("fast_filter_threshold 0..6")
        if watchdog not in (0, 1):
            raise ValueError("watchdog 0/1")

        power_mode = 0  # full power
        lsb = ((hysteresis & 0b11) << 2) | power_mode
        msb = ((watchdog & 1) << 13) | ((fast_filter_threshold & 0b111) << 10) | ((slow_filter & 0b11) << 8)
        self._i2c.write_u8(self._addr, _REG_CONF_H, (msb >> 8) & 0xFF)
        self._i2c.write_u8(self._addr, _REG_CONF_L, lsb & 0xFF)

    def agc(self) -> int:
        self._i2c.readfrom_mem_into(self._addr, _REG_AGC, self._b1)
        return self._b1[0]

    def magnitude(self) -> int:
        self._i2c.readfrom_mem_into(self._addr, _REG_MAG_H, self._b2)
        return ((self._b2[0] << 8) | self._b2[1]) & 0x0FFF

    def set_soft_zero_now(self):
        self._soft_z_raw = self._raw_angle_dec() & 0x0FFF
        ticks = 0
        self._angle_ema.reset(ticks * _DEC2RAD)
        self.reset_cache()

    def calibrate_soft_zero(self, *,
                            samples=64,
                            still_samples=20,
                            still_timeout_ms=4000,
                            still_thresh_lsb=1,
                            still_mode=_CALIB_MODE_FIXED,
                            still_window=16,
                            still_k=3.0,
                            still_warmup=8,
                            verbose=False,
                            save_path: str = None) -> bool:
        last = self._raw_angle_dec()
        still = 0
        t0 = time.ticks_ms()

        if still_mode not in (_CALIB_MODE_FIXED, _CALIB_MODE_ADAPTIVE):
            raise ValueError("still_mode must be CALIB_SOFT_ZERO_MODE_FIXED or CALIB_SOFT_ZERO_MODE_ADAPTIVE")

        hist = []
        maxw = max(4, int(still_window))
        warmup = max(2, int(still_warmup))

        while still < still_samples:
            now = self._raw_angle_dec()
            d = now - last
            if d > 2048:
                d -= 4096
            elif d < -2048: 
                d += 4096
            ad = abs(d)
            last = now

            if still_mode == _CALIB_MODE_FIXED:
                ok = (ad <= still_thresh_lsb)
            else:
                if len(hist) >= maxw:
                    hist.pop(0)
                hist.append(ad)
                if len(hist) < warmup:
                    ok = (ad <= max(1, 2 * still_thresh_lsb))
                else:
                    med = self._median(hist)
                    mad = self._mad(hist, med)
                    sigma = 1.4826 * mad
                    dyn_thresh = med + still_k * sigma
                    dyn_thresh = max(float(still_thresh_lsb), dyn_thresh)
                    ok = (ad <= dyn_thresh)
                    if verbose and (still == 0 or (still % 10) == 0):
                        print(f"ADAPT med={med:.2f} mad={mad:.2f} sig={sigma:.2f} thr={dyn_thresh:.2f} | ad={ad}")

            still = still + 1 if ok else 0
            if time.ticks_diff(time.ticks_ms(), t0) > still_timeout_ms:
                raise RuntimeError("Stop detection timeout")
            time.sleep_ms(5)

        if verbose:
            print(f"Stop confirmed (mode={still_mode})")

        acc_raw = 0
        for _ in range(samples):
            acc_raw += self._raw_angle_dec()
            time.sleep_ms(2)
        self._soft_z_raw = (acc_raw // samples) & 0x0FFF

        r_now = ((self._raw_angle_dec() - self._soft_z_raw) & 0x0FFF) * _DEC2RAD
        self._angle_ema.reset(r_now)

        self.reset_cache()
        return self._save_soft_zero_to_file(save_path or self._cal_file)

    def angle(self, *, soft_zero=True, filtered=False) -> float:
        ticks, dec, ts = self._ensure_sample()
        if soft_zero:
            r = ticks * _DEC2RAD
        else:
            r = (dec & 0x0FFF) * _DEC2RAD
        if filtered:
            r = self._angle_ema.update(r)
        r = (r + _TAU) % _TAU  # 0..2pi

        self._last_angle = r
        self._last_ts_us = ts
        return r

    def angle_deg(self, *, soft_zero=True, filtered=False) -> float:
        return self.angle(soft_zero=soft_zero, filtered=filtered) * 180.0 / math.pi

    def velocity_rpm(self, *, filtered=False) -> float:
        return self.velocity(filtered=filtered) * self.VELOCITY_UNIT_RAD_S_TO_RPM

    def velocity(self, *,
                 filtered=False,
                 tick_emit=4,
                 tick_hold=2,
                 dt_min_s=0.003,
                 dt_max_s=0.5,
                 omega_clip=None):
        ticks, dec, ts = self._ensure_sample()

        if self._v_last_dec is None:
            self._v_last_dec = dec
            self._v_last_ts = ts
            self._v_rad_s = 0.0
            self._v_residual = 0
            self._v_last_emit_ts = ts
            self._v_last_vel = 0.0
            self._last_vel = 0.0
            self._last_ts_us = ts
            return 0.0

        d = ((dec - self._v_last_dec + 2048) & 0xFFF) - 2048
        self._v_last_dec = dec

        residual = self._v_residual + d
        if -tick_hold < residual < tick_hold:
            residual = 0

        emit = 0
        while residual >= tick_emit:
            emit += 1
            residual -= tick_emit
        while residual <= -tick_emit:
            emit -= 1
            residual += tick_emit
        self._v_residual = residual

        dt_call = time.ticks_diff(ts, self._v_last_ts) / 1_000_000.0
        self._v_last_ts = ts
        if dt_call < 0:
            dt_call = 1e-6

        if emit == 0:
            self._v_rad_s = 0.0
            self._last_vel = 0.0
            self._last_ts_us = ts
            return 0.0

        dt_emit = time.ticks_diff(ts, self._v_last_emit_ts) / 1_000_000.0
        if dt_emit < dt_min_s or dt_emit <= 0.0:
            self._last_vel = self._v_last_vel
            self._last_ts_us = ts
            return self._last_vel

        if dt_emit > dt_max_s:
            self._v_last_emit_ts = ts
            self._v_last_vel = 0.0
            self._v_rad_s = 0.0
            self._last_vel = 0.0
            self._last_ts_us = ts
            return 0.0

        rad_s = (emit * tick_emit * _DEC2RAD) / dt_emit
        if omega_clip is not None:
            if rad_s >  omega_clip: rad_s =  omega_clip
            if rad_s < -omega_clip: rad_s = -omega_clip

        if filtered:
            rad_s = self._vel_lp.update_with_dt(rad_s, dt_emit)
            rad_s = self._vel_slew.update_with_dt(rad_s, dt_emit)

        self._v_last_emit_ts = ts
        self._v_last_vel = rad_s
        self._v_rad_s = rad_s

        self._last_vel = rad_s
        self._last_ts_us = ts
        return rad_s

    def reset_velocity(self):
        self._v_last_dec = None
        self._v_last_ts = None
        self._v_rad_s = 0.0
        self._v_residual = 0
        self._v_last_emit_ts = None
        self._v_last_vel = 0.0
        self._last_vel = 0.0

    def reset_turn(self):
        self._mt_accum = 0.0
        self._mt_path = 0.0
        self._mt_last = None
        self._mt_last_dec = None
        self._mt_residual_ticks = 0
        self._mt_streak_sign = 0
        self._mt_streak_len = 0
        self._mt_streak_sum = 0

    def turn(self, *, soft_zero=True, filtered=False, tick_thr=2, confirm_samples=3):
        ticks, dec_now, ts = self._ensure_sample()
        if soft_zero:
            now = ticks * _DEC2RAD
        else:
            now = (dec_now & 0x0FFF) * _DEC2RAD
        if filtered:
            now = self._angle_ema.update(now)
        now = (now + _TAU) % _TAU

        if self._mt_last is None:
            self._mt_last = now
            self._mt_last_dec = dec_now
            self._mt_accum = 0.0
            self._mt_path = 0.0
            self._mt_residual_ticks = 0
            self._mt_streak_sign = 0
            self._mt_streak_len = 0
            self._mt_streak_sum = 0
            self._last_turn = (0.0, 0.0)
            self._last_ts_us = ts
            return 0.0, 0.0

        d0 = dec_now - self._mt_last_dec
        if d0 > 2048:
            d0 -= 4096
        elif d0 < -2048:
            d0 += 4096

        if abs(d0) >= 1:
            s = 1 if d0 > 0 else -1
            if s == self._mt_streak_sign:
                self._mt_streak_len += 1
                self._mt_streak_sum += d0
            else:
                self._mt_streak_sign = s
                self._mt_streak_len = 1
                self._mt_streak_sum = d0
        else:
            self._mt_streak_sign = 0
            self._mt_streak_len = 0
            self._mt_streak_sum = 0

        emit_ticks = 0
        if self._mt_streak_len >= confirm_samples:
            self._mt_residual_ticks += self._mt_streak_sum
            self._mt_streak_sign = 0
            self._mt_streak_len = 0
            self._mt_streak_sum = 0

            while self._mt_residual_ticks >= tick_thr:
                emit_ticks += 1
                self._mt_residual_ticks -= 1

            while self._mt_residual_ticks <= -tick_thr:
                emit_ticks -= 1
                self._mt_residual_ticks += 1

        if emit_ticks != 0:
            d_rad = emit_ticks * _DEC2RAD
            self._mt_accum += d_rad
            self._mt_path += abs(d_rad)
            self._mt_last = now
            self._mt_last_dec = dec_now

        out = (self._mt_accum / _TAU, self._mt_path / _TAU)
        self._last_turn = out
        self._last_ts_us = ts
        return out

    @staticmethod
    def _median(seq):
        n = len(seq)
        if n == 0:
            return 0
        b = sorted(seq)
        mid = n // 2
        if n & 1:
            return b[mid]
        return 0.5 * (b[mid-1] + b[mid])

    @staticmethod
    def _mad(seq, med):
        n = len(seq)
        if n == 0:
            return 0
        dev = bytearray(n)
        for i, x in enumerate(seq):
            d = abs(x - med)
            dev[i] = int(d) if d < 256 else 255
        b = sorted(dev)
        mid = n // 2
        if n & 1:
            return b[mid]
        return 0.5 * (b[mid-1] + b[mid])

    def _raw_angle_dec(self) -> int:
        self._i2c.readfrom_mem_into(self._addr, _REG_RAW_ANGLE_H, self._b2)
        return ((self._b2[0] << 8) | self._b2[1]) & 0x0FFF

    def _save_soft_zero_to_file(self, path: str) -> bool:
        try:
            p = path or self._cal_file
            buf = int(self._soft_z_raw & 0x0FFF).to_bytes(2, "big")

            with open(p, "wb") as f:
                f.write(buf)
            return True
        except Exception:
            return False

    def _load_soft_zero_from_file(self, path: str) -> bool:
        try:
            p = path or self._cal_file
            with open(p, "rb") as f:
                b = f.read()

            if len(b) != 2:
                return False
            self._soft_z_raw = int.from_bytes(b, "big") & 0x0FFF
            return True
        except Exception:
            return False
