# @package: as5600_async
# @version: 1.1.0
# @type: device-std
# @category: orientation
# @sensor_type: D
# @interface: I2C
# @depends: as5600
# @platforms: *
# @tags: encoder, magnetic, angle, async, asyncio
# @author: PlanXLab Development Team

import asyncio
from .as5600 import AS5600


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
        dev = self._dev
        angle = dev.angle()
        velocity = dev.velocity()
        net_turn, path_turn = dev.turn()
        self._n += 1
        await asyncio.sleep_ms(self._poll_ms)
        return {
            'angle': angle,
            'velocity': velocity,
            'turn_net': net_turn,
            'turn_path': path_turn,
        }


class _StreamAngleIter:
    def __init__(self, dev, poll_ms, count, soft_zero, filtered):
        self._dev = dev
        self._poll_ms = poll_ms
        self._count = count
        self._soft_zero = soft_zero
        self._filtered = filtered
        self._n = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._count != 0 and self._n >= self._count:
            raise StopAsyncIteration
        val = self._dev.angle(soft_zero=self._soft_zero, filtered=self._filtered)
        self._n += 1
        await asyncio.sleep_ms(self._poll_ms)
        return val


class _StreamVelocityIter:
    def __init__(self, dev, poll_ms, count, filtered):
        self._dev = dev
        self._poll_ms = poll_ms
        self._count = count
        self._filtered = filtered
        self._n = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._count != 0 and self._n >= self._count:
            raise StopAsyncIteration
        val = self._dev.velocity(filtered=self._filtered)
        self._n += 1
        await asyncio.sleep_ms(self._poll_ms)
        return val


class AS5600Async:
    def __init__(self, device: AS5600):
        self._dev = device

    @property
    def device(self) -> AS5600:
        return self._dev

    async def angle(self, *, soft_zero=True, filtered=False) -> float:
        return self._dev.angle(soft_zero=soft_zero, filtered=filtered)

    async def angle_deg(self, *, soft_zero=True, filtered=False) -> float:
        return self._dev.angle_deg(soft_zero=soft_zero, filtered=filtered)

    async def velocity(self, *,
                       filtered=False,
                       tick_emit=4,
                       tick_hold=2,
                       dt_min_s=0.003,
                       dt_max_s=0.5,
                       omega_clip=None) -> float:
        return self._dev.velocity(
            filtered=filtered,
            tick_emit=tick_emit,
            tick_hold=tick_hold,
            dt_min_s=dt_min_s,
            dt_max_s=dt_max_s,
            omega_clip=omega_clip
        )

    async def velocity_rpm(self, *, filtered=False) -> float:
        return self._dev.velocity_rpm(filtered=filtered)

    async def turn(self, *, soft_zero=True, filtered=False, tick_thr=2, confirm_samples=3):
        return self._dev.turn(
            soft_zero=soft_zero,
            filtered=filtered,
            tick_thr=tick_thr,
            confirm_samples=confirm_samples
        )

    def reset_turn(self):
        self._dev.reset_turn()

    def reset_velocity(self):
        self._dev.reset_velocity()

    async def status(self) -> int:
        return self._dev.status()

    def stream(self, poll_ms: int = 10, count: int = 0) -> "_StreamIter":
        return _StreamIter(self._dev, poll_ms, count)

    def stream_angle(self, poll_ms: int = 10, count: int = 0, *, soft_zero=True, filtered=False) -> "_StreamAngleIter":
        return _StreamAngleIter(self._dev, poll_ms, count, soft_zero, filtered)

    def stream_velocity(self, poll_ms: int = 10, count: int = 0, *, filtered=False) -> "_StreamVelocityIter":
        return _StreamVelocityIter(self._dev, poll_ms, count, filtered)
