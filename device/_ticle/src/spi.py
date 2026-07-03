# @package: spi
# @version: 1.5.0
# @type: device-specific
# @category: peripheral
# @interface: SPI
# @depends: bus_lock, utools
# @platforms: rp2
# @tags: spi, bus, spinlock, thread-safe, multicore, pio, dma, slave
# @author: PlanXLab Development Team

import rp2
import machine
import uctypes
import time
from .bus_lock import STAT_OK, STAT_BUS_ERR, SPI0_SPINLOCK_ID, SPI1_SPINLOCK_ID, SpinLock
from .utools import find_free_sm

class _CSCtx:
    __slots__ = ("_spi",)
    def __init__(self, spi): 
        self._spi = spi

    def __enter__(self):
        s = self._spi
        s._acquire()
        if s._ctx_depth == 0:
            s._assert_cs()
        s._ctx_depth += 1
        return s

    def __exit__(self, et, ev, tb):
        s = self._spi
        s._ctx_depth -= 1
        if s._ctx_depth == 0:
            s._deassert_cs()
        s._release()

_SPI_PIN_MAP = {
    0: {
        'miso': {0, 4, 16},
        'cs':   {1, 5, 17},
        'sck':  {2, 6, 18},
        'mosi': {3, 7, 19},
    },
    1: {
        'mosi': { 8, 12},
        'cs':   { 9, 13},
        'sck':  {10, 14},
        'miso': {11, 15},
    },
}

