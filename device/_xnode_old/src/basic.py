# @package: basic
# @version: 1.1.0
# @type: device-specific
# @category: board
# @interface: GPIO, I2C
# @depends: none
# @platforms: xbee
# @tags: buzzer, led, button, actuator

import time
import machine
from micropython import const


PCA9535_ADDR = const(0x24)

class _I2CtoGPIO:
    def __init__(self):
        self._i2c = machine.I2C(1)
        self._i2c.writeto_mem(PCA9535_ADDR, 0x06, bytes([0xFF]))
        self._i2c.writeto_mem(PCA9535_ADDR, 0x07, bytes([0x00]))
    
    def read(self):
        return ~self._i2c.readfrom_mem(PCA9535_ADDR, 0x00, 1)[0] & 0x03

    def write(self, n):
        self._i2c.writeto_mem(PCA9535_ADDR, 0x03, bytes([0xFF & ~n]))


class _LedIter():
    def __init__(self, leds):
        self._index = 0
        self._leds = leds
        
    def on(self):
        self._leds[self._index-1] = True
    
    def off(self):
        self._leds[self._index-1] = False


class Buzzer:
    def __init__(self):
        self._pin = machine.Pin('P0', machine.Pin.OUT, value=0)

    def on(self):
        self._pin.value(1)

    def off(self):
        self._pin.value(0)

    def beep(self, delay, on=50, off=10):
        self.on()
        t_on = time.ticks_ms()
        t_off = 0
        
        while delay:               
            if t_on and time.ticks_diff(time.ticks_ms(), t_on) > on:        
                self.off()
                t_on = 0
                t_off = time.ticks_ms()
                
            if t_off and time.ticks_diff(time.ticks_ms(), t_off) > off:
                t_on = time.ticks_ms()
                t_off = 0
                            
                self.on()  
                delay -= 1
                    
        self.off()      


class Leds(_I2CtoGPIO):
    def __init__(self):
        super().__init__()
        self._stat = 0x00
        self._count = 8

    def __call__(self):
        return tuple([((self._stat >> i) & 0x1) == 1 for i in range(7+1)])
    
    def __getitem__(self, index):
        return ((self._stat >> index) & 0x01) == 1
    
    def __setitem__(self, index, value):
        if value:
            self._stat |= (1 << index)
        else:
            self._stat &= ~(1 << index)
        self.write(self._stat)

    def __iter__(self):
        self._led = _LedIter(self)
        return self
    
    def __next__(self):
        if self._led._index < self._count:
            self._led._index += 1
            return self._led
        else:
            raise StopIteration

    def write(self, n):
        self._stat = n
        super().write(self._stat)
        
    def clear(self):
        self._stat = 0x00
        self.write(self._stat)


class Buttons(_I2CtoGPIO):
    def __init__(self):
        super().__init__()

    def __getitem__(self, index):
        bits = self.read()
        return (bits & 0x01) if index == 0 else ((bits >> 1) & 0x01) if index == 1 else None
    
    def __call__(self):
        bits = self.read()        
        return bits & 0x01, (bits >> 1) & 0x01
