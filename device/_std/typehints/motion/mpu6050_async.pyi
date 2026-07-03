"""
Async Wrapper for MPU6050 6-DoF IMU

Provides asyncio-compatible interface for the MPU6050 motion tracking
sensor. This wrapper enables non-blocking operation in async applications,
particularly useful when multiple sensors or network tasks run concurrently.

Since MPU6050 is a Type D (Immediate) sensor, the async wrapper primarily
benefits:
- Cooperative multitasking with other async code
- Periodic streaming with consistent timing
- DMP mode sensor stabilization

In DMP mode, all data in stream() is frame-synchronized from the same
DMP packet, ensuring temporal consistency for orientation calculations.
"""

from typing import AsyncIterator
from .mpu6050 import MPU6050


class MPU6050Async:
    """
    Async wrapper for MPU6050 IMU driver.

    Provides asyncio-compatible interface for cooperative multitasking.
    Optimized for both RAW and DMP modes with proper frame synchronization.

    Example
    -------
    ```python
    import asyncio
    from mpu6050 import MPU6050
    from mpu6050_async import MPU6050Async

    async def main():
        imu = MPU6050(sda=0, scl=1, mode=MPU6050.Mode.DMP_STABLE,
                      coord='flu', remap='x-zy')
        async_imu = MPU6050Async(imu)

        # Wait for sensor to stabilize
        await async_imu.wait_stable()

        # Stream 100 samples (DMP mode includes linear acceleration)
        async for data in async_imu.stream(poll_ms=20, count=100):
            print(f"Roll: {data['euler'][0]:.2f}")
            if 'linear' in data:
                print(f"Linear: {data['linear']}")

        imu.deinit()

    asyncio.run(main())
    ```
    """

    def __init__(self, device: MPU6050) -> None:
        """
        Initialize the async wrapper.

        :param device: Underlying MPU6050 driver instance.
        """
        ...

    @property
    def device(self) -> MPU6050:
        """
        Access the underlying MPU6050 driver.

        Use this property to access sensor data directly:
        - ``device.accel`` - Acceleration (m/s^2)
        - ``device.gyro`` - Angular velocity (rad/s)
        - ``device.quat`` - Quaternion (w, x, y, z), transformed by coord/remap
        - ``device.euler`` - Euler angles (roll, pitch, yaw) in radians
        - ``device.linear`` - Linear acceleration (m/s^2)
        - ``device.zero_heading()`` - Reset yaw reference

        :return: The underlying MPU6050 instance.
        """
        ...

    async def wait_stable(self, samples: int = 50, poll_ms: int = 20) -> None:
        """
        Wait for sensor readings to stabilize.

        Performs multiple reads to allow bias estimation to settle.
        In DMP mode, also reads quaternion to stabilize orientation output.

        :param samples: Number of samples to read (default 50).
        :param poll_ms: Delay between samples in milliseconds (default 20).
        """
        ...

    def stream(
        self,
        poll_ms: int = 10,
        count: int = 0
    ) -> AsyncIterator[dict[str, tuple]]:
        """
        Async generator yielding sensor data dictionaries.

        In DMP mode, yields frame-synchronized data:
        - ``'accel'``: (ax, ay, az) in m/s^2 (from DMP packet, transformed by coord/remap)
        - ``'gyro'``: (gx, gy, gz) in rad/s
        - ``'quat'``: (w, x, y, z) quaternion transformed by coord/remap
                - ``'euler'``: (roll, pitch, yaw) in radians; roll/pitch are from the
                    frame-synchronized DMP acceleration and yaw is relative gyro heading
        - ``'linear'``: (ax, ay, az) gravity-compensated in m/s^2

        In RAW mode, yields:
        - ``'accel'``: (ax, ay, az) in m/s^2
        - ``'gyro'``: (gx, gy, gz) in rad/s

        :param poll_ms: Delay between samples in milliseconds (default 10).
        :param count: Number of samples to yield. 0 for infinite (default 0).
        :yield: Dictionary with sensor data.
        """
        ...
