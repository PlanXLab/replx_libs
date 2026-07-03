"""
Async Digital GPIO Helpers.

Asyncio wrappers around Din, Dout, and Dio for cooperative waits, event streams,
blinking, and pulses.

Example
-------
```python
    >>> button = AsyncDin(Din(17))
    >>> led = AsyncDout(Dout(25))
    >>> await button[0].wait_for_edge()
    >>> await led[0].pulse(100)
```
"""
from typing import AsyncIterator
from dio import Din, Dout, Dio

class AsyncDin:
    """Async wrapper around Din.

    Example
    -------
    ```python
        >>> button = AsyncDin(Din(17))
    ```
    """
    def __init__(self, din: Din) -> None:
        """Wrap a Din instance.

        :param din: Digital input object.
        
        Example
        -------
        ```python
            >>> button = AsyncDin(Din(17))
        ```
        """
        ...

    def __enter__(self) -> "AsyncDin":
        """Enter context manager.

        :return: Self.
        
        Example
        -------
        ```python
            >>> with AsyncDin(Din(17)) as button:
            ...     button.read()
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and deinitialize wrapped Din.

        Example
        -------
        ```python
            >>> with AsyncDin(Din(17)) as button:
            ...     pass
        ```
        """
        ...

    def __len__(self) -> int:
        """Return input count.

        :return: Number of input pins.
        
        Example
        -------
        ```python
            >>> len(button)
        ```
        """
        ...

    def __getitem__(self, idx: int) -> "AsyncDinView":
        """Get async view for one input pin.

        :param idx: Pin index.
        :return: AsyncDinView.
        
        Example
        -------
        ```python
            >>> await button[0].wait_for_edge()
        ```
        """
        ...

    @property
    def din(self) -> Din:
        """Get wrapped Din.

        :return: Din instance.
        
        Example
        -------
        ```python
            >>> button.din.read()
        ```
        """
        ...

    def read(self, idx: int = 0) -> int:
        """Read an input immediately.

        :param idx: Pin index.
        :return: Pin value.
        
        Example
        -------
        ```python
            >>> button.read()
        ```
        """
        ...

    async def wait_for_value(self, idx: int = 0, target: int = 1, poll_ms: int = 1) -> bool:
        """Wait until an input reaches a target value.

        :param idx: Pin index.
        :param target: Target value.
        :param poll_ms: Poll interval.
        :return: True when reached.
        
        Example
        -------
        ```python
            >>> await button.wait_for_value(target=1)
        ```
        """
        ...

    async def wait_for_value_timeout(self, idx: int = 0, target: int = 1, timeout_ms: int = 1000, poll_ms: int = 1) -> bool:
        """Wait for a value with timeout.

        :param timeout_ms: Timeout in milliseconds.
        :return: True if reached, False on timeout.
        
        Example
        -------
        ```python
            >>> ok = await button.wait_for_value_timeout(timeout_ms=1000)
        ```
        """
        ...

    def events(self, idx: int = 0, edge: int = ...) -> AsyncIterator[int]:
        """Return async edge event iterator.

        :param idx: Pin index.
        :param edge: Edge mask.
        :return: Async iterator yielding pin values.
        
        Example
        -------
        ```python
            >>> async for value in button.events():
            ...     print(value)
        ```
        """
        ...

