# @package: pout
# @version: 2.0
# @type: core
# @category: peripheral
# @interface: PWM
# @depends: none
# @platforms: *
# @tags: pwm, output, duty, frequency, analog-output
# @author: PlanXLab Development Team

import machine
import micropython
import time


def _is_seq(value):
    return not isinstance(value, (int, float, bool)) and hasattr(value, "__len__")

_FULL_RANGE = micropython.const(65535)
_MICROS_PER_SEC = micropython.const(1000000)


class Pout:
    def __init__(self, pins, *, freq=1000, duty_u16=0):
        if isinstance(pins, int):
            pins = (pins,)
        if not pins:
            raise ValueError("pins must not be empty")
        self._pin_nums = tuple(pins)
        self._pwm = [machine.PWM(machine.Pin(pin)) for pin in self._pin_nums]
        self._freq = [int(freq)] * len(self._pwm)
        self._duty = [0] * len(self._pwm)
        self._enabled = [True] * len(self._pwm)
        self._view = Pout._View(self)
        for i in range(len(self._pwm)):
            self._pwm[i].freq(self._freq[i])
            self.set_duty_u16(duty_u16, idx=i)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def __len__(self):
        return len(self._pwm)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return self._view._set(tuple(range(*idx.indices(len(self)))))
        if idx < 0:
            idx += len(self)
        if not 0 <= idx < len(self):
            raise IndexError("PWM channel index out of range")
        return self._view._set((idx,))

    def deinit(self):
        for pwm in self._pwm:
            try:
                pwm.duty_u16(0)
            except Exception:
                pass
        time.sleep_ms(20)
        for pwm in self._pwm:
            try:
                pwm.deinit()
            except Exception:
                pass

    def freq(self, idx=0):
        return self._freq[idx]

    def set_freq(self, hz=1000, idx=0):
        hz = int(hz)
        if hz <= 0:
            raise ValueError("freq must be positive")
        self._freq[idx] = hz
        self._pwm[idx].freq(hz)

    def set_freq_all(self, hz):
        for i in range(len(self._pwm)):
            self.set_freq(hz, idx=i)

    def period_us(self, idx=0):
        return _MICROS_PER_SEC // self._freq[idx]

    def set_period_us(self, us=1000, idx=0):
        us = int(us)
        if us <= 0:
            raise ValueError("period must be positive")
        self.set_freq(_MICROS_PER_SEC // us, idx=idx)

    def duty(self, idx=0):
        return self._duty[idx] * 100.0 / _FULL_RANGE

    def set_duty(self, percent=0, idx=0):
        if percent < 0:
            percent = 0
        elif percent > 100:
            percent = 100
        self.set_duty_u16(int(percent * _FULL_RANGE / 100), idx=idx)

    def duty_u16(self, idx=0):
        return self._duty[idx]

    def set_duty_u16(self, value=0, idx=0):
        value = int(value)
        if value < 0:
            value = 0
        elif value > _FULL_RANGE:
            value = _FULL_RANGE
        self._duty[idx] = value
        self._pwm[idx].duty_u16(value if self._enabled[idx] else 0)

    def duty_us(self, idx=0):
        return self._duty[idx] * self.period_us(idx) // _FULL_RANGE

    def set_duty_us(self, us=0, idx=0):
        period = self.period_us(idx)
        value = int(us) * _FULL_RANGE // period
        self.set_duty_u16(value, idx=idx)

    def enabled(self, idx=0):
        return self._enabled[idx]

    def enable(self, flag=True, idx=0):
        self._enabled[idx] = bool(flag)
        self._pwm[idx].duty_u16(self._duty[idx] if flag else 0)

    class _View:
        __slots__ = ("_p", "_i", "_cache")

        def __init__(self, parent):
            self._p = parent
            self._i = ()
            self._cache = []

        def _set(self, indices):
            self._i = indices
            return self

        def _buf(self):
            n = len(self._i)
            buf = self._cache
            if len(buf) != n:
                if len(buf) < n:
                    buf.extend([0] * (n - len(buf)))
                else:
                    del buf[n:]
            return buf

        def __len__(self):
            return len(self._i)

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                return self._set(tuple(self._i[j] for j in range(*idx.indices(len(self._i)))))
            return self._set((self._i[idx],))

        def _single(self):
            if len(self._i) != 1:
                raise ValueError("operation requires a single PWM channel")
            return self._i[0]

        def set_freq(self, hz):
            for i in self._i:
                self._p.set_freq(hz, idx=i)

        def period_us(self):
            return self._p.period_us(self._single())

        def set_period_us(self, us):
            for i in self._i:
                self._p.set_period_us(us, idx=i)

        @property
        def period(self):
            buf = self._buf()
            for out_i, pwm_i in enumerate(self._i):
                buf[out_i] = self._p.period_us(pwm_i)
            return buf

        @period.setter
        def period(self, us):
            self._set_many(us, self._p.set_period_us)

        def set_duty(self, percent):
            for i in self._i:
                self._p.set_duty(percent, idx=i)

        def set_duty_u16(self, value):
            for i in self._i:
                self._p.set_duty_u16(value, idx=i)

        def set_duty_us(self, us):
            for i in self._i:
                self._p.set_duty_us(us, idx=i)

        def enable(self, flag=True):
            for i in self._i:
                self._p.enable(flag, idx=i)

        @property
        def freq(self):
            buf = self._buf()
            for out_i, pwm_i in enumerate(self._i):
                buf[out_i] = self._p.freq(pwm_i)
            return buf

        @freq.setter
        def freq(self, hz):
            self._set_many(hz, self._p.set_freq)

        @property
        def duty(self):
            buf = self._buf()
            for out_i, pwm_i in enumerate(self._i):
                buf[out_i] = self._p.duty(pwm_i)
            return buf

        @duty.setter
        def duty(self, percent):
            self._set_many(percent, self._p.set_duty)

        @property
        def duty_u16(self):
            buf = self._buf()
            for out_i, pwm_i in enumerate(self._i):
                buf[out_i] = self._p.duty_u16(pwm_i)
            return buf

        @duty_u16.setter
        def duty_u16(self, value):
            self._set_many(value, self._p.set_duty_u16)

        @property
        def duty_us(self):
            buf = self._buf()
            for out_i, pwm_i in enumerate(self._i):
                buf[out_i] = self._p.duty_us(pwm_i)
            return buf

        @duty_us.setter
        def duty_us(self, us):
            self._set_many(us, self._p.set_duty_us)

        @property
        def enabled(self):
            buf = self._buf()
            for out_i, pwm_i in enumerate(self._i):
                buf[out_i] = self._p.enabled(pwm_i)
            return buf

        @enabled.setter
        def enabled(self, flag):
            self._set_many(flag, self._p.enable)

        def _set_many(self, value, setter):
            if _is_seq(value):
                if len(value) != len(self._i):
                    raise ValueError("value length must match channel count")
                for pwm_i, v in zip(self._i, value):
                    setter(v, idx=pwm_i)
            else:
                for pwm_i in self._i:
                    setter(value, idx=pwm_i)
