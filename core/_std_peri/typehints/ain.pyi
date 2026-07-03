"""
Analog Input Driver. 

Allocation-conscious ADC API for single-channel and multi-channel analog input.
Scalar methods default to channel 0. View objects and view property result lists
are reused internally; copy returned lists when a long-lived snapshot is needed.

Example
-------
```python
    >>> from ain import Ain
    >>> ain = Ain([27, 28])
    >>> vr = ain.read()
    >>> cds = ain.read(idx=1)
    >>> values = ain[:].value.copy()
    >>> ain.deinit()
```
"""

class Ain:
    """
    Multi-channel analog input.

    :param pins: Single ADC pin number or list/tuple of ADC pin numbers.
    :param vref: ADC reference voltage used by voltage conversion.

    :raises ValueError: If no pin is provided.

    Example
    -------
    ```python
        >>> ain = Ain([27, 28], vref=3.3)
        >>> ain.read_voltage()
    ```
    """
    def __init__(self, pins: int | list[int] | tuple[int, ...], *, vref: float = 3.3, bits: int = 16) -> None:
        """
        Initialize ADC channel(s).

        :param pins: GPIO pin number or pin sequence.
        :param vref: Reference voltage used for `read_voltage()`.
        :param bits: ADC resolution. 16 for raw 16-bit output, 12 for 12-bit output.

        :raises ValueError: If `pins` is empty or `bits` is not 16 or 12.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28])           # default 16-bit
            >>> ain12 = Ain(27, bits=12)      # 12-bit
        ```
        """
        ...

    @property
    def bits(self) -> int:
        """
        ADC resolution configured at construction time.

        :return: 16 or 12.

        Example
        -------
        ```python
            >>> ain = Ain(27, bits=12)
            >>> ain.bits
            12
        ```
        """
        ...

    def __enter__(self) -> "Ain":
        """
        Enter context manager.

        :return: This Ain instance.

        Example
        -------
        ```python
            >>> with Ain(27) as ain:
            ...     ain.read()
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context manager and release ADC resources.

        :param exc_type: Exception type from the context body.
        :param exc_val: Exception value from the context body.
        :param exc_tb: Exception traceback from the context body.

        Example
        -------
        ```python
            >>> with Ain(27) as ain:
            ...     pass
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return number of ADC channels.

        :return: Channel count.

        Example
        -------
        ```python
            >>> len(Ain([27, 28]))
            2
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "Ain._View":
        """
        Get view for ADC channel(s).

        :param idx: Channel index or slice.
        :return: Reusable view for selected channel(s).

        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28])
            >>> ain[1].read()
            >>> values = ain[:].value
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Release ADC resources.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> ain.deinit()
        ```
        """
        ...

    def read(self, idx: int = 0) -> int:
        """
        Read one ADC channel scaled to the configured bit width.

        :param idx: Channel index. Defaults to channel 0.
        :return: ADC value in the range 0..(2**bits - 1).

        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> raw = ain.read()           # 0..65535
            >>> ain12 = Ain(27, bits=12)
            >>> raw12 = ain12.read()       # 0..4095
        ```
        """
        ...

    def read_percent(self, idx: int = 0) -> float:
        """
        Read one ADC channel as a percentage.

        :param idx: Channel index. Defaults to channel 0.
        :return: ADC value scaled to 0.0..100.0.

        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> pct = ain.read_percent()
        ```
        """
        ...

    def read_voltage(self, idx: int = 0) -> float:
        """
        Read one ADC channel as voltage.

        :param idx: Channel index. Defaults to channel 0.
        :return: ADC value scaled by `vref`.

        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28], vref=3.3)
            >>> volts = ain.read_voltage(idx=1)
        ```
        """
        ...

    def read_into(self, buf) -> list:
        """
        Read all channels into an existing mutable buffer.

        Values are scaled to the configured bit width.

        :param buf: Mutable buffer with at least `len(ain)` slots.
        :return: The same buffer object passed in `buf`.

        :raises ValueError: If `buf` is too short.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28], bits=12)
            >>> buf = [0, 0]
            >>> ain.read_into(buf)
            [1234, 2048]
        ```
        """
        ...

    def filtered(self, filt, samples: int = 10, *, idx: int = 0, interval_us: int = 100) -> float:
        """
        Feed channel readings into a filter object and return the final output.

        Each sample is read, scaled to the configured bit width, and passed to
        filt(value). The value returned by the last filt() call is returned.

        :param filt: Callable that accepts a numeric sample and returns a float.
                     Any ufilter.Base subclass (Alpha, MovingAverage, Median, …) works.
        :param samples: Number of samples to feed into the filter.
        :param idx: Channel index. Defaults to channel 0.
        :param interval_us: Delay between samples in microseconds.
        :return: Filtered output value from the last filt() call.

        :raises ValueError: If `samples` is less than 1.
        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> from ufilter import Alpha, MovingAverage
            >>> ain = Ain(27, bits=12)
            >>> stable = ain.filtered(Alpha(0.3), 20)
            >>> stable = ain.filtered(MovingAverage(8), 8)
        ```
        """
        ...

    def min_max(self, samples: int = 100, *, idx: int = 0, interval_us: int = 100) -> tuple[int, int]:
        """
        Measure the minimum and maximum values from one channel.

        :param samples: Number of samples to inspect.
        :param idx: Channel index. Defaults to channel 0.
        :param interval_us: Delay between samples in microseconds.
        :return: Tuple of (minimum, maximum) values at the configured bit width.

        :raises ValueError: If `samples` is less than 1.
        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain(27, bits=12)
            >>> lo, hi = ain.min_max(32)  # both in 0..4095
        ```
        """
        ...

    class _View:
        """
        Reusable view for selected ADC channels.

        View property getters return a reused list. Call `.copy()` when the
        values must be kept after the next read.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28])
            >>> values = ain[:].value.copy()
        ```
        """
        __slots__ = ("_p", "_i", "_cache")
        def __len__(self) -> int:
            """
            Return number of channels in this view.

            :return: View channel count.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> len(ain[:])
                2
            ```
            """
            ...

        def __getitem__(self, idx: int | slice) -> "Ain._View":
            """
            Get a narrower view from this view.

            :param idx: View-local channel index or slice.
            :return: Reusable view for the selected channel(s).

            :raises IndexError: If index is out of range.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> ain[:][0].read()
            ```
            """
            ...

        def read(self) -> int:
            """
            Read the selected single channel scaled to the configured bit width.

            :return: ADC value in the range 0..(2**bits - 1).

            :raises ValueError: If the view does not contain exactly one channel.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> raw = ain[0].read()
            ```
            """
            ...

        def read_percent(self) -> float:
            """
            Read the selected single channel as a percentage.

            :return: ADC value scaled to 0.0..100.0.

            :raises ValueError: If the view does not contain exactly one channel.

            Example
            -------
            ```python
                >>> ain = Ain(27)
                >>> pct = ain[0].read_percent()
            ```
            """
            ...

        def read_voltage(self) -> float:
            """
            Read the selected single channel as voltage.

            :return: ADC value scaled by the parent Ain reference voltage.

            :raises ValueError: If the view does not contain exactly one channel.

            Example
            -------
            ```python
                >>> ain = Ain(27, vref=3.3)
                >>> volts = ain[0].read_voltage()
            ```
            """
            ...

        def read_into(self, buf) -> list:
            """
            Read view channels into an existing mutable buffer.

            Values are scaled to the configured bit width.

            :param buf: Mutable buffer with at least `len(view)` slots.
            :return: The same buffer object passed in `buf`.

            :raises ValueError: If `buf` is too short.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28], bits=12)
                >>> buf = [0, 0]
                >>> ain[:].read_into(buf)
            ```
            """
            ...

        @property
        def value(self) -> list[int]:
            """
            Get selected channels as a reused list of values.

            Values are scaled to the configured bit width.

            :return: Reused list containing values in the range 0..(2**bits - 1).

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> values = ain[:].value.copy()
            ```
            """
            ...

        @property
        def percent(self) -> list[float]:
            """
            Get selected channels as a reused list of percentages.

            :return: Reused list containing values scaled to 0.0..100.0.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> values = ain[:].percent.copy()
            ```
            """
            ...

        @property
        def voltage(self) -> list[float]:
            """
            Get selected channels as a reused list of voltages.

            :return: Reused list containing values scaled by `vref`.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28], vref=3.3)
                >>> volts = ain[:].voltage.copy()
            ```
            """
            ...

        def filtered(self, filt, samples: int = 10, interval_us: int = 100) -> float:
            """
            Feed the selected single channel readings into a filter and return the final output.

            :param filt: Callable accepting a numeric sample and returning a float.
            :param samples: Number of samples to feed into the filter.
            :param interval_us: Delay between samples in microseconds.
            :return: Filtered output value from the last filt() call.

            :raises ValueError: If the view is not a single channel or `samples` is less than 1.

            Example
            -------
            ```python
                >>> from ufilter import Alpha
                >>> ain = Ain(27, bits=12)
                >>> stable = ain[0].filtered(Alpha(0.3), 20)
            ```
            """
            ...

        def min_max(self, samples: int = 100, interval_us: int = 100) -> tuple[int, int]:
            """
            Measure minimum and maximum values from the selected single channel.

            :param samples: Number of samples to inspect.
            :param interval_us: Delay between samples in microseconds.
            :return: Tuple of (minimum, maximum) values at the configured bit width.

            :raises ValueError: If the view is not a single channel or `samples` is less than 1.

            Example
            -------
            ```python
                >>> ain = Ain(27, bits=12)
                >>> lo, hi = ain[0].min_max(32)  # both in 0..4095
            ```
            """
            ...
