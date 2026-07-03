# @package: bno055_async
# @version: 1.1.0
# @type: device-std
# @category: motion
# @sensor_type: D
# @interface: I2C
# @depends: bno055
# @platforms: *
# @tags: imu, 9dof, async, asyncio, bno055
# @author: PlanXLab Development Team

import time
import asyncio
from .bno055 import BNO055


class _StreamIter:
    def __init__(self, dev, poll_ms, count):
        self._dev = dev
        self._poll_ms = poll_ms
        self._count = count
        self._n = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._count != 0 and self._n >= self._count:
            raise StopAsyncIteration
        val = self._dev.read()
        self._n += 1
        await asyncio.sleep_ms(self._poll_ms)
        return val


class BNO055Async:

    def __init__(self, device: BNO055):
        self._dev = device

    @property
    def device(self) -> BNO055:
        return self._dev

    async def wait_ready(self, timeout_s: int = 15, poll_ms: int = 150) -> bool:
        deadline = time.ticks_add(time.ticks_ms(), timeout_s * 1000)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            diag = self._dev.diagnostics
            sys_, gyr, acc, mag = diag['calib']
            if sys_ == 3 and gyr == 3 and acc == 3 and mag == 3:
                return True
            await asyncio.sleep_ms(poll_ms)
        return False

    def stream(self, poll_ms: int = 10, count: int = 0) -> "_StreamIter":
        return _StreamIter(self._dev, poll_ms, count)
