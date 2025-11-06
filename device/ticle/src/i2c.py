import machine
import utime
from .bus_lock import STAT_OK, STAT_BUS_ERR, I2C0_SPINLOCK_ID, I2C1_SPINLOCK_ID, SpinLock

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


def i2cdetect(*, 
              id: int | None = None, 
              sda: int | None = None, 
              scl: int | None = None, 
              deny_pairs: set | None = None, 
              show: bool = False) -> list | None:
    I2C_PIN_MAP = {
        0: ((0, 1), (4, 5), (8, 9), (12, 13), (16, 17), (20, 21)),
        1: ((2, 3), (6, 7), (10, 11), (14, 15), (18, 19), (26, 27)),
    }

    def _check(i2c_id, sda_pin, scl_pin):
        try:
            i2c = machine.I2C(id=i2c_id, sda=machine.Pin(sda_pin), scl=machine.Pin(scl_pin), freq=100_000)
            return i2c.scan()
        except Exception:
            return []
        finally:
            try:
                machine.Pin(scl_pin, machine.Pin.IN)
                machine.Pin(sda_pin, machine.Pin.IN)
            except Exception:
                pass

    def _add_plan(plan, seen, i2c_id, sda_pin, scl_pin):
        key = (i2c_id, sda_pin, scl_pin)
        if key in seen:
            return
        if deny_pairs and (sda_pin, scl_pin) in deny_pairs:
            return
        plan.append(key)
        seen.add(key)

    plan = []
    seen = set()

    if sda is not None and scl is not None:
        if id is None:
            ids_containing = [i for i, pairs in I2C_PIN_MAP.items() if (sda, scl) in pairs]
            ids_others     = [i for i in I2C_PIN_MAP.keys() if i not in ids_containing]
            try_ids = ids_containing + ids_others or [0, 1]
            for i2c_id in try_ids:
                _add_plan(plan, seen, i2c_id, sda, scl)
        else:
            if id in I2C_PIN_MAP and (sda, scl) in I2C_PIN_MAP[id]:
                _add_plan(plan, seen, id, sda, scl)
            else:
                _add_plan(plan, seen, id, sda, scl)
                for p in I2C_PIN_MAP.get(id, ()):
                    if p == (sda, scl):
                        continue
                    _add_plan(plan, seen, id, p[0], p[1])
    elif id is not None:
        for p in I2C_PIN_MAP.get(id, ()):
            _add_plan(plan, seen, id, p[0], p[1])
    else:
        for i2c_id, pairs in I2C_PIN_MAP.items():
            for p in pairs:
                _add_plan(plan, seen, i2c_id, p[0], p[1])

    if not plan:
        return []

    found_any = []

    for i2c_id, sda_pin, scl_pin in plan:
        devices = _check(i2c_id, sda_pin, scl_pin)
        if not devices:
            continue

        found_any.append(((sda_pin, scl_pin), devices))

        if show:
            print(f"I2C{i2c_id} on SDA={sda_pin}, SCL={scl_pin}: {len(devices)} device(s) found")
            print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
            for i in range(0, 8):
                print("{:02x}:".format(i * 16), end='')
                for j in range(0, 16):
                    address = i * 16 + j
                    if address in devices:
                        print(" \x1b[93m{:02x}\x1b[0m".format(address), end='')
                    else:
                        print(" --", end='')
                print()

    return found_any


_I2C_PIN_MAP =  {
    0: {'sda': {0, 4, 8, 12, 16, 20}, 'scl': {1, 5, 9, 13, 17, 21}},
    1: {'sda': {2, 6, 10, 14, 18, 26}, 'scl': {3, 7, 11, 15, 19, 27}},
}


