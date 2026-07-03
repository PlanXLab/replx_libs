# @package: us
# @version: 3.5
# @type: device-std
# @category: distance
# @sensor_type: B
# @interface: GPIO
# @depends: dio, ufilter
# @platforms: *
# @tags: ultrasonic, distance, sr04, hc-sr04, ranging, multi-sensor
# @author: PlanXLab Development Team

from micropython import const
import machine
import time
from dio import Din, Dout
from ufilter import Median, TauLowPass, FilterChain

_TRIG_PULSE_US = const(10)
_ECHO_TIMEOUT_US = const(30000)  # absolute ceiling: ~5.15 m round-trip at 343 m/s
_GUARD_MARGIN_US  = const(5000)  # reverberation settling added on top of echo timeout


class SR04:
    def __init__(
        self, *,
        echo: int | list[int],
        trig: int | list[int],
        sound_speed_ms: float = 343.2,
        min_valid_m: float = 0.02,
        max_valid_m: float = 4.5,
        interference_delay_ms: int = 0,
        median: int | None = None,
        lpf: float | None = None
    ):
        if isinstance(echo, int):
            echo = [echo]
        if isinstance(trig, int):
            trig = [trig]
        
        if len(echo) != len(trig):
            raise ValueError("echo and trig must have same length")
        
        self._n = len(echo)
        self._single = (self._n == 1)
        
        self._echo = Din(echo)
        self._trig = Dout(trig)
        self._echo_pin = self._echo.pins
        self._trig_pin = self._trig.pins
        
        self._c = float(sound_speed_ms)
        self._min_m = float(min_valid_m)
        self._max_m = float(max_valid_m)
        self._interference_ms = int(interference_delay_ms)

        # Derive echo timeout from max_valid_m so the driver never blocks
        # longer than necessary.  Round-trip time (µs) + 2 ms margin, capped
        # at the hardware ceiling _ECHO_TIMEOUT_US.
        echo_us = int(max_valid_m * 2.0 / float(sound_speed_ms) * 1_000_000) + 2000
        self._echo_timeout_us: int = min(int(_ECHO_TIMEOUT_US), max(2000, echo_us))
        # Guard = echo timeout + 5 ms for reverberation to dissipate.
        # This is typically 15-35 ms instead of the old hard-coded 60 ms.
        self._guard_us: int = self._echo_timeout_us + int(_GUARD_MARGIN_US)

        initial_trig_us = time.ticks_add(time.ticks_us(), -self._guard_us)
        self._last_trig_us = [initial_trig_us] * self._n
        self._last_m = [float('nan')] * self._n
        self._pending = [False] * self._n
        
        self._filters = [None] * self._n
        for i in range(self._n):
            self._filters[i] = self._create_filter(median, lpf)
        
        self._view = SR04._View(self)

    def _create_filter(self, median: int | None, lpf: float | None):
        if median is not None and median > 1:
            med = Median(median)
            if lpf is not None and lpf > 0:
                lp = TauLowPass(lpf, initial=0.0)
                return FilterChain(med, lp)
            return med
        elif lpf is not None and lpf > 0:
            return TauLowPass(lpf, initial=0.0)
        return None

    def _normalize_timeout_ms(self, timeout_ms) -> int:
        """Return the clamped echo timeout in milliseconds.

        Pass *None* to use the instance default derived from *max_valid_m*.
        """
        if timeout_ms is None:
            return max(1, (self._echo_timeout_us + 999) // 1000)
        timeout_us = int(timeout_ms) * 1000
        if timeout_us <= 0 or timeout_us > self._echo_timeout_us:
            timeout_us = self._echo_timeout_us
        return max(1, (timeout_us + 999) // 1000)

    def _wait_echo_low(self, idx: int, timeout_ms: int) -> bool:
        echo_pin = self._echo_pin[idx]
        if echo_pin.value() == 0:
            return True  # fast path – pin already idle
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while echo_pin.value() == 1:
            if time.ticks_diff(time.ticks_ms(), deadline) >= 0:
                return False
            time.sleep_us(50)
        return True

    def _stop_pulse_capture(self, idx: int) -> None:
        try:
            self._echo.stop_pulse_capture(idx)
        except Exception:
            pass
        self._echo._pulse_ready[idx] = False
        self._echo._pulse_start[idx] = 0
        self._echo._pulse_end[idx] = 0
        self._pending[idx] = False

    def _emit_trigger_pulse(self, idx: int) -> None:
        trig_pin = self._trig_pin[idx]
        trig_pin.value(0)
        time.sleep_us(2)
        trig_pin.value(1)
        time.sleep_us(_TRIG_PULSE_US)
        trig_pin.value(0)
        self._last_trig_us[idx] = time.ticks_us()

    def _measure_pulse_blocking(self, idx: int, timeout_ms=None) -> int:
        timeout_ms = self._normalize_timeout_ms(timeout_ms)
        self._stop_pulse_capture(idx)

        elapsed_us = time.ticks_diff(time.ticks_us(), self._last_trig_us[idx])
        if 0 <= elapsed_us < self._guard_us:
            time.sleep_us(self._guard_us - elapsed_us)

        if not self._wait_echo_low(idx, timeout_ms):
            return -1

        self._emit_trigger_pulse(idx)

        try:
            return machine.time_pulse_us(self._echo_pin[idx], 1, timeout_ms * 1000)
        except Exception:
            return -1

    def _distance_from_pulse(self, idx: int, dt_us: int) -> float:
        if dt_us <= 0:
            return float('nan')

        d = (self._c * dt_us) * 0.5e-6
        if d < self._min_m or d > self._max_m:
            return float('nan')

        if self._filters[idx] is not None:
            try:
                d = float(self._filters[idx].update(d))
            except Exception:
                pass

        self._last_m[idx] = d
        return d

    def deinit(self):
        try:
            self._echo.deinit()
            self._trig.deinit()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def __len__(self) -> int:
        return self._n

    def __getitem__(self, idx: int | slice) -> "_View":
        if isinstance(idx, slice):
            indices = tuple(range(*idx.indices(self._n)))
            return self._view._set(indices)
        elif isinstance(idx, int):
            if not (0 <= idx < self._n):
                raise IndexError("Sensor index out of range")
            return self._view._set((idx,))
        else:
            raise TypeError("Index must be int or slice")

    @property
    def last(self) -> float:
        if not self._single:
            raise RuntimeError("Use sr04[idx].last for multi-sensor")
        return self._last_m[0]

    def trigger(self) -> None:
        if not self._single:
            raise RuntimeError("Use sr04[idx].trigger() for multi-sensor")
        idx = 0
        now = time.ticks_us()
        if self._pending[idx]:
            return
        elapsed_us = time.ticks_diff(now, self._last_trig_us[idx])
        if 0 <= elapsed_us < self._guard_us:
            return
        if not self._wait_echo_low(idx, 5):
            return
        self._pending[idx] = True
        self._echo.start_pulse_capture(idx, level=1)
        self._emit_trigger_pulse(idx)

    def ready(self) -> bool:
        if not self._single:
            raise RuntimeError("Use sr04[idx].ready for multi-sensor")
        return self._pending[0] and self._echo.pulse_ready(0)

    def result(self, timeout_ms=None) -> float:
        if not self._single:
            raise RuntimeError("Use sr04[idx].result() for multi-sensor")
        idx = 0
        if not self._pending[idx]:
            return float('nan')

        timeout_ms = self._normalize_timeout_ms(timeout_ms)
        capture_ok = self._echo.wait_pulse_ready(idx, timeout_ms=timeout_ms)

        self._pending[idx] = False
        dt_us = self._echo.pulse_width_us(idx)
        self._echo.stop_pulse_capture(idx)
        if not capture_ok or dt_us <= 0:
            dt_us = self._measure_pulse_blocking(idx, timeout_ms)

        return self._distance_from_pulse(idx, dt_us)

    def read(self, timeout_ms=None) -> float:
        if not self._single:
            raise RuntimeError("Use sr04[idx].read() for multi-sensor")
        dt_us = self._measure_pulse_blocking(0, timeout_ms)
        return self._distance_from_pulse(0, dt_us)

    def reset_filter(self):
        for f in self._filters:
            if f is not None:
                try:
                    f.reset()
                except AttributeError:
                    pass

    class _View:
        __slots__ = ('_p', '_i')

        def __init__(self, parent: "SR04"):
            self._p = parent
            self._i = None

        def _set(self, indices) -> "SR04._View":
            self._i = indices
            return self

        def __len__(self) -> int:
            return len(self._i)

        def __getitem__(self, idx: int | slice) -> "SR04._View":
            if isinstance(idx, slice):
                self._i = [self._i[j] for j in range(*idx.indices(len(self._i)))]
            else:
                self._i = [self._i[idx]]
            return self

        @property
        def last(self) -> list[float]:
            return [self._p._last_m[i] for i in self._i]

        def trigger(self) -> None:
            p = self._p
            now = time.ticks_us()

            trigger_indices = []
            for idx in self._i:
                if p._pending[idx]:
                    continue
                elapsed_us = time.ticks_diff(now, p._last_trig_us[idx])
                if 0 <= elapsed_us < p._guard_us:
                    continue

                if not p._wait_echo_low(idx, 5):
                    continue

                p._pending[idx] = True
                trigger_indices.append(idx)

            if not trigger_indices:
                return

            for idx in trigger_indices:
                p._echo[idx].start_pulse_capture(level=1)

            for idx in trigger_indices:
                p._emit_trigger_pulse(idx)

        @property
        def ready(self) -> list[bool]:
            p = self._p
            result = []
            for idx in self._i:
                if not p._pending[idx]:
                    result.append(False)
                else:
                    result.append(p._echo.pulse_ready(idx))
            return result

        def result(self, timeout_ms=None) -> list[float]:
            p = self._p
            results = []
            timeout_ms = p._normalize_timeout_ms(timeout_ms)
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            for idx in self._i:
                if not p._pending[idx]:
                    results.append(float('nan'))
                    continue
                
                echo_view = p._echo[idx]

                remaining_ms = time.ticks_diff(deadline, time.ticks_ms())
                if remaining_ms < 0:
                    remaining_ms = 0
                capture_ok = echo_view.wait_pulse_ready(timeout_ms=remaining_ms)

                p._pending[idx] = False
                dt_us = echo_view.pulse_width_us()
                echo_view.stop_pulse_capture()

                # The IRQ capture path can miss edges on some boards even
                # though machine.time_pulse_us remains stable. Fall back to a
                # direct blocking measurement so read()/result() return a real
                # reading instead of repeating timeout-only failures.
                if not capture_ok or dt_us <= 0:
                    dt_us = p._measure_pulse_blocking(idx, timeout_ms)

                results.append(p._distance_from_pulse(idx, dt_us))
            
            return results

        def read(self, timeout_ms=None) -> list[float]:
            p = self._p
            timeout_ms = p._normalize_timeout_ms(timeout_ms)
            results = []

            for idx in self._i:
                dt_us = p._measure_pulse_blocking(idx, timeout_ms)
                results.append(p._distance_from_pulse(idx, dt_us))
                if idx != self._i[-1] and p._interference_ms > 0:
                    time.sleep_ms(p._interference_ms)

            return results

        @property
        def sound_speed(self) -> float:
            return self._p._c

        @sound_speed.setter
        def sound_speed(self, value: float):
            self._p._c = float(value)

        def reset_filter(self):
            for idx in self._i:
                f = self._p._filters[idx]
                if f is not None:
                    try:
                        f.reset()
                    except AttributeError:
                        pass
