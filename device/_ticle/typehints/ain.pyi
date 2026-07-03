"""
TiCLE Analog Input Driver.

Allocation-conscious ADC API for single-channel and multi-channel analog input.
Scalar methods default to channel 0. View objects and view property result lists
are reused internally; copy returned lists when a long-lived snapshot is needed.
TiCLE boards also provide RP2 DMA burst and continuous sampling helpers.

Example
-------
```python
    >>> from ticle_lite.ain import Ain
    >>> ain = Ain([27, 28])
    >>> vr = ain.read_u12()
    >>> cds = ain.read_u12(idx=1)
    >>> values = ain[:].value_u12.copy()
    >>> ain.deinit()
```
"""

from typing import Callable
import array

class Ain:
    """
    TiCLE multi-channel analog input.

    :param pins: Single ADC pin number or list/tuple of ADC pin numbers.
    :param vref: ADC reference voltage used by voltage conversion.

    :raises ValueError: If no pin is provided or a pin is not ADC-capable.
    :raises OSError: If ADC initialization fails.

    Example
    -------
    ```python
        >>> ain = Ain([27, 28], vref=3.3)
        >>> ain.read_voltage()
    ```
    """
    _FULL_RANGE: int
    _ADC_BITS: int
    _DEFAULT_VREF: float

    def __init__(self, pins: int | list[int] | tuple[int, ...], *, vref: float = 3.3) -> None:
        """
        Initialize TiCLE ADC channel(s).

        :param pins: ADC GPIO pin number or pin sequence. RP2 ADC pins are 26..29.
        :param vref: Reference voltage used for `read_voltage()`.

        :raises ValueError: If `pins` is empty or contains a non-ADC pin.
        :raises OSError: If the ADC hardware cannot be initialized.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28])
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
            ...     ain.read_u12()
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context manager and release ADC/DMA resources.

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
        :raises TypeError: If index is not int or slice.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28])
            >>> ain[1].read_u12()
            >>> values = ain[:].value_u12
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Stop DMA sampling and release ADC/DMA resources.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> ain.deinit()
        ```
        """
        ...

    def read_u16(self, idx: int = 0) -> int:
        """
        Read one ADC channel as a raw 16-bit value.

        :param idx: Channel index. Defaults to channel 0.
        :return: Raw ADC value in the range 0..65535.

        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28])
            >>> raw = ain.read_u16()
            >>> raw2 = ain.read_u16(idx=1)
        ```
        """
        ...

    def read_u12(self, idx: int = 0) -> int:
        """
        Read one ADC channel as a 12-bit value.

        :param idx: Channel index. Defaults to channel 0.
        :return: ADC value in the range 0..4095.

        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28])
            >>> vr = ain.read_u12()
            >>> cds = ain.read_u12(idx=1)
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
        :return: ADC value scaled by per-channel reference, offset, and scale.

        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28], vref=3.3)
            >>> volts = ain.read_voltage(idx=1)
        ```
        """
        ...

    def read_into(self, buf, *, bits: int = 16):
        """
        Read all channels into an existing mutable buffer.

        :param buf: Mutable buffer with at least `len(ain)` slots.
        :param bits: Output resolution. Use 16 for raw u16 or another value for u12.
        :return: The same buffer object passed in `buf`.

        :raises ValueError: If `buf` is too short.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28])
            >>> buf = [0, 0]
            >>> ain.read_into(buf, bits=12)
            [1234, 2048]
        ```
        """
        ...

    def filtered_u16(self, samples: int = 10, *, idx: int = 0, interval_us: int = 100) -> int:
        """
        Read one channel repeatedly and return the average 16-bit value.

        :param samples: Number of samples to average.
        :param idx: Channel index. Defaults to channel 0.
        :param interval_us: Delay between samples in microseconds.
        :return: Average raw ADC value in the range 0..65535.

        :raises ValueError: If `samples` is less than 1.
        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> stable = ain.filtered_u16(8)
        ```
        """
        ...

    def filtered_u12(self, samples: int = 10, *, idx: int = 0, interval_us: int = 100) -> int:
        """
        Read one channel repeatedly and return the average 12-bit value.

        :param samples: Number of samples to average.
        :param idx: Channel index. Defaults to channel 0.
        :param interval_us: Delay between samples in microseconds.
        :return: Average ADC value in the range 0..4095.

        :raises ValueError: If `samples` is less than 1.
        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain([27, 28])
            >>> stable = ain.filtered_u12(8, idx=1)
        ```
        """
        ...

    def min_max_u16(self, samples: int = 100, *, idx: int = 0, interval_us: int = 100) -> tuple[int, int]:
        """
        Measure the minimum and maximum 16-bit values from one channel.

        :param samples: Number of samples to inspect.
        :param idx: Channel index. Defaults to channel 0.
        :param interval_us: Delay between samples in microseconds.
        :return: Tuple of `(minimum, maximum)` raw values.

        :raises ValueError: If `samples` is less than 1.
        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> lo, hi = ain.min_max_u16(32)
        ```
        """
        ...

    def start_continuous(self, channel: int, buffer: array.array, *, rate: int = 100_000, callback: Callable[[array.array], None] | None = None) -> None:
        """
        Start RP2350 DMA sampling into an existing unsigned-short array buffer.

        :param channel: ADC channel index in this Ain object.
        :param buffer: Destination `array.array('H')` buffer.
        :param rate: Sampling rate in Hz. Valid range is 1..500000.
        :param callback: Optional callback scheduled with the filled buffer.

        :raises RuntimeError: If DMA sampling is already running.
        :raises ValueError: If channel or rate is invalid.
        :raises TypeError: If buffer is not `array.array('H')`.

        Example
        -------
        ```python
            >>> import array
            >>> ain = Ain(27)
            >>> buf = array.array('H', [0] * 128)
            >>> ain.start_continuous(0, buf, rate=20000)
            >>> ain.stop_continuous()
        ```
        """
        ...

    def stop_continuous(self) -> None:
        """
        Stop RP2 DMA sampling if it is running.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> ain.stop_continuous()
        ```
        """
        ...

    @property
    def is_running(self) -> bool:
        """
        Return whether DMA sampling is active.

        :return: True while DMA sampling is running.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> running = ain.is_running
        ```
        """
        ...

    @property
    def samples_remaining(self) -> int:
        """
        Return remaining DMA transfer count.

        :return: Remaining sample count, or 0 when DMA is stopped.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> left = ain.samples_remaining
        ```
        """
        ...

    def read_burst(self, channel: int, count: int, *, rate: int = 100_000) -> array.array:
        """
        Capture a blocking DMA burst as raw 16-bit samples.

        :param channel: ADC channel index in this Ain object.
        :param count: Number of samples to capture.
        :param rate: Sampling rate in Hz. Valid range is 1..500000.
        :return: New `array.array('H')` containing captured samples.

        :raises RuntimeError: If DMA sampling is already running.
        :raises ValueError: If channel or rate is invalid.
        :raises TypeError: If the internal DMA buffer type is invalid.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> raw = ain.read_burst(0, 128, rate=20000)
        ```
        """
        ...

    def read_burst_voltage(self, channel: int, count: int, *, rate: int = 100_000) -> list[float]:
        """
        Capture a blocking DMA burst and convert samples to voltages.

        :param channel: ADC channel index in this Ain object.
        :param count: Number of samples to capture.
        :param rate: Sampling rate in Hz. Valid range is 1..500000.
        :return: New list of voltage values.

        :raises RuntimeError: If DMA sampling is already running.
        :raises ValueError: If channel or rate is invalid.
        :raises TypeError: If the internal DMA buffer type is invalid.

        Example
        -------
        ```python
            >>> ain = Ain(27)
            >>> volts = ain.read_burst_voltage(0, 128, rate=20000)
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
            >>> values = ain[:].value_u12.copy()
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
                >>> ain[:][0].read_u12()
            ```
            """
            ...

        def read_u16(self) -> int:
            """
            Read the selected single channel as a raw 16-bit value.

            :return: Raw ADC value in the range 0..65535.

            :raises ValueError: If the view does not contain exactly one channel.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> raw = ain[0].read_u16()
            ```
            """
            ...

        def read_u12(self) -> int:
            """
            Read the selected single channel as a 12-bit value.

            :return: ADC value in the range 0..4095.

            :raises ValueError: If the view does not contain exactly one channel.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> raw = ain[0].read_u12()
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

            :return: ADC value scaled by reference voltage, offset, and scale.

            :raises ValueError: If the view does not contain exactly one channel.

            Example
            -------
            ```python
                >>> ain = Ain(27, vref=3.3)
                >>> volts = ain[0].read_voltage()
            ```
            """
            ...

        def read_into(self, buf, *, bits: int = 16):
            """
            Read view channels into an existing mutable buffer.

            :param buf: Mutable buffer with at least `len(view)` slots.
            :param bits: Output resolution. Use 16 for raw u16 or another value for u12.
            :return: The same buffer object passed in `buf`.

            :raises ValueError: If `buf` is too short.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> buf = [0, 0]
                >>> ain[:].read_into(buf, bits=12)
            ```
            """
            ...

        @property
        def value_u16(self) -> list[int]:
            """
            Get selected channels as a reused list of 16-bit values.

            :return: Reused list containing raw values in the range 0..65535.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> values = ain[:].value_u16.copy()
            ```
            """
            ...

        @property
        def value_u12(self) -> list[int]:
            """
            Get selected channels as a reused list of 12-bit values.

            :return: Reused list containing values in the range 0..4095.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> values = ain[:].value_u12.copy()
            ```
            """
            ...

        @property
        def value_percent(self) -> list[float]:
            """
            Get selected channels as a reused list of percentages.

            :return: Reused list containing values scaled to 0.0..100.0.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28])
                >>> values = ain[:].value_percent.copy()
            ```
            """
            ...

        @property
        def voltage(self) -> list[float]:
            """
            Get selected channels as a reused list of voltages.

            :return: Reused list containing voltage values.

            Example
            -------
            ```python
                >>> ain = Ain([27, 28], vref=3.3)
                >>> volts = ain[:].voltage.copy()
            ```
            """
            ...

        def filtered_u16(self, samples: int = 10, interval_us: int = 100) -> int:
            """
            Read the selected single channel repeatedly and average raw values.

            :param samples: Number of samples to average.
            :param interval_us: Delay between samples in microseconds.
            :return: Average raw ADC value in the range 0..65535.

            :raises ValueError: If the view is not a single channel or `samples` is less than 1.

            Example
            -------
            ```python
                >>> ain = Ain(27)
                >>> stable = ain[0].filtered_u16(8)
            ```
            """
            ...

        def filtered_u12(self, samples: int = 10, interval_us: int = 100) -> int:
            """
            Read the selected single channel repeatedly and average 12-bit values.

            :param samples: Number of samples to average.
            :param interval_us: Delay between samples in microseconds.
            :return: Average ADC value in the range 0..4095.

            :raises ValueError: If the view is not a single channel or `samples` is less than 1.

            Example
            -------
            ```python
                >>> ain = Ain(27)
                >>> stable = ain[0].filtered_u12(8)
            ```
            """
            ...

        def min_max_u16(self, samples: int = 100, interval_us: int = 100) -> tuple[int, int]:
            """
            Measure minimum and maximum values from the selected single channel.

            :param samples: Number of samples to inspect.
            :param interval_us: Delay between samples in microseconds.
            :return: Tuple of `(minimum, maximum)` raw 16-bit values.

            :raises ValueError: If the view is not a single channel or `samples` is less than 1.

            Example
            -------
            ```python
                >>> ain = Ain(27)
                >>> lo, hi = ain[0].min_max_u16(32)
            ```
            """
            ...

        def read_burst(self, count: int, *, rate: int = 100_000) -> array.array:
            """
            Capture a blocking DMA burst from the selected single channel.

            :param count: Number of samples to capture.
            :param rate: Sampling rate in Hz. Valid range is 1..500000.
            :return: New `array.array('H')` containing captured samples.

            :raises ValueError: If the view is not a single channel or rate is invalid.
            :raises RuntimeError: If DMA sampling is already running.

            Example
            -------
            ```python
                >>> ain = Ain(27)
                >>> raw = ain[0].read_burst(128, rate=20000)
            ```
            """
            ...

        def read_burst_voltage(self, count: int, *, rate: int = 100_000) -> list[float]:
            """
            Capture a blocking DMA burst from the selected channel as voltages.

            :param count: Number of samples to capture.
            :param rate: Sampling rate in Hz. Valid range is 1..500000.
            :return: New list containing voltage values.

            :raises ValueError: If the view is not a single channel or rate is invalid.
            :raises RuntimeError: If DMA sampling is already running.

            Example
            -------
            ```python
                >>> ain = Ain(27)
                >>> volts = ain[0].read_burst_voltage(128, rate=20000)
            ```
            """
            ...