class AsyncDinView:
    """Async single-input view.

    Example
    -------
    ```python
        >>> view = AsyncDin(Din(17))[0]
    ```
    """
    def __init__(self, din: Din, idx: int) -> None:
        """Create async input view.

        :param din: Wrapped input object.
        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> view = AsyncDinView(sw, 0)
        ```
        """
        ...

    def read(self) -> int:
        """Read selected input.

        :return: Pin value.
        
        Example
        -------
        ```python
            >>> view.read()
        ```
        """
        ...

    async def wait_for_value(self, target: int = 1, poll_ms: int = 1) -> bool:
        """Wait until selected input reaches target.

        :param target: Target value.
        :return: True when reached.
        
        Example
        -------
        ```python
            >>> await view.wait_for_value(1)
        ```
        """
        ...

    async def wait_for_value_timeout(self, target: int = 1, timeout_ms: int = 1000, poll_ms: int = 1) -> bool:
        """Wait for selected input with timeout.

        :param timeout_ms: Timeout in milliseconds.
        :return: True if reached, False on timeout.
        
        Example
        -------
        ```python
            >>> ok = await view.wait_for_value_timeout(1, 1000)
        ```
        """
        ...

    async def wait_for_edge(self, edge: int = ...) -> bool:
        """Wait for selected input edge.

        :param edge: Edge mask.
        :return: True when edge occurs.
        
        Example
        -------
        ```python
            >>> await view.wait_for_edge(Din.CB_RISING)
        ```
        """
        ...

    async def wait_for_edge_timeout(self, edge: int = ..., timeout_ms: int = 1000) -> bool:
        """Wait for selected input edge with timeout.

        :param timeout_ms: Timeout in milliseconds.
        :return: True if edge occurs, False on timeout.
        
        Example
        -------
        ```python
            >>> ok = await view.wait_for_edge_timeout(timeout_ms=1000)
        ```
        """
        ...

    def events(self, edge: int = ...) -> AsyncIterator[int]:
        """Return selected input event iterator.

        :param edge: Edge mask.
        :return: Async iterator yielding values.
        
        Example
        -------
        ```python
            >>> async for value in view.events():
            ...     print(value)
        ```
        """
        ...

class AsyncDout:
    """Async wrapper around Dout.

    Example
    -------
    ```python
        >>> led = AsyncDout(Dout(25))
    ```
    """
    def __init__(self, dout: Dout) -> None:
        """Wrap a Dout instance.

        :param dout: Digital output object.
        
        Example
        -------
        ```python
            >>> led = AsyncDout(Dout(25))
        ```
        """
        ...

    def __enter__(self) -> "AsyncDout":
        """Enter context manager.

        :return: Self.
        
        Example
        -------
        ```python
            >>> with AsyncDout(Dout(25)) as led:
            ...     led.write(1)
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and deinitialize wrapped Dout.

        Example
        -------
        ```python
            >>> with AsyncDout(Dout(25)) as led:
            ...     pass
        ```
        """
        ...

    def __len__(self) -> int:
        """Return output count.

        :return: Number of output pins.
        
        Example
        -------
        ```python
            >>> len(led)
        ```
        """
        ...

    def __getitem__(self, idx: int) -> "AsyncDoutView":
        """Get async view for one output.

        :param idx: Pin index.
        :return: AsyncDoutView.
        
        Example
        -------
        ```python
            >>> await led[0].blink(count=3)
        ```
        """
        ...

    @property
    def dout(self) -> Dout:
        """Get wrapped Dout.

        :return: Dout instance.
        
        Example
        -------
        ```python
            >>> led.dout.write(1)
        ```
        """
        ...

    def write(self, value: int = 1, idx: int = 0) -> None:
        """Write output immediately.

        :param value: Output value.
        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> led.write(1)
        ```
        """
        ...

    async def blink(self, idx: int = 0, on_ms: int = 500, off_ms: int = 500, count: int = 0) -> None:
        """Blink an output asynchronously.

        :param idx: Pin index.
        :param count: Number of blinks, or 0 forever.
        
        Example
        -------
        ```python
            >>> await led.blink(count=3)
        ```
        """
        ...

    async def pulse(self, idx: int = 0, duration_ms: int = 10, value: int = 1) -> None:
        """Pulse an output asynchronously.

        :param idx: Pin index.
        :param duration_ms: Pulse duration.
        
        Example
        -------
        ```python
            >>> await led.pulse(duration_ms=100)
        ```
        """
        ...

