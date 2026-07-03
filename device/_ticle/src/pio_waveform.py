# @package: pio_waveform
# @version: 1.0.0
# @type: device-specific
# @category: pio
# @interface: GPIO
# @depends: none
# @platforms: rp2
# @tags: pio, waveform, dma, gpio, output, pwm, signal
# @author: PlanXLab Development Team

import machine
import micropython
import array
from rp2 import PIO, StateMachine, DMA, asm_pio
from .utools import find_free_sm

@asm_pio(out_init=PIO.OUT_LOW, out_shiftdir=PIO.SHIFT_RIGHT, autopull=True, pull_thresh=32)
def _waveform_1bit():
    out(pins, 1)

@asm_pio(out_init=(PIO.OUT_LOW,)*8, out_shiftdir=PIO.SHIFT_RIGHT, autopull=True, pull_thresh=8)
def _waveform_8bit():
    out(pins, 8)

@asm_pio(sideset_init=PIO.OUT_LOW, out_shiftdir=PIO.SHIFT_RIGHT, autopull=True, pull_thresh=32)
def _waveform_sideset():
    out(x, 32)
    label("loop")
    jmp(x_dec, "loop")  .side(1)
    out(x, 32)
    label("loop2")
    jmp(x_dec, "loop2") .side(0)

_DREQ_PIO0_TX0 = micropython.const(0)
_DREQ_PIO1_TX0 = micropython.const(8)

class PioWaveform:
    
    MODE_1BIT = micropython.const(0)
    MODE_8BIT = micropython.const(1)
    MODE_PWM = micropython.const(2)

    def __init__(
        self,
        pin: int | list[int],
        *,
        mode: int = 0,
        freq: int = 1_000_000
    ):
        self._mode = mode
        self._freq = freq
        
        if isinstance(pin, int):
            self._pins = [pin]
            self._base_pin = pin
            self._pin_count = 1
        else:
            self._pins = list(pin)
            if not self._pins:
                raise ValueError("At least one pin required")
            self._base_pin = min(self._pins)
            self._pin_count = len(self._pins)
            if mode == self.MODE_8BIT and self._pin_count != 8:
                raise ValueError("8-bit mode requires exactly 8 consecutive pins")
        
        self._sm_id = find_free_sm(1)[0]
        
        self._sm = None
        self._dma = None
        self._buffer = None
        self._callback = None
        self._running = False
        self._loop = False
        
        self._init_sm()

    def _init_sm(self):
        out_pins = [machine.Pin(p, machine.Pin.OUT) for p in self._pins]
        
        if self._mode == self.MODE_1BIT:
            self._sm = StateMachine(
                self._sm_id,
                _waveform_1bit,
                freq=self._freq,
                out_base=machine.Pin(self._base_pin),
            )
        elif self._mode == self.MODE_8BIT:
            self._sm = StateMachine(
                self._sm_id,
                _waveform_8bit,
                freq=self._freq * 8,
                out_base=machine.Pin(self._base_pin),
            )
        elif self._mode == self.MODE_PWM:
            self._sm = StateMachine(
                self._sm_id,
                _waveform_sideset,
                freq=self._freq,
                sideset_base=machine.Pin(self._base_pin),
            )
        else:
            raise ValueError(f"Invalid waveform mode: {self._mode}")

    def deinit(self):
        self.stop()
        if self._sm is not None:
            try:
                self._sm.active(0)
            except:
                pass
            self._sm = None
        if self._dma is not None:
            try:
                self._dma.close()
            except:
                pass
            self._dma = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.deinit()

    def set_freq(self, freq: int):
        if self._sm is None:
            raise RuntimeError("StateMachine not initialized")
        if freq <= 0 or freq > 125_000_000:
            raise ValueError("Frequency must be 1 to 125000000 Hz")
        self._freq = freq
        effective_freq = freq * 8 if self._mode == self.MODE_8BIT else freq
        self._sm.freq(effective_freq)

    @property
    def freq(self) -> int:
        return self._freq

    def start(
        self,
        buffer: array.array,
        *,
        loop: bool = False,
        callback: callable = None
    ) -> bool:
        if self._running:
            return False
        
        if self._mode == self.MODE_8BIT:
            if buffer.typecode not in ('B', 'b'):
                raise ValueError("8-bit mode requires array('B', ...)")
        else:
            if buffer.typecode != 'I':
                raise ValueError("Buffer must be array('I', ...)")
        
        self._buffer = buffer
        self._callback = callback
        self._loop = loop
        
        dreq = _DREQ_PIO0_TX0 if self._pio_id == 0 else _DREQ_PIO1_TX0
        dreq += self._sm_id
        
        pio_base = 0x50200000 if self._pio_id == 0 else 0x50300000
        txf_addr = pio_base + 0x10 + (self._sm_id * 4)
        
        self._dma = DMA()
        
        size = 0 if self._mode == self.MODE_8BIT else 2
        
        ctrl = self._dma.pack_ctrl(
            size=size,
            inc_read=True,
            inc_write=False,
            treq_sel=dreq,
            irq_quiet=0 if (callback and not loop) else 1,
            ring_sel=0 if loop else 0,
            ring_size=0,
        )
        
        self._dma.config(
            read=buffer,
            write=txf_addr,
            count=len(buffer),
            ctrl=ctrl,
            trigger=False,
        )
        
        if callback and not loop:
            self._dma.irq(handler=self._dma_irq_handler)
        
        self._running = True
        self._dma.active(1)
        self._sm.active(1)
        
        return True

    def stop(self):
        if not self._running:
            return
        
        self._running = False
        
        if self._sm is not None:
            try:
                self._sm.active(0)
            except:
                pass
        
        if self._dma is not None:
            try:
                self._dma.active(0)
            except:
                pass
        
        for p in self._pins:
            try:
                machine.Pin(p, machine.Pin.OUT).value(0)
            except:
                pass

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_complete(self) -> bool:
        if not self._running:
            return True
        if self._loop:
            return False
        if self._dma is None:
            return True
        return not self._dma.active()

    def wait(self, timeout_ms: int = None) -> bool:
        import utime
        if self._loop:
            return False
        
        if timeout_ms is None:
            while self._running and self._dma.active():
                pass
            return True
        
        deadline = utime.ticks_add(utime.ticks_ms(), timeout_ms)
        while self._running and self._dma.active():
            if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
                return False
        return True

    def play_once(
        self,
        buffer: array.array,
        *,
        timeout_ms: int = 10000
    ) -> bool:
        self.start(buffer, loop=False)
        result = self.wait(timeout_ms)
        self.stop()
        return result

    def _dma_irq_handler(self, dma):
        self._running = False
        if self._callback:
            try:
                micropython.schedule(self._callback, self._buffer)
            except:
                pass

    @staticmethod
    def generate_square(periods: int, high_cycles: int, low_cycles: int) -> array.array:
        data = []
        for _ in range(periods):
            data.append(high_cycles - 1)
            data.append(low_cycles - 1)
        return array.array('I', data)

    @staticmethod
    def generate_pwm_pattern(values: list[tuple[int, int]]) -> array.array:
        data = []
        for high, low in values:
            if high > 0:
                data.append(high - 1)
            else:
                data.append(0)
            if low > 0:
                data.append(low - 1)
            else:
                data.append(0)
        return array.array('I', data)
