# @package: pio_capture
# @version: 1.0.0
# @type: device-specific
# @category: pio
# @interface: GPIO
# @depends: none
# @platforms: rp2
# @tags: pio, capture, dma, gpio, logic-analyzer, pulse, timing
# @author: PlanXLab Development Team

import machine
import micropython
import array
from rp2 import PIO, StateMachine, DMA, asm_pio
from .utools import find_free_sm
        
@asm_pio(sideset_init=None, autopush=True, push_thresh=32)
def _capture_rising():
    wait(0, pin, 0)
    wait(1, pin, 0)
    in_(pins, 1)

@asm_pio(sideset_init=None, autopush=True, push_thresh=32)
def _capture_falling():
    wait(1, pin, 0)
    wait(0, pin, 0)
    in_(pins, 1)

@asm_pio(sideset_init=None, autopush=True, push_thresh=32)
def _capture_both():
    mov(x, pins)
    label("wait_change")
    mov(y, pins)
    jmp(x_not_y, "changed")
    jmp("wait_change")
    label("changed")
    in_(pins, 1)
    mov(x, y)

@asm_pio(in_shiftdir=PIO.SHIFT_LEFT, autopush=True, push_thresh=32)
def _capture_parallel():
    in_(pins, 8)

@asm_pio(sideset_init=None, autopush=True, push_thresh=32)
def _capture_continuous():
    in_(pins, 1)

_DREQ_PIO0_RX0 = micropython.const(4)
_DREQ_PIO1_RX0 = micropython.const(12)

class PioCapture:
    
    RISING = micropython.const(0)
    FALLING = micropython.const(1)
    BOTH = micropython.const(2)
    CONTINUOUS = micropython.const(3)
    PARALLEL = micropython.const(4)

    def __init__(
        self,
        pin: int | list[int],
        *,
        mode: int = 0
    ):
        self._mode = mode
        
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
            if mode == self.PARALLEL and self._pin_count > 8:
                raise ValueError("Parallel mode supports max 8 pins")
        
        self._sm_id = find_free_sm(1)[0]
        
        self._sm = None
        self._dma = None
        self._buffer = None
        self._callback = None
        self._running = False
        
        self._init_sm()

    def _init_sm(self):
        programs = {
            self.RISING: _capture_rising,
            self.FALLING: _capture_falling,
            self.BOTH: _capture_both,
            self.CONTINUOUS: _capture_continuous,
            self.PARALLEL: _capture_parallel,
        }
        
        prog = programs.get(self._mode)
        if prog is None:
            raise ValueError(f"Invalid capture mode: {self._mode}")
        
        if self._mode == self.PARALLEL:
            self._sm = StateMachine(
                self._sm_id,
                prog,
                freq=125_000_000,
                in_base=machine.Pin(self._base_pin),
            )
        else:
            self._sm = StateMachine(
                self._sm_id,
                prog,
                freq=125_000_000,
                in_base=machine.Pin(self._base_pin),
                jmp_pin=machine.Pin(self._base_pin),
            )

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
        self._sm.freq(freq)

    def start(
        self,
        buffer: array.array,
        *,
        count: int = None,
        callback: callable = None
    ) -> bool:
        if self._running:
            return False
        
        if buffer.typecode != 'I':
            raise ValueError("Buffer must be array('I', ...)")
        
        self._buffer = buffer
        self._callback = callback
        
        buf_words = len(buffer)
        if count is not None:
            buf_words = min(count, buf_words)
        
        dreq = _DREQ_PIO0_RX0 if self._pio_id == 0 else _DREQ_PIO1_RX0
        dreq += self._sm_id
        
        pio_base = 0x50200000 if self._pio_id == 0 else 0x50300000
        rxf_addr = pio_base + 0x20 + (self._sm_id * 4)
        
        self._dma = DMA()
        
        ctrl = self._dma.pack_ctrl(
            size=2,
            inc_read=False,
            inc_write=True,
            treq_sel=dreq,
            irq_quiet=0 if callback else 1,
        )
        
        self._dma.config(
            read=rxf_addr,
            write=buffer,
            count=buf_words,
            ctrl=ctrl,
            trigger=False,
        )
        
        if callback:
            self._dma.irq(handler=self._dma_irq_handler)
        
        while self._sm.rx_fifo() > 0:
            self._sm.get()
        
        self._running = True
        self._sm.active(1)
        self._dma.active(1)
        
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

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_complete(self) -> bool:
        if not self._running:
            return True
        if self._dma is None:
            return True
        return not self._dma.active()

    def bytes_captured(self) -> int:
        if self._dma is None:
            return 0
        write_addr = self._dma.write
        start_addr = id(self._buffer) + 8
        return write_addr - start_addr

    def wait(self, timeout_ms: int = None) -> bool:
        import utime
        if timeout_ms is None:
            while self._running and self._dma.active():
                pass
            return True
        
        deadline = utime.ticks_add(utime.ticks_ms(), timeout_ms)
        while self._running and self._dma.active():
            if utime.ticks_diff(deadline, utime.ticks_ms()) <= 0:
                return False
        return True

    def read_blocking(
        self,
        count: int,
        *,
        timeout_ms: int = 5000
    ) -> array.array:
        buf = array.array('I', [0] * count)
        self.start(buf, count=count)
        if not self.wait(timeout_ms):
            self.stop()
            raise TimeoutError("Capture timeout")
        self.stop()
        return buf

    def _dma_irq_handler(self, dma):
        self._running = False
        if self._callback:
            try:
                micropython.schedule(self._callback, self._buffer)
            except:
                pass
