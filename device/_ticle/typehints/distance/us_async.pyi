"""
Async wrapper for Ultrasonic Distance Sensor (ticle / RP2350).

Provides asyncio-compatible interface for PIO-based non-blocking distance
measurement. Unlike the _std version, no AsyncDin or IRQ capture is required —
the PIO State Machine handles all timing autonomously and this wrapper simply
polls the RX FIFO.

Key Features
------------
- True non-blocking: PIO SM runs independently; asyncio only polls FIFO
- Event loop friendly: yields during echo wait
- Multi-sensor support: View pattern for grouped operations
- Compatible with _std SR04Async API for single-sensor use

Distance unit: metres (float)
"""

from typing import AsyncIterator, TYPE_CHECKING

if TYPE_CHECKING:
    from .us import SR04


class SR04Async:
    """
    Async wrapper for ticle SR04 using PIO-based pulse measurement.

    Supports single and multiple sensors with asyncio-compatible interface.
    Class-level methods target sensor 0; use ``[idx]`` indexing for other sensors.

    Example
    -------
    ```python
        >>> import asyncio
        >>> from ticle_lite.us import SR04
        >>> from ticle_lite.us_async import SR04Async
        >>> 
        >>> sonic = SR04(trig=10, echo=11)
        >>> async_sonic = SR04Async(sonic)
        >>> 
        >>> async def main():
        ...     dist = await async_sonic.read()
        ...     print(f"Distance: {dist:.3f} m")
        >>> 
        >>> asyncio.run(main())
        >>> 
        >>> # Multiple sensors
        >>> sensors = SR04([(10, 11), (12, 13)])
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
        :param poll_ms: FIFO polling interval in milliseconds (default: 1)

        Example
        -------
        ```python
            >>> from ticle_lite.us import SR04
            >>> from ticle_lite.us_async import SR04Async
            >>> sonic = SR04(trig=10, echo=11)
            >>> async_sonic = SR04Async(sonic)
        ```
        """
        ...

    @property
    def device(self) -> "SR04":
        """
        Get the underlying SR04 instance.

        :return: The wrapped SR04 device.

        Example
        -------
        ```python
            >>> async_sonic.device.reset_filter()
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return number of configured sensors.

        :return: Sensor count.

        Example
        -------
        ```python
            >>> sensors = SR04([(10, 11), (12, 13)])
            >>> async_s = SR04Async(sensors)
            >>> len(async_s)
            2
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Access sensor(s) by index or slice.

        :param idx: Integer index or slice.
        :return: ``_View`` for the selected sensor(s).

        :raises IndexError: If index is out of range.
        :raises TypeError: If idx is not int or slice.

        Example
        -------
        ```python
            >>> sensors = SR04([(10, 11), (12, 13)])
            >>> async_s = SR04Async(sensors)
            >>> dist = await async_s[0].read()
            >>> dists = await async_s[:].read()
        ```
        """
        ...

    @property
    def last(self) -> float:
        """
        Last valid distance in metres for sensor 0.

        :return: Last measurement in metres, or -1.0 if none yet.

        Example
        -------
        ```python
            >>> await async_sonic.read()
            >>> print(async_sonic.last)
        ```
        """
        ...

    def trigger(self) -> None:
        """
        Fire trigger pulse for sensor 0 (non-blocking).

        Follow with ``await result()`` to retrieve the value.

        Example
        -------
        ```python
            >>> async_sonic.trigger()
            >>> dist = await async_sonic.result(timeout_ms=50)
        ```
        """
        ...

    async def result(self, timeout_ms: int = 50) -> float:
        """
        Await and return pending echo result for sensor 0.

        Polls the PIO FIFO until data arrives or timeout expires.

        :param timeout_ms: Maximum wait time in milliseconds (default: 50).
        :return: Distance in metres, or ``float('nan')`` on timeout/invalid.

        Example
        -------
        ```python
            >>> async_sonic.trigger()
            >>> dist = await async_sonic.result(timeout_ms=50)
            >>> print(f"{dist:.3f} m")
        ```
        """
        ...

    async def read(self, timeout_ms: int = 50) -> float:
        """
        Trigger and await distance measurement for sensor 0.

        Combines ``trigger()`` and ``result()`` in one call. Yields to the
        event loop during the echo wait.

        :param timeout_ms: Echo wait timeout in milliseconds (default: 50).
        :return: Distance in metres, or ``float('nan')`` on timeout/invalid.

        Example
        -------
        ```python
            >>> import asyncio
            >>> from ticle_lite.us import SR04
            >>> from ticle_lite.us_async import SR04Async
            >>> async_sonic = SR04Async(SR04(trig=10, echo=11))
            >>> 
            >>> async def main():
            ...     while True:
            ...         d = await async_sonic.read()
            ...         print(f"{d:.3f} m")
            ...         await asyncio.sleep_ms(100)
        ```
        """
        ...

    def stream(
        self, count: int | None = None, interval_ms: int = 100
    ) -> AsyncIterator[float]:
        """
        Async iterator yielding distance readings for sensor 0.

        :param count: Number of readings to yield. ``None`` for infinite.
        :param interval_ms: Minimum interval between readings in ms (default: 100).
        :return: Async iterator of distances in metres.

        Example
        -------
        ```python
            >>> async def monitor():
            ...     async for dist in async_sonic.stream(count=10, interval_ms=200):
            ...         print(f"{dist:.3f} m")
        ```
        """
        ...

    def __aiter__(self) -> AsyncIterator[float]:
        """
        Default async iterator (infinite stream, 100 ms interval).

        Example
        -------
        ```python
            >>> async for dist in async_sonic:
            ...     print(f"{dist:.3f} m")
            ...     await asyncio.sleep_ms(50)
        ```
        """
        ...

    async def __anext__(self) -> float:
        """
        Return the next distance reading.

        :return: Distance in metres.

        Example
        -------
        ```python
            >>> dist = await async_sonic.__anext__()
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Deinitialize the underlying SR04 and release hardware resources.

        Example
        -------
        ```python
            >>> async_sonic.deinit()
        ```
        """
        ...


