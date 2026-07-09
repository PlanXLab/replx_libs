# @package: us_async
# @version: 1.0
# @type: device-specific
# @category: distance
# @sensor_type: B
# @interface: GPIO
# @depends: us
# @platforms: rp2
# @tags: ultrasonic, distance, sr04, pio, async, asyncio, multi-sensor
# @author: PlanXLab Development Team

import asyncio
import time
from .us import SR04


class _ViewStreamIter:
    def __init__(self, view, count, interval_ms):
        self._v = view
        self._count = count
        self._interval_ms = interval_ms
        self._n = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._count is not None and self._n >= self._count:
            raise StopAsyncIteration
        val = await self._v.read()
        self._n += 1
        if self._interval_ms > 0:
            await asyncio.sleep_ms(self._interval_ms)
        return val


class _SR04StreamIter:
    def __init__(self, view_iter):
        self._vi = view_iter

    def __aiter__(self):
        return self

    async def __anext__(self):
        val = await self._vi.__anext__()
        return val[0] if isinstance(val, list) else val


class SR04Async:
    def __init__(self, device: SR04, poll_ms: int = 1):
        self._dev = device
        self._poll_ms = poll_ms
        self._view = SR04Async._View(self)

    @property
    def device(self) -> SR04:
        return self._dev

    def __len__(self) -> int:
        return len(self._dev)

    def __getitem__(self, idx: int | slice) -> "_View":
        if isinstance(idx, slice):
            indices = list(range(*idx.indices(len(self._dev))))
            return self._view._set(indices)
        elif isinstance(idx, int):
            if not (0 <= idx < len(self._dev)):
                raise IndexError("Sensor index out of range")
            return self._view._set([idx])
        else:
            raise TypeError("Index must be int or slice")

    @property
    def last(self) -> float:
        return self._dev.last

    def trigger(self) -> None:
        self._dev.trigger()

    async def result(self, timeout_ms: int = 50) -> float:
        results = await self._view._set([0]).result(timeout_ms)
        return results[0]

    async def read(self, timeout_ms: int = 50) -> float:
        results = await self._view._set([0]).read(timeout_ms)
        return results[0]

    def stream(self, count: int | None = None, interval_ms: int = 100) -> "_SR04StreamIter":
        return _SR04StreamIter(_ViewStreamIter(self._view._set([0]), count, interval_ms))

    def __aiter__(self):
        return _SR04StreamIter(_ViewStreamIter(self._view._set([0]), None, 100))

    async def __anext__(self) -> float:
        return await self.read()

    def deinit(self):
        self._dev.deinit()

    class _View:
        __slots__ = ('_p', '_i')

        def __init__(self, parent: "SR04Async"):
            self._p = parent
            self._i = None

        def _set(self, indices: list[int]) -> "SR04Async._View":
            self._i = indices
            return self

        def __len__(self) -> int:
            return len(self._i)

        def __getitem__(self, idx: int | slice) -> "SR04Async._View":
            if isinstance(idx, slice):
                self._i = [self._i[j] for j in range(*idx.indices(len(self._i)))]
            else:
                self._i = [self._i[idx]]
            return self

        @property
        def last(self) -> list[float]:
            return [self._p._dev._last_m[i] for i in self._i]

        def trigger(self) -> None:
            dev = self._p._dev
            for idx in self._i:
                dev._trigger_single(idx)

        @property
        def ready(self) -> list[bool]:
            dev = self._p._dev
            return [dev._sms[idx].rx_fifo() > 0 for idx in self._i]

        async def result(self, timeout_ms: int = 50) -> list[float]:
            p = self._p
            dev = p._dev
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)

            # Yield until all triggered SMs have pushed their result or timeout
            while True:
                if all(dev._sms[idx].rx_fifo() > 0 for idx in self._i):
                    break
                if time.ticks_diff(time.ticks_ms(), deadline) >= 0:
                    break
                await asyncio.sleep_ms(p._poll_ms)

            results = []
            for idx in self._i:
                sm = dev._sms[idx]
                if sm.rx_fifo() == 0:
                    sm.active(0)
                    results.append(float('nan'))
                    continue

                count = sm.get()
                sm.active(0)

                if 0 < count < dev._TIMEOUT_US:
                    raw_m = count * dev._m_per_count(dev._temp_c[idx])
                    if dev._MIN_M <= raw_m <= dev._MAX_M:
                        filtered_m = dev._filters[idx].update(raw_m, 0.06)
                        r = max(dev._MIN_M, min(filtered_m, dev._MAX_M))
                        dev._last_m[idx] = r
                        results.append(r)
                        continue

                results.append(float('nan'))

            return results

        async def read(self, timeout_ms: int = 50) -> list[float]:
            self.trigger()
            await asyncio.sleep_ms(0)  # yield so other tasks can run during echo
            return await self.result(timeout_ms)

        def stream(self, count: int | None = None, interval_ms: int = 100) -> "_ViewStreamIter":
            return _ViewStreamIter(self, count, interval_ms)

        def __aiter__(self):
            return _ViewStreamIter(self, None, 100)

        async def __anext__(self) -> list[float]:
            return await self.read()