class I2CMaster:
    __slots__ = (
        "_id","_scl","_sda","_timeout_us","_freq","_i2c","_lock",
        "_retry_retries","_retry_delay_us","_b1","_b2","_stats_last_err"
    )

    def __init__(self, *, sda:int, scl:int, freq:int=400_000, timeout_us:int=50_000):
        self._id = self._infer_bus_id_from_pins(sda, scl)
        self._scl, self._sda = scl, sda
        self._freq = freq
        self._timeout_us = timeout_us
        self._retry_retries = 1
        self._retry_delay_us = 200
        self._b1 = bytearray(1)
        self._b2 = bytearray(2)
        self._stats_last_err = STAT_OK
        self._lock = SpinLock(lock_id=(I2C0_SPINLOCK_ID if self._id == 0 else I2C1_SPINLOCK_ID))

        self._i2c = machine.I2C(self._id, scl=machine.Pin(self._scl), sda=machine.Pin(self._sda), freq=self._freq, timeout=self._timeout_us)

    @property
    def bus_id(self) -> int:
        return self._id

    @property
    def pins(self):
        return (self._sda, self._scl)

    @property
    def last_error(self) -> int:
        return self._stats_last_err

    def __repr__(self):
        return f"<I2CMaster id={self._id} sda={self._sda} scl={self._scl} freq={self._freq} timeout_us={self._timeout_us}>"

    def set_retry_policy(self, *, retries:int=None, delay_us:int=None):
        if retries is not None: 
            self._retry_retries = max(0, int(retries))
        
        if delay_us is not None: 
            self._retry_delay_us = max(0, int(delay_us))

    def set_timeout(self, timeout_us:int):
        self._timeout_us = max(0, int(timeout_us))
        self._acquire()
        try:
            self._i2c.init(freq=self._freq, timeout=self._timeout_us)
        except (TypeError, AttributeError):
            self._i2c = machine.I2C(self._id, scl=machine.Pin(self._scl), sda=machine.Pin(self._sda), freq=self._freq, timeout=self._timeout_us)
        finally:
            self._release()

    def set_freq(self, freq:int):
        if freq <= 0:
            raise ValueError("freq must be > 0")
        self._acquire()
        self._freq = freq
        try:
            self._i2c.init(freq=self._freq, timeout=self._timeout_us)
        except (TypeError, AttributeError):
            self._i2c = machine.I2C(self._id, scl=machine.Pin(self._scl), sda=machine.Pin(self._sda), freq=self._freq, timeout=self._timeout_us)
        finally:
            self._release()
 
    def scoped_freq(self, freq:int):
        class _Ctx:
            def __init__(self, m, f): 
                self.m, self.f, self.prev = m, f, None
            
            def __enter__(self):
                self.prev = self.m._freq
                if self.f is not None and self.f != self.prev:
                    self.m.set_freq(self.f)
                return self.m
            
            def __exit__(self, et, ev, tb):
                if self.prev is not None and self.prev != self.m._freq:
                    self.m.set_freq(self.prev)
        
        return _Ctx(self, freq)

    def deinit(self):
        try: self._i2c.deinit()
        except AttributeError: pass

    def _infer_bus_id_from_pins(self, sda, scl):
        for _id, pins in _I2C_PIN_MAP.items():
            if sda in pins['sda'] and scl in pins['scl']:
                return _id
        raise ValueError("Invalid I2C pins for RP2350 map: SDA={}, SCL={}".format(sda, scl))

    def _with_retry(self, fn, *a, retries=None, delay_us=None, **kw):
        r = self._retry_retries if retries is None else retries
        d = self._retry_delay_us if delay_us is None else delay_us
        last = None
        for i in range(r + 1):
            try:
                out = fn(*a, **kw)
                self._stats_last_err = STAT_OK
                return out
            except OSError as e:
                last = f"The device is not recognized: {e}"
                if i == r:
                    self._stats_last_err = STAT_BUS_ERR
                    raise
                utime.sleep_us(d)
        raise last

    def _validate_addr(self, addr:int):
        if not (0 <= addr <= 0x7F):
            raise ValueError("I2C 7-bit address required (0..0x7F)")

    def _validate_addrsize(self, sz:int):
        if sz not in (8, 16):
            raise ValueError("addrsize must be 8 or 16")

    def _validate_reg(self, reg:int, addrsize:int):
        if addrsize == 8 and not (0 <= reg <= 0xFF):
            raise ValueError("reg out of range for 8-bit addrsize")
        if addrsize == 16 and not (0 <= reg <= 0xFFFF):
            raise ValueError("reg out of range for 16-bit addrsize")

    def _acquire(self):
        self._lock.acquire()

    def _release(self):
        self._lock.release()

    def probe(self, addr:int) -> bool:
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto, addr, b"", stop=True)
            return True
        except OSError:
            return False
        finally:
            self._release()

    def readfrom(self, addr:int, nbytes:int, *, stop:bool=True) -> bytes:
        self._validate_addr(addr)
        self._acquire()
        try:
            return self._with_retry(self._i2c.readfrom, addr, nbytes, stop=stop)
        finally:
            self._release()

    def readfrom_into(self, addr:int, buf, *, stop:bool=True) -> None:
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.readfrom_into, addr, buf, stop=stop)
        finally:
            self._release()

    def writeto(self, addr:int, buf, *, stop:bool=True) -> int:
        self._validate_addr(addr)
        self._acquire()
        try:
            return self._with_retry(self._i2c.writeto, addr, buf, stop=stop)
        finally:
            self._release()

    def readfrom_mem(self, addr:int, reg:int, nbytes:int, *, addrsize:int=8) -> bytes:
        self._validate_addr(addr); self._validate_addrsize(addrsize); self._validate_reg(reg, addrsize)
        self._acquire()
        try:
            return self._with_retry(self._i2c.readfrom_mem, addr, reg, nbytes, addrsize=addrsize)
        finally:
            self._release()

    def readfrom_mem_into(self, addr:int, reg:int, buf, *, addrsize:int=8) -> None:
        self._validate_addr(addr); self._validate_addrsize(addrsize); self._validate_reg(reg, addrsize)
        self._acquire()
        try:
            self._with_retry(self._i2c.readfrom_mem_into, addr, reg, buf, addrsize=addrsize)
        finally:
            self._release()

    def writeto_mem(self, addr:int, reg:int, buf, *, addrsize:int=8) -> None:
        self._validate_addr(addr); self._validate_addrsize(addrsize); self._validate_reg(reg, addrsize)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto_mem, addr, reg, buf, addrsize=addrsize)
        finally:
            self._release()

    def read_u8(self, addr:int, reg:int, *, addrsize:int=8) -> int:
        self._validate_addr(addr)
        self.readfrom_mem_into(addr, reg, self._b1, addrsize=addrsize)
        return self._b1[0]

    def read_u16(self, addr:int, reg:int, *, little_endian:bool=True, addrsize:int=8) -> int:
        self._validate_addr(addr)
        self.readfrom_mem_into(addr, reg, self._b2, addrsize=addrsize)
        return (self._b2[0] | (self._b2[1] << 8)) if little_endian else ((self._b2[0] << 8) | self._b2[1])

    def write_u8(self, addr:int, reg:int, val:int, *, addrsize:int=8) -> None:
        self._validate_addr(addr)
        self._b1[0] = val & 0xFF
        self.writeto_mem(addr, reg, self._b1, addrsize=addrsize)

    def write_u16(self, addr:int, reg:int, val:int, *, little_endian:bool=True, addrsize:int=8) -> None:
        self._validate_addr(addr)
        v = val & 0xFFFF
        if little_endian:
            self._b2[0], self._b2[1] = (v & 0xFF), ((v >> 8) & 0xFF)
        else:
            self._b2[0], self._b2[1] = ((v >> 8) & 0xFF), (v & 0xFF)
        self.writeto_mem(addr, reg, self._b2, addrsize=addrsize)

    def write_mem_ex(self, addr:int, reg_bytes:bytes, payload:bytes, *, stop:bool=True) -> None:
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto, addr, reg_bytes, stop=False)
            self._with_retry(self._i2c.writeto, addr, payload, stop=stop)
        finally:
            self._release()

    def read_mem_ex(self, addr:int, reg_bytes:bytes, n:int, out:bytearray=None):
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto, addr, reg_bytes, stop=False)
            if out is None:
                return self._with_retry(self._i2c.readfrom, addr, n, stop=True)
            else:
                self._with_retry(self._i2c.readfrom_into, addr, out, stop=True)
                return None
        finally:
            self._release()
