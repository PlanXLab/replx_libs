# @package: i2c
# @version: 1.0
# @type: core
# @category: peripheral
# @interface: I2C
# @depends: none
# @platforms: *
# @tags: i2c, bus, master, communication, sensor
# @author: PlanXLab Development Team

import machine
import time


class I2CController:
    __slots__ = (
        "_id", "_scl", "_sda", "_freq", "_i2c",
        "_retry_retries", "_retry_delay_us", "_b1", "_b2", "_last_err"
    )

    STAT_OK = 0
    STAT_TIMEOUT = 1
    STAT_BUS_ERR = 2
    STAT_NO_DEVICE = 4

    def __init__(self, *, sda: int, scl: int, id: int = 0, freq: int = 400_000):
        self._id = id
        self._scl = scl
        self._sda = sda
        self._freq = freq
        self._retry_retries = 1
        self._retry_delay_us = 200
        self._b1 = bytearray(1)
        self._b2 = bytearray(2)
        self._last_err = self.STAT_OK

        self._i2c = machine.I2C(
            self._id,
            scl=machine.Pin(self._scl),
            sda=machine.Pin(self._sda),
            freq=self._freq
        )

    @property
    def bus_id(self) -> int:
        return self._id

    @property
    def pins(self) -> tuple:
        return (self._sda, self._scl)

    @property
    def freq(self) -> int:
        return self._freq

    @property
    def last_error(self) -> int:
        return self._last_err

    def __repr__(self):
        return f"<I2CController id={self._id} sda={self._sda} scl={self._scl} freq={self._freq}>"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def deinit(self):
        try:
            self._i2c.deinit()
        except AttributeError:
            pass

    def set_retry_policy(self, *, retries: int = None, delay_us: int = None):
        if retries is not None:
            self._retry_retries = max(0, int(retries))
        if delay_us is not None:
            self._retry_delay_us = max(0, int(delay_us))

    def set_freq(self, freq: int):
        if freq <= 0:
            raise ValueError("freq must be > 0")
        self._acquire()
        try:
            self._freq = freq
            self._reinit_i2c()
        finally:
            self._release()

    def _reinit_i2c(self):
        try:
            if hasattr(self._i2c, 'deinit'):
                self._i2c.deinit()
        except Exception:
            pass
        self._i2c = machine.I2C(
            self._id,
            scl=machine.Pin(self._scl),
            sda=machine.Pin(self._sda),
            freq=self._freq
        )

    def scoped_freq(self, freq: int):
        class _FreqCtx:
            def __init__(ctx, master, new_freq):
                ctx._master = master
                ctx._new_freq = new_freq
                ctx._prev_freq = None

            def __enter__(ctx):
                ctx._prev_freq = ctx._master._freq
                if ctx._new_freq is not None and ctx._new_freq != ctx._prev_freq:
                    ctx._master.set_freq(ctx._new_freq)
                return ctx._master

            def __exit__(ctx, et, ev, tb):
                if ctx._prev_freq is not None and ctx._prev_freq != ctx._master._freq:
                    ctx._master.set_freq(ctx._prev_freq)

        return _FreqCtx(self, freq)

    def _acquire(self):
        pass

    def _release(self):
        pass

    def _with_retry(self, fn, *args, retries=None, delay_us=None, **kwargs):
        r = self._retry_retries if retries is None else retries
        d = self._retry_delay_us if delay_us is None else delay_us
        last_err = None

        for i in range(r + 1):
            try:
                result = fn(*args, **kwargs)
                self._last_err = self.STAT_OK
                return result
            except OSError as e:
                last_err = e
                if i == r:
                    self._last_err = self.STAT_BUS_ERR
                    raise
                time.sleep_us(d)

        raise last_err

    def _validate_addr(self, addr: int):
        if not (0 <= addr <= 0x7F):
            raise ValueError("I2C 7-bit address required (0..0x7F)")

    def _validate_addrsize(self, sz: int):
        if sz not in (8, 16):
            raise ValueError("addrsize must be 8 or 16")

    def _validate_reg(self, reg: int, addrsize: int):
        if addrsize == 8 and not (0 <= reg <= 0xFF):
            raise ValueError("reg out of range for 8-bit addrsize")
        if addrsize == 16 and not (0 <= reg <= 0xFFFF):
            raise ValueError("reg out of range for 16-bit addrsize")

    def scan(self) -> list:
        self._acquire()
        try:
            return self._i2c.scan()
        finally:
            self._release()

    def probe(self, addr: int) -> bool:
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto, addr, b"", True)
            return True
        except OSError:
            return False
        finally:
            self._release()

    def readfrom(self, addr: int, nbytes: int, *, stop: bool = True) -> bytes:
        self._validate_addr(addr)
        self._acquire()
        try:
            return self._with_retry(self._i2c.readfrom, addr, nbytes, stop)
        finally:
            self._release()

    def readfrom_into(self, addr: int, buf, *, stop: bool = True) -> None:
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.readfrom_into, addr, buf, stop)
        finally:
            self._release()

    def writeto(self, addr: int, buf, *, stop: bool = True) -> int:
        self._validate_addr(addr)
        self._acquire()
        try:
            return self._with_retry(self._i2c.writeto, addr, buf, stop)
        finally:
            self._release()

    def readfrom_mem(self, addr: int, reg: int, nbytes: int, *, addrsize: int = 8) -> bytes:
        self._validate_addr(addr)
        self._validate_addrsize(addrsize)
        self._validate_reg(reg, addrsize)
        self._acquire()
        try:
            return self._with_retry(self._i2c.readfrom_mem, addr, reg, nbytes, addrsize=addrsize)
        finally:
            self._release()

    def readfrom_mem_into(self, addr: int, reg: int, buf, *, addrsize: int = 8) -> None:
        self._validate_addr(addr)
        self._validate_addrsize(addrsize)
        self._validate_reg(reg, addrsize)
        self._acquire()
        try:
            self._with_retry(self._i2c.readfrom_mem_into, addr, reg, buf, addrsize=addrsize)
        finally:
            self._release()

    def writeto_mem(self, addr: int, reg: int, buf, *, addrsize: int = 8) -> None:
        self._validate_addr(addr)
        self._validate_addrsize(addrsize)
        self._validate_reg(reg, addrsize)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto_mem, addr, reg, buf, addrsize=addrsize)
        finally:
            self._release()

    def read_u8(self, addr: int, reg: int, *, addrsize: int = 8) -> int:
        self._validate_addr(addr)
        self.readfrom_mem_into(addr, reg, self._b1, addrsize=addrsize)
        return self._b1[0]

    def read_u16(self, addr: int, reg: int, *, little_endian: bool = True, addrsize: int = 8) -> int:
        self._validate_addr(addr)
        self.readfrom_mem_into(addr, reg, self._b2, addrsize=addrsize)
        if little_endian:
            return self._b2[0] | (self._b2[1] << 8)
        else:
            return (self._b2[0] << 8) | self._b2[1]

    def write_u8(self, addr: int, reg: int, val: int, *, addrsize: int = 8) -> None:
        self._validate_addr(addr)
        self._b1[0] = val & 0xFF
        self.writeto_mem(addr, reg, self._b1, addrsize=addrsize)

    def write_u16(self, addr: int, reg: int, val: int, *, little_endian: bool = True, addrsize: int = 8) -> None:
        self._validate_addr(addr)
        v = val & 0xFFFF
        if little_endian:
            self._b2[0] = v & 0xFF
            self._b2[1] = (v >> 8) & 0xFF
        else:
            self._b2[0] = (v >> 8) & 0xFF
            self._b2[1] = v & 0xFF
        self.writeto_mem(addr, reg, self._b2, addrsize=addrsize)

    def write_mem_ex(self, addr: int, reg_bytes: bytes, payload: bytes, *, stop: bool = True) -> None:
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto, addr, reg_bytes, False)
            self._with_retry(self._i2c.writeto, addr, payload, stop)
        finally:
            self._release()

    def read_mem_ex(self, addr: int, reg_bytes: bytes, n: int, out: bytearray = None):
        self._validate_addr(addr)
        self._acquire()
        try:
            self._with_retry(self._i2c.writeto, addr, reg_bytes, False)
            if out is None:
                return self._with_retry(self._i2c.readfrom, addr, n, True)
            else:
                self._with_retry(self._i2c.readfrom_into, addr, out, True)
                return None
        finally:
            self._release()


