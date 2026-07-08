"""
PIO Capture Module

High-speed GPIO capture using RP2040/RP2350 PIO and DMA.
Captures edge events or continuous samples at rates up to 125 MHz with
zero CPU overhead during acquisition.

Features:

- Edge detection: rising, falling, or both edges
- Continuous single-pin or 8-pin parallel sampling at configurable rate
- DMA transfer for zero-CPU-load capture
- Optional async callback on capture complete

Use cases:

- Logic analyzer functionality
- Protocol decoding (UART, SPI bit-banging)
- Pulse-width measurement and frequency counting
- High-speed event logging (up to 125 MHz)

"""

import array
from typing import Callable


class PioCapture:
    """
    PIO-based high-speed GPIO capture.

    Uses an RP2040/RP2350 PIO state machine and DMA channel to capture GPIO
    events or continuous samples with minimal CPU overhead.  Capture modes
    select which edge(s) trigger a sample or enable continuous or parallel
    sampling.

    :param pin: GPIO pin number, or list of up to 8 pins for parallel mode.
    :param mode: Capture mode constant - one of ``RISING``, ``FALLING``,
        ``BOTH``, ``CONTINUOUS``, or ``PARALLEL``.

    :raises ValueError: If pin configuration is invalid for the selected mode.
    :raises RuntimeError: If no free state machines are available.

    Example
    -------
    ```python
        >>> import array
        >>> from ticle_lite.pio_capture import PioCapture
        >>>
        >>> # Edge capture - count rising edges on pin 15
        >>> cap = PioCapture(pin=15, mode=PioCapture.RISING)
        >>> buf = array.array('I', [0] * 500)
        >>> cap.start(buf)
        >>> cap.wait(timeout_ms=5000)
        >>> cap.stop()
        >>> print(f"Captured {cap.bytes_captured()} bytes")
        >>>
        >>> # Parallel 8-bit capture
        >>> cap8 = PioCapture(pin=[0, 1, 2, 3, 4, 5, 6, 7], mode=PioCapture.PARALLEL)
        >>> cap8.deinit()
    ```
    """

    RISING: int
    """Capture on rising edge (low-to-high transition)."""

    FALLING: int
    """Capture on falling edge (high-to-low transition)."""

    BOTH: int
    """Capture on any edge (both rising and falling transitions)."""

    CONTINUOUS: int
    """Continuous sampling at a fixed rate."""

    PARALLEL: int
    """Capture 8 pins simultaneously as a byte per sample."""

    def __init__(
        self,
        pin: int | list[int],
        *,
        mode: int = 0,
    ) -> None:
        """
        Initialize PIO capture on one or more GPIO pins.

        :param pin: GPIO pin number, or list of pins for parallel mode.
        :param mode: Capture mode - ``RISING``, ``FALLING``, ``BOTH``,
            ``CONTINUOUS``, or ``PARALLEL`` (default: ``RISING``).

        :raises ValueError: If pin list is empty or exceeds 8 pins in
            parallel mode.
        :raises RuntimeError: If no free state machines are available.

        Example
        -------
        ```python
            >>> cap = PioCapture(pin=15, mode=PioCapture.RISING)
            >>> cap8 = PioCapture(pin=[0, 1, 2, 3, 4, 5, 6, 7],
            ...                   mode=PioCapture.PARALLEL)
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Stop capture and release PIO and DMA resources.

        Safe to call even if capture is not running.  Called automatically
        when using the context-manager interface.

        Example
        -------
        ```python
            >>> cap = PioCapture(pin=15, mode=PioCapture.RISING)
            >>> cap.deinit()
        ```
        """
        ...

    def __enter__(self) -> "PioCapture":
        """
        Return ``self`` for use as a context manager.

        :return: This ``PioCapture`` instance.

        Example
        -------
        ```python
            >>> with PioCapture(pin=15, mode=PioCapture.RISING) as cap:
            ...     buf = array.array('I', [0] * 500)
            ...     cap.start(buf)
            ...     cap.wait(timeout_ms=3000)
        ```
        """
        ...

    def __exit__(self, *args) -> None:
        """
        Call ``deinit()`` when leaving the ``with`` block.

        :param args: Exception info forwarded from the context manager protocol.

        Example
        -------
        ```python
            >>> with PioCapture(pin=15) as cap:
            ...     pass    # deinit() called automatically on exit
        ```
        """
        ...

    def set_freq(self, freq: int) -> None:
        """
        Set the PIO state machine clock frequency.

        Controls the capture sample rate in ``CONTINUOUS`` mode and the
        edge-detection resolution in edge-triggered modes.

        :param freq: Frequency in Hz (1-125 000 000).

        :raises ValueError: If *freq* is outside 1-125 000 000 Hz.
        :raises RuntimeError: If the state machine is not initialized.

        Example
        -------
        ```python
            >>> cap = PioCapture(pin=15, mode=PioCapture.CONTINUOUS)
            >>> cap.set_freq(1_000_000)    # 1 MHz sample rate
            >>> cap.set_freq(125_000_000)  # Maximum rate
        ```
        """
        ...

    def start(
        self,
        buffer: array.array,
        *,
        count: int | None = None,
        callback: Callable[[array.array], None] | None = None,
    ) -> bool:
        """
        Start capturing into *buffer* via DMA.

        The capture runs until the buffer is full or ``stop()`` is called.
        An optional callback is invoked via ``micropython.schedule()`` when
        the DMA transfer completes.

        :param buffer: Destination ``array.array('I', ...)`` buffer.
        :param count: Number of 32-bit words to capture (default: full buffer).
        :param callback: Optional function called with the buffer when capture
            completes.
        :return: ``True`` if capture started, ``False`` if already running.

        :raises ValueError: If *buffer* is not ``array('I')``.

        Example
        -------
        ```python
            >>> buf = array.array('I', [0] * 1000)
            >>> cap.start(buf)
            >>>
            >>> # With completion callback
            >>> def on_done(data):
            ...     print(f"Captured {len(data)} samples")
            >>> cap.start(buf, callback=on_done)
            >>>
            >>> # Capture only first 200 words
            >>> cap.start(buf, count=200)
        ```
        """
        ...

    def stop(self) -> None:
        """
        Stop capture immediately.

        Halts DMA and the PIO state machine.  Partial data remains in the
        buffer up to ``bytes_captured()`` bytes.

        Example
        -------
        ```python
            >>> cap.start(buf)
            >>> time.sleep_ms(100)
            >>> cap.stop()
            >>> print(f"Got {cap.bytes_captured()} bytes")
        ```
        """
        ...

    @property
    def is_running(self) -> bool:
        """
        ``True`` if a capture is currently in progress.

        Example
        -------
        ```python
            >>> cap.start(buf)
            >>> while cap.is_running:
            ...     time.sleep_ms(10)
        ```
        """
        ...

    @property
    def is_complete(self) -> bool:
        """
        ``True`` if the DMA transfer filled the entire buffer.

        Example
        -------
        ```python
            >>> cap.start(buf)
            >>> while not cap.is_complete:
            ...     time.sleep_ms(10)
            >>> print("Buffer full")
        ```
        """
        ...

    def bytes_captured(self) -> int:
        """
        Return the number of bytes written to the buffer so far.

        :return: Bytes written (multiple of 4 since each word is 32 bits).

        Example
        -------
        ```python
            >>> cap.start(buf)
            >>> time.sleep_ms(50)
            >>> print(f"Progress: {cap.bytes_captured()} / {len(buf) * 4} bytes")
        ```
        """
        ...

    def wait(self, timeout_ms: int | None = None) -> bool:
        """
        Block until capture completes or *timeout_ms* elapses.

        :param timeout_ms: Maximum wait time in milliseconds.  Pass ``None``
            to wait indefinitely.
        :return: ``True`` if capture completed, ``False`` if timed out.

        Example
        -------
        ```python
            >>> cap.start(buf)
            >>> if cap.wait(timeout_ms=5000):
            ...     print("Complete")
            ... else:
            ...     print("Timed out")
            ...     cap.stop()
        ```
        """
        ...

    def read_blocking(
        self,
        count: int,
        *,
        timeout_ms: int = 5000,
    ) -> array.array:
        """
        Allocate a buffer, capture *count* samples, and return the data.

        Convenience wrapper around ``start()`` + ``wait()`` + ``stop()``.

        :param count: Number of 32-bit words to capture.
        :param timeout_ms: Maximum capture time in milliseconds (default: 5000).
        :return: ``array.array('I')`` containing the captured data.

        :raises TimeoutError: If capture does not complete within *timeout_ms*.

        Example
        -------
        ```python
            >>> cap = PioCapture(pin=15, mode=PioCapture.RISING)
            >>> data = cap.read_blocking(1000, timeout_ms=10000)
            >>> print(f"Got {len(data)} edge events")
        ```
        """
        ...
