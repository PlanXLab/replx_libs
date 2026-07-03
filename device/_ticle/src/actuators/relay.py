# @package: relay
# @version: 1.0.0
# @type: device-specific
# @category: actuators
# @interface: GPIO
# @depends: none
# @platforms: rp2
# @tags: relay, safety, interlock, pio, watchdog, industrial
# @author: PlanXLab Development Team

# pyright: reportUndefinedVariable=false

import rp2
from rp2 import PIO, StateMachine
from machine import Pin, WDT
import time
from .utools import find_free_sm

@rp2.asm_pio(
    out_init=rp2.PIO.OUT_LOW,
    set_init=rp2.PIO.OUT_LOW,
    sideset_init=rp2.PIO.OUT_LOW,
)
def _relay_with_watchdog():
    wrap_target()
    
    pull(noblock)
    mov(x, osr)
    
    mov(y, x)
    jmp(not_y, "output_off")
    
    set(pins, 1)
    jmp("done")
    
    label("output_off")
    set(pins, 0)
    
    label("done")
    wrap()

@rp2.asm_pio(
    set_init=(rp2.PIO.OUT_LOW, rp2.PIO.OUT_LOW),
)
def _interlock_pair():
    wrap_target()
    
    pull(noblock)
    mov(x, osr)
    
    mov(y, x)
    set(pins, 0b00)
    
    jmp(not_y, "check_ch1")
    
    label("ch0_on")
    set(pins, 0b01)
    jmp("done")
    
    label("check_ch1")
    in_(x, 1)
    mov(y, isr)
    jmp(not_y, "done")
    set(pins, 0b10)
    
    label("done")
    wrap()

