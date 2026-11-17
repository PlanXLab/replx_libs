# @package: autoctrl
# @version: 1.3.0
# @type: device-specific
# @category: board
# @interface: GPIO, I2C
# @depends: xnode
# @platforms: xbee
# @tags: relay, pwm, fan, gas, door

import utime
import ustruct
import gc
import machine
from micropython import const
from xnode import Din, Dout, I2c

class Dio:
    LOW = const(0)
    HIGH = const(1)

    IN = machine.Pin.IN
    OUT = machine.Pin.OUT
    PULL_UP = machine.Pin.PULL_UP
    PULL_DOWN = machine.Pin.PULL_DOWN

    class Device:
        RELAY = const(0)
        PWM = const(1)

    P_RELAYS = {0: 'D0', 1: 'D6', 2: 'D5'}

    @staticmethod
    def Relays(value=LOW):
        return [Dout(Dio.P_RELAYS[i], value=value) for i in range(len(Dio.P_RELAYS))]

    @staticmethod
    def P18(*, active_low=True):
        return Din('D7', active_low=active_low)

    @staticmethod
    def P17(*, active_low=True):
        return Din('P2', active_low=active_low)

    @staticmethod
    def P8(mode, *, pull=None, value=LOW):
        if mode == Dio.IN:
            return machine.Pin('P0', mode, pull=pull)
        return machine.Pin('P0', mode, pull=pull, value=value)

    @staticmethod
    def P23(mode, *, pull=None, value=LOW):
        if mode == Dio.IN:
            return machine.Pin('D4', mode, pull=pull)
        return machine.Pin('D4', mode, pull=pull, value=value)

class DoorLock:
    def __init__(self, relay, *, feedback=None, active_low=True, pulse_ms=800):
        self._doorlock = relay
        self._feedback = feedback
        self._active_low = active_low
        self._pulse_ms = pulse_ms

    @property
    def has_feedback(self):
        return self._feedback is not None

    def is_opened(self):
        if self._feedback is None:
            raise RuntimeError("Feedback pin is not configured")
        current = self._feedback.raw_value() if hasattr(self._feedback, 'raw_value') else self._feedback.value()
        return (current == 0) if self._active_low else (current == 1)

    def open(self):
        if self._feedback is None:
            raise RuntimeError("Feedback pin is not configured")
        if not self.is_opened():
            self.work()
            return True
        return False

    def close(self):
        if self._feedback is None:
            raise RuntimeError("Feedback pin is not configured")
        if self.is_opened():
            self.work()
            return True
        return False

    def work(self, pulse_ms=None):
        ms = self._pulse_ms if pulse_ms is None else pulse_ms
        if hasattr(self._doorlock, 'on'):
            self._doorlock.on()
            utime.sleep_ms(ms)
            self._doorlock.off()
        else:
            self._doorlock.value(1)
            utime.sleep_ms(ms)
            self._doorlock.value(0)
        utime.sleep_ms(ms)

    trigger = work

class PCA9685:
    ADDR = const(0x40)

    def __init__(self, freq=100, addr=ADDR):
        self._i2c = I2c(addr)
        self._buf4 = bytearray(4)
        self._freq = 0

        self.reset()
        self._i2c.writeto_mem(0x26, ustruct.pack('<HH', 4096, 0))  # Enable A (ch 0, 1)
        self._i2c.writeto_mem(0x2A, ustruct.pack('<HH', 4096, 0))  # Enable B (ch 2, 3)
        self._i2c.writeto_mem(0x06, ustruct.pack('<HHHHHHHH', 0, 4096, 0, 4096, 0, 4096, 0, 4096))

        self.freq(freq)

    def reset(self):
        self._i2c.write_u8(0x00, 0x06)  # Mode 1, reset(0x06)
        utime.sleep_us(10)
        self._i2c.write_u8(0x00, 0xA0)  # Mode 1, restart(0x80) | auto increment(0x20)

    def sleep(self):
        old_mode = self._i2c.read_u8(0x00)
        self._i2c.write_u8(0x00, (old_mode & 0x7F) | 0x10)

    def wake(self):
        old_mode = self._i2c.read_u8(0x00)
        self._i2c.write_u8(0x00, old_mode & ~0x10)
        utime.sleep_us(500)
        if old_mode & 0x80:
            self._i2c.write_u8(0x00, (old_mode & ~0x10) | 0x80)

    def freq(self, freq=None):
        if freq is None:
            return self._freq
        self._freq = freq
        prescale = int(round(25000000.0 / (4096.0 * freq)) - 1)
        prescale = 3 if prescale < 3 else 255 if prescale > 255 else prescale
        old_mode = self._i2c.read_u8(0x00)
        self._i2c.write_u8(0x00, (old_mode & 0x7F) | 0x10)  # Sleep
        self._i2c.write_u8(0xFE, prescale)                  # Prescale
        self._i2c.write_u8(0x00, old_mode)                  # Restore
        utime.sleep_us(500)

    def pwm(self, ch, on=None, off=None):
        reg = 0x06 + (ch << 2)
        if on is None or off is None:
            self._i2c.readfrom_mem_into(reg, self._buf4)
            return ustruct.unpack('<HH', self._buf4)
        ustruct.pack_into('<HH', self._buf4, 0, on, off)
        self._i2c.writeto_mem(reg, self._buf4)

    def duty(self, ch, value):
        if value <= 0:
            self.pwm(ch, 0, 4096)
        elif value >= 100:
            self.pwm(ch, 4096, 0)
        else:
            self.pwm(ch, 0, int((value - 1) * 4094 / 98 + 1))

    def off_all(self):
        for ch in range(16):
            self.pwm(ch, 0, 4096)

