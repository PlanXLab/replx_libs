# @package: mpu6050_async
# @version: 1.2.0
# @type: device-std
# @category: motion
# @sensor_type: D
# @interface: I2C
# @depends: mpu6050
# @platforms: *
# @tags: imu, 6dof, dmp, async, asyncio, mpu6050
# @author: PlanXLab Development Team

import asyncio
from .mpu6050 import MPU6050


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
        use_dmp = dev._use_dmp
        if use_dmp:
            quat = dev.quat
            result = {
                'accel': dev._apply_body_transform(dev._dmp_accel[0], dev._dmp_accel[1], dev._dmp_accel[2]),
                'gyro': dev.gyro,
                'quat': quat,
                'euler': dev._euler_from_quat(quat),
                'linear': dev._linear_from_quat(quat, dev._dmp_accel),
            }
        else:
            result = {
                'accel': dev.accel,
                'gyro': dev.gyro,
            }
        self._n += 1
        await asyncio.sleep_ms(self._poll_ms)
        return result


class MPU6050Async:
    def __init__(self, device: MPU6050):
        self._dev = device

    @property
    def device(self) -> MPU6050:
        return self._dev

    async def wait_stable(self, samples: int = 50, poll_ms: int = 20) -> None:
        dev = self._dev
        for _ in range(samples):
            _ = dev.accel
            _ = dev.gyro
            if dev._use_dmp:
                _ = dev.quat
            await asyncio.sleep_ms(poll_ms)

    def stream(self, poll_ms: int = 10, count: int = 0) -> "_StreamIter":
        return _StreamIter(self._dev, poll_ms, count)
