# @package: ain
# @version: 2.0.0
# @type: device-specific
# @category: peripheral
# @interface: ADC
# @depends: none
# @platforms: rp2
# @tags: adc, analog, dma, burst, continuous, rp2040, rp2350

import machine
import time
import array
import micropython
from micropython import const
from rp2 import DMA

# RP2040 ADC register addresses
_ADC_BASE = const(0x4004c000)
_ADC_CS = const(_ADC_BASE + 0x00)      # Control and status
_ADC_RESULT = const(_ADC_BASE + 0x04)  # Result
_ADC_FCS = const(_ADC_BASE + 0x08)     # FIFO control and status
_ADC_FIFO = const(_ADC_BASE + 0x0c)    # FIFO read
_ADC_DIV = const(_ADC_BASE + 0x10)     # Clock divider
_ADC_INTR = const(_ADC_BASE + 0x14)    # Raw interrupts
_ADC_INTE = const(_ADC_BASE + 0x18)    # Interrupt enable
_ADC_INTF = const(_ADC_BASE + 0x1c)    # Interrupt force
_ADC_INTS = const(_ADC_BASE + 0x20)    # Interrupt status

# DREQ for ADC
_DREQ_ADC = const(36)

# ADC clock: 48MHz, max sample rate ~500kHz
_ADC_CLOCK = const(48_000_000)


