# @package: dio
# @version: 2.1
# @type: core
# @category: peripheral
# @interface: GPIO
# @depends: none
# @platforms: *
# @tags: gpio, digital, input, output, dio, irq
# @author: PlanXLab Development Team

import machine
import time
from micropython import const, schedule

LOW = const(0)
HIGH = const(1)
_QSIZE = const(8)


def _as_pins(pins):
    if isinstance(pins, int):
        pins = (pins,)
    if not pins:
        raise ValueError("pins must not be empty")
    return tuple(pins)


def _clamp_bit(value):
    return 1 if value else 0


def _is_seq(value):
    return not isinstance(value, (int, bool)) and hasattr(value, "__len__")


class Din:
    PULL_DOWN = machine.Pin.PULL_DOWN
    PULL_UP = machine.Pin.PULL_UP
    OPEN_DRAIN = machine.Pin.OPEN_DRAIN
    CB_FALLING = machine.Pin.IRQ_FALLING
    CB_RISING = machine.Pin.IRQ_RISING
    CB_BOTH = machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING

    def __init__(self, pins, *, pull=None):
        self._pin_nums = _as_pins(pins)
        self._pins = [machine.Pin(pin, machine.Pin.IN, pull=pull)
                      for pin in self._pin_nums]
        n = len(self._pins)
        self._pull = [pull] * n
        self._debounce_us = [0] * n
        self._irq = [None] * n
        self._callback = [None] * n
        self._last_us = [0] * n
        self._pulse_start = [0] * n
        self._pulse_end = [0] * n
        self._pulse_ready = [False] * n
        self._pulse_irq = [None] * n
        self._view = Din._View(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def __len__(self):
        return len(self._pins)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return self._view._set(tuple(range(*idx.indices(len(self)))))
        if idx < 0:
            idx += len(self)
        if not 0 <= idx < len(self):
            raise IndexError("pin index out of range")
        return self._view._set((idx,))

    @property
    def pins(self):
        return self._pins

    def deinit(self):
        for i, pin in enumerate(self._pins):
            try:
                pin.irq(handler=None)
            except Exception:
                pass
            self._irq[i] = None
            self._callback[i] = None
            self._pulse_irq[i] = None

    def read(self, idx=0):
        return self._pins[idx].value()

    def read_into(self, buf):
        pins = self._pins
        for i in range(len(pins)):
            buf[i] = pins[i].value()
        return buf

    def set_pull(self, idx, pull):
        self._pull[idx] = pull
        self._pins[idx].init(mode=machine.Pin.IN, pull=pull)

    def set_pull_all(self, pull):
        for i in range(len(self._pins)):
            self.set_pull(i, pull)

    def set_debounce_us(self, idx, us):
        self._debounce_us[idx] = int(us)

    def set_debounce_all(self, us):
        us = int(us)
        for i in range(len(self._pins)):
            self._debounce_us[i] = us

    def irq(self, idx, callback=None, *, trigger=CB_BOTH,
            debounce_us=0, hard=True):
        pin = self._pins[idx]
        pin.irq(handler=None)
        self._callback[idx] = callback
        self._irq[idx] = None
        self._debounce_us[idx] = int(debounce_us)
        if callback is None or trigger == 0:
            return

        levels = [0] * _QSIZE
        state = [0, 0, 0]  # head, tail, scheduled
        pin_num = self._pin_nums[idx]

        def _run(_):
            while state[1] != state[0]:
                tail = state[1]
                value = levels[tail]
                state[1] = (tail + 1) % _QSIZE
                cb = self._callback[idx]
                if cb is not None:
                    try:
                        cb(pin_num, value)
                    except Exception:
                        pass
            state[2] = 0
            if state[1] != state[0]:
                _post()

        def _post():
            if state[2]:
                return
            state[2] = 1
            schedule(_run, 0)

        def _handler(pin_obj):
            now = time.ticks_us()
            debounce = self._debounce_us[idx]
            if debounce and time.ticks_diff(now, self._last_us[idx]) < debounce:
                return
            self._last_us[idx] = now

            head = state[0]
            nxt = (head + 1) % _QSIZE
            if nxt == state[1]:
                state[1] = (state[1] + 1) % _QSIZE
            levels[head] = pin_obj.value()
            state[0] = nxt
            _post()

        self._irq[idx] = _handler
        try:
            pin.irq(trigger=trigger, handler=_handler, hard=hard)
        except TypeError:
            pin.irq(trigger=trigger, handler=_handler)

    def measure_pulse_width(self, idx=0, level=1, timeout_us=1000000):
        return machine.time_pulse_us(self._pins[idx], level, timeout_us)

    def start_pulse_capture(self, idx=0, level=1):
        pin = self._pins[idx]
        pin.irq(handler=None)
        self._pulse_start[idx] = 0
        self._pulse_end[idx] = 0
        self._pulse_ready[idx] = False
        target = 1 if level else 0

        def _handler(pin_obj):
            t = time.ticks_us()
            if pin_obj.value() == target:
                self._pulse_start[idx] = t
            elif self._pulse_start[idx]:
                self._pulse_end[idx] = t
                self._pulse_ready[idx] = True

        self._pulse_irq[idx] = _handler
        pin.irq(trigger=Din.CB_BOTH, handler=_handler, hard=True)

    def stop_pulse_capture(self, idx=0):
        self._pins[idx].irq(handler=None)
        self._pulse_irq[idx] = None

    def pulse_ready(self, idx=0):
        return self._pulse_ready[idx]

    def pulse_width_us(self, idx=0):
        if not self._pulse_ready[idx]:
            return -1
        return time.ticks_diff(self._pulse_end[idx], self._pulse_start[idx])

    def wait_pulse_ready(self, idx=0, timeout_ms=50):
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while not self._pulse_ready[idx]:
            if time.ticks_diff(time.ticks_ms(), deadline) >= 0:
                return False
        return True

    def wait_for_value(self, idx=0, target=1, timeout_ms=0):
        pin = self._pins[idx]
        if timeout_ms <= 0:
            while pin.value() != target:
                pass
            return True
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while pin.value() != target:
            if time.ticks_diff(time.ticks_ms(), deadline) >= 0:
                return False
        return True

    def wait_for_edge(self, idx=0, edge=CB_BOTH, timeout_ms=0):
        pin = self._pins[idx]
        last = pin.value()
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while True:
            cur = pin.value()
            if cur != last:
                if edge == Din.CB_BOTH:
                    return True
                if edge == Din.CB_RISING and last == 0 and cur == 1:
                    return True
                if edge == Din.CB_FALLING and last == 1 and cur == 0:
                    return True
                last = cur
            if timeout_ms > 0 and time.ticks_diff(time.ticks_ms(), deadline) >= 0:
                return False

    class _View:
        __slots__ = ("_p", "_i", "_cache")

        def __init__(self, parent):
            self._p = parent
            self._i = ()
            self._cache = []

        def _set(self, indices):
            self._i = indices
            return self

        def _buf(self):
            n = len(self._i)
            buf = self._cache
            if len(buf) != n:
                if len(buf) < n:
                    buf.extend([0] * (n - len(buf)))
                else:
                    del buf[n:]
            return buf

        def __len__(self):
            return len(self._i)

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                return self._set(tuple(self._i[j] for j in range(*idx.indices(len(self._i)))))
            return self._set((self._i[idx],))

        def _single(self):
            if len(self._i) != 1:
                raise ValueError("operation requires a single pin")
            return self._i[0]

        def read(self):
            return self._p.read(self._single())

        def read_into(self, buf):
            for out_i, pin_i in enumerate(self._i):
                buf[out_i] = self._p.read(pin_i)
            return buf

        @property
        def value(self):
            return self.read_into(self._buf())

        @property
        def pull(self):
            buf = self._buf()
            pull = self._p._pull
            for out_i, pin_i in enumerate(self._i):
                buf[out_i] = pull[pin_i]
            return buf

        @pull.setter
        def pull(self, value):
            self.set_pull(value)

        @property
        def debounce_us(self):
            buf = self._buf()
            debounce = self._p._debounce_us
            for out_i, pin_i in enumerate(self._i):
                buf[out_i] = debounce[pin_i]
            return buf

        @debounce_us.setter
        def debounce_us(self, us):
            self.set_debounce_us(us)

        @property
        def callback(self):
            buf = self._buf()
            callbacks = self._p._callback
            for out_i, pin_i in enumerate(self._i):
                buf[out_i] = callbacks[pin_i]
            return buf

        @callback.setter
        def callback(self, fn):
            self.irq(fn)

        def set_pull(self, pull):
            for i in self._i:
                self._p.set_pull(i, pull)

        def set_debounce_us(self, us):
            for i in self._i:
                self._p.set_debounce_us(i, us)

        def irq(self, callback=None, *, trigger=None,
                debounce_us=0, hard=True):
            if trigger is None:
                trigger = machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING
            for i in self._i:
                self._p.irq(i, callback, trigger=trigger,
                            debounce_us=debounce_us, hard=hard)

        def start_pulse_capture(self, level=1):
            self._p.start_pulse_capture(self._single(), level)

        def stop_pulse_capture(self):
            self._p.stop_pulse_capture(self._single())

        def pulse_ready(self):
            return self._p.pulse_ready(self._single())

        def pulse_width_us(self):
            return self._p.pulse_width_us(self._single())

        def wait_pulse_ready(self, timeout_ms=50):
            return self._p.wait_pulse_ready(self._single(), timeout_ms)


class Dout:
    LOGIC_HIGH = True
    LOGIC_LOW = False
    PULL_DOWN = machine.Pin.PULL_DOWN
    PULL_UP = machine.Pin.PULL_UP
    OPEN_DRAIN = machine.Pin.OPEN_DRAIN

    def __init__(self, pins, *, value=0, active_high=True,
                 mode=machine.Pin.OUT):
        self._pin_nums = _as_pins(pins)
        self._active = [bool(active_high)] * len(self._pin_nums)
        phys = _clamp_bit(value) if bool(active_high) else 1 - _clamp_bit(value)
        self._pins = [machine.Pin(pin, mode, value=phys)
                      for pin in self._pin_nums]
        self._view = Dout._View(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def __len__(self):
        return len(self._pins)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return self._view._set(tuple(range(*idx.indices(len(self)))))
        if idx < 0:
            idx += len(self)
        if not 0 <= idx < len(self):
            raise IndexError("pin index out of range")
        return self._view._set((idx,))

    @property
    def pins(self):
        return self._pins

    def deinit(self):
        for pin in self._pins:
            try:
                pin.value(0)
                pin.init(mode=machine.Pin.IN, pull=machine.Pin.PULL_DOWN)
            except Exception:
                pass

    def _physical(self, idx, value):
        return _clamp_bit(value) if self._active[idx] else 1 - _clamp_bit(value)

    def write(self, value=1, idx=0):
        self._pins[idx].value(self._physical(idx, value))

    def read(self, idx=0):
        value = self._pins[idx].value()
        return value if self._active[idx] else 1 - value

    def read_physical(self, idx=0):
        return self._pins[idx].value()

    def write_all(self, value):
        for i in range(len(self._pins)):
            self.write(value, idx=i)

    def read_into(self, buf):
        for i in range(len(self._pins)):
            buf[i] = self.read(i)
        return buf

    def set_active(self, idx, active_high=True):
        old = self.read(idx)
        self._active[idx] = bool(active_high)
        self.write(old, idx=idx)

    def toggle(self, idx=0):
        self.write(1 - self.read(idx), idx=idx)

    def pulse(self, value=1, *, idx=0, duration_us=10):
        self.write(value, idx=idx)
        time.sleep_us(duration_us)
        self.write(1 - _clamp_bit(value), idx=idx)

    class _View:
        __slots__ = ("_p", "_i", "_cache")

        def __init__(self, parent):
            self._p = parent
            self._i = ()
            self._cache = []

        def _set(self, indices):
            self._i = indices
            return self

        def _buf(self):
            n = len(self._i)
            buf = self._cache
            if len(buf) != n:
                if len(buf) < n:
                    buf.extend([0] * (n - len(buf)))
                else:
                    del buf[n:]
            return buf

        def __len__(self):
            return len(self._i)

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                return self._set(tuple(self._i[j] for j in range(*idx.indices(len(self._i)))))
            return self._set((self._i[idx],))

        def _single(self):
            if len(self._i) != 1:
                raise ValueError("operation requires a single pin")
            return self._i[0]

        def write(self, value):
            for i in self._i:
                self._p.write(value, idx=i)

        def read(self):
            return self._p.read(self._single())

        def read_into(self, buf):
            for out_i, pin_i in enumerate(self._i):
                buf[out_i] = self._p.read(pin_i)
            return buf

        @property
        def value(self):
            return self.read_into(self._buf())

        @value.setter
        def value(self, val):
            if _is_seq(val):
                if len(val) != len(self._i):
                    raise ValueError("value length must match pin count")
                for pin_i, v in zip(self._i, val):
                    self._p.write(v, idx=pin_i)
            else:
                self.write(val)

        @property
        def physical_value(self):
            buf = self._buf()
            for out_i, pin_i in enumerate(self._i):
                buf[out_i] = self._p.read_physical(pin_i)
            return buf

        @property
        def active(self):
            buf = self._buf()
            active = self._p._active
            for out_i, pin_i in enumerate(self._i):
                buf[out_i] = active[pin_i]
            return buf

        @active.setter
        def active(self, value):
            if _is_seq(value):
                if len(value) != len(self._i):
                    raise ValueError("active length must match pin count")
                for pin_i, v in zip(self._i, value):
                    self._p.set_active(pin_i, v)
            else:
                for pin_i in self._i:
                    self._p.set_active(pin_i, value)

        def toggle(self):
            for i in self._i:
                self._p.toggle(i)

        def pulse(self, value=1, duration_us=10):
            for i in self._i:
                self._p.pulse(value, idx=i, duration_us=duration_us)


class Dio:
    MODE_IN = const(0)
    MODE_OUT = const(1)
    MODE_OPEN_DRAIN = const(2)
    PULL_DOWN = machine.Pin.PULL_DOWN
    PULL_UP = machine.Pin.PULL_UP
    OPEN_DRAIN = machine.Pin.OPEN_DRAIN
    CB_FALLING = machine.Pin.IRQ_FALLING
    CB_RISING = machine.Pin.IRQ_RISING
    CB_BOTH = machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING

    def __init__(self, pins, *, mode=MODE_IN, pull=None, value=0):
        self._pin_nums = _as_pins(pins)
        n = len(self._pin_nums)
        self._pins = [machine.Pin(pin, machine.Pin.IN) for pin in self._pin_nums]
        self._mode = [Dio.MODE_IN] * n
        self._pull = [pull] * n
        self._debounce_us = [0] * n
        self._irq = [None] * n
        self._callback = [None] * n
        self._last_us = [0] * n
        self._view = Dio._View(self)
        for i in range(n):
            self.set_mode(i, mode, pull=pull)
            if mode != Dio.MODE_IN:
                self.write(value, idx=i)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def __len__(self):
        return len(self._pins)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return self._view._set(tuple(range(*idx.indices(len(self)))))
        if idx < 0:
            idx += len(self)
        if not 0 <= idx < len(self):
            raise IndexError("pin index out of range")
        return self._view._set((idx,))

    def deinit(self):
        for i, pin in enumerate(self._pins):
            try:
                pin.irq(handler=None)
            except Exception:
                pass
            self._irq[i] = None
            self._callback[i] = None
            try:
                pin.init(mode=machine.Pin.IN, pull=machine.Pin.PULL_DOWN)
            except Exception:
                pass

    def set_mode(self, idx=0, mode=MODE_IN, *, pull=None):
        self._mode[idx] = mode
        self._pull[idx] = pull
        pin = self._pins[idx]
        if mode == Dio.MODE_IN:
            pin.init(machine.Pin.IN, pull=pull)
        elif mode == Dio.MODE_OUT:
            pin.init(machine.Pin.OUT)
        elif mode == Dio.MODE_OPEN_DRAIN:
            pin.init(machine.Pin.OPEN_DRAIN, pull=pull)
        else:
            raise ValueError("invalid mode")

    def read(self, idx=0):
        return self._pins[idx].value()

    def write(self, value=1, idx=0):
        if self._mode[idx] != Dio.MODE_IN:
            self._pins[idx].value(_clamp_bit(value))

    def toggle(self, idx=0):
        if self._mode[idx] != Dio.MODE_IN:
            self._pins[idx].value(1 - self._pins[idx].value())

    def irq(self, idx, callback=None, *, trigger=CB_BOTH,
            debounce_us=0, hard=True):
        if self._mode[idx] != Dio.MODE_IN:
            return
        pin = self._pins[idx]
        pin.irq(handler=None)
        self._callback[idx] = callback
        self._irq[idx] = None
        self._debounce_us[idx] = int(debounce_us)
        if callback is None or trigger == 0:
            return

        levels = [0] * _QSIZE
        state = [0, 0, 0]  # head, tail, scheduled
        pin_num = self._pin_nums[idx]

        def _run(_):
            while state[1] != state[0]:
                tail = state[1]
                value = levels[tail]
                state[1] = (tail + 1) % _QSIZE
                cb = self._callback[idx]
                if cb is not None:
                    try:
                        cb(pin_num, value)
                    except Exception:
                        pass
            state[2] = 0
            if state[1] != state[0]:
                _post()

        def _post():
            if state[2]:
                return
            state[2] = 1
            schedule(_run, 0)

        def _handler(pin_obj):
            now = time.ticks_us()
            debounce = self._debounce_us[idx]
            if debounce and time.ticks_diff(now, self._last_us[idx]) < debounce:
                return
            self._last_us[idx] = now
            head = state[0]
            nxt = (head + 1) % _QSIZE
            if nxt == state[1]:
                state[1] = (state[1] + 1) % _QSIZE
            levels[head] = pin_obj.value()
            state[0] = nxt
            _post()

        self._irq[idx] = _handler
        try:
            pin.irq(trigger=trigger, handler=_handler, hard=hard)
        except TypeError:
            pin.irq(trigger=trigger, handler=_handler)

    class _View:
        __slots__ = ("_p", "_i", "_cache")

        def __init__(self, parent):
            self._p = parent
            self._i = ()
            self._cache = []

        def _set(self, indices):
            self._i = indices
            return self

        def _buf(self):
            n = len(self._i)
            buf = self._cache
            if len(buf) != n:
                if len(buf) < n:
                    buf.extend([0] * (n - len(buf)))
                else:
                    del buf[n:]
            return buf

        def __len__(self):
            return len(self._i)

        def __getitem__(self, idx):
            if isinstance(idx, slice):
                return self._set(tuple(self._i[j] for j in range(*idx.indices(len(self._i)))))
            return self._set((self._i[idx],))

        def _single(self):
            if len(self._i) != 1:
                raise ValueError("operation requires a single pin")
            return self._i[0]

        def read(self):
            return self._p.read(self._single())

        def write(self, value):
            for i in self._i:
                self._p.write(value, idx=i)

        @property
        def value(self):
            buf = self._buf()
            for out_i, pin_i in enumerate(self._i):
                buf[out_i] = self._p.read(pin_i)
            return buf

        @value.setter
        def value(self, val):
            if _is_seq(val):
                if len(val) != len(self._i):
                    raise ValueError("value length must match pin count")
                for pin_i, v in zip(self._i, val):
                    self._p.write(v, idx=pin_i)
            else:
                self.write(val)

        @property
        def mode(self):
            buf = self._buf()
            mode = self._p._mode
            for out_i, pin_i in enumerate(self._i):
                buf[out_i] = mode[pin_i]
            return buf

        @mode.setter
        def mode(self, value):
            if _is_seq(value):
                if len(value) != len(self._i):
                    raise ValueError("mode length must match pin count")
                for pin_i, v in zip(self._i, value):
                    self._p.set_mode(pin_i, v, pull=self._p._pull[pin_i])
            else:
                for pin_i in self._i:
                    self._p.set_mode(pin_i, value, pull=self._p._pull[pin_i])

        def toggle(self):
            for i in self._i:
                self._p.toggle(i)
