# @package: i2c
# @version: 1.0.0
# @type: device-specific
# @category: peripheral
# @interface: I2C
# @depends: i2c, bus_lock
# @platforms: rp2
# @tags: i2c, bus, spinlock, thread-safe, multicore
# @author: PlanXLab Development Team

import machine
from i2c import I2CController as _I2CControllerBase
from i2c import I2CTarget as I2CTarget
from i2c import i2cdetect as i2cdetect

from .bus_lock import SpinLock, I2C0_SPINLOCK_ID, I2C1_SPINLOCK_ID

_I2C_PIN_MAP = {
    0: {'sda': {0, 4, 8, 12, 16, 20}, 'scl': {1, 5, 9, 13, 17, 21}},
    1: {'sda': {2, 6, 10, 14, 18, 26}, 'scl': {3, 7, 11, 15, 19, 27}},
}

def i2cdetect_auto(*,
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
            ids_others = [i for i in I2C_PIN_MAP.keys() if i not in ids_containing]
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

class I2CController(_I2CControllerBase):
    __slots__ = ("_lock",)

    def __init__(self, *, sda: int, scl: int, freq: int = 400_000):
        bus_id = self._infer_bus_id(sda, scl)
        super().__init__(sda=sda, scl=scl, id=bus_id, freq=freq)

        lock_id = I2C0_SPINLOCK_ID if bus_id == 0 else I2C1_SPINLOCK_ID
        self._lock = SpinLock(lock_id=lock_id)

    def __repr__(self):
        return f"<I2CController id={self._id} sda={self._sda} scl={self._scl} freq={self._freq}>"

    @staticmethod
    def _infer_bus_id(sda: int, scl: int) -> int:
        for _id, pins in _I2C_PIN_MAP.items():
            if sda in pins['sda'] and scl in pins['scl']:
                return _id
        raise ValueError(f"Invalid I2C pins for RP2350: SDA={sda}, SCL={scl}")

    def _acquire(self):
        self._lock.acquire()

    def _release(self):
        self._lock.release()