class I2CTarget:
    __slots__ = (
        "_id", "_scl", "_sda", "_addr", "_addrsize", "_mem", "_mem_addrsize",
        "_i2c", "_handler", "_memaddr"
    )

    IRQ_ADDR_MATCH_READ = 0x01
    IRQ_ADDR_MATCH_WRITE = 0x02
    IRQ_READ_REQ = 0x04
    IRQ_WRITE_REQ = 0x08
    IRQ_END_READ = 0x10
    IRQ_END_WRITE = 0x20

    def __init__(
        self,
        addr: int,
        *,
        id: int = 0,
        sda: int | None = None,
        scl: int | None = None,
        addrsize: int = 7,
        mem: bytearray | None = None,
        mem_addrsize: int = 8
    ):
        if not hasattr(machine, 'I2CTarget'):
            raise NotImplementedError("machine.I2CTarget not available on this platform")

        if not (0 <= addr <= (0x7F if addrsize == 7 else 0x3FF)):
            raise ValueError(f"Invalid address for {addrsize}-bit addressing")

        self._id = id
        self._sda = sda
        self._scl = scl
        self._addr = addr
        self._addrsize = addrsize
        self._mem = mem
        self._mem_addrsize = mem_addrsize
        self._handler = None
        self._memaddr = 0

        kwargs = {"addr": addr, "addrsize": addrsize, "mem_addrsize": mem_addrsize}
        if mem is not None:
            kwargs["mem"] = mem
        if sda is not None:
            kwargs["sda"] = machine.Pin(sda)
        if scl is not None:
            kwargs["scl"] = machine.Pin(scl)

        self._i2c = machine.I2CTarget(id, **kwargs)

    @property
    def addr(self) -> int:
        return self._addr

    @property
    def bus_id(self) -> int:
        return self._id

    @property
    def pins(self) -> tuple:
        return (self._sda, self._scl)

    @property
    def memaddr(self) -> int:
        return self._i2c.memaddr if hasattr(self._i2c, 'memaddr') else self._memaddr

    def __repr__(self):
        return f"<I2CTarget id={self._id} addr=0x{self._addr:02X}>"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def deinit(self):
        try:
            self._i2c.deinit()
        except (AttributeError, OSError):
            pass

    def readinto(self, buf: bytearray) -> int:
        return self._i2c.readinto(buf)

    def write(self, buf: bytes | bytearray) -> int:
        return self._i2c.write(buf)

    def irq(
        self,
        handler=None,
        trigger: int = None,
        hard: bool = False
    ):
        if trigger is None:
            trigger = self.IRQ_END_READ | self.IRQ_END_WRITE

        self._handler = handler
        return self._i2c.irq(handler=handler, trigger=trigger, hard=hard)

    @staticmethod
    def available() -> bool:
        return hasattr(machine, 'I2CTarget')


def i2cdetect(i2c: I2CController, *, color: bool = True) -> list[int]:
    devices = i2c.scan()
    
    hi = "\x1b[93m" if color else ""
    rs = "\x1b[0m" if color else ""
    
    print(f"I2C id={i2c.bus_id} SDA={i2c.pins[0]} SCL={i2c.pins[1]}: {len(devices)} device(s)")
    print("     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f")
    for row in range(8):
        print("{:02x}:".format(row * 16), end='')
        for col in range(16):
            addr = row * 16 + col
            if addr in devices:
                print(f" {hi}{addr:02x}{rs}", end='')
            else:
                print(" --", end='')
        print()
    
    return devices
