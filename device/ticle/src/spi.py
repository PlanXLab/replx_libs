import machine
import utime
from .bus_lock import STAT_OK, STAT_BUS_ERR, SPI0_SPINLOCK_ID, SPI1_SPINLOCK_ID, SpinLock

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


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

        self._spi = machine.SPI(self._id,
                                sck=machine.Pin(self._sck),
                                mosi=machine.Pin(self._mosi),
                                miso=machine.Pin(self._miso),
                                baudrate=self._baudrate,
                                polarity=self._polarity,
                                phase=self._phase,
                                bits=self._bits,
                                firstbit=self._firstbit)

        self._lock_depth = 0
        self._ctx_depth  = 0

    def _infer_bus_id_from_pins(self, sck, mosi, miso):
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
                utime.sleep_us(d)
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
    def cs_pin(self):
        return self._cs

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
        try: 
            self._spi.deinit()
        except AttributeError: 
            pass

    def reinit(self, *, baudrate=None, polarity=None, phase=None, bits=None, firstbit=None):
        self._set_cs_inactive()
        
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

    def write(self, buf, *, hold_cs:bool=False):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write, buf)
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._deassert_cs()
        finally:
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._release()

    def readinto(self, buf, *, write:int=0xFF, hold_cs:bool=False):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.readinto, buf, write)
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._deassert_cs()
        finally:
            if not (hold_cs or (self._ctx_depth > 0)): 
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

    def write_readinto(self, wbuf, rbuf, *, hold_cs:bool=False):
        self._acquire()
        try:
            self._assert_cs()
            self._with_retry(self._spi.write_readinto, wbuf, rbuf)
            if not (hold_cs or (self._ctx_depth > 0)): 
                self._deassert_cs()
        finally:
            if not (hold_cs or (self._ctx_depth > 0)): 
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
