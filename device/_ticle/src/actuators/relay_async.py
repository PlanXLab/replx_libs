# @package: relay_async
# @version: 1.0.0
# @type: device-specific
# @category: actuators
# @interface: GPIO
# @depends: relay
# @platforms: rp2
# @tags: relay, actuator, async, asyncio, pio
# @author: PlanXLab Development Team

import asyncio
from .relay import Relay


class RelayAsync:
    __slots__ = ('_relay', '_view')

    def __init__(self, relay: Relay):
        self._relay = relay
        self._view = RelayAsync._View(self)

    def __len__(self) -> int:
        return len(self._relay)

    def __getitem__(self, idx: int | slice) -> "_View":
        relay_view = self._relay[idx]
        return self._view._set(relay_view._i)

    @property
    def relay(self) -> Relay:
        return self._relay

    def all_off(self):
        self._relay.all_off()

    def emergency_stop(self):
        self._relay.emergency_stop()

    class _View:
        __slots__ = ('_p', '_i', '_rv')

        def __init__(self, parent: "RelayAsync"):
            self._p = parent
            self._i = None
            self._rv = None

        def _set(self, indices: list[int]) -> "RelayAsync._View":
            self._i = indices
            self._rv = self._p._relay._view._set(indices)
            return self

        def __getitem__(self, idx: int | slice) -> "RelayAsync._View":
            sub_view = self._rv[idx]
            return self._set(sub_view._i)

        def __len__(self) -> int:
            return len(self._i)

        @property
        def state(self) -> list[int]:
            return self._rv.state

        @state.setter
        def state(self, value: int | list[int]):
            self._rv.state = value

        @property
        def contact_type(self) -> list[bool]:
            return self._rv.contact_type

        @contact_type.setter
        def contact_type(self, ct: bool):
            self._rv.contact_type = ct

        @property
        def feedback(self) -> list[bool | None]:
            return self._rv.feedback

        def toggle(self):
            self._rv.toggle()

        async def pulse(self, duration_ms: int, state: int = Relay.ON):
            opposite = Relay.OFF if state == Relay.ON else Relay.ON
            self._rv.state = state
            await asyncio.sleep_ms(duration_ms)
            self._rv.state = opposite

        def all_off(self):
            self._rv.all_off()

        def emergency_stop(self):
            self._rv.emergency_stop()
