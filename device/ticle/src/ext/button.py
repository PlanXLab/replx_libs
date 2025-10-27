__version__ = "1.1.0"
__author__  = "PlanX Lab Development Team"

from . import (
    machine
)


class Button:
    ACTIVE_HIGH = True
    ACTIVE_LOW  = False

    def __init__(self, pin: int, *, active_high: bool = True, pull: int | None = None):
        if pull is None:
            pull = (machine.Pin.PULL_DOWN if active_high else machine.Pin.PULL_UP)
        self._pin = machine.Pin(pin, machine.Pin.IN, pull)
        self._active_high = bool(active_high)

    def deinit(self):
        try:
            _ = self._pin.value()
        except Exception:
            pass

    def value(self) -> int:
        return 1 if self._pin.value() else 0

    @property
    def pressed(self) -> bool:
        raw = self.value()
        return bool(raw) if self._active_high else bool(1 - raw)
