"""
Async wrapper for Ultrasonic Distance Sensor.

Provides asyncio-compatible interface for non-blocking distance measurement.
Supports single and multiple sensors with View pattern.

Key Features
------------
- True non-blocking: Uses io.py IRQ-based pulse capture
- Event loop friendly: Yields during measurement wait
- Multi-sensor support: View pattern for grouped operations
- Same precision as sync version (~±3mm)
"""

from typing import AsyncGenerator, AsyncIterator, TYPE_CHECKING

if TYPE_CHECKING:
    from .us import SR04


class SR04Async:
    """
    Async wrapper for SR04 using IRQ-based pulse measurement.
    
    Supports single and multiple sensors with asyncio-compatible interface.
    
    Example
    -------
    ```python
        >>> import asyncio
        >>> from ticle.us import SR04
        >>> from ticle.us_async import SR04Async
        >>> 
        >>> # Single sensor
        >>> us = SR04(echo=16, trig=17)
        >>> async_us = SR04Async(us)
        >>> 
        >>> async def main():
        ...     distance = await async_us.read()
        ...     print(f"Distance: {distance:.3f} m")
        >>> 
        >>> asyncio.run(main())
        >>> 
        >>> # Multiple sensors
        >>> sensors = SR04(echo=[16, 18], trig=[17, 19])
        >>> async_sensors = SR04Async(sensors)
        >>> 
        >>> async def multi():
        ...     distances = await async_sensors[:].read()
        ...     for i, d in enumerate(distances):
        ...         print(f"Sensor {i}: {d:.3f} m")
    ```
    """

    def __init__(self, device: "SR04", poll_ms: int = 1) -> None:
        """
        Initialize async wrapper.
        
        :param device: SR04 sensor instance
        :param poll_ms: Polling interval for async wait (default: 1ms)
        """
        ...

    @property
    def device(self) -> "SR04":
        """Get underlying SR04 instance."""
        ...

    def __len__(self) -> int:
        """Return number of sensors."""
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """Get view for selected sensor(s)."""
        ...

    @property
    def last(self) -> float:
        """Last measured distance (single sensor only)."""
        ...

    def trigger(self) -> None:
        """Trigger measurement (single sensor only)."""
        ...

    async def result(self, timeout_ms: int = 50) -> float:
        """Get measurement result (single sensor only)."""
        ...

    async def read(self, timeout_ms: int = 50) -> float:
        """Trigger and read distance (single sensor only)."""
        ...

    def stream(
        self, count: int | None = None, interval_ms: int = 100
    ) -> AsyncIterator[float]:
        """Async iterator for continuous readings (single sensor only)."""
        ...

    def __aiter__(self) -> AsyncIterator[float]:
        ...

    async def __anext__(self) -> float:
        ...

    def deinit(self) -> None:
        """Release resources."""
        ...

    class _View:
        """View for selected sensor(s)."""
        
        def __len__(self) -> int:
            ...

        def __getitem__(self, idx: int | slice) -> "SR04Async._View":
            ...

        @property
        def last(self) -> list[float]:
            """Get last measured distances."""
            ...

        def trigger(self) -> None:
            """Trigger measurement for selected sensors."""
            ...

        @property
        def ready(self) -> list[bool]:
            """Check if measurements are ready."""
            ...

        async def result(self, timeout_ms: int = 50) -> list[float]:
            """Wait for and calculate distances asynchronously."""
            ...

        async def read(self, timeout_ms: int = 50) -> list[float]:
            """Trigger and read distances asynchronously."""
            ...

        def stream(
            self, count: int | None = None, interval_ms: int = 100
        ) -> AsyncIterator[list[float]]:
            """Async iterator for continuous readings."""
            ...

        def __aiter__(self) -> AsyncIterator[list[float]]:
            ...

        async def __anext__(self) -> list[float]:
            ...
