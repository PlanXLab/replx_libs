__version__ = "1.0.1"
__author__  = "PlanX Lab Development Team"

from . import (
    utime, 
    machine
)
from ufilter import Median, TauLowPass, FilterChain


class SR04:
    _TRIG_PULSE_US   = 10         # ≥10us
    _ECHO_TIMEOUT_US = 30000      # 30ms -> 5m upper limit
    _GUARD_US        = 6000       # Minimum interval after last trigger (echo prevention)

    def __init__(self, *, echo:int, trig:int,
                 sound_speed_ms:float=343.2,
                 min_valid_m:float=0.02, max_valid_m:float=4.5,
                 use_median:bool=True, median_window:int=5,
                 use_lpf:bool=False, lpf_tau_s:float=0.05):
        self._echo = machine.Pin(echo, machine.Pin.IN)
        self._trig = machine.Pin(trig, machine.Pin.OUT, value=0)

        self._c = float(sound_speed_ms)
        self._min_m = float(min_valid_m)
        self._max_m = float(max_valid_m)

        self._last_trig_us = -10_000  # Reset to the past enough
        self._last_m = -1             # Previous measurement value to return on guard hit (if none, -1)

        self._filter = None
        if use_median and (median_window and median_window > 1):
            med = Median(median_window)
            if use_lpf and lpf_tau_s and lpf_tau_s > 0:
                lp = TauLowPass(lpf_tau_s, initial=0.0)
                self._filter = FilterChain(med, lp)
            else:
                self._filter = med
        elif use_lpf and lpf_tau_s and lpf_tau_s > 0:
            self._filter = TauLowPass(lpf_tau_s, initial=0.0)

    def deinit(self):
        try:
            self._trig.value(0)
        except Exception:
            pass

    def read(self, timeout_ms:int=50):
        now = utime.ticks_us()
        if utime.ticks_diff(now, self._last_trig_us) < self._GUARD_US:
            return self._last_m

        self._trig.value(0)
        self._trig.value(1)
        utime.sleep_us(self._TRIG_PULSE_US)
        self._trig.value(0)
        self._last_trig_us = utime.ticks_us()

        timeout_us = int(timeout_ms) * 1000
        if timeout_us <= 0 or timeout_us > self._ECHO_TIMEOUT_US:
            timeout_us = self._ECHO_TIMEOUT_US

        try:
            dt_us = machine.time_pulse_us(self._echo, 1, timeout_us)
        except Exception:
            dt_us = -2  # Driver internal error

        if dt_us <= 0:
            # timeout(0), negative error
            self._last_m = -1
            return -1

        d = (self._c * dt_us) * 0.5e-6
        if not (self._min_m <= d <= self._max_m):
            self._last_m = -1
            return -1

        if self._filter is not None:
            try:
                d = float(self._filter.update(d))
            except Exception:
                pass

        self._last_m = d
        return d
