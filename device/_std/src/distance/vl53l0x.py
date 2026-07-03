# @package: vl53l0x
# @version: 2.1.0
# @type: device-std
# @category: distance
# @sensor_type: A
# @interface: I2C
# @depends: i2c, ufilter
# @platforms: *
# @tags: tof, lidar, distance, laser, vl53l0x, ranging
# @author: PlanXLab Development Team

import time
from micropython import const
from i2c import I2CController
from ufilter import Median, TauLowPass, FilterChain

_SYSRANGE_START                      = const(0x00)
_SYSTEM_SEQUENCE_CONFIG              = const(0x01)
_SYSTEM_INTERMEASUREMENT_PERIOD      = const(0x04)
_SYSTEM_INTERRUPT_CONFIG_GPIO        = const(0x0A)
_SYSTEM_INTERRUPT_CLEAR              = const(0x0B)
_GPIO_HV_MUX_ACTIVE_HIGH             = const(0x84)
_RESULT_INTERRUPT_STATUS             = const(0x13)
_RESULT_RANGE_STATUS                 = const(0x14)
_RESULT_RANGE_MM_BE16                = const(0x1E)
_FINAL_RANGE_MIN_CNT_RATE_RTN_LIMIT  = const(0x44)
_MSRC_CONFIG_CONTROL                 = const(0x60)
_MSRC_CONFIG_TIMEOUT_MACROP          = const(0x46)
_PRE_RANGE_CONFIG_VCSEL_PERIOD       = const(0x50)
_PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI  = const(0x51)
_FINAL_RANGE_CONFIG_VCSEL_PERIOD     = const(0x70)
_FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI = const(0x71)
_IDENTIFICATION_MODEL_ID             = const(0xC0)

_VCSEL_PERIOD_PRE_RANGE              = const(0)
_VCSEL_PERIOD_FINAL_RANGE            = const(1)

