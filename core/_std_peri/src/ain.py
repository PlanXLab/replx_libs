# @package: ain
# @version: 2.3
# @type: core
# @category: peripheral
# @interface: ADC
# @depends: none
# @platforms: *
# @tags: adc, analog, input, voltage, sensor
# @author: PlanXLab Development Team

import machine
import micropython
import time

_FULL_RANGE = micropython.const(65535)
_ADC_BITS = micropython.const(4)

class Ain:
    def __init__(self, pins, *, vref=3.3, bits=16):
        if isinstance(pins, int):
            pins = (pins,)
        if not pins:
            raise ValueError("At least one pin must be provided")
        if bits not in (16, 12):
            raise ValueError("bits must be 16 or 12")

        self._pins = tuple(pins)
        self._adc = tuple(machine.ADC(machine.Pin(pin)) for pin in self._pins)
        self._vref = float(vref)
        self._bits = bits
        self._shift = 0 if bits == 16 else _ADC_BITS
        self._full_range = (1 << bits) - 1  # 65535 for 16-bit, 4095 for 12-bit
        self._view = Ain._View(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def __len__(self):
        return len(self._pins)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return self._view._set(tuple(range(*idx.indices(len(self._pins)))))
        if idx < 0:
            idx += len(self._pins)
        if not 0 <= idx < len(self._pins):
            raise IndexError("ADC channel index out of range")
        return self._view._set((idx,))

    def deinit(self):
        pass

    @property
    def bits(self):
        return self._bits

    def read(self, idx=0):
        return self._adc[idx].read_u16() >> self._shift

    def read_percent(self, idx=0):
        return (self._adc[idx].read_u16() >> self._shift) * 100.0 / self._full_range

    def read_voltage(self, idx=0):
        return (self._adc[idx].read_u16() >> self._shift) * self._vref / self._full_range

    def read_into(self, buf):
        shift = self._shift
        if len(buf) < len(self._adc):
            raise ValueError(
                "buf length (%d) is smaller than channel count (%d)"
                % (len(buf), len(self._adc))
            )
        for i, adc_ch in enumerate(self._adc):
            buf[i] = adc_ch.read_u16() >> shift
        return buf

    def filtered(self, filt, samples=10, *, idx=0, interval_us=100):
        if samples <= 0:
            raise ValueError("samples must be positive")
        adc = self._adc[idx]
        shift = self._shift
        result = 0.0
        if interval_us > 0:
            for _ in range(samples):
                result = filt(adc.read_u16() >> shift)
                time.sleep_us(interval_us)
        else:
            for _ in range(samples):
                result = filt(adc.read_u16() >> shift)
        return result

    def min_max(self, samples=100, *, idx=0, interval_us=100):
        if samples <= 0:
            raise ValueError("samples must be positive")
        adc = self._adc[idx]
        min_val = _FULL_RANGE
        max_val = 0
        if interval_us > 0:
            for _ in range(samples):
                val = adc.read_u16()
                if val < min_val:
                    min_val = val
                if val > max_val:
                    max_val = val
                time.sleep_us(interval_us)
        else:
            for _ in range(samples):
                val = adc.read_u16()
                if val < min_val:
                    min_val = val
                if val > max_val:
                    max_val = val
        shift = self._shift
        return min_val >> shift, max_val >> shift

    class _View:
        __slots__ = ("_p", "_i", "_cache")

        def __init__(self, parent):
            self._p = parent
            self._i = ()
            self._cache = []

        def _set(self, indices):
            self._i = indices
            return self

        def __len__(self):
            return len(self._i)

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                return self._set(self._i[idx])
            return self._set((self._i[idx],))

        def _single(self):
            if len(self._i) != 1:
                raise ValueError("single-channel operation requires one channel")
            return self._i[0]

        def _buf(self):
            n = len(self._i)
            buf = self._cache
            while len(buf) < n:
                buf.append(0)
            del buf[n:]
            return buf

        def read(self):
            return self._p.read(self._single())

        def read_percent(self):
            return self._p.read_percent(self._single())

        def read_voltage(self):
            return self._p.read_voltage(self._single())

        def read_into(self, buf):
            shift = self._p._shift
            if len(buf) < len(self._i):
                raise ValueError(
                    "buf length (%d) is smaller than selected channel count (%d)"
                    % (len(buf), len(self._i))
                )
            adc = self._p._adc
            for out_i, adc_i in enumerate(self._i):
                buf[out_i] = adc[adc_i].read_u16() >> shift
            return buf

        @property
        def value(self):
            return self.read_into(self._buf())

        @property
        def percent(self):
            buf = self._buf()
            adc = self._p._adc
            scale = 100.0 / self._p._full_range
            shift = self._p._shift
            for out_i, adc_i in enumerate(self._i):
                buf[out_i] = (adc[adc_i].read_u16() >> shift) * scale
            return buf

        @property
        def voltage(self):
            buf = self._buf()
            adc = self._p._adc
            scale = self._p._vref / self._p._full_range
            shift = self._p._shift
            for out_i, adc_i in enumerate(self._i):
                buf[out_i] = (adc[adc_i].read_u16() >> shift) * scale
            return buf

        def filtered(self, filt, samples=10, interval_us=100):
            return self._p.filtered(filt, samples, idx=self._single(), interval_us=interval_us)

        def min_max(self, samples=100, interval_us=100):
            return self._p.min_max(samples, idx=self._single(), interval_us=interval_us)