class Relay:
    ON = 1
    OFF = 0
    
    NORMALLY_OPEN = True
    NORMALLY_CLOSED = False

    def __init__(
        self,
        pins: int | list[int] | tuple[int, ...],
        *,
        contact_type: bool = NORMALLY_OPEN,
        interlock_pairs: list[tuple[int, int]] = None,
        feedback_pins: list[int] = None,
        watchdog_ms: int = 0
    ):
        if isinstance(pins, int):
            pins = [pins]
        
        if not pins:
            raise ValueError("At least one pin must be provided")
        
        self._pin_nums = list(pins)
        self._n = len(self._pin_nums)
        
        self._sm_ids = find_free_sm(self._n)
        
        self._contact_type = [contact_type] * self._n
        self._logical_state = [Relay.OFF] * self._n
        
        self._interlock_pairs = interlock_pairs or []
        self._interlock_map = {}
        for a, b in self._interlock_pairs:
            if not (0 <= a < self._n and 0 <= b < self._n):
                raise ValueError(f"Interlock pair ({a}, {b}) out of range")
            self._interlock_map[a] = b
            self._interlock_map[b] = a
        
        self._feedback_pins = None
        self._feedback_din = None
        if feedback_pins:
            self._feedback_pins = list(feedback_pins)
            self._feedback_din = [Pin(p, Pin.IN, Pin.PULL_DOWN) for p in self._feedback_pins]
        
        self._wdt = None
        self._watchdog_ms = watchdog_ms
        
        self._state_machines = []
        self._pins = []
        
        self._init_pio()
        
        self._view = Relay._View(self)

    def _init_pio(self):
        for i, pin_num in enumerate(self._pin_nums):
            pin = Pin(pin_num, Pin.OUT, value=0)
            self._pins.append(pin)
            
            sm_id = self._sm_ids[i]
            
            sm = StateMachine(
                sm_id,
                _relay_with_watchdog,
                freq=10000,
                set_base=pin,
            )
            sm.put(0)
            sm.active(1)
            self._state_machines.append(sm)

    def enable_watchdog(self, timeout_ms: int = None):
        if timeout_ms is not None:
            self._watchdog_ms = timeout_ms
        
        if self._watchdog_ms > 0:
            self._wdt = WDT(timeout=min(self._watchdog_ms, 8388))
        return self

    def feed(self):
        if self._wdt:
            self._wdt.feed()

    def deinit(self):
        try:
            for sm in self._state_machines:
                sm.put(0)
                time.sleep_ms(10)
                sm.active(0)
            
            for pin in self._pins:
                pin.init(Pin.IN)
            
            self._state_machines.clear()
            self._pins.clear()
        except:
            pass

    def __enter__(self) -> "Relay":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.deinit()

    def __getitem__(self, idx: int | slice) -> "_View":
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(self._n)))
            return self._view._set(indices)
        elif isinstance(idx, int):
            if not (0 <= idx < self._n):
                raise IndexError("Relay index out of range")
            return self._view._set([idx])
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        return self._n

    def _check_interlock(self, idx: int, new_state: int) -> bool:
        if new_state == Relay.ON and idx in self._interlock_map:
            partner = self._interlock_map[idx]
            if self._logical_state[partner] == Relay.ON:
                self._set_relay_hw(partner, Relay.OFF)
                self._logical_state[partner] = Relay.OFF
                time.sleep_us(100)
        return True

    def _set_relay_hw(self, idx: int, state: int):
        if self._contact_type[idx] == Relay.NORMALLY_OPEN:
            physical = state
        else:
            physical = 1 - state
        
        self._state_machines[idx].put(physical)

    def _set_relay_state(self, idx: int, state: int) -> bool:
        self._check_interlock(idx, state)
        self._logical_state[idx] = state
        self._set_relay_hw(idx, state)
        return True

    def verify_feedback(self, idx: int) -> bool | None:
        if self._feedback_din is None or idx >= len(self._feedback_din):
            return None
        
        expected = self._logical_state[idx]
        if self._contact_type[idx] == Relay.NORMALLY_CLOSED:
            expected = 1 - expected
        
        time.sleep_ms(20)
        actual = self._feedback_din[idx].value()
        return actual == expected

    def verify_all_feedback(self) -> list[bool | None]:
        return [self.verify_feedback(i) for i in range(self._n)]

    def all_off(self):
        for i in range(self._n):
            self._logical_state[i] = Relay.OFF
            self._set_relay_hw(i, Relay.OFF)

    def emergency_stop(self):
        for sm in self._state_machines:
            sm.put(0)
        
        for i in range(self._n):
            self._logical_state[i] = Relay.OFF

    class _View:
        __slots__ = ('_p', '_i')

        def __init__(self, parent: "Relay"):
            self._p = parent
            self._i = None
        
        def _set(self, indices: list[int]) -> "Relay._View":
            self._i = indices
            return self

        def __getitem__(self, idx: int | slice) -> "Relay._View":
            if isinstance(idx, slice):
                selected = [self._i[i] for i in range(*idx.indices(len(self._i)))]
                return self._set(selected)
            else:
                return self._set([self._i[idx]])

        def __len__(self) -> int:
            return len(self._i)

        @property
        def state(self) -> list[int]:
            return [self._p._logical_state[i] for i in self._i]

        @state.setter
        def state(self, value: int | list[int]):
            if isinstance(value, (list, tuple)):
                if len(value) != len(self._i):
                    raise ValueError("List length must match relay count")
                for i, s in zip(self._i, value):
                    self._p._set_relay_state(i, s)
            else:
                for i in self._i:
                    self._p._set_relay_state(i, value)

        @property
        def contact_type(self) -> list[bool]:
            return [self._p._contact_type[i] for i in self._i]

        @contact_type.setter
        def contact_type(self, ct: bool):
            for i in self._i:
                self._p._contact_type[i] = ct
                self._p._set_relay_hw(i, self._p._logical_state[i])

        @property
        def feedback(self) -> list[bool | None]:
            return [self._p.verify_feedback(i) for i in self._i]

        def toggle(self):
            for i in self._i:
                new_state = Relay.OFF if self._p._logical_state[i] == Relay.ON else Relay.ON
                self._p._set_relay_state(i, new_state)

        def pulse(self, duration_ms: int, state: int = 1):
            opposite = Relay.OFF if state == Relay.ON else Relay.ON
            self.state = state
            time.sleep_ms(duration_ms)
            self.state = opposite

        def all_off(self):
            for i in self._i:
                self._p._logical_state[i] = Relay.OFF
                self._p._set_relay_hw(i, Relay.OFF)

        def emergency_stop(self):
            for i in self._i:
                self._p._state_machines[i].put(0)
                self._p._logical_state[i] = Relay.OFF
