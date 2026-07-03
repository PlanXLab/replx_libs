# @package: dio_async
# @version: 2.1
# @type: core
# @category: peripheral
# @interface: GPIO
# @depends: dio
# @platforms: *
# @tags: gpio, digital, async, asyncio, input, output
# @author: PlanXLab Development Team

import asyncio
from dio import Din


class _EdgeIter:
    def __init__(self, source, idx, edge):
        self._source = source
        self._idx = idx
        self._edge = edge
        self._event = asyncio.ThreadSafeFlag()
        self._active = False

    def _cb(self, _pin, _value):
        self._event.set()

    def close(self):
        if self._active:
            self._source.irq(self._idx, None)
            self._active = False
            self._event.set()

    def __aiter__(self):
        if not self._active:
            self._source.irq(self._idx, self._cb, trigger=self._edge)
            self._active = True
        return self

    async def __anext__(self):
        if not self._active:
            raise StopAsyncIteration
        await self._event.wait()
        if not self._active:
            raise StopAsyncIteration
        return self._source.read(self._idx)


class AsyncDin:
    def __init__(self, din):
        self._din = din

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._din.deinit()

    def __len__(self):
        return len(self._din)

    def __getitem__(self, idx):
        return AsyncDinView(self._din, idx)

    @property
    def din(self):
        return self._din

    def read(self, idx=0):
        return self._din.read(idx)

    async def wait_for_value(self, idx=0, target=1, poll_ms=1):
        while self._din.read(idx) != target:
            await asyncio.sleep_ms(poll_ms)
        return True

    async def wait_for_value_timeout(self, idx=0, target=1,
                                     timeout_ms=1000, poll_ms=1):
        try:
            return await asyncio.wait_for_ms(
                self.wait_for_value(idx, target, poll_ms), timeout_ms)
        except asyncio.TimeoutError:
            return False

    def events(self, idx=0, edge=Din.CB_BOTH):
        return _EdgeIter(self._din, idx, edge)


class AsyncDinView:
    def __init__(self, din, idx):
        self._din = din
        self._idx = idx

    def read(self):
        return self._din.read(self._idx)

    async def wait_for_value(self, target=1, poll_ms=1):
        while self._din.read(self._idx) != target:
            await asyncio.sleep_ms(poll_ms)
        return True

    async def wait_for_value_timeout(self, target=1, timeout_ms=1000,
                                     poll_ms=1):
        try:
            return await asyncio.wait_for_ms(
                self.wait_for_value(target, poll_ms), timeout_ms)
        except asyncio.TimeoutError:
            return False

    async def wait_for_edge(self, edge=Din.CB_BOTH):
        flag = asyncio.ThreadSafeFlag()

        def _cb(_pin, _value):
            flag.set()

        self._din.irq(self._idx, _cb, trigger=edge)
        try:
            await flag.wait()
            return True
        finally:
            self._din.irq(self._idx, None)

    async def wait_for_edge_timeout(self, edge=Din.CB_BOTH,
                                    timeout_ms=1000):
        try:
            return await asyncio.wait_for_ms(
                self.wait_for_edge(edge), timeout_ms)
        except asyncio.TimeoutError:
            self._din.irq(self._idx, None)
            return False

    def events(self, edge=Din.CB_BOTH):
        return _EdgeIter(self._din, self._idx, edge)


class AsyncDout:
    def __init__(self, dout):
        self._dout = dout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._dout.deinit()

    def __len__(self):
        return len(self._dout)

    def __getitem__(self, idx):
        return AsyncDoutView(self._dout, idx)

    @property
    def dout(self):
        return self._dout

    def write(self, value=1, idx=0):
        self._dout.write(value, idx=idx)

    async def blink(self, idx=0, on_ms=500, off_ms=500, count=0):
        n = 0
        while count == 0 or n < count:
            self._dout.write(1, idx=idx)
            await asyncio.sleep_ms(on_ms)
            self._dout.write(0, idx=idx)
            await asyncio.sleep_ms(off_ms)
            n += 1

    async def pulse(self, idx=0, duration_ms=10, value=1):
        self._dout.write(value, idx=idx)
        await asyncio.sleep_ms(duration_ms)
        self._dout.write(1 - (1 if value else 0), idx=idx)


class AsyncDoutView:
    def __init__(self, dout, idx):
        self._dout = dout
        self._idx = idx

    def write(self, value=1):
        self._dout.write(value, idx=self._idx)

    def read(self):
        return self._dout.read(self._idx)

    def toggle(self):
        self._dout.toggle(self._idx)

    async def blink(self, on_ms=500, off_ms=500, count=0):
        n = 0
        while count == 0 or n < count:
            self._dout.write(1, idx=self._idx)
            await asyncio.sleep_ms(on_ms)
            self._dout.write(0, idx=self._idx)
            await asyncio.sleep_ms(off_ms)
            n += 1

    async def pulse(self, duration_ms=10, value=1):
        self._dout.write(value, idx=self._idx)
        await asyncio.sleep_ms(duration_ms)
        self._dout.write(1 - (1 if value else 0), idx=self._idx)


class AsyncDio:
    def __init__(self, dio):
        self._dio = dio

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._dio.deinit()

    def __len__(self):
        return len(self._dio)

    def __getitem__(self, idx):
        return AsyncDioView(self._dio, idx)

    @property
    def dio(self):
        return self._dio

    def read(self, idx=0):
        return self._dio.read(idx)

    def write(self, value=1, idx=0):
        self._dio.write(value, idx=idx)


class AsyncDioView:
    def __init__(self, dio, idx):
        self._dio = dio
        self._idx = idx

    def read(self):
        return self._dio.read(self._idx)

    def write(self, value=1):
        self._dio.write(value, idx=self._idx)

    def toggle(self):
        self._dio.toggle(self._idx)
