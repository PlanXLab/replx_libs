# @package: relay
# @version: 1.0.0
# @type: device-std
# @category: actuators
# @interface: GPIO
# @depends: dio
# @platforms: *
# @tags: relay, actuator, switch, gpio, interlock
# @author: PlanXLab Development Team

import time
from dio import Dout

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
        interlock_pairs: list[tuple[int, int]] | None = None
    ):
        if isinstance(pins, int):
            pins = [pins]
        
        if not pins:
            raise ValueError("At least one pin must be provided")
        
        self._pin_nums = list(pins)
        self._n = len(self._pin_nums)
        
        self._dout = Dout(self._pin_nums)
        
        self._contact_type = [contact_type] * self._n
        self._logical_state = [Relay.OFF] * self._n
        
        self._interlock_pairs = interlock_pairs or []
        self._interlock_map = {}
        for a, b in self._interlock_pairs:
            if not (0 <= a < self._n and 0 <= b < self._n):
                raise ValueError(f"Interlock pair ({a}, {b}) out of range")
            self._interlock_map[a] = b
            self._interlock_map[b] = a
        
        for i in range(self._n):
            self._set_relay_hw(i, Relay.OFF)
        
        self._view = Relay._View(self)

    def deinit(self):
        try:
            for i in range(self._n):
                self._set_relay_hw(i, Relay.OFF)
            self._dout.deinit()
        except Exception:
            pass

    def __enter__(self) -> "Relay":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.deinit()

    def __len__(self) -> int:
        return self._n

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
        
        self._dout.write(physical, idx=idx)

    def _set_relay_state(self, idx: int, state: int) -> bool:
        self._check_interlock(idx, state)
        self._logical_state[idx] = state
        self._set_relay_hw(idx, state)
        return True

    def all_off(self):
        for i in range(self._n):
            self._logical_state[i] = Relay.OFF
            self._set_relay_hw(i, Relay.OFF)

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
