# @package: bus_lock
# @version: 1.1.0
# @type: device-specific
# @category: utility
# @interface: none
# @depends: none
# @platforms: rp2
# @tags: spinlock, mutex, i2c, spi, multicore, thread-safe

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"

import machine
import time
from micropython import const

STAT_OK        = const(0)
STAT_TIMEOUT   = const(1 << 0)
STAT_BUS_ERR   = const(1 << 1)
STAT_NO_DEVICE = const(1 << 2)

SPI0_SPINLOCK_ID = const(28)
SPI1_SPINLOCK_ID = const(29)
I2C0_SPINLOCK_ID = const(30)
I2C1_SPINLOCK_ID = const(31)

_SPINLOCK_BASE  = const(0xD0000100)

class SpinLock:
    __slots__ = ("_addr", "_polite", "_yield_every")

    def __init__(self, *, lock_id: int, polite: bool = False, yield_every: int = 64):
        if not (0 <= lock_id <= 31):
            raise ValueError("lock_id must be 0..31")
        self._addr = _SPINLOCK_BASE + (lock_id << 2)
        self._polite = polite
        self._yield_every = yield_every if yield_every > 0 else 64

    def acquire(self) -> None:
        addr = self._addr
        if not self._polite:
            while not machine.mem32[addr]:
                pass
        else:
            cnt = 0
            while not machine.mem32[addr]:
                cnt += 1
                if cnt >= self._yield_every:
                    cnt = 0
                    try:
                        machine.idle()
                    except:
                        time.sleep_us(1)

    def release(self) -> None:
        machine.mem32[self._addr] = 1

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, et, ev, tb):
        self.release()