Pwm = PCA9685

class GasDetector:
    def __init__(self, *, active_low=False):
        self._pin = Dio.P18(active_low=active_low)

    def read(self):
        return self._pin.value()

    def is_detected(self):
        return self._pin.value() == 1

class GasBreaker:
    STATE_UNKNOWN = const(-1)
    STATE_CLOSED = const(0)
    STATE_OPENED = const(1)
    STATE_STOPPED = const(2)

    def __init__(self, red, black, *, pwm=None):
        self._red = red
        self._black = black
        self._pwm = pwm if pwm is not None else PCA9685()
        self._state = self.STATE_UNKNOWN

    @property
    def state(self):
        return self._state

    def init(self):
        self.close(True)

    def open(self, duration_ms=None):
        self._pwm.duty(self._red, 100)
        self._pwm.duty(self._black, 0)
        self._state = self.STATE_OPENED
        if duration_ms is not None and duration_ms > 0:
            utime.sleep_ms(duration_ms)
            self.stop()

    def close(self, init=False, duration_ms=None):
        self._pwm.duty(self._red, 0)
        self._pwm.duty(self._black, 100)
        self._state = self.STATE_CLOSED
        if duration_ms is not None and duration_ms > 0:
            utime.sleep_ms(duration_ms)
            self.stop()

    def stop(self):
        self._pwm.duty(self._red, 0)
        self._pwm.duty(self._black, 0)
        if self._state == self.STATE_UNKNOWN:
            self._state = self.STATE_STOPPED

_FAN = const(0)
_LIGHT = const(1)

class _PwmActuator(PCA9685):
    _FAN_TBL = (0, 40, 55, 70, 85, 100)
    _LIGHT_TBL = (0, 2, 6, 20, 40, 100)
    _DUMMY_TBL = (0, 0, 0, 0, 0, 0)

    def __init__(self, act_id, ch, value=0):
        super().__init__()
        self._ch = ch
        self._levels = self._FAN_TBL if act_id == _FAN else self._LIGHT_TBL if act_id == _LIGHT else self._DUMMY_TBL
        self._pos = 0
        self._duty = 0
        if value:
            if 0 <= value <= 5:
                self.change(value)
            else:
                self.duty(value)

    def on(self):
        self._pos = 5
        self._duty = self._levels[5]
        super().duty(self._ch, self._duty)

    def off(self):
        self._pos = 0
        self._duty = self._levels[0]
        super().duty(self._ch, self._duty)

    def toggle(self):
        if self._duty > 0 or self._pos > 0:
            self.off()
        else:
            self.on()

    def change(self, level):
        if not (0 <= level < len(self._levels)):
            raise ValueError("level must be between 0 and 5")
        self._pos = level
        self._duty = self._levels[level]
        super().duty(self._ch, self._duty)

    set_level = change

    @property
    def level(self):
        return self._pos

    @level.setter
    def level(self, val):
        self.change(val)

    def duty(self, value=None, ch=None):
        if value is None:
            return self._duty
        target_ch = self._ch if ch is None else ch
        self._duty = 0 if value < 0 else 100 if value > 100 else value
        super().duty(target_ch, self._duty)

    def value(self, n=None):
        if n is None:
            return 1 if self._duty > 0 else 0
        if n:
            self.on()
        else:
            self.off()

    def state(self):
        return self._pos

def _FanLight(act_id, dev_type, ch, value=0):
    if dev_type == Dio.Device.RELAY:
        return Dout(Dio.P_RELAYS[ch], value=value)
    elif dev_type == Dio.Device.PWM:
        return _PwmActuator(act_id, ch, value)
    raise ValueError("Invalid device type")

def Fan(device_type, ch, value=0):
    return _FanLight(_FAN, device_type, ch, value)

def Light(device_type, ch, value=0):
    return _FanLight(_LIGHT, device_type, ch, value)

gc.collect()