class AsyncDoutView:
    """Async single-output view.

    Example
    -------
    ```python
        >>> view = AsyncDout(Dout(25))[0]
    ```
    """
    def __init__(self, dout: Dout, idx: int) -> None:
        """Create async output view.

        :param dout: Wrapped output object.
        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> view = AsyncDoutView(led, 0)
        ```
        """
        ...

    def write(self, value: int = 1) -> None:
        """Write selected output.

        :param value: Output value.
        
        Example
        -------
        ```python
            >>> view.write(1)
        ```
        """
        ...

    def read(self) -> int:
        """Read selected output.

        :return: Output value.
        
        Example
        -------
        ```python
            >>> view.read()
        ```
        """
        ...

    def toggle(self) -> None:
        """Toggle selected output.

        Example
        -------
        ```python
            >>> view.toggle()
        ```
        """
        ...

    async def blink(self, on_ms: int = 500, off_ms: int = 500, count: int = 0) -> None:
        """Blink selected output asynchronously.

        :param count: Number of blinks, or 0 forever.
        
        Example
        -------
        ```python
            >>> await view.blink(count=3)
        ```
        """
        ...

    async def pulse(self, duration_ms: int = 10, value: int = 1) -> None:
        """Pulse selected output asynchronously.

        :param duration_ms: Pulse duration.
        
        Example
        -------
        ```python
            >>> await view.pulse(100)
        ```
        """
        ...

class AsyncDio:
    """Async wrapper around Dio.

    Example
    -------
    ```python
        >>> pins = AsyncDio(Dio(16))
    ```
    """
    def __init__(self, dio: Dio) -> None:
        """Wrap a Dio instance.

        :param dio: Bidirectional pin object.
        
        Example
        -------
        ```python
            >>> pins = AsyncDio(Dio(16))
        ```
        """
        ...

    def __enter__(self) -> "AsyncDio":
        """Enter context manager.

        :return: Self.
        
        Example
        -------
        ```python
            >>> with AsyncDio(Dio(16)) as pins:
            ...     pins.read()
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and deinitialize wrapped Dio.

        Example
        -------
        ```python
            >>> with AsyncDio(Dio(16)) as pins:
            ...     pass
        ```
        """
        ...

    def __len__(self) -> int:
        """Return pin count.

        :return: Number of pins.
        
        Example
        -------
        ```python
            >>> len(pins)
        ```
        """
        ...

    def __getitem__(self, idx: int) -> "AsyncDioView":
        """Get async view for one bidirectional pin.

        :param idx: Pin index.
        :return: AsyncDioView.
        
        Example
        -------
        ```python
            >>> pins[0].write(1)
        ```
        """
        ...

    @property
    def dio(self) -> Dio:
        """Get wrapped Dio.

        :return: Dio instance.
        
        Example
        -------
        ```python
            >>> pins.dio.read()
        ```
        """
        ...

    def read(self, idx: int = 0) -> int:
        """Read a pin immediately.

        :param idx: Pin index.
        :return: Pin value.
        
        Example
        -------
        ```python
            >>> pins.read()
        ```
        """
        ...

    def write(self, value: int = 1, idx: int = 0) -> None:
        """Write a pin immediately.

        :param value: Output value.
        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> pins.write(1)
        ```
        """
        ...

class AsyncDioView:
    """Async single-Dio view.

    Example
    -------
    ```python
        >>> view = AsyncDio(Dio(16))[0]
    ```
    """
    def __init__(self, dio: Dio, idx: int) -> None:
        """Create async Dio view.

        :param dio: Wrapped Dio object.
        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> view = AsyncDioView(pin, 0)
        ```
        """
        ...

    def read(self) -> int:
        """Read selected pin.

        :return: Pin value.
        
        Example
        -------
        ```python
            >>> view.read()
        ```
        """
        ...

    def write(self, value: int = 1) -> None:
        """Write selected pin.

        :param value: Output value.
        
        Example
        -------
        ```python
            >>> view.write(1)
        ```
        """
        ...

    def toggle(self) -> None:
        """Toggle selected pin.

        Example
        -------
        ```python
            >>> view.toggle()
        ```
        """
        ...
