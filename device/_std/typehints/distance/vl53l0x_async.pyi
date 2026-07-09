"""
Async wrapper for VL53L0X Time-of-Flight Distance Sensor.

Provides asyncio-compatible interface for non-blocking distance measurement
in cooperative multitasking environments (MQTT, web servers, multi-sensor).
"""

from typing import AsyncGenerator, AsyncIterator, TYPE_CHECKING
from i2c import I2CController

if TYPE_CHECKING:
    from .vl53l0x import VL53L0X


class VL53L0XAsync:
    """
    Async wrapper for VL53L0X sensor.
    
    Wraps a VL53L0X instance to provide asyncio-compatible methods.
    Yields control during polling to allow other coroutines to run.
    
    Example
    -------
    ```python
        >>> # With MQTT client
        >>> async def sensor_task(async_sensor, mqtt):
        ...     async for distance in async_sensor.stream():
        ...         await mqtt.publish("sensor/distance", f"{distance:.3f}")
        ...         await asyncio.sleep_ms(100)
    ```
    """

    def __init__(self, device: "VL53L0X", poll_ms: int = 10) -> None:
        """
        Initialize async wrapper.
        
        :param device: VL53L0X sensor instance (must be started).
        :param poll_ms: Polling interval in milliseconds (default: 10).
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> async_sensor = VL53L0XAsync(sensor, poll_ms=20)
        ```
        """
        ...

    @property
    def device(self) -> "VL53L0X":
        """
        Get underlying VL53L0X sensor instance.
        
        :return: The wrapped VL53L0X sensor instance.
        
        Example
        -------
        ```python
            >>> async_sensor.device
            <VL53L0X object at ...>
        ```
        """
        ...

    @property
    def last(self) -> float:
        """
        Get last valid measurement from sensor.
        
        :return: Last distance in meters, or nan if no valid reading.
        
        Example
        -------
        ```python
            >>> await async_sensor.read()
            >>> async_sensor.last
            0.532
        ```
        """
        ...

    async def read(self, timeout_ms: int | None = None) -> float:
        """
        Read distance asynchronously.
        
        Polls sensor.ready() with async sleep until data available or timeout.
        Yields control to event loop during polling.
        
        :param timeout_ms: Timeout in milliseconds (default: sensor's timeout).
        :return: Distance in meters, or last valid value on timeout.
        
        Example
        -------
        ```python
            >>> distance = await async_sensor.read()
            >>> distance = await async_sensor.read(timeout_ms=500)
        ```
        """
        ...

    def stream(
        self, count: int | None = None, interval_ms: int = 0
    ) -> "AsyncIterator[float]":
        """
        Async generator for continuous distance readings.
        
        :param count: Number of readings (None for infinite).
        :param interval_ms: Minimum interval between readings (default: 0).
        :yields: Distance in meters.
        
        Example
        -------
        ```python
            >>> # Read 100 samples
            >>> async for d in async_sensor.stream(count=100):
            ...     print(d)
            >>> 
            >>> # Continuous with interval
            >>> async for d in async_sensor.stream(interval_ms=50):
            ...     process(d)
        ```
        """
        ...

    def __aiter__(self) -> "VL53L0XAsync":
        """
        Return async iterator for continuous readings.
        
        :return: Self as async iterator.
        
        Example
        -------
        ```python
            >>> async for distance in async_sensor:
            ...     print(f"{distance:.3f} m")
        ```
        """
        ...

    async def __anext__(self) -> float:
        """
        Get next distance reading.
        
        :return: Distance in meters.
        
        Example
        -------
        ```python
            >>> it = async_sensor.__aiter__()
            >>> d = await it.__anext__()
            >>> print(f"{d:.3f} m")
        ```
        """
        ...