class Spi:
    __slots__ = (
        "_id", "_sck","_mosi","_miso","_cs_active_low","_cs",
        "_baudrate","_polarity","_phase","_bits","_firstbit",
        "_lock","_retry_retries","_retry_delay_us",
        "_stats_last_err","_b1", "_spi",
        "_lock_depth","_ctx_depth",
    )

    def __init__(self, *,
                 sck:int=None, mosi:int=None, miso:int=None,
                 cs:int=None, cs_active_low:bool=True,
                 baudrate:int=10_000_000, polarity:int=0, phase:int=0,
                 bits:int=8, firstbit:int=None):
        if firstbit is None:
            firstbit = getattr(machine.SPI, "MSB", 0)
        if sck is None or mosi is None or miso is None or cs is None:
            raise ValueError("sck/mosi/miso/cs required")
        if len({sck, mosi, miso, cs}) != 4:
            raise ValueError("sck/mosi/miso/cs must be distinct pins")

        self._id = self._infer_bus_id_from_pins(sck, mosi, miso)
        if cs not in _SPI_PIN_MAP[self._id]['cs']:
            raise ValueError("CS pin %d not valid for SPI%d" % (cs, self._id))
        self._sck, self._mosi, self._miso = sck, mosi, miso

        self._cs = machine.Pin(cs, machine.Pin.OUT)
        self._cs_active_low = cs_active_low
        self._set_cs_inactive()

        self._baudrate = baudrate
        self._polarity = polarity
        self._phase    = phase
        self._bits     = bits
        self._firstbit = firstbit
        self._lock = SpinLock(lock_id=SPI0_SPINLOCK_ID if self._id == 0 else SPI1_SPINLOCK_ID)
        self._retry_retries  = 1
        self._retry_delay_us = 200
        self._stats_last_err = STAT_OK
        self._b1 = bytearray(1)
        self._lock_depth = 0
        self._ctx_depth  = 0

        self._spi = machine.SPI(self._id,
                                sck=machine.Pin(self._sck),
                                mosi=machine.Pin(self._mosi),
                                miso=machine.Pin(self._miso),
                                baudrate=self._baudrate,
                                polarity=self._polarity,
                                phase=self._phase,
                                bits=self._bits,
                                firstbit=self._firstbit)

    @staticmethod
    def _infer_bus_id_from_pins(sck, mosi, miso):
        for _id, pins in _SPI_PIN_MAP.items():
            if (sck in pins['sck']) and (mosi in pins['mosi']) and (miso in pins['miso']):
                return _id
        raise ValueError("Invalid SPI pins for RP2350 map: SCK={}, MOSI={}, MISO={}".format(sck, mosi, miso))

    def _with_retry(self, fn, *a, retries=None, delay_us=None, **kw):
        r = self._retry_retries if retries is None else retries
        d = self._retry_delay_us if delay_us is None else delay_us
        last = None
        for i in range(r+1):
            try:
                out = fn(*a, **kw)
                self._stats_last_err = STAT_OK
                return out
            except OSError as e:
                last = e
                if i == r:
                    self._stats_last_err = STAT_BUS_ERR
                    raise
                time.sleep_us(d)
        raise last

    def _acquire(self):
        if self._lock_depth == 0:
            self._lock.acquire()
        self._lock_depth += 1

    def _release(self):
        if self._lock_depth <= 0:
            return
        self._lock_depth -= 1
        if self._lock_depth == 0:
            self._lock.release()

    def _set_cs_active(self):
        self._cs.value(0 if self._cs_active_low else 1)

    def _set_cs_inactive(self):
        self._cs.value(1 if self._cs_active_low else 0)

    def _assert_cs(self):
        self._set_cs_active()

    def _deassert_cs(self):
        self._set_cs_inactive()

    @property
    def bus_id(self): 
        return self._id
    
    @property
    def pins(self):   
        return (self._sck, self._mosi, self._miso)

    @property
    def cs_pin(self) -> int:
        return self._cs.id()

    @property
    def last_error(self) -> int:
        return self._stats_last_err

    def __repr__(self):
        cs_id = self._cs.id()
        fb = "MSB" if self._firstbit == getattr(machine.SPI, "MSB", 0) else "LSB"
        return ("<Spi id=%d sck=%s mosi=%s miso=%s cs=%s baud=%d pol=%d pha=%d bits=%d firstbit=%s>" %
                (self._id, self._sck, self._mosi, self._miso, cs_id,
                 self._baudrate, self._polarity, self._phase, self._bits, fb))

    def set_retry_policy(self, *, retries:int=None, delay_us:int=None):
        if retries is not None:
            if retries < 0: raise ValueError("retries must be >= 0")
            self._retry_retries = retries
        if delay_us is not None:
            if delay_us < 0: raise ValueError("delay_us must be >= 0")
            self._retry_delay_us = delay_us

    def deinit(self):
        try:
            self._set_cs_inactive()
        except Exception:
            pass
        if self._lock_depth > 0:
            self._lock_depth = 0
            self._lock.release()
        try:
            self._spi.deinit()
        except AttributeError:
            pass

    def reinit(self, *, baudrate=None, polarity=None, phase=None, bits=None, firstbit=None):
        self._set_cs_inactive()
        self._lock_depth = 0
        self._ctx_depth  = 0

        if baudrate is not None:
            self._baudrate = baudrate
        if polarity is not None: 
            self._polarity = polarity
        if phase is not None: 
            self._phase    = phase
        if bits is not None: 
            self._bits     = bits
        if firstbit is not None: 
            self._firstbit = firstbit
        try:
            self._spi.init(baudrate=self._baudrate, polarity=self._polarity, phase=self._phase, bits=self._bits, firstbit=self._firstbit)
        except AttributeError:
            self._spi.deinit()
            self._spi = machine.SPI(self._id,
                                    sck=machine.Pin(self._sck),
                                    mosi=machine.Pin(self._mosi),
                                    miso=machine.Pin(self._miso),
                                    baudrate=self._baudrate,
                                    polarity=self._polarity,
                                    phase=self._phase,
                                    bits=self._bits,
                                    firstbit=self._firstbit)

    def select(self):
        self._acquire()
        self._assert_cs()

    def deselect(self):
        self._deassert_cs()
        self._release()

    def selected(self):
        return _CSCtx(self)

    def write(self, buf):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write, buf)
            if self._ctx_depth == 0:
                self._deassert_cs()
        finally:
            if self._ctx_depth == 0:
                self._release()

    def readinto(self, buf, *, write:int=0xFF):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.readinto, buf, write)
            if self._ctx_depth == 0:
                self._deassert_cs()
        finally:
            if self._ctx_depth == 0:
                self._release()

    def read(self, n:int, *, write:int=0xFF) -> bytes:
        self._acquire()
        try:
            self._assert_cs()
            data = self._with_retry(self._spi.read, n, write)
            if self._ctx_depth == 0:
                self._deassert_cs()
            return data
        finally:
            if self._ctx_depth == 0:
                self._release()

    def write_readinto(self, wbuf, rbuf):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write_readinto, wbuf, rbuf)
            if self._ctx_depth == 0:
                self._deassert_cs()
        finally:
            if self._ctx_depth == 0:
                self._release()

    def write_then_readinto(self, cmd_bytes, rx_buf, *, dummy:int=0xFF):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write, cmd_bytes)
            self._with_retry(self._spi.readinto, rx_buf, dummy)
            if self._ctx_depth == 0:
                self._deassert_cs()
        finally:
            if self._ctx_depth == 0:
                self._release()

    def write_then_write(self, cmd_bytes, payload_bytes):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write, cmd_bytes)
            self._with_retry(self._spi.write, payload_bytes)
            if self._ctx_depth == 0:
                self._deassert_cs()
        finally:
            if self._ctx_depth == 0:
                self._release()

    def write_u8(self, v:int):
        self._b1[0] = v & 0xFF
        self.write(self._b1)

    def read_u8(self) -> int:
        self.readinto(self._b1)
        return self._b1[0]