class Ain:
    
    _FULL_RANGE = 65_535
    _ADC_BITS = 4
    _DEFAULT_VREF = 3.3

    def __init__(self, pins: int | list[int] | tuple[int, ...], *, vref: float = 3.3):
        if isinstance(pins, int):
            pins = (pins,)
        if not pins:
            raise ValueError("At least one pin must be provided")
        
        self._pins = tuple(pins)
        n = len(self._pins)
        
        # Validate RP2040 ADC pins (26-29 for ADC0-3)
        for pin in self._pins:
            if pin not in (26, 27, 28, 29):
                raise ValueError(f"Invalid ADC pin {pin}. RP2040 supports pins 26-29")
        
        try:
            self._adc = [machine.ADC(machine.Pin(pin)) for pin in self._pins]
        except Exception as e:
            raise OSError(f"Failed to initialize ADC pins: {e}")
        
        self._vref = [vref] * n
        self._offset = [0] * n
        self._scale = [1.0] * n
        
        # DMA resources
        self._dma = None
        self._dma_running = False
        self._dma_buffer = None
        self._dma_callback = None
        self._current_channel = None
        
        self._view = Ain._View(self)

    def deinit(self) -> None:
        self.stop_continuous()
        if self._dma is not None:
            try:
                self._dma.close()
            except:
                pass
            self._dma = None

    def __enter__(self) -> "Ain":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.deinit()

    def __getitem__(self, idx: int | slice) -> "_View":
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

    def __len__(self) -> int:
        return len(self._pins)

    def read_u16(self, idx: int = 0) -> int:
        return self._adc[idx].read_u16()

    def read_u12(self, idx: int = 0) -> int:
        return self._adc[idx].read_u16() >> 4

    def read_percent(self, idx: int = 0) -> float:
        return self._adc[idx].read_u16() * 100.0 / Ain._FULL_RANGE

    def read_voltage(self, idx: int = 0) -> float:
        raw = self._adc[idx].read_u16()
        return ((raw + self._offset[idx]) * self._scale[idx]) * self._vref[idx] / Ain._FULL_RANGE

    def read_into(self, buf, *, bits: int = 16):
        shift = 0 if bits == 16 else Ain._ADC_BITS
        for i in range(len(self._adc)):
            buf[i] = self._adc[i].read_u16() >> shift
        return buf

    def filtered_u16(self, samples: int = 10, *, idx: int = 0,
                     interval_us: int = 100) -> int:
        if samples <= 0:
            raise ValueError("samples must be positive")
        adc = self._adc[idx]
        total = 0
        for _ in range(samples):
            total += adc.read_u16()
            if interval_us > 0:
                time.sleep_us(interval_us)
        return total // samples

    def filtered_u12(self, samples: int = 10, *, idx: int = 0,
                     interval_us: int = 100) -> int:
        return self.filtered_u16(samples, idx=idx,
                                 interval_us=interval_us) >> Ain._ADC_BITS

    def min_max_u16(self, samples: int = 100, *, idx: int = 0,
                    interval_us: int = 100) -> tuple[int, int]:
        if samples <= 0:
            raise ValueError("samples must be positive")
        adc = self._adc[idx]
        min_val = Ain._FULL_RANGE
        max_val = 0
        for _ in range(samples):
            val = adc.read_u16()
            if val < min_val:
                min_val = val
            if val > max_val:
                max_val = val
            if interval_us > 0:
                time.sleep_us(interval_us)
        return min_val, max_val
    
    def start_continuous(
        self,
        channel: int,
        buffer: array.array,
        *,
        rate: int = 100_000,
        loop: bool = False,
        callback: callable = None
    ) -> None:
        if self._dma_running:
            raise RuntimeError("DMA sampling already running")
        
        if not (0 <= channel < len(self._pins)):
            raise ValueError(f"Invalid channel {channel}")
        
        if not isinstance(buffer, array.array) or buffer.typecode != 'H':
            raise TypeError("Buffer must be array.array('H', ...)")
        
        if not (1 <= rate <= 500_000):
            raise ValueError("Rate must be 1 to 500000 Hz")
        
        self._current_channel = channel
        self._dma_buffer = buffer
        self._dma_callback = callback
        
        # Calculate clock divider for desired sample rate
        # div = (48MHz / rate) - 1, stored as 8.4 fixed point (upper 8 bits integer)
        div_int = (_ADC_CLOCK // rate) - 1
        if div_int < 0:
            div_int = 0
        div_reg = div_int << 8  # 8.4 fixed point, frac=0
        
        # Get ADC channel number (pin 26=ADC0, 27=ADC1, etc.)
        adc_channel = self._pins[channel] - 26
        
        # Configure ADC for free-running mode with FIFO
        # Reset ADC state
        machine.mem32[_ADC_CS] = 0
        machine.mem32[_ADC_FCS] = 0
        
        # Set clock divider
        machine.mem32[_ADC_DIV] = div_reg
        
        # Configure FIFO:
        # - Enable FIFO (bit 0)
        # - Enable DMA request (bit 3)
        # - Threshold = 1 (bits 24-27)
        machine.mem32[_ADC_FCS] = (1 << 0) | (1 << 3) | (1 << 24)
        
        # Drain any existing FIFO data
        while machine.mem32[_ADC_FCS] & (0xF << 16):  # LEVEL bits
            _ = machine.mem32[_ADC_FIFO]
        
        # Configure DMA
        if self._dma is None:
            self._dma = DMA()
        
        # Pack DMA control register
        ctrl = self._dma.pack_ctrl(
            size=1,           # 1 = halfword (16-bit)
            inc_read=False,   # ADC FIFO address is fixed
            inc_write=True,   # Increment buffer pointer
            treq_sel=_DREQ_ADC,  # Pace by ADC FIFO
            irq_quiet=not bool(callback),
        )
        
        # Configure DMA transfer
        self._dma.config(
            read=_ADC_FIFO,
            write=buffer,
            count=len(buffer),
            ctrl=ctrl,
            trigger=False
        )
        
        # Set up IRQ if callback provided
        if callback:
            self._dma.irq(handler=self._dma_irq_handler)
        
        # Start DMA
        self._dma.active(1)
        
        # Enable ADC:
        # - Power on (bit 0)
        # - Enable (bit 1)  
        # - Select channel (bits 12-14)
        # - Start continuous (bit 3)
        cs_val = (1 << 0) | (1 << 3) | (adc_channel << 12)
        machine.mem32[_ADC_CS] = cs_val
        
        self._dma_running = True

    def stop_continuous(self) -> None:
        if not self._dma_running:
            return
        
        # Stop ADC
        machine.mem32[_ADC_CS] = 0
        
        # Disable FIFO
        machine.mem32[_ADC_FCS] = 0
        
        # Stop DMA
        if self._dma is not None:
            self._dma.active(0)
        
        self._dma_running = False
        self._current_channel = None

    @property
    def is_running(self) -> bool:
        return self._dma_running

    @property
    def samples_remaining(self) -> int:
        if self._dma is None or not self._dma_running:
            return 0
        return self._dma.count

    def _dma_irq_handler(self, dma):
        if self._dma_callback:
            try:
                micropython.schedule(self._dma_callback, self._dma_buffer)
            except RuntimeError:
                pass

    def read_burst(
        self,
        channel: int,
        count: int,
        *,
        rate: int = 100_000
    ) -> array.array:
        buf = array.array('H', (0 for _ in range(count)))
        self.start_continuous(channel, buf, rate=rate, loop=False)
        
        # Wait for completion
        while self._dma.active():
            pass
        
        self.stop_continuous()
        return buf

    def read_burst_voltage(
        self,
        channel: int,
        count: int,
        *,
        rate: int = 100_000
    ) -> list[float]:
        raw = self.read_burst(channel, count, rate=rate)
        vref = self._vref[channel]
        offset = self._offset[channel]
        scale = self._scale[channel]
        
        return [
            ((v + offset) * scale) * vref / Ain._FULL_RANGE
            for v in raw
        ]

    class _View:
        __slots__ = ('_p', '_i', '_cache')
        
        def __init__(self, parent: "Ain"):
            self._p = parent
            self._i = None
            self._cache = []
        
        def _set(self, indices) -> "Ain._View":
            self._i = indices
            return self

        def __getitem__(self, idx: int | slice) -> "Ain._View":
            if isinstance(idx, slice):
                return self._set(self._i[idx])
            else:
                return self._set((self._i[idx],))

        def __len__(self) -> int:
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

        def read_u16(self) -> int:
            if len(self._i) != 1:
                raise ValueError("read_u16 only works with single channel")
            return self._p.read_u16(self._i[0])

        def read_u12(self) -> int:
            if len(self._i) != 1:
                raise ValueError("read_u12 only works with single channel")
            return self._p.read_u12(self._i[0])

        def read_percent(self) -> float:
            if len(self._i) != 1:
                raise ValueError("read_percent only works with single channel")
            return self._p.read_percent(self._i[0])

        def read_voltage(self) -> float:
            if len(self._i) != 1:
                raise ValueError("read_voltage only works with single channel")
            return self._p.read_voltage(self._i[0])

        def read_into(self, buf, *, bits: int = 16):
            shift = 0 if bits == 16 else Ain._ADC_BITS
            adc = self._p._adc
            for out_i, adc_i in enumerate(self._i):
                buf[out_i] = adc[adc_i].read_u16() >> shift
            return buf

        @property
        def value_u16(self):
            return self.read_into(self._buf(), bits=16)

        @property
        def value_u12(self):
            return self.read_into(self._buf(), bits=12)

        @property
        def value_percent(self):
            buf = self._buf()
            adc = self._p._adc
            full = Ain._FULL_RANGE
            for out_i, adc_i in enumerate(self._i):
                buf[out_i] = adc[adc_i].read_u16() * 100.0 / full
            return buf

        @property
        def voltage(self):
            buf = self._buf()
            adc = self._p._adc
            for out_i, adc_i in enumerate(self._i):
                raw = adc[adc_i].read_u16()
                buf[out_i] = ((raw + self._p._offset[adc_i]) *
                              self._p._scale[adc_i] *
                              self._p._vref[adc_i] / Ain._FULL_RANGE)
            return buf

        def filtered_u16(self, samples: int = 10, interval_us: int = 100) -> int:
            if len(self._i) != 1:
                raise ValueError("filtered_u16 only works with single channel")
            return self._p.filtered_u16(samples, idx=self._i[0],
                                        interval_us=interval_us)

        def filtered_u12(self, samples: int = 10, interval_us: int = 100) -> int:
            if len(self._i) != 1:
                raise ValueError("filtered_u12 only works with single channel")
            return self._p.filtered_u12(samples, idx=self._i[0],
                                        interval_us=interval_us)

        def min_max_u16(self, samples: int = 100,
                        interval_us: int = 100) -> tuple[int, int]:
            if len(self._i) != 1:
                raise ValueError("min_max_u16 only works with single channel")
            return self._p.min_max_u16(samples, idx=self._i[0],
                                       interval_us=interval_us)

        # DMA methods for single channel view
        def read_burst(self, count: int, *, rate: int = 100_000) -> array.array:
            if len(self._i) != 1:
                raise ValueError("read_burst only works with single channel view")
            return self._p.read_burst(self._i[0], count, rate=rate)

        def read_burst_voltage(self, count: int, *, rate: int = 100_000) -> list[float]:
            if len(self._i) != 1:
                raise ValueError("read_burst_voltage only works with single channel view")
            return self._p.read_burst_voltage(self._i[0], count, rate=rate)
