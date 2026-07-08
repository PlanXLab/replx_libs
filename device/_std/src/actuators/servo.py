# @package: servo
# @version: 4.5
# @type: device-std
# @category: actuators
# @interface: PWM
# @depends: pout, utools
# @platforms: *
# @tags: servo, motor, actuator, pwm, positional, continuous, easing
# @author: PlanXLab Development Team

import time
import machine
from pout import Pout
from utools import clamp

from micropython import const

_POSITIONAL = const(0)
_CONTINUOUS = const(1)

_EASE_LINEAR = const(0)
_EASE_QUAD = const(1)
_EASE_CUBIC = const(2)

_AUTO_MS_PER_DEG = 400.0 / 60.0
_AUTO_MOVE_MARGIN_MS = const(50)
_MIN_MOVE_MS = const(50)

# Properties on _View that can be set via Servo.__setattr__ in single-servo mode
_VIEW_SETABLE = frozenset({'angle', 'speed', 'duty_us', 'home_angle', 'calibration'})

def _ease(t, mode):
    if mode == _EASE_LINEAR:
        return t
    if mode == _EASE_QUAD:
        if t < 0.5:
            return 2.0 * t * t
        return -1.0 + (4.0 - 2.0 * t) * t
    if mode == _EASE_CUBIC:
        if t < 0.5:
            return 4.0 * t * t * t
        t2 = 2.0 * t - 2.0
        return 0.5 * t2 * t2 * t2 + 1.0
    return t

def _easing_mode(easing):
    if easing not in _EASING_MAP:
        raise ValueError("easing must be 'linear', 'quad', or 'cubic'")
    return _EASING_MAP[easing]

_EASING_MAP = {
    'linear': _EASE_LINEAR,
    'quad': _EASE_QUAD,
    'cubic': _EASE_CUBIC,
}