@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8, fifo_join=rp2.PIO.JOIN_RX)
def _spi_slave_rx():
    label("wait_cs")
    jmp(pin, "wait_cs")
    wrap_target()
    wait(0, pin, 31)
    wait(1, pin, 31)
    in_(pins, 1)
    wrap()


@rp2.asm_pio(out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=8,
             out_init=rp2.PIO.OUT_LOW)
def _spi_slave_tx():
    label("wait_cs")
    jmp(pin, "wait_cs")
    out(pins, 1)
    wrap_target()
    wait(1, pin, 31)
    out(pins, 1)
    wait(0, pin, 31)
    wrap()


_PIO_BASE = (0x50200000, 0x50300000, 0x50400000)
_RX_DREQ  = (4,  5,  6,  7,   12, 13, 14, 15,   20, 21, 22, 23)
_TX_DREQ  = (0,  1,  2,  3,    8,  9, 10, 11,   16, 17, 18, 19)


def _rxf_addr(sm_id):
    return _PIO_BASE[sm_id // 4] + 0x20 + (sm_id % 4) * 4


def _txf_addr(sm_id):
    return _PIO_BASE[sm_id // 4] + 0x10 + (sm_id % 4) * 4


class SpiSlave:
    __slots__ = (
        "_buf_size", "_cs_pin", "_mosi_pin",
        "_rx_sm", "_buf", "_baddr", "_rx_dma", "_rx_ctrl", "_rxf",
        "_active", "_done_buf", "_done_n", "_ready",
        "_miso_pin", "_tx_sm", "_tx_dma", "_tx_ctrl", "_txf", "_tx_buf",
    )

    def __init__(self, sck=2, mosi=3, cs=5, *, sm=None, miso=None, buf_size=8192):
        if mosi != sck + 1:
            raise ValueError("MOSI must equal SCK+1 (e.g., sck=2, mosi=3)")

        self._buf_size = buf_size

        needed = 2 if miso is not None else 1
        if sm is None:
            ids = find_free_sm(needed)
            rx_id = ids[0]
            tx_id = ids[1] if needed == 2 else None
        else:
            rx_id = sm
            tx_id = sm + 1 if miso is not None else None

        self._cs_pin   = machine.Pin(cs,   machine.Pin.IN, pull=machine.Pin.PULL_UP)
        self._mosi_pin = machine.Pin(mosi, machine.Pin.IN)
        machine.Pin(sck, machine.Pin.IN)

        self._rx_sm = rp2.StateMachine(
            rx_id, _spi_slave_rx,
            in_base=self._mosi_pin,
            jmp_pin=self._cs_pin,
        )

        self._buf   = [bytearray(buf_size), bytearray(buf_size)]
        self._baddr = [uctypes.addressof(self._buf[0]), uctypes.addressof(self._buf[1])]
        self._rx_dma = rp2.DMA()
        self._rx_ctrl = self._rx_dma.pack_ctrl(
            size=0, inc_read=False, inc_write=True, treq_sel=_RX_DREQ[rx_id]
        )
        self._rxf = _rxf_addr(rx_id)

        self._active   = 0
        self._done_buf = None
        self._done_n   = 0
        self._ready    = False

        self._tx_sm  = None
        self._tx_dma = None
        if miso is not None:
            self._miso_pin = machine.Pin(miso, machine.Pin.OUT, value=0)
            self._tx_sm = rp2.StateMachine(
                tx_id, _spi_slave_tx,
                in_base=self._mosi_pin,
                out_base=self._miso_pin,
                jmp_pin=self._cs_pin,
            )
            self._tx_buf  = bytearray(buf_size)
            self._tx_dma  = rp2.DMA()
            self._tx_ctrl = self._tx_dma.pack_ctrl(
                size=0, inc_read=True, inc_write=False, treq_sel=_TX_DREQ[tx_id]
            )
            self._txf = _txf_addr(tx_id)
            self._tx_sm.active(1)

        self._rx_sm.active(1)
        self._cs_pin.irq(self._cs_irq, machine.Pin.IRQ_RISING)
        self._arm_rx(0)


    def _arm_rx(self, idx):
        self._active = idx
        self._rx_dma.config(
            read=self._rxf, write=self._buf[idx],
            count=self._buf_size, ctrl=self._rx_ctrl, trigger=True
        )

    def _cs_irq(self, pin):
        n = self._rx_dma.write - self._baddr[self._active]
        self._rx_dma.active(0)
        self._rx_sm.active(0)
        self._rx_sm.restart()
        self._rx_sm.active(1)
        self._done_buf = self._buf[self._active]
        self._done_n   = n
        self._ready    = True
        self._arm_rx(1 - self._active)

    def any(self):
        return self._ready

    def read(self, timeout=10000):
        end = time.ticks_add(time.ticks_ms(), timeout)
        while not self._ready:
            if time.ticks_diff(end, time.ticks_ms()) <= 0:
                return None
        buf = bytes(memoryview(self._done_buf)[:self._done_n])
        self._ready = False
        return buf

    def readinto(self, buf, timeout=10000):
        end = time.ticks_add(time.ticks_ms(), timeout)
        while not self._ready:
            if time.ticks_diff(end, time.ticks_ms()) <= 0:
                return 0
        n = min(self._done_n, len(buf))
        buf[:n] = memoryview(self._done_buf)[:n]
        self._ready = False
        return n

    def write(self, data):
        if self._tx_dma is None:
            raise OSError("MISO pin not configured")
        n = min(len(data), self._buf_size)
        self._tx_buf[:n] = data[:n]
        self._tx_sm.restart()
        self._tx_dma.config(
            read=uctypes.addressof(self._tx_buf), write=self._txf,
            count=n, ctrl=self._tx_ctrl, trigger=True
        )

    def writeinto(self, data, buf, timeout=10000):
        self.write(data)
        return self.readinto(buf, timeout)

    def deinit(self):
        self._cs_pin.irq(None)
        self._rx_dma.active(0)
        self._rx_dma.close()
        self._rx_sm.active(0)
        if self._tx_dma is not None:
            self._tx_dma.active(0)
            self._tx_dma.close()
            self._tx_sm.active(0)