class VL53L0X:
    MODE_PRESET_DEFAULT                  = 1
    MODE_PRESET_LONG_RANGE               = 2
    MODE_PRESET_HIGH_ACCURACY            = 3
    MODE_PRESET_HIGH_SPEED               = 4

    def __init__(self, sda: int, scl: int, *, addr: int = 0x29,
                 preset: int = MODE_PRESET_DEFAULT,
                 period_ms: int = 0,
                 timeout_ms: int = 250,
                 min_valid_m: float = 0.05,
                 max_valid_m: float | None = 1.2,
                 median: int | None = 5,
                 lpf: float | None = None):
        self._i2c  = I2CController(sda=sda, scl=scl)
        self._addr = int(addr)

        self._timeout_ms = int(timeout_ms)
        self._stop_variable = 0
        self._started = False
        self._period_ms = int(period_ms)

        self._min_m = float(min_valid_m)
        self._max_m = None if max_valid_m is None else float(max_valid_m)
        self._last_m = float('nan')

        self._filter = None
        if median is not None and median > 1:
            w = int(median)
            if w < 3:
                w = 3
            if (w & 1) == 0:
                w += 1
            med = Median(w)
            if lpf is not None and lpf > 0:
                lp = TauLowPass(lpf, initial=0.0)
                self._filter = FilterChain(med, lp)
            else:
                self._filter = med
        elif lpf is not None and lpf > 0:
            self._filter = TauLowPass(lpf, initial=0.0)

        try:
            _ = self._i2c.read_u8(self._addr, _IDENTIFICATION_MODEL_ID)
        except OSError:
            raise RuntimeError("VL53L0X not responding")

        self._core_init()

        if preset == self.MODE_PRESET_LONG_RANGE:
            self.set_signal_rate_limit_mcps(0.1)
            self.set_measurement_timing_budget_us(200_000)
        elif preset == self.MODE_PRESET_HIGH_ACCURACY:
            self.set_signal_rate_limit_mcps(0.25)
            self.set_measurement_timing_budget_us(200_000)
        elif preset == self.MODE_PRESET_HIGH_SPEED:
            self.set_signal_rate_limit_mcps(0.25)
            self.set_measurement_timing_budget_us(20_000)
        elif preset == self.MODE_PRESET_DEFAULT:
            self.set_signal_rate_limit_mcps(0.25)
            self.set_measurement_timing_budget_us(33_000)
        else:
            raise ValueError("Invalid preset")

        self.start(period_ms=self._period_ms)

    def deinit(self):
        if self._started:
            self.stop()

    @property
    def last(self) -> float:
        return self._last_m

    def start(self, period_ms: int = 0):
        if self._started:
            return
        seq = ((0x80, 0x01), (0xFF, 0x01), (0x00, 0x00),
               (0x91, self._stop_variable), (0x00, 0x01), (0xFF, 0x00), (0x80, 0x00))
        for reg, val in seq:
            self._i2c.write_u8(self._addr, reg, val)

        if period_ms and period_ms > 0:
            b = bytes(((period_ms >> 24) & 0xFF, (period_ms >> 16) & 0xFF,
                       (period_ms >> 8) & 0xFF, period_ms & 0xFF))
            self._i2c.writeto_mem(self._addr, _SYSTEM_INTERMEASUREMENT_PERIOD, b, addrsize=8)
            self._i2c.write_u8(self._addr, _SYSRANGE_START, 0x04)
        else:
            self._i2c.write_u8(self._addr, _SYSRANGE_START, 0x02)

        t_end = time.ticks_add(time.ticks_ms(), 50)
        while (self._i2c.read_u8(self._addr, _SYSRANGE_START) & 0x01) > 0:
            if time.ticks_diff(t_end, time.ticks_ms()) <= 0:
                break
        self._started = True

    def stop(self):
        if not self._started:
            return
        self._i2c.write_u8(self._addr, _SYSRANGE_START, 0x01)
        self._started = False

    def ready(self) -> bool:
        if not self._started:
            return False
        return (self._i2c.read_u8(self._addr, _RESULT_INTERRUPT_STATUS) & 0x07) != 0

    def result(self) -> float | None:
        if not self._started:
            return None

        st = (self._i2c.read_u8(self._addr, _RESULT_RANGE_STATUS) & 0x78) >> 3
        mm = self._i2c.read_u16(self._addr, _RESULT_RANGE_MM_BE16, little_endian=False)
        self._i2c.write_u8(self._addr, _SYSTEM_INTERRUPT_CLEAR, 0x01)

        if mm == 0xFFFF or st not in (0, 5, 11):
            return None

        d = mm * 0.001
        if d < self._min_m or (self._max_m is not None and d > self._max_m):
            return None

        if self._filter is not None:
            try:
                d = float(self._filter.update(d))
            except Exception:
                pass

        self._last_m = d
        return d

    def read(self, timeout_ms: int | None = None) -> float:
        if not self._started:
            raise RuntimeError("not started")

        t = timeout_ms if timeout_ms is not None else self._timeout_ms
        deadline = time.ticks_add(time.ticks_ms(), t)

        while not self.ready():
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                return self._last_m
            time.sleep_ms(1)

        val = self.result()
        return val if val is not None else self._last_m

    def reset_filter(self):
        if self._filter is not None:
            try:
                self._filter.reset()
            except AttributeError:
                pass

    def set_signal_rate_limit_mcps(self, limit_mcps: float = 0.25):
        if limit_mcps < 0.0:
            limit_mcps = 0.0
        val = int(limit_mcps * (1 << 7)) & 0xFFFF
        self._i2c.write_u16(self._addr, _FINAL_RANGE_MIN_CNT_RATE_RTN_LIMIT,
                            val, little_endian=False)

    def get_measurement_timing_budget_us(self) -> int:
        tcc, dss, msrc, pre, final = self._get_sequence_step_enables()
        msrc_us, pre_us, final_us, _, _ = self._get_sequence_step_timeouts(pre)
        budget = 1910
        if tcc:
            budget += msrc_us + 590
        if dss:
            budget += 2 * (msrc_us + 690)
        elif msrc:
            budget += msrc_us + 660
        if pre:
            budget += pre_us + 660
        if final:
            budget += final_us + 550
        return int(budget)

    def set_measurement_timing_budget_us(self, budget_us: int):
        if budget_us < 20000:
            budget_us = 20000
        tcc, dss, msrc, pre, final = self._get_sequence_step_enables()
        msrc_us, pre_us, _, final_vcsel_pclks, pre_mclks = self._get_sequence_step_timeouts(pre)

        used = 1910
        if tcc:
            used += msrc_us + 590
        if dss:
            used += 2 * (msrc_us + 690)
        elif msrc:
            used += msrc_us + 660
        if pre:
            used += pre_us + 660
        if final:
            used += 550
            if used > budget_us:
                raise ValueError("budget too small")
            final_timeout_us = budget_us - used
            final_timeout_mclks = self._timeout_us_to_mclks(final_timeout_us, final_vcsel_pclks)
            if pre:
                final_timeout_mclks += pre_mclks
            self._i2c.write_u16(self._addr, _FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI,
                                self._encode_timeout(final_timeout_mclks), little_endian=False)

    def _core_init(self):
        for reg, val in ((0x88, 0x00), (0x80, 0x01), (0xFF, 0x01), (0x00, 0x00)):
            self._i2c.write_u8(self._addr, reg, val)

        self._stop_variable = self._i2c.read_u8(self._addr, 0x91)
        for reg, val in ((0x00, 0x01), (0xFF, 0x00), (0x80, 0x00)):
            self._i2c.write_u8(self._addr, reg, val)

        self._i2c.write_u8(self._addr, _SYSTEM_INTERRUPT_CONFIG_GPIO, 0x04)
        self._i2c.write_u8(self._addr, _GPIO_HV_MUX_ACTIVE_HIGH, 0x00)
        self._i2c.write_u8(self._addr, _SYSTEM_INTERRUPT_CLEAR, 0x01)
        self._i2c.write_u8(self._addr, _MSRC_CONFIG_CONTROL,
                           self._i2c.read_u8(self._addr, _MSRC_CONFIG_CONTROL) | 0x12)

        self._i2c.write_u8(self._addr, _SYSTEM_SEQUENCE_CONFIG, 0xFF)
        tuning = (
            (0xFF, 0x01), (0x00, 0x00), (0xFF, 0x00), (0x09, 0x00), (0x10, 0x00),
            (0x11, 0x00), (0x24, 0x01), (0x25, 0xFF), (0x75, 0x00), (0xFF, 0x01),
            (0x4E, 0x2C), (0x48, 0x00), (0x30, 0x20), (0xFF, 0x00), (0x30, 0x09),
            (0x54, 0x00), (0x31, 0x04), (0x32, 0x03), (0x40, 0x83), (0x46, 0x25),
            (0x60, 0x00), (0x27, 0x00), (0x50, 0x06), (0x51, 0x00), (0x52, 0x96),
            (0x56, 0x08), (0x57, 0x30), (0x61, 0x00), (0x62, 0x00), (0x64, 0x00),
            (0x65, 0x00), (0x66, 0xA0), (0xFF, 0x01), (0x22, 0x32), (0x47, 0x14),
            (0x49, 0xFF), (0x4A, 0x00), (0xFF, 0x00), (0x7A, 0x0A), (0x7B, 0x00),
            (0x78, 0x21), (0xFF, 0x01), (0x23, 0x34), (0x42, 0x00), (0x44, 0xFF),
            (0x45, 0x26), (0x46, 0x05), (0x40, 0x40), (0x0E, 0x06), (0x20, 0x1A),
            (0x43, 0x40), (0xFF, 0x00), (0x34, 0x03), (0x35, 0x44), (0xFF, 0x01),
            (0x31, 0x04), (0x4B, 0x09), (0x4C, 0x05), (0x4D, 0x04), (0xFF, 0x00),
        )
        for reg, val in tuning:
            self._i2c.write_u8(self._addr, reg, val)

    def _get_sequence_step_enables(self):
        sc = self._i2c.read_u8(self._addr, _SYSTEM_SEQUENCE_CONFIG)
        tcc = ((sc >> 4) & 1) != 0
        dss = ((sc >> 3) & 1) != 0
        msrc = ((sc >> 2) & 1) != 0
        pre = ((sc >> 6) & 1) != 0
        final = ((sc >> 7) & 1) != 0
        return tcc, dss, msrc, pre, final

    def _get_vcsel_pulse_period(self, which):
        if which == _VCSEL_PERIOD_PRE_RANGE:
            return self._i2c.read_u8(self._addr, _PRE_RANGE_CONFIG_VCSEL_PERIOD)
        else:
            return self._i2c.read_u8(self._addr, _FINAL_RANGE_CONFIG_VCSEL_PERIOD)

    def _get_sequence_step_timeouts(self, pre_enabled: bool):
        pre_vcsel = self._get_vcsel_pulse_period(_VCSEL_PERIOD_PRE_RANGE)
        msrc_mclks = (self._i2c.read_u8(self._addr, _MSRC_CONFIG_TIMEOUT_MACROP) + 1) & 0xFF
        msrc_us = self._timeout_mclks_to_us(msrc_mclks, pre_vcsel)

        pre_mclks = self._decode_timeout(
            self._i2c.read_u16(self._addr, _PRE_RANGE_CONFIG_TIMEOUT_MACROP_HI, little_endian=False))
        pre_us = self._timeout_mclks_to_us(pre_mclks, pre_vcsel)

        final_vcsel = self._get_vcsel_pulse_period(_VCSEL_PERIOD_FINAL_RANGE)
        final_mclks = self._decode_timeout(
            self._i2c.read_u16(self._addr, _FINAL_RANGE_CONFIG_TIMEOUT_MACROP_HI, little_endian=False))
        if pre_enabled:
            final_mclks -= pre_mclks

        final_us = self._timeout_mclks_to_us(final_mclks, final_vcsel)
        return msrc_us, pre_us, final_us, final_vcsel, pre_mclks

    def _decode_timeout(self, val):
        ls = val & 0xFF
        ms = (val >> 8) & 0xFF
        return int(ls * (1 << ms) + 1)

    def _encode_timeout(self, timeout_mclks):
        if timeout_mclks <= 0:
            return 0
        
        ls = int(timeout_mclks) - 1
        ms = 0
        while ls > 255:
            ls >>= 1
            ms += 1
        return ((ms << 8) | (ls & 0xFF)) & 0xFFFF

    def _macro_period_ns(self, vcsel_period_pclks: int) -> int:
        return ((2304 * vcsel_period_pclks * 1655) + 500) // 1000

    def _timeout_mclks_to_us(self, timeout_mclks: int, vcsel_period_pclks: int) -> int:
        mp_ns = self._macro_period_ns(vcsel_period_pclks)
        return ((timeout_mclks * mp_ns) + (mp_ns // 2)) // 1000

    def _timeout_us_to_mclks(self, timeout_us: int, vcsel_period_pclks: int) -> int:
        mp_ns = self._macro_period_ns(vcsel_period_pclks)
        return ((timeout_us * 1000) + (mp_ns // 2)) // mp_ns
