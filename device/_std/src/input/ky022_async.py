# @package: ky022_async
# @version: 1.1.0
# @type: device-std
# @category: input
# @sensor_type: C
# @interface: GPIO (IRQ)
# @depends: ky022, asyncio
# @platforms: *
# @tags: ir, infrared, remote, receiver, async
# @author: PlanXLab Development Team

import asyncio
import time
from .ky022 import KY022


class _EventsIter:
    def __init__(self, dev, poll_ms):
        self._dev = dev
        self._poll_ms = poll_ms

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            evt = self._dev.get(block=False)
            if evt is not None:
                return evt
            await asyncio.sleep_ms(self._poll_ms)


class KY022Async:

    def __init__(self, device: KY022):
        self._dev = device

    async def get(self, timeout_ms: int = 1000):
        deadline = time.ticks_add(time.ticks_ms(), int(timeout_ms))
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            evt = self._dev.get(block=False)
            if evt is not None:
                return evt
            await asyncio.sleep_ms(1)
        return None

    def events(self, poll_ms: int = 10) -> "_EventsIter":
        return _EventsIter(self._dev, poll_ms)
