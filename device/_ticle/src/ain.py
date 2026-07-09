# @package: ain_rp2
# @version: 2.3
# @type: device-specific
# @category: peripheral
# @interface: ADC
# @depends: none
# @platforms: rp2
# @tags: adc, analog, dma, burst, continuous, rp2040, rp2350
# @author: PlanXLab Development Team

import machine
import time
import array
import micropython
from micropython import const
from rp2 import DMA

_ADC_BASE = const(0x400A8000)
_ADC_CS   = const(_ADC_BASE + 0x00)
_ADC_FCS  = const(_ADC_BASE + 0x08)
_ADC_FIFO = const(_ADC_BASE + 0x0c)
_ADC_DIV  = const(_ADC_BASE + 0x10)

_DREQ_ADC = const(48)

_ADC_CLOCK  = const(48_000_000)
_FULL_RANGE = const(65535)
_ADC_BITS   = const(4)


class Ain:
    def __init__(self, pins, *, vref=3.3, bits=16):
        if isinstance(pins, int):
            pins = (pins,)
        if not pins:
            raise ValueError("At least one pin must be provided")
        if bits not in (16, 12):
            raise ValueError("bits must be 16 or 12")

        self._pins = tuple(pins)
        n = len(self._pins)

        for pin in self._pins:
            if pin not in (26, 27, 28, 29):
                raise ValueError(f"Invalid ADC pin {pin}. RP2350 ADC pins are 26..29")

        try:
            self._adc = tuple(machine.ADC(machine.Pin(pin)) for pin in self._pins)
        except Exception as e:
            raise OSError(f"Failed to initialize ADC pins: {e}")

        self._bits = bits
        self._shift = 0 if bits == 16 else _ADC_BITS
        self._full_range = (1 << bits) - 1
        self._vref = [vref] * n

        self._dma = None
        self._dma_running = False
        self._dma_buffer = None
        self._dma_callback = None

        self._view = Ain._View(self)

    def deinit(self):
        self.stop_continuous()
        if self._dma is not None:
            try:
                self._dma.close()
            except Exception:
                pass
            self._dma = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            indices = tuple(range(*idx.indices(len(self._pins))))
            return self._view._set(indices)
        elif isinstance(idx, int):
            if idx < 0:
                idx += len(self._pins)
            if not (0 <= idx < len(self._pins)):
                raise IndexError("ADC channel index out of range")
            return self._view._set((idx,))
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self):
        return len(self._pins)

    @property
    def bits(self):
        return self._bits

    def read(self, idx=0):
        return self._adc[idx].read_u16() >> self._shift

    def read_percent(self, idx=0):
        return (self._adc[idx].read_u16() >> self._shift) * 100.0 / self._full_range

    def read_voltage(self, idx=0):
        return (self._adc[idx].read_u16() >> self._shift) * self._vref[idx] / self._full_range

    def read_into(self, buf):
        if len(buf) < len(self._adc):
            raise ValueError(
                "buf length (%d) is smaller than channel count (%d)"
                % (len(buf), len(self._adc))
            )
        shift = self._shift
        for i, adc_ch in enumerate(self._adc):
            buf[i] = adc_ch.read_u16() >> shift
        return buf

    def filtered(self, filt, samples=10, *, idx=0, interval_us=100):
        if samples <= 0:
            raise ValueError("samples must be positive")
        adc = self._adc[idx]
        shift = self._shift
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
    
    def start_continuous(self, channel, buffer, *, rate=100_000, callback=None):
        if self._dma_running:
            raise RuntimeError("DMA sampling already running")
        
        if not (0 <= channel < len(self._pins)):
            raise ValueError(f"Invalid channel {channel}")
        
        if not isinstance(buffer, array.array) or buffer.typecode != 'H':
            raise TypeError("Buffer must be array.array('H', ...)")
        
        if not (1 <= rate <= 500_000):
            raise ValueError("Rate must be 1 to 500000 Hz")
        
        self._dma_buffer = buffer
        self._dma_callback = callback

        div_reg = ((_ADC_CLOCK // rate) - 1) << 8
        adc_channel = self._pins[channel] - 26
        
        machine.mem32[_ADC_CS] = 0
        machine.mem32[_ADC_FCS] = 0
        
        machine.mem32[_ADC_DIV] = div_reg
        machine.mem32[_ADC_FCS] = (1 << 0) | (1 << 3) | (1 << 24)
        
        while machine.mem32[_ADC_FCS] & (0xF << 16):
            _ = machine.mem32[_ADC_FIFO]
        
        if self._dma is None:
            self._dma = DMA()
        
        ctrl = self._dma.pack_ctrl(
            size=1,
            inc_read=False,
            inc_write=True,
            treq_sel=_DREQ_ADC,
            irq_quiet=not bool(callback),
        )
        
        self._dma.config(
            read=_ADC_FIFO,
            write=buffer,
            count=len(buffer),
            ctrl=ctrl,
            trigger=False
        )
        
        if callback:
            self._dma.irq(handler=self._dma_irq_handler)
        
        self._dma.active(1)
        
        cs_val = (1 << 0) | (1 << 3) | (adc_channel << 12)
        machine.mem32[_ADC_CS] = cs_val
        
        self._dma_running = True

    def stop_continuous(self):
        if not self._dma_running:
            return
        
        machine.mem32[_ADC_CS] = 0
        machine.mem32[_ADC_FCS] = 0
        
        if self._dma is not None:
            self._dma.active(0)
        
        self._dma_running = False
        self._dma_callback = None
        self._dma_buffer = None

    @property
    def is_running(self):
        return self._dma_running

    @property
    def samples_remaining(self):
        if self._dma is None or not self._dma_running:
            return 0
        return self._dma.count

    def _dma_irq_handler(self, dma):
        if self._dma_callback:
            try:
                micropython.schedule(self._dma_callback, self._dma_buffer)
            except RuntimeError:
                pass

    def read_burst(self, channel, count, *, rate=100_000):
        buf = array.array('H', bytes(count * 2))
        self.start_continuous(channel, buf, rate=rate)
        
        while self._dma.active():
            machine.idle()
        
        self.stop_continuous()
        return buf

    def read_burst_voltage(self, channel, count, *, rate=100_000):
        raw = self.read_burst(channel, count, rate=rate)
        vref = self._vref[channel]
        full = self._full_range
        fifo_shift = _ADC_BITS - self._shift
        return [(((v & 0x0FFF) << fifo_shift) * vref / full) for v in raw]

    class _View:
        __slots__ = ('_p', '_i', '_cache')

        def __init__(self, parent):
            self._p = parent
            self._i = ()
            self._cache = []

        def _set(self, indices):
            self._i = indices
            return self

        def _single(self):
            if len(self._i) != 1:
                raise ValueError("single-channel operation requires one channel")
            return self._i[0]

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                return self._set(self._i[idx])
            return self._set((self._i[idx],))

        def __len__(self):
            return len(self._i)

        def _buf(self):
            n = len(self._i)
            buf = self._cache
            if len(buf) != n:
                if len(buf) < n:
                    buf.extend([0] * (n - len(buf)))
                else:
                    del buf[n:]
            return buf

        def read(self):
            return self._p.read(self._single())

        def read_percent(self):
            return self._p.read_percent(self._single())

        def read_voltage(self):
            return self._p.read_voltage(self._single())

        def read_into(self, buf):
            if len(buf) < len(self._i):
                raise ValueError(
                    "buf length (%d) is smaller than selected channel count (%d)"
                    % (len(buf), len(self._i))
                )
            shift = self._p._shift
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
            shift = self._p._shift
            full = self._p._full_range
            vref = self._p._vref
            for out_i, adc_i in enumerate(self._i):
                buf[out_i] = (adc[adc_i].read_u16() >> shift) * vref[adc_i] / full
            return buf

        def filtered(self, filt, samples=10, interval_us=100):
            return self._p.filtered(filt, samples, idx=self._single(), interval_us=interval_us)

        def min_max(self, samples=100, interval_us=100):
            return self._p.min_max(samples, idx=self._single(), interval_us=interval_us)

        def read_burst(self, count, *, rate=100_000):
            return self._p.read_burst(self._single(), count, rate=rate)

        def read_burst_voltage(self, count, *, rate=100_000):
            return self._p.read_burst_voltage(self._single(), count, rate=rate)
