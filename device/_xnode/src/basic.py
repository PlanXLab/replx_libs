# @package: basic
# @version: 1.3.0
# @type: device-specific
# @category: board
# @interface: GPIO, I2C
# @depends: none
# @platforms: xbee
# @tags: buzzer, led, button, actuator

import utime
import gc
import machine
from micropython import const

PCA9535_ADDR = const(0x24)

class _I2CtoGPIO:
    def __init__(self):
        self._i2c = machine.I2C(1)
        self._buf1 = bytearray(1)
        self._write_reg(0x06, 0xFF)
        self._write_reg(0x07, 0x00)

    def _write_reg(self, reg, val):
        self._buf1[0] = val & 0xFF
        self._i2c.writeto_mem(PCA9535_ADDR, reg, self._buf1)

    def read(self):
        self._i2c.readfrom_mem_into(PCA9535_ADDR, 0x00, self._buf1)
        return (~self._buf1[0]) & 0x03

    def write(self, n):
        self._write_reg(0x03, 0xFF & ~n)

class _LedProxy:
    def __init__(self, leds, index=0):
        self._leds = leds
        self._index = index

    def on(self):
        self._leds[self._index] = True

    def off(self):
        self._leds[self._index] = False

    def toggle(self):
        self._leds.toggle(self._index)

    def value(self, val=None):
        if val is None:
            return 1 if self._leds[self._index] else 0
        self._leds[self._index] = bool(val)

_LedIter = _LedProxy

class Buzzer:
    def __init__(self):
        self._pin = machine.Pin('P0', machine.Pin.OUT, value=0)

    def on(self):
        self._pin.value(1)

    def off(self):
        self._pin.value(0)

    def toggle(self):
        self._pin.toggle()

    def value(self, n=None):
        if n is None:
            return self._pin.value()
        self._pin.value(1 if n else 0)

    def beep(self, count=1, on_ms=50, off_ms=10, *, on=None, off=None):
        if on is not None:
            on_ms = on
        if off is not None:
            off_ms = off
        if count <= 0:
            self.off()
            return
        self.on()
        t_on = utime.ticks_ms()
        t_off = 0

        while count > 0:
            now = utime.ticks_ms()
            if t_on and utime.ticks_diff(now, t_on) >= on_ms:
                self.off()
                t_on = 0
                t_off = now
                count -= 1
                if count <= 0:
                    break
            elif t_off and utime.ticks_diff(now, t_off) >= off_ms:
                self.on()
                t_on = now
                t_off = 0
            utime.sleep_ms(1)

        self.off()

class Leds(_I2CtoGPIO):
    def __init__(self):
        super().__init__()
        self._stat = 0x00
        self._count = 8
        self._iter_idx = 0
        self._proxy = _LedProxy(self, 0)

    def __len__(self):
        return self._count

    def __call__(self):
        s = self._stat
        return tuple(((s >> i) & 0x01) == 1 for i in range(8))

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self[i] for i in range(*index.indices(self._count)))
        if index < 0:
            index += self._count
        if not (0 <= index < self._count):
            raise IndexError("LED index out of range")
        return ((self._stat >> index) & 0x01) == 1

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            indices = range(*index.indices(self._count))
            if isinstance(value, (tuple, list)):
                for i, v in zip(indices, value):
                    if v:
                        self._stat |= (1 << i)
                    else:
                        self._stat &= ~(1 << i)
            else:
                for i in indices:
                    if value:
                        self._stat |= (1 << i)
                    else:
                        self._stat &= ~(1 << i)
            self.write(self._stat)
            return
        if index < 0:
            index += self._count
        if not (0 <= index < self._count):
            raise IndexError("LED index out of range")
        if value:
            self._stat |= (1 << index)
        else:
            self._stat &= ~(1 << index)
        self.write(self._stat)

    def __iter__(self):
        self._iter_idx = 0
        return self

    def __next__(self):
        if self._iter_idx < self._count:
            self._proxy._index = self._iter_idx
            self._iter_idx += 1
            return self._proxy
        raise StopIteration

    @property
    def value(self):
        return self._stat

    @value.setter
    def value(self, n):
        self.write(n)

    def write(self, n):
        self._stat = n & 0xFF
        super().write(self._stat)

    def on(self, index=None):
        if index is None:
            self.write(0xFF)
        else:
            self[index] = True

    def off(self, index=None):
        if index is None:
            self.write(0x00)
        else:
            self[index] = False

    def toggle(self, index=None):
        if index is None:
            self.write((~self._stat) & 0xFF)
        else:
            if index < 0:
                index += self._count
            if not (0 <= index < self._count):
                raise IndexError("LED index out of range")
            self.write(self._stat ^ (1 << index))

    def clear(self):
        self.write(0x00)

    def fill(self, value=True):
        self.write(0xFF if value else 0x00)

class Buttons(_I2CtoGPIO):
    def __init__(self):
        super().__init__()
        self._count = 2

    def __len__(self):
        return self._count

    def __getitem__(self, index):
        if index < 0:
            index += self._count
        if not (0 <= index < self._count):
            raise IndexError("Button index out of range (0 or 1)")
        bits = self.read()
        return (bits >> index) & 0x01

    def __call__(self):
        bits = self.read()
        return bits & 0x01, (bits >> 1) & 0x01

    def is_pressed(self, index):
        return self[index] == 1

    def any_pressed(self):
        return self.read() != 0

gc.collect()
