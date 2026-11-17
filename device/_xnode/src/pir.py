# @package: pir
# @version: 1.3.0
# @type: device-specific
# @category: board
# @interface: GPIO
# @depends: none
# @platforms: xbee
# @tags: pir, sensor

import utime
import gc
import machine
from micropython import const

class Pir:
    NONE = const(0)
    DETECT = const(1)
    ENTER = const(2)
    LEAVE = const(3)

    def __init__(self, pin='P2'):
        self._pin = machine.Pin(pin, machine.Pin.IN)
        self._t0 = 0
        self._last_state = self._pin.value()

    def reset(self):
        self._t0 = 0
        self._last_state = self._pin.value()

    def read(self):
        return self._pin.value()

    def state(self, sample_ms=0):
        if sample_ms > 0:
            old_state = self._pin.value()
            utime.sleep_ms(sample_ms)
            curr_state = self._pin.value()
        else:
            old_state = self._last_state
            curr_state = self._pin.value()
        self._last_state = curr_state
        if old_state != curr_state:
            return self.ENTER if curr_state else self.LEAVE
        return curr_state

    def detect(self, hold_ms=1500, *, timeout=None):
        if timeout is not None:
            hold_ms = timeout
        if self._pin.value() == self.DETECT:
            now = utime.ticks_ms()
            if self._t0 == 0:
                self._t0 = now
            return utime.ticks_diff(now, self._t0) >= hold_ms
        self._t0 = 0
        return False

gc.collect()
