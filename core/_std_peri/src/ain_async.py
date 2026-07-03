# @package: ain_async
# @version: 2.2
# @type: core
# @category: peripheral
# @interface: ADC
# @depends: ain
# @platforms: *
# @tags: adc, analog, async, asyncio, input
# @author: PlanXLab Development Team

import asyncio
from ain import Ain


class AsyncAin:
    def __init__(self, ain):
        self._ain = ain

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ain.deinit()

    def __len__(self):
        return len(self._ain)

    def __getitem__(self, idx):
        return AsyncAinView(self._ain[idx])

    @property
    def ain(self):
        return self._ain

    def read(self, idx=0):
        return self._ain.read(idx)

    def read_percent(self, idx=0):
        return self._ain.read_percent(idx)

    def read_voltage(self, idx=0):
        return self._ain.read_voltage(idx)

    async def filtered(self, filt, samples=10, *, idx=0, interval_ms=1):
        if samples <= 0:
            raise ValueError("samples must be positive")
        ain = self._ain
        result = 0.0
        if interval_ms > 0:
            for _ in range(samples):
                result = filt(ain.read(idx))
                await asyncio.sleep_ms(interval_ms)
        else:
            for _ in range(samples):
                result = filt(ain.read(idx))
        return result

    async def wait_for_threshold(self, threshold, *, idx=0, above=True, poll_ms=10):
        read = self._ain.read
        while True:
            value = read(idx)
            if (above and value > threshold) or ((not above) and value < threshold):
                return value
            await asyncio.sleep_ms(poll_ms)

    async def wait_for_threshold_timeout(self, threshold, timeout_ms,
                                         *, idx=0, above=True, poll_ms=10):
        try:
            return await asyncio.wait_for_ms(
                self.wait_for_threshold(threshold, idx=idx, above=above, poll_ms=poll_ms),
                timeout_ms
            )
        except asyncio.TimeoutError:
            return None

    def monitor(self, idx=0, *, interval_ms=100):
        return _MonitorIter(self, idx, interval_ms)


class AsyncAinView:
    def __init__(self, view):
        self._view = view

    def __len__(self):
        return len(self._view)

    def __getitem__(self, idx):
        return AsyncAinView(self._view[idx])

    def read(self):
        return self._view.read()

    def read_percent(self):
        return self._view.read_percent()

    def read_voltage(self):
        return self._view.read_voltage()

    async def filtered(self, filt, samples=10, interval_ms=1):
        if samples <= 0:
            raise ValueError("samples must be positive")
        view = self._view
        result = 0.0
        if interval_ms > 0:
            for _ in range(samples):
                result = filt(view.read())
                await asyncio.sleep_ms(interval_ms)
        else:
            for _ in range(samples):
                result = filt(view.read())
        return result

    async def wait_for_threshold(self, threshold, *, above=True, poll_ms=10):
        view = self._view
        while True:
            value = view.read()
            if (above and value > threshold) or ((not above) and value < threshold):
                return value
            await asyncio.sleep_ms(poll_ms)

    async def wait_for_threshold_timeout(self, threshold, timeout_ms,
                                         *, above=True, poll_ms=10):
        try:
            return await asyncio.wait_for_ms(
                self.wait_for_threshold(threshold, above=above, poll_ms=poll_ms),
                timeout_ms
            )
        except asyncio.TimeoutError:
            return None

    def monitor(self, *, interval_ms=100):
        return _MonitorIter(self, 0, interval_ms)


class _MonitorIter:
    def __init__(self, source, idx, interval_ms):
        self._source = source
        self._idx = idx
        self._interval_ms = interval_ms

    def __aiter__(self):
        return self

    async def __anext__(self):
        if isinstance(self._source, AsyncAin):
            value = self._source.read(self._idx)
        else:
            value = self._source.read()
        await asyncio.sleep_ms(self._interval_ms)
        return value
