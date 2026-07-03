"""
Async Analog Input Helpers.

Asyncio wrapper for Ain threshold waits, filtering, and monitor streams.

Example
-------
```python
    >>> async_ain = AsyncAin(Ain([27, 28]))
    >>> value = await async_ain.wait_for_threshold(3000)
```
"""
from typing import AsyncIterator
from ain import Ain

class AsyncAin:
    """Async wrapper around Ain.

    Example
    -------
    ```python
        >>> adc = AsyncAin(Ain(27))
    ```
    """
    def __init__(self, ain: Ain) -> None:
        """Wrap an Ain instance.

        :param ain: Ain object to wrap.
        
        Example
        -------
        ```python
            >>> adc = AsyncAin(Ain(27))
        ```
        """
        ...

    def __enter__(self) -> "AsyncAin":
        """Enter context manager.

        :return: Self.
        
        Example
        -------
        ```python
            >>> with AsyncAin(Ain(27)) as adc:
            ...     adc.read()
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and deinitialize wrapped Ain.

        Example
        -------
        ```python
            >>> with AsyncAin(Ain(27)) as adc:
            ...     pass
        ```
        """
        ...

    def __len__(self) -> int:
        """Return channel count.

        :return: Number of channels.
        
        Example
        -------
        ```python
            >>> len(adc)
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "AsyncAinView":
        """Get async view for selected channel(s).

        :param idx: Channel index or slice.
        :return: Async view.
        
        Example
        -------
        ```python
            >>> adc[0].read()
        ```
        """
        ...

    @property
    def ain(self) -> Ain:
        """Get wrapped Ain instance.

        :return: Ain object.
        
        Example
        -------
        ```python
            >>> adc.ain.read_u12()
        ```
        """
        ...

    def read(self, idx: int = 0) -> int:
        """Read value scaled to configured bit width.

        :param idx: Channel index.
        :return: ADC value in range 0..(2**bits - 1).
        
        Example
        -------
        ```python
            >>> adc.read()
        ```
        """
        ...

    def read_percent(self, idx: int = 0) -> float:
        """Read percent value immediately.

        :param idx: Channel index.
        :return: Percent value.
        
        Example
        -------
        ```python
            >>> adc.read_percent()
        ```
        """
        ...

    def read_voltage(self, idx: int = 0) -> float:
        """Read voltage immediately.

        :param idx: Channel index.
        :return: Voltage.
        
        Example
        -------
        ```python
            >>> adc.read_voltage()
        ```
        """
        ...

    async def filtered(self, samples: int = 10, *, idx: int = 0, interval_ms: int = 1) -> int:
        """Return async averaged samples.

        :param samples: Number of samples.
        :param idx: Channel index.
        :param interval_ms: Delay between samples in milliseconds.
        :return: Average value at configured bit width.
        
        Example
        -------
        ```python
            >>> value = await adc.filtered(8)
        ```
        """
        ...

    async def wait_for_threshold(self, threshold: int, *, idx: int = 0, above: bool = True, poll_ms: int = 10) -> int:
        """Wait until a channel crosses a threshold.

        :param threshold: Threshold value at the configured bit width.
        :param above: True for greater-than, False for less-than.
        :param idx: Channel index.
        :param poll_ms: Poll interval in milliseconds.
        :return: Value that satisfied the condition.
        
        Example
        -------
        ```python
            >>> value = await adc.wait_for_threshold(3000)
        ```
        """
        ...

    async def wait_for_threshold_timeout(self, threshold: int, timeout_ms: int, *, idx: int = 0, above: bool = True, poll_ms: int = 10) -> int | None:
        """Wait for threshold with timeout.

        :param threshold: Threshold value at the configured bit width.
        :param timeout_ms: Timeout in milliseconds.
        :param above: True for greater-than, False for less-than.
        :param idx: Channel index.
        :param poll_ms: Poll interval in milliseconds.
        :return: Matching value, or None on timeout.
        
        Example
        -------
        ```python
            >>> value = await adc.wait_for_threshold_timeout(3000, 1000)
        ```
        """
        ...

    def monitor(self, idx: int = 0, *, interval_ms: int = 100) -> AsyncIterator[int]:
        """Return async iterator of sampled values.

        :param idx: Channel index.
        :param interval_ms: Sampling interval in milliseconds.
        :return: Async iterator yielding values at the configured bit width.
        
        Example
        -------
        ```python
            >>> async for value in adc.monitor():
            ...     print(value)
        ```
        """
        ...

class AsyncAinView:
    """Async wrapper around an Ain view.

    Example
    -------
    ```python
        >>> view = AsyncAin(Ain([27, 28]))[0]
    ```
    """
    def __init__(self, view: Ain._View) -> None:
        """Wrap an Ain view.

        :param view: Ain view.
        
        Example
        -------
        ```python
            >>> view = AsyncAinView(ain[0])
        ```
        """
        ...

    def __len__(self) -> int:
        """Return view channel count.

        :return: Channel count.
        
        Example
        -------
        ```python
            >>> len(view)
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "AsyncAinView":
        """Return narrowed async view.

        :param idx: View-relative index or slice.
        :return: Async view.
        
        Example
        -------
        ```python
            >>> view[0].read()
        ```
        """
        ...

    def read(self) -> int:
        """Read selected single channel scaled to configured bit width.

        :return: ADC value in range 0..(2**bits - 1).
        
        Example
        -------
        ```python
            >>> view.read()
        ```
        """
        ...

    def read_percent(self) -> float:
        """Read selected single channel as percent.

        :return: Percent value.
        
        Example
        -------
        ```python
            >>> view.read_percent()
        ```
        """
        ...

    def read_voltage(self) -> float:
        """Read selected single channel as voltage.

        :return: Voltage.
        
        Example
        -------
        ```python
            >>> view.read_voltage()
        ```
        """
        ...

    async def filtered(self, filt, samples: int = 10, interval_ms: int = 1) -> float:
        """Feed selected channel readings into a filter object asynchronously.

        :param filt: Callable accepting a numeric sample and returning a float.
        :param samples: Number of samples to feed into the filter.
        :param interval_ms: Delay between samples in milliseconds.
        :return: Filtered output value from the last filt() call.
        
        Example
        -------
        ```python
            >>> from ufilter import Alpha
            >>> value = await view.filtered(Alpha(0.3), 20)
        ```
        """
        ...

    async def wait_for_threshold(self, threshold: int, *, above: bool = True, poll_ms: int = 10) -> int:
        """Wait for selected channel to cross threshold.

        :param threshold: Threshold value at the configured bit width.
        :param above: True for greater-than, False for less-than.
        :param poll_ms: Poll interval in milliseconds.
        :return: Matching value.
        
        Example
        -------
        ```python
            >>> value = await view.wait_for_threshold(3000)
        ```
        """
        ...

    async def wait_for_threshold_timeout(self, threshold: int, timeout_ms: int, *, above: bool = True, poll_ms: int = 10) -> int | None:
        """Wait for threshold with timeout.

        :param threshold: Threshold value at the configured bit width.
        :param timeout_ms: Timeout in milliseconds.
        :param above: True for greater-than, False for less-than.
        :param poll_ms: Poll interval in milliseconds.
        :return: Matching value or None.
        
        Example
        -------
        ```python
            >>> value = await view.wait_for_threshold_timeout(3000, 1000)
        ```
        """
        ...

    def monitor(self, *, interval_ms: int = 100) -> AsyncIterator[int]:
        """Return async iterator for selected channel.

        :param interval_ms: Sampling interval in milliseconds.
        :return: Async iterator yielding values at the configured bit width.
        
        Example
        -------
        ```python
            >>> async for value in view.monitor():
            ...     print(value)
        ```
        """
        ...
