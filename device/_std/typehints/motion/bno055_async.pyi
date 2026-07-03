"""
Async Wrapper for BNO055 9-DoF IMU

Provides asyncio-compatible interface for the BNO055 absolute orientation
sensor. This wrapper enables non-blocking operation in async applications,
particularly useful when multiple sensors or network tasks run concurrently.

Since BNO055 is a Type D (Immediate) sensor with fast I2C reads (~100μs),
the async wrapper primarily benefits:

- Non-blocking `wait_ready()` during calibration
- Continuous data streaming via `stream()` generator

For direct sensor data access, use `async_imu.device.accel` etc.

Example
-------
```python
import asyncio
from bno055 import BNO055
from bno055_async import BNO055Async

async def main():
    imu = BNO055(sda=4, scl=5)
    async_imu = BNO055Async(imu)
    
    # Non-blocking calibration wait
    if await async_imu.wait_ready(timeout_s=30):
        print("Calibrated!")
    
    # Direct sensor access via device property
    roll, pitch, yaw = async_imu.device.euler
    
    # Stream orientation data (limited count)
    async for data in async_imu.stream(poll_ms=20, count=100):
        accel, gyro, mag, quat, euler, linear, gravity, temp = data
        print(f"Euler: {euler}")

asyncio.run(main())
```
"""
from typing import AsyncGenerator, AsyncIterator, Tuple
from .bno055 import BNO055


class BNO055Async:
    """
    Async wrapper for BNO055 IMU.

    Wraps a synchronous BNO055 instance to provide asyncio-compatible methods.
    For direct sensor readings, access the underlying device via `device` property.
    """

    def __init__(self, device: BNO055) -> None:
        """
        Create async wrapper for BNO055 device.

        :param device: Initialized BNO055 instance

        Example
        -------
        ```python
        imu = BNO055(sda=4, scl=5)
        async_imu = BNO055Async(imu)
        ```
        """

    @property
    def device(self) -> BNO055:
        """
        Access the underlying BNO055 device.

        Use this property to access sensor data directly:
        - `async_imu.device.accel` - Accelerometer (m/s²)
        - `async_imu.device.gyro` - Gyroscope (rad/s)
        - `async_imu.device.euler` - Euler angles (rad)
        - `async_imu.device.quat` - Quaternion
        - `async_imu.device.linear` - Linear acceleration
        - `async_imu.device.gravity` - Gravity vector
        - `async_imu.device.temp` - Temperature (°C)
        - `async_imu.device.diagnostics` - Calibration status

        :return: The wrapped BNO055 instance
        """

    async def wait_ready(self, timeout_s: int = 15, poll_ms: int = 150) -> bool:
        """
        Wait for full calibration asynchronously.

        Non-blocking version that yields to the event loop between
        calibration status checks.

        :param timeout_s: Maximum wait time in seconds
        :param poll_ms: Polling interval in milliseconds
        :return: True if fully calibrated, False if timeout

        Example
        -------
        ```python
        async def setup():
            imu = BNO055(sda=4, scl=5)
            async_imu = BNO055Async(imu)
            
            # Other tasks can run while waiting
            if await async_imu.wait_ready(timeout_s=60):
                print("IMU ready")
        ```
        """

    def stream(
        self, poll_ms: int = 10, count: int = 0
    ) -> AsyncIterator[
        Tuple[
            Tuple[float, float, float],  # accel
            Tuple[float, float, float],  # gyro
            Tuple[float, float, float],  # magnetic
            Tuple[float, float, float, float],  # quat
            Tuple[float, float, float],  # euler
            Tuple[float, float, float],  # linear
            Tuple[float, float, float],  # gravity
            int,  # temp
        ]
    ]:
        """
        Continuous data stream as async generator.

        Yields sensor data at specified intervals, allowing integration
        with asyncio event loops.

        :param poll_ms: Polling interval in milliseconds
        :param count: Number of readings to yield (0 = infinite)
        :yields: Sensor data tuple (accel, gyro, magnetic, quat, euler, linear, gravity, temp)

        Example
        -------
        ```python
        async def monitor_orientation():
            imu = BNO055(sda=4, scl=5)
            async_imu = BNO055Async(imu)
            
            # Stream 100 readings
            async for data in async_imu.stream(poll_ms=50, count=100):
                _, _, _, quat, euler, _, _, _ = data
                roll, pitch, yaw = euler
                print(f"Roll: {roll:.2f}")
            
            # Or infinite stream with break
            async for data in async_imu.stream(poll_ms=50):
                if some_condition:
                    break
        ```
        """