class _View:
    """
    View into a subset of sensors within SR04Async.

    Returned by ``SR04Async.__getitem__``; not instantiated directly.

    Example
    -------
    ```python
        >>> sensors = SR04([(10, 11), (12, 13)])
        >>> async_s = SR04Async(sensors)
        >>> view = async_s[:]          # all sensors
        >>> view = async_s[0]          # first sensor only
        >>> dists = await view.read()  # list[float]
    ```
    """

    def __len__(self) -> int:
        """
        Return number of sensors in this view.

        :return: Sensor count.

        Example
        -------
        ```python
            >>> len(async_s[:])
            2
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Further narrow this view.

        :param idx: Integer index or slice relative to this view.
        :return: Narrowed ``_View``.

        Example
        -------
        ```python
            >>> first = async_s[:][0]
            >>> dist = await first.read()
        ```
        """
        ...

    @property
    def last(self) -> list[float]:
        """
        Last valid distance in metres for each sensor in the view.

        :return: List of last measurements in metres (-1.0 if none yet).

        Example
        -------
        ```python
            >>> await async_s[:].read()
            >>> print(async_s[:].last)  # e.g. [0.235, 1.048]
        ```
        """
        ...

    def trigger(self) -> None:
        """
        Fire trigger pulses for all sensors in the view (non-blocking).

        All PIO State Machines are started simultaneously, then run in
        parallel. Follow with ``await result()`` to collect values.

        Example
        -------
        ```python
            >>> async_s[:].trigger()
            >>> dists = await async_s[:].result(timeout_ms=50)
        ```
        """
        ...

    @property
    def ready(self) -> list[bool]:
        """
        Check which sensors have a result waiting in the FIFO.

        :return: List of booleans, True when ``result()`` is available.

        Example
        -------
        ```python
            >>> async_s[:].trigger()
            >>> while not all(async_s[:].ready):
            ...     await asyncio.sleep_ms(1)
            >>> dists = await async_s[:].result()
        ```
        """
        ...

    async def result(self, timeout_ms: int = 50) -> list[float]:
        """
        Await and return pending echo results for sensors in the view.

        Polls PIO FIFOs until all sensors report or timeout expires.
        Sensors that time out contribute ``float('nan')``.

        :param timeout_ms: Maximum wait time in milliseconds (default: 50).
        :return: List of distances in metres (``nan`` for timeout/invalid).

        Example
        -------
        ```python
            >>> async_s[:].trigger()
            >>> dists = await async_s[:].result(timeout_ms=50)
            >>> for i, d in enumerate(dists):
            ...     if d == d:  # nan check
            ...         print(f"Sensor {i}: {d:.3f} m")
        ```
        """
        ...

    async def read(self, timeout_ms: int = 50) -> list[float]:
        """
        Trigger and await distance measurements for all sensors in the view.

        Triggers all PIO State Machines, yields once to the event loop,
        then waits for results.

        :param timeout_ms: Echo wait timeout in milliseconds (default: 50).
        :return: List of distances in metres (``nan`` for timeout/invalid).

        Example
        -------
        ```python
            >>> dists = await async_s[:].read()
            >>> for i, d in enumerate(dists):
            ...     print(f"Sensor {i}: {d:.3f} m")
        ```
        """
        ...

    def stream(
        self, count: int | None = None, interval_ms: int = 100
    ) -> AsyncIterator[list[float]]:
        """
        Async iterator yielding distance lists for all sensors in the view.

        :param count: Number of readings to yield. ``None`` for infinite.
        :param interval_ms: Minimum interval between readings in ms (default: 100).
        :return: Async iterator of ``list[float]`` in metres.

        Example
        -------
        ```python
            >>> async for dists in async_s[:].stream(count=5):
            ...     print(dists)
        ```
        """
        ...

    def __aiter__(self) -> AsyncIterator[list[float]]:
        """
        Default async iterator (infinite stream, 100 ms interval).

        Example
        -------
        ```python
            >>> async for dists in async_s[:]:
            ...     print(dists)
        ```
        """
        ...

    async def __anext__(self) -> list[float]:
        """
        Return the next list of distance readings.

        :return: List of distances in metres.

        Example
        -------
        ```python
            >>> dists = await async_s[:].__anext__()
        ```
        """
        ...
