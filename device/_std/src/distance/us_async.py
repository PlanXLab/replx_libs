# @package: us_async
# @version: 2.2.0
# @type: device-std
# @category: distance
# @sensor_type: B
# @interface: GPIO
# @depends: sr04, io_async
# @platforms: *
# @tags: ultrasonic, distance, sr04, hc-sr04, ranging, async, asyncio, irq, multi-sensor
# @author: PlanXLab Development Team

from micropython import const
import time
import asyncio
from io_async import AsyncDin
from .us import SR04

_ECHO_TIMEOUT_US = const(30000)


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
        self._async_echo = AsyncDin(device._echo)
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
        if not self._dev._single:
            raise RuntimeError("Use async_sr04[idx].last for multi-sensor")
        return self._dev._last_m[0]

    def trigger(self) -> None:
        if not self._dev._single:
            raise RuntimeError("Use async_sr04[idx].trigger() for multi-sensor")
        self._view._set([0]).trigger()

    async def result(self, timeout_ms: int = 50) -> float:
        if not self._dev._single:
            raise RuntimeError("Use async_sr04[idx].result() for multi-sensor")
        results = await self._view._set([0]).result(timeout_ms)
        return results[0]

    async def read(self, timeout_ms: int = 50) -> float:
        if not self._dev._single:
            raise RuntimeError("Use async_sr04[idx].read() for multi-sensor")
        results = await self._view._set([0]).read(timeout_ms)
        return results[0]

    def stream(self, count: int | None = None, interval_ms: int = 100) -> "_SR04StreamIter":
        if not self._dev._single:
            raise RuntimeError("Use async_sr04[idx].stream() for multi-sensor")
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
            self._p._dev._view._set(self._i).trigger()

        @property
        def ready(self) -> list[bool]:
            return self._p._dev._view._set(self._i).ready

        async def result(self, timeout_ms: int = 50) -> list[float]:
            p = self._p
            dev = p._dev
            results = []
            timeout_ms = dev._normalize_timeout_ms(timeout_ms)
            deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
            while True:
                all_done = True
                for idx in self._i:
                    if dev._pending[idx] and not dev._echo.pulse_ready(idx):
                        all_done = False
                        break
                if all_done:
                    break
                if time.ticks_diff(time.ticks_ms(), deadline) >= 0:
                    break
                await asyncio.sleep_ms(p._poll_ms)
            
            for idx in self._i:
                if not dev._pending[idx]:
                    results.append(float('nan'))
                    continue

                dev._pending[idx] = False
                echo_view = dev._echo[idx]
                dt_us = echo_view.pulse_width_us()
                echo_view.stop_pulse_capture()

                if dt_us <= 0:
                    await asyncio.sleep_ms(0)
                    dt_us = dev._measure_pulse_blocking(idx, timeout_ms)

                results.append(dev._distance_from_pulse(idx, dt_us))
            
            return results

        async def read(self, timeout_ms: int = 50) -> list[float]:
            p = self._p
            dev = p._dev
            timeout_ms = dev._normalize_timeout_ms(timeout_ms)
            results = []

            for idx in self._i:
                await asyncio.sleep_ms(0)
                dt_us = dev._measure_pulse_blocking(idx, timeout_ms)
                results.append(dev._distance_from_pulse(idx, dt_us))
                if idx != self._i[-1]:
                    if dev._interference_ms > 0:
                        await asyncio.sleep_ms(dev._interference_ms)
                    else:
                        await asyncio.sleep_ms(0)

            return results

        def stream(self, count: int | None = None, interval_ms: int = 100) -> "_ViewStreamIter":
            return _ViewStreamIter(self, count, interval_ms)

        def __aiter__(self):
            return _ViewStreamIter(self, None, 100)

        async def __anext__(self) -> list[float]:
            return await self.read()
