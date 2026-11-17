# @package: pir
# @version: 1.1.0
# @type: device-specific
# @category: board
# @interface: GPIO
# @depends: none
# @platforms: xbee
# @tags: pir, sensor

import time
import machine


class Pir:
    NONE = 0
    DETECT = 1
    ENTER = 2
    LEAVE = 3
    
    def __init__(self):
        self.__pin = machine.Pin('P2', machine.Pin.IN)
        self.__t0 = 0
        
    def read(self):
        return self.__pin.value()

    def state(self, timeout=1):
        old_state = self.read()
        time.sleep_ms(timeout)
        curr_state = self.read()
        if old_state != curr_state:
            return self.ENTER if curr_state else self.LEAVE
        else:
            return curr_state
    
    def detect(self, timeout=1500):
        n = self.read()
        if n == self.DETECT and not self.__t0:
            self.__t0 = time.ticks_ms()
        elif self.__t0:
            if time.ticks_diff(time.ticks_ms(), self.__t0) >= timeout:
                self.__t0 = 0
            n = not self.DETECT
        return n == self.DETECT