class Servo:
    MODE_POSITIONAL = 'positional'
    MODE_CONTINUOUS = 'continuous'

    EASE_LINEAR = 'linear'
    EASE_QUAD = 'quad'
    EASE_CUBIC = 'cubic'

    def __init__(
        self,
        pins: int | list[int] | tuple[int, ...],
        *,
        mode: str = 'positional',
        freq: int = 50,
        min_us: int = 500,
        max_us: int = 2500,
        center_us: int = 1500,
        home_angle: float = 90.0
    ):
        self._single = isinstance(pins, int)
        if isinstance(pins, int):
            pins = [pins]
        if not pins:
            raise ValueError("pins must not be empty")
        if mode not in (self.MODE_POSITIONAL, self.MODE_CONTINUOUS):
            raise ValueError("mode must be 'positional' or 'continuous'")
        if min_us >= max_us:
            raise ValueError("min_us must be less than max_us")
        if not (min_us <= center_us <= max_us):
            raise ValueError("center_us must be between min_us and max_us")
        if freq <= 0:
            raise ValueError("freq must be positive")

        self._pout = Pout(pins)
        self._pout.set_freq_all(freq)
        self._n = len(pins)
        self._mode = _CONTINUOUS if mode == self.MODE_CONTINUOUS else _POSITIONAL

        self._min_us = [min_us] * self._n
        self._max_us = [max_us] * self._n
        self._center_us = [center_us] * self._n
        self._home = [clamp(float(home_angle), 0.0, 180.0)] * self._n

        self._value = [0.0] * self._n
        self._target = [0.0] * self._n
        self._is_moving = [False] * self._n
        self._move_start = [0] * self._n
        self._move_from = [0.0] * self._n
        self._move_dur = [1000] * self._n
        self._ease_mode = [_EASE_LINEAR] * self._n

        self._timer = None
        self._timer_active = False
        self._shutdown = False
        self._views = [Servo._View(self, (i,)) for i in range(self._n)]
        if self._mode == _POSITIONAL:
            for i in range(self._n):
                self._value[i] = self._home[i]
                self._target[i] = self._home[i]
                self._pout.set_duty_us(self._angle_to_us(self._home[i], i), idx=i)
        else:
            for i in range(self._n):
                self._pout.set_duty_us(self._center_us[i], idx=i)

    def deinit(self):
        self._shutdown = True
        self._timer_active = False
        if self._timer is not None:
            try:
                self._timer.deinit()
            except:
                pass
            self._timer = None
        time.sleep_ms(20)
        self._pout.deinit()

    def __len__(self):
        return self._n

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            indices = tuple(range(*idx.indices(self._n)))
        elif isinstance(idx, int):
            if idx < 0:
                idx += self._n
            if not (0 <= idx < self._n):
                raise IndexError("Index out of range")
            return self._views[idx]
        else:
            raise TypeError("Index must be int or slice")
        return Servo._View(self, indices)

    def __getattr__(self, name):
        """Delegate attribute lookups to _views[0] in single-servo mode."""
        try:
            single = object.__getattribute__(self, '_single')
        except AttributeError:
            raise AttributeError(name)
        if single:
            return getattr(object.__getattribute__(self, '_views')[0], name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        """Delegate settable _View properties to _views[0] in single-servo mode."""
        if name.startswith('_'):
            object.__setattr__(self, name, value)
            return
        try:
            single = object.__getattribute__(self, '_single')
        except AttributeError:
            object.__setattr__(self, name, value)
            return
        if single and name in _VIEW_SETABLE:
            setattr(object.__getattribute__(self, '_views')[0], name, value)
        else:
            object.__setattr__(self, name, value)

    def _angle_to_us(self, deg, i):
        deg = clamp(deg, 0.0, 180.0)
        return int(self._min_us[i] + (self._max_us[i] - self._min_us[i]) * deg / 180.0)

    def _us_to_angle(self, us, i):
        span = self._max_us[i] - self._min_us[i]
        return clamp((int(us) - self._min_us[i]) * 180.0 / span, 0.0, 180.0)

    def _speed_to_us(self, spd, i):
        spd = clamp(spd, -100.0, 100.0)
        if abs(spd) < 1.0:
            return self._center_us[i]
        delta = (self._max_us[i] - self._center_us[i]) if spd > 0 else (self._center_us[i] - self._min_us[i])
        return int(self._center_us[i] + delta * spd / 100.0)

    def _us_to_speed(self, us, i):
        us = int(us)
        if us == self._center_us[i]:
            return 0.0
        if us > self._center_us[i]:
            span = self._max_us[i] - self._center_us[i]
            return clamp((us - self._center_us[i]) * 100.0 / span, -100.0, 100.0)
        span = self._center_us[i] - self._min_us[i]
        return clamp((us - self._center_us[i]) * 100.0 / span, -100.0, 100.0)

    def _auto_move_ms(self, i, target):
        travel = abs(float(target) - self._value[i])
        return max(_MIN_MOVE_MS, int(travel * _AUTO_MS_PER_DEG) + _AUTO_MOVE_MARGIN_MS)

    def _start_timer(self):
        if self._timer is None:
            self._timer = machine.Timer()
        if not self._timer_active:
            self._timer_active = True
            self._timer.init(period=20, mode=machine.Timer.PERIODIC, callback=self._tick)

    def _stop_timer(self):
        if self._timer_active:
            self._timer_active = False
            if self._timer is not None:
                try:
                    self._timer.deinit()
                except:
                    pass
            # Timer object is kept alive for reuse; only deinit() should set it to None

    def _tick(self, t):
        try:
            if self._shutdown:
                return
            any_active = False
            now = time.ticks_ms()

            for i in range(self._n):
                if not self._is_moving[i]:
                    continue

                elapsed = time.ticks_diff(now, self._move_start[i])
                dur = self._move_dur[i]

                if elapsed >= dur:
                    self._value[i] = self._target[i]
                    self._is_moving[i] = False
                    self._pout.set_duty_us(self._angle_to_us(self._target[i], i), idx=i)
                else:
                    progress = _ease(elapsed / dur, self._ease_mode[i])
                    self._value[i] = self._move_from[i] + (self._target[i] - self._move_from[i]) * progress
                    self._pout.set_duty_us(self._angle_to_us(self._value[i], i), idx=i)
                    any_active = True

            if not any_active:
                self._stop_timer()
        except KeyboardInterrupt:
            self._stop_timer()

    class _View:
        __slots__ = ('_p', '_i')

        def __init__(self, parent, indices):
            self._p = parent
            self._i = indices

        def __len__(self):
            return len(self._i)

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                indices = tuple(self._i[j] for j in range(*idx.indices(len(self._i))))
            else:
                return self._p._views[self._i[idx]]
            return Servo._View(self._p, indices)

        @property
        def angle(self):
            return [self._p._value[i] for i in self._i]

        @angle.setter
        def angle(self, val):
            if self._p._mode != _POSITIONAL:
                raise RuntimeError("Use 'speed' in continuous mode")
            if isinstance(val, (list, tuple)):
                if len(val) != len(self._i):
                    raise ValueError("Length mismatch")
                for i, v in zip(self._i, val):
                    v = clamp(float(v), 0.0, 180.0)
                    self._p._value[i] = v
                    self._p._target[i] = v
                    self._p._is_moving[i] = False
                    self._p._pout.set_duty_us(self._p._angle_to_us(v, i), idx=i)
            else:
                v = clamp(float(val), 0.0, 180.0)
                for i in self._i:
                    self._p._value[i] = v
                    self._p._target[i] = v
                    self._p._is_moving[i] = False
                    self._p._pout.set_duty_us(self._p._angle_to_us(v, i), idx=i)
            if not any(self._p._is_moving):
                self._p._stop_timer()

        def move_to(self, deg, ms=None, easing='linear'):
            if self._p._mode != _POSITIONAL:
                raise RuntimeError("Use 'speed' in continuous mode")
            deg = clamp(float(deg), 0.0, 180.0)
            ease_mode = _easing_mode(easing)
            now = time.ticks_ms()
            for i in self._i:
                self._p._move_from[i] = self._p._value[i]
                self._p._target[i] = deg
                dur = max(_MIN_MOVE_MS, int(ms)) if ms is not None else self._p._auto_move_ms(i, deg)
                self._p._move_dur[i] = dur
                self._p._move_start[i] = now
                self._p._ease_mode[i] = ease_mode
                self._p._is_moving[i] = abs(deg - self._p._value[i]) > 0.0
                if not self._p._is_moving[i]:
                    self._p._pout.set_duty_us(self._p._angle_to_us(deg, i), idx=i)
            if any(self._p._is_moving):
                self._p._start_timer()
            else:
                self._p._stop_timer()

        def home(self, ms=None, easing='quad'):
            if self._p._mode != _POSITIONAL:
                raise RuntimeError("Use 'stop' in continuous mode")
            ease_mode = _easing_mode(easing)
            now = time.ticks_ms()
            for i in self._i:
                self._p._move_from[i] = self._p._value[i]
                self._p._target[i] = self._p._home[i]
                self._p._move_dur[i] = max(_MIN_MOVE_MS, int(ms)) if ms is not None else self._p._auto_move_ms(i, self._p._home[i])
                self._p._move_start[i] = now
                self._p._ease_mode[i] = ease_mode
                self._p._is_moving[i] = abs(self._p._home[i] - self._p._value[i]) > 0.0
                if not self._p._is_moving[i]:
                    self._p._pout.set_duty_us(self._p._angle_to_us(self._p._home[i], i), idx=i)
            if any(self._p._is_moving):
                self._p._start_timer()
            else:
                self._p._stop_timer()

        @property
        def home_angle(self):
            return [self._p._home[i] for i in self._i]

        @home_angle.setter
        def home_angle(self, val):
            if isinstance(val, (list, tuple)):
                if len(val) != len(self._i):
                    raise ValueError("Length mismatch")
                for i, v in zip(self._i, val):
                    self._p._home[i] = clamp(float(v), 0.0, 180.0)
            else:
                v = clamp(float(val), 0.0, 180.0)
                for i in self._i:
                    self._p._home[i] = v

        @property
        def speed(self):
            return [self._p._value[i] for i in self._i]

        @speed.setter
        def speed(self, val):
            if self._p._mode != _CONTINUOUS:
                raise RuntimeError("Use 'angle' in positional mode")
            if isinstance(val, (list, tuple)):
                if len(val) != len(self._i):
                    raise ValueError("Length mismatch")
                for i, v in zip(self._i, val):
                    v = clamp(float(v), -100.0, 100.0)
                    self._p._value[i] = v
                    self._p._target[i] = v
                    self._p._is_moving[i] = False
                    self._p._pout.set_duty_us(self._p._speed_to_us(v, i), idx=i)
            else:
                v = clamp(float(val), -100.0, 100.0)
                for i in self._i:
                    self._p._value[i] = v
                    self._p._target[i] = v
                    self._p._is_moving[i] = False
                    self._p._pout.set_duty_us(self._p._speed_to_us(v, i), idx=i)
            if not any(self._p._is_moving):
                self._p._stop_timer()

        @property
        def duty_us(self):
            return [self._p._pout.duty_us(i) for i in self._i]

        @duty_us.setter
        def duty_us(self, val):
            if isinstance(val, (list, tuple)):
                if len(val) != len(self._i):
                    raise ValueError("Length mismatch")
                for i, v in zip(self._i, val):
                    v = int(v)
                    self._p._is_moving[i] = False
                    self._p._pout.set_duty_us(v, idx=i)
                    if self._p._mode == _POSITIONAL:
                        self._p._value[i] = self._p._target[i] = self._p._us_to_angle(v, i)
                    else:
                        self._p._value[i] = self._p._target[i] = self._p._us_to_speed(v, i)
            else:
                for i in self._i:
                    v = int(val)
                    self._p._is_moving[i] = False
                    self._p._pout.set_duty_us(v, idx=i)
                    if self._p._mode == _POSITIONAL:
                        self._p._value[i] = self._p._target[i] = self._p._us_to_angle(v, i)
                    else:
                        self._p._value[i] = self._p._target[i] = self._p._us_to_speed(v, i)
            if not any(self._p._is_moving):
                self._p._stop_timer()

        @property
        def is_moving(self):
            return [self._p._is_moving[i] for i in self._i]

        @property
        def calibration(self):
            if self._p._mode == _POSITIONAL:
                return [{'min_us': self._p._min_us[i], 'max_us': self._p._max_us[i]} for i in self._i]
            else:
                return [{'center_us': self._p._center_us[i], 'min_us': self._p._min_us[i], 'max_us': self._p._max_us[i]} for i in self._i]

        @calibration.setter
        def calibration(self, params):
            if not isinstance(params, dict):
                raise TypeError("dict required")
            for i in self._i:
                min_us = int(params.get('min_us', self._p._min_us[i]))
                max_us = int(params.get('max_us', self._p._max_us[i]))
                center_us = int(params.get('center_us', self._p._center_us[i]))
                if min_us >= max_us:
                    raise ValueError("min_us must be less than max_us")
                if not (min_us <= center_us <= max_us):
                    raise ValueError("center_us must be between min_us and max_us")
                self._p._min_us[i] = min_us
                self._p._max_us[i] = max_us
                self._p._center_us[i] = center_us
                if self._p._mode == _POSITIONAL:
                    self._p._pout.set_duty_us(self._p._angle_to_us(self._p._value[i], i), idx=i)
                else:
                    self._p._pout.set_duty_us(self._p._speed_to_us(self._p._value[i], i), idx=i)

        def wait(self, timeout_ms=10000):
            start = time.ticks_ms()
            while any(self._p._is_moving[i] for i in self._i):
                if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                    return False
                time.sleep_ms(10)
            return True

        def stop(self):
            for i in self._i:
                self._p._is_moving[i] = False
                if self._p._mode == _POSITIONAL:
                    self._p._target[i] = self._p._value[i]
                    self._p._pout.set_duty_us(self._p._angle_to_us(self._p._value[i], i), idx=i)
                else:
                    self._p._value[i] = 0.0
                    self._p._target[i] = 0.0
                    self._p._pout.set_duty_us(self._p._center_us[i], idx=i)
            if not any(self._p._is_moving):
                self._p._stop_timer()
