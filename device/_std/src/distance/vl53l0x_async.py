# @package: vl53l0x_async
# @version: 1.1.0
# @type: device-std
# @category: distance
# @sensor_type: A
# @interface: I2C
# @depends: vl53l0x
# @platforms: *
# @tags: tof, lidar, distance, laser, vl53l0x, ranging, async, asyncio
# @author: PlanXLab Development Team

import asyncio
from .vl53l0x import VL53L0X


class _StreamIter:
    def __init__(self, parent, count, interval_ms):
        self._p = parent
        self._count = count
        self._interval_ms = interval_ms
        self._n = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._count is not None and self._n >= self._count:
            raise StopAsyncIteration
        val = await self._p.read()
        self._n += 1
        if self._interval_ms > 0:
            await asyncio.sleep_ms(self._interval_ms)
        return val


class VL53L0XAsync:
    def __init__(self, device: VL53L0X, poll_ms: int = 10):
        self._dev = device
        self._poll_ms = poll_ms

    @property
    def device(self) -> VL53L0X:
        return self._dev

    @property
    def last(self) -> float:
        return self._dev.last

    async def read(self, timeout_ms: int | None = None) -> float:
        if timeout_ms is None:
            timeout_ms = self._dev._timeout_ms

        elapsed = 0
        while not self._dev.ready():
            if elapsed >= timeout_ms:
                return self._dev.last
            await asyncio.sleep_ms(self._poll_ms)
            elapsed += self._poll_ms

        val = self._dev.result()
        return val if val is not None else self._dev.last

    def stream(self, count: int | None = None, interval_ms: int = 0) -> "_StreamIter":
        return _StreamIter(self, count, interval_ms)

    def __aiter__(self):
        return _StreamIter(self, None, 0)

    async def __anext__(self) -> float:
        return await self.read()
