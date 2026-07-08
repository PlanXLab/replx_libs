"""
PIO Waveform Module

Arbitrary waveform output using RP2040/RP2350 PIO and DMA.
Generates digital patterns at rates up to 125 MHz with zero CPU load
during playback.

Features:

- 1-bit waveform: Single pin high/low pattern output
- 8-bit parallel: 8 consecutive pins simultaneously (DAC / bus applications)
- PWM mode: Variable duty cycle patterns via sideset timing
- DMA-driven: Zero CPU overhead during playback
- Loop mode: Continuous waveform repetition

Use cases:

- Arbitrary waveform generation
- Protocol simulation (UART, SPI, I2C bit-banging)
- LED pattern generation
- Servo / motor control pulses
- Audio output (with an external R-2R DAC)

"""

import array
from typing import Callable


class PioWaveform:
    """
    PIO-based arbitrary waveform generator.

    Uses an RP2040/RP2350 PIO state machine and DMA channel to output
    arbitrary digital patterns with minimal CPU overhead.

    :param pin: Output GPIO pin number, or list of exactly 8 consecutive
        pins for ``MODE_8BIT``.
    :param mode: Output mode - one of ``MODE_1BIT``, ``MODE_8BIT``, or
        ``MODE_PWM`` (default: ``MODE_1BIT``).
    :param freq: PIO state machine frequency in Hz (default: 1 000 000).

    :raises ValueError: If pin configuration is invalid for the selected mode.
    :raises RuntimeError: If no free state machines are available.

    Example
    -------
    ```python
        >>> import array
        >>> from ticle_lite.pio_waveform import PioWaveform
        >>>
        >>> # 1 MHz square wave on pin 15
        >>> wf = PioWaveform(pin=15, freq=1_000_000)
        >>> pattern = array.array('I', [0xAAAAAAAA] * 100)
        >>> wf.start(pattern, loop=True)
        >>> # ... waveform runs continuously ...
        >>> wf.stop()
        >>> wf.deinit()
    ```
    """

    MODE_1BIT: int
    """Single-bit output mode (32 bits per 32-bit word, one bit per PIO cycle)."""

    MODE_8BIT: int
    """8-bit parallel output mode (8 consecutive pins, 1 byte per sample)."""

    MODE_PWM: int
    """PWM mode using sideset timing for variable duty-cycle patterns."""

    def __init__(
        self,
        pin: int | list[int],
        *,
        mode: int = 0,
        freq: int = 1_000_000,
    ) -> None:
        """
        Initialize the PIO waveform generator.

        :param pin: Output pin number, or list of 8 consecutive pins for
            ``MODE_8BIT``.
        :param mode: Output mode - ``MODE_1BIT``, ``MODE_8BIT``, or
            ``MODE_PWM`` (default: ``MODE_1BIT``).
        :param freq: PIO state machine clock frequency in Hz (default: 1 MHz).

        :raises ValueError: If the pin list is empty, or does not contain
            exactly 8 pins when ``MODE_8BIT`` is selected.
        :raises RuntimeError: If no free state machines are available.

        Example
        -------
        ```python
            >>> wf = PioWaveform(pin=15, freq=1_000_000)
            >>> wf8 = PioWaveform(pin=[0, 1, 2, 3, 4, 5, 6, 7],
            ...                   mode=PioWaveform.MODE_8BIT, freq=100_000)
            >>> wf_pwm = PioWaveform(pin=15, mode=PioWaveform.MODE_PWM, freq=50)
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Stop waveform output and release PIO and DMA resources.

        Sets output pins low and frees the state machine.  Called
        automatically when using the context-manager interface.

        Example
        -------
        ```python
            >>> wf = PioWaveform(pin=15)
            >>> wf.deinit()
        ```
        """
        ...

    def __enter__(self) -> "PioWaveform":
        """
        Return ``self`` for use as a context manager.

        :return: This ``PioWaveform`` instance.

        Example
        -------
        ```python
            >>> with PioWaveform(pin=15, freq=500_000) as wf:
            ...     wf.start(pattern, loop=True)
            ...     time.sleep(2)
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
            >>> with PioWaveform(pin=15) as wf:
            ...     pass   # deinit() called automatically on exit
        ```
        """
        ...

    def set_freq(self, freq: int) -> None:
        """
        Change the output frequency while the waveform generator is idle.

        :param freq: New PIO clock frequency in Hz (1-125 000 000).

        :raises ValueError: If *freq* is outside 1-125 000 000 Hz.
        :raises RuntimeError: If the state machine is not initialized.

        Example
        -------
        ```python
            >>> wf = PioWaveform(pin=15, freq=1_000_000)
            >>> wf.stop()
            >>> wf.set_freq(2_000_000)
            >>> wf.start(pattern)
        ```
        """
        ...

    @property
    def freq(self) -> int:
        """
        Current PIO state machine clock frequency in Hz.

        :return: Frequency in Hz.

        Example
        -------
        ```python
            >>> wf = PioWaveform(pin=15, freq=500_000)
            >>> print(wf.freq)
            500000
        ```
        """
        ...

    def start(
        self,
        buffer: array.array,
        *,
        loop: bool = False,
        callback: Callable[[array.array], None] | None = None,
    ) -> bool:
        """
        Start waveform output from *buffer* via DMA.

        Output continues until the buffer is exhausted or ``stop()`` is
        called.  In loop mode the DMA wraps around to the start of the
        buffer continuously.

        :param buffer: Source data — ``array('I')`` for ``MODE_1BIT`` /
            ``MODE_PWM``, ``array('B')`` for ``MODE_8BIT``.
        :param loop: If ``True``, repeat the buffer continuously.
        :param callback: Optional function called with the buffer when
            single-shot playback completes.  Ignored when *loop* is ``True``.
        :return: ``True`` if output started, ``False`` if already running.

        :raises ValueError: If buffer typecode does not match the mode.

        Example
        -------
        ```python
            >>> # One-shot playback
            >>> pattern = array.array('I', [0xFFFF0000] * 50)
            >>> wf.start(pattern)
            >>>
            >>> # Continuous loop
            >>> wf.start(pattern, loop=True)
            >>>
            >>> # With completion callback
            >>> def on_done(buf):
            ...     print("Playback finished")
            >>> wf.start(pattern, callback=on_done)
        ```
        """
        ...

    def stop(self) -> None:
        """
        Stop waveform output and set output pins low.

        Halts DMA and the PIO state machine.

        Example
        -------
        ```python
            >>> wf.start(pattern, loop=True)
            >>> time.sleep(1)
            >>> wf.stop()
        ```
        """
        ...

    @property
    def is_running(self) -> bool:
        """
        ``True`` if waveform output is currently active.

        Example
        -------
        ```python
            >>> wf.start(pattern)
            >>> if wf.is_running:
            ...     print("Still playing")
        ```
        """
        ...

    @property
    def is_complete(self) -> bool:
        """
        ``True`` if single-shot DMA playback finished (always ``False`` in
        loop mode).

        Example
        -------
        ```python
            >>> wf.start(pattern)
            >>> while not wf.is_complete:
            ...     time.sleep_ms(10)
            >>> print("Done")
        ```
        """
        ...

    def wait(self, timeout_ms: int | None = None) -> bool:
        """
        Block until playback completes or *timeout_ms* elapses.

        Returns immediately with ``False`` if loop mode is active.

        :param timeout_ms: Maximum wait time in milliseconds.  Pass ``None``
            to wait indefinitely.
        :return: ``True`` if playback completed, ``False`` if timed out or
            loop mode is active.

        Example
        -------
        ```python
            >>> wf.start(pattern)
            >>> if wf.wait(timeout_ms=5000):
            ...     print("Done")
            ... else:
            ...     print("Timed out or looping")
        ```
        """
        ...

    def play_once(
        self,
        buffer: array.array,
        *,
        timeout_ms: int = 10000,
    ) -> bool:
        """
        Start playback, wait for completion, and stop — all in one call.

        :param buffer: Waveform data buffer.
        :param timeout_ms: Maximum playback time in milliseconds (default: 10000).
        :return: ``True`` if playback completed within *timeout_ms*, ``False``
            if timed out.

        Example
        -------
        ```python
            >>> pattern = PioWaveform.generate_square(100, 500, 500)
            >>> success = wf.play_once(pattern, timeout_ms=2000)
        ```
        """
        ...

    @staticmethod
    def generate_square(
        periods: int,
        high_cycles: int,
        low_cycles: int,
    ) -> array.array:
        """
        Generate a square-wave pattern for ``MODE_PWM``.

        Each period consists of *high_cycles* PIO clock cycles high followed
        by *low_cycles* clock cycles low.

        :param periods: Number of complete high-low cycles to generate.
        :param high_cycles: PIO clock cycles for the high phase.
        :param low_cycles: PIO clock cycles for the low phase.
        :return: ``array.array('I')`` suitable for ``MODE_PWM``.

        Example
        -------
        ```python
            >>> # 50% duty cycle, 1000 cycles total
            >>> pattern = PioWaveform.generate_square(100, 500, 500)
            >>>
            >>> # 25% duty cycle
            >>> pattern = PioWaveform.generate_square(100, 250, 750)
            >>>
            >>> wf = PioWaveform(pin=15, mode=PioWaveform.MODE_PWM, freq=1_000_000)
            >>> wf.play_once(pattern)
        ```
        """
        ...

    @staticmethod
    def generate_pwm_pattern(
        values: list[tuple[int, int]],
    ) -> array.array:
        """
        Generate an arbitrary PWM pattern from a list of (high, low) cycle pairs.

        :param values: List of ``(high_cycles, low_cycles)`` tuples, one per
            period.
        :return: ``array.array('I')`` suitable for ``MODE_PWM``.

        Example
        -------
        ```python
            >>> # Servo signal: 50 Hz, 1-2 ms pulse width
            >>> servo_pattern = PioWaveform.generate_pwm_pattern([
            ...     (1500, 18500),   # 1.5 ms pulse (90 degrees)
            ... ] * 50)
            >>> wf = PioWaveform(pin=15, mode=PioWaveform.MODE_PWM, freq=1_000_000)
            >>> wf.start(servo_pattern, loop=True)
        ```
        """
        ...
