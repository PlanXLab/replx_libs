"""
PIO Waveform Module

Arbitrary waveform output using RP2040/RP2350 PIO and DMA.
Generates digital waveforms at rates up to 125MHz with zero CPU load.

Key Features:

    - 1-bit waveform: Single pin high/low pattern
    - 8-bit parallel: 8 pins simultaneously (DAC applications)
    - PWM mode: Variable duty cycle patterns via sideset
    - DMA-driven: Zero CPU overhead during playback
    - Loop mode: Continuous waveform repetition

Use Cases:

    - Arbitrary waveform generation
    - Protocol simulation (UART, SPI, I2C bit-banging)
    - LED pattern generation
    - Servo/motor control pulses
    - Audio output (with external DAC)

Author: PlanXLab Development Team
"""

import array
from typing import Callable


class PioWaveform:
    """
    PIO-based arbitrary waveform generator.
    
    Uses RP2040/RP2350 PIO state machine and DMA for outputting
    arbitrary digital patterns with minimal CPU overhead.
    
    Output Modes:
    
        - MODE_1BIT: Single pin, 32 bits per word
        - MODE_8BIT: 8 parallel pins, 1 byte per sample
        - MODE_PWM: Variable pulse widths via sideset timing
    
    Example
    --------
    Basic square wave::
    
        >>> from pio_waveform import PioWaveform
        >>> import array
        >>> 
        >>> wf = PioWaveform(pin=15, freq=1_000_000)
        >>> pattern = array.array('I', [0xAAAAAAAA] * 100)  # 1MHz square wave
        >>> wf.start(pattern, loop=True)
        >>> # ... waveform runs continuously ...
        >>> wf.stop()
    """
    
    MODE_1BIT: int
    """Single-bit output mode (32 bits per word)."""
    
    MODE_8BIT: int
    """8-bit parallel output mode."""
    
    MODE_PWM: int
    """PWM mode with programmable pulse widths."""

    def __init__(
        self,
        pin: int | list[int],
        *,
        mode: int = 0,
        freq: int = 1_000_000
    ):
        """
        Initialize PIO waveform generator.
        
        :param pin: Output GPIO pin, or list of 8 pins for 8-bit mode
        :param mode: Output mode (MODE_1BIT, MODE_8BIT, MODE_PWM)
        :param freq: Output frequency/sample rate in Hz
        
        :raises ValueError: If pin configuration invalid for mode
        :raises RuntimeError: If no free state machines available
        
        Note
        ----
        Uses 1 PIO State Machine. Call deinit() to release.
        
        Example
        --------
        ```python
            >>> # 1MHz single-bit output
            >>> wf = PioWaveform(pin=15, freq=1_000_000)
            
            >>> # 8-bit parallel DAC output at 100kHz
            >>> wf = PioWaveform(
            ...     pin=[0,1,2,3,4,5,6,7],
            ...     mode=PioWaveform.MODE_8BIT,
            ...     freq=100_000
            ... )
            
            >>> # PWM mode for servo control
            >>> wf = PioWaveform(pin=15, mode=PioWaveform.MODE_PWM, freq=50)
        ```
        """

    def deinit(self) -> None:
        """
        Release PIO and DMA resources.
        
        Stops waveform output and sets output pins low.
        Called automatically when using context manager.
        
        Example
        --------
        ```python
            >>> wf = PioWaveform(pin=15)
            >>> # ... use waveform ...
            >>> wf.deinit()
        ```
        """

    def __enter__(self) -> "PioWaveform":
        """Enter context manager."""

    def __exit__(self, *args) -> None:
        """Exit context manager, calls deinit()."""

    def set_freq(self, freq: int) -> None:
        """
        Set output frequency.
        
        For MODE_1BIT: bits per second
        For MODE_8BIT: bytes per second  
        For MODE_PWM: base clock for timing
        
        :param freq: Frequency in Hz (1 to 125000000)
        
        :raises ValueError: If frequency out of range
        :raises RuntimeError: If state machine not initialized
        
        Example
        --------
        ```python
            >>> wf.set_freq(2_000_000)  # 2MHz output rate
        ```
        """

    @property
    def freq(self) -> int:
        """
        Current output frequency.
        
        :return: Frequency in Hz
        """

    def start(
        self,
        buffer: array.array,
        *,
        loop: bool = False,
        callback: Callable[[array.array], None] = None
    ) -> bool:
        """
        Start waveform output.
        
        Begins DMA transfer from buffer to PIO TX FIFO.
        Output continues until buffer exhausted or stop() called.
        
        :param buffer: Source data (array('I') for 1bit/PWM, array('B') for 8bit)
        :param loop: If True, repeat buffer continuously
        :param callback: Called when playback completes (ignored if loop=True)
        
        :return: True if started, False if already running
        
        :raises ValueError: If buffer type doesn't match mode
        
        Example
        --------
        ```python
            >>> # One-shot playback
            >>> pattern = array.array('I', [0xFFFFFFFF, 0x00000000] * 50)
            >>> wf.start(pattern)
            
            >>> # Continuous loop
            >>> wf.start(pattern, loop=True)
            
            >>> # With completion callback
            >>> def done(buf):
            ...     print("Playback finished")
            >>> wf.start(pattern, callback=done)
        ```
        """

    def stop(self) -> None:
        """
        Stop waveform output.
        
        Halts DMA and PIO, sets output pins low.
        
        Example
        --------
        ```python
            >>> wf.start(pattern, loop=True)
            >>> time.sleep(1)
            >>> wf.stop()
        ```
        """

    @property
    def is_running(self) -> bool:
        """
        Check if waveform is active.
        
        :return: True if output in progress
        """

    @property
    def is_complete(self) -> bool:
        """
        Check if playback completed.
        
        Always False if loop mode is active.
        
        :return: True if DMA transfer finished
        """

    def wait(self, timeout_ms: int = None) -> bool:
        """
        Wait for playback to complete.
        
        Returns immediately with False if in loop mode.
        
        :param timeout_ms: Maximum wait time (None = infinite)
        
        :return: True if completed, False if timeout or looping
        
        Example
        --------
        ```python
            >>> wf.start(pattern)
            >>> if wf.wait(timeout_ms=5000):
            ...     print("Done")
        ```
        """

    def play_once(
        self,
        buffer: array.array,
        *,
        timeout_ms: int = 10000
    ) -> bool:
        """
        Play waveform once (blocking).
        
        Convenience method that starts, waits, and stops.
        
        :param buffer: Waveform data
        :param timeout_ms: Maximum playback time
        
        :return: True if completed, False if timeout
        
        Example
        --------
        ```python
            >>> pattern = PioWaveform.generate_square(100, 500, 500)
            >>> wf.play_once(pattern)
        ```
        """

    @staticmethod
    def generate_square(
        periods: int,
        high_cycles: int,
        low_cycles: int
    ) -> array.array:
        """
        Generate square wave pattern for PWM mode.
        
        :param periods: Number of complete cycles
        :param high_cycles: Clock cycles for high phase
        :param low_cycles: Clock cycles for low phase
        
        :return: Array suitable for MODE_PWM
        
        Example
        --------
        ```python
            >>> # 50% duty cycle, 1000 cycles per period
            >>> pattern = PioWaveform.generate_square(100, 500, 500)
            
            >>> # 25% duty cycle
            >>> pattern = PioWaveform.generate_square(100, 250, 750)
        ```
        """

    @staticmethod
    def generate_pwm_pattern(
        values: list[tuple[int, int]]
    ) -> array.array:
        """
        Generate arbitrary PWM pattern.
        
        Each tuple specifies (high_cycles, low_cycles) for one pulse.
        
        :param values: List of (high, low) cycle counts
        
        :return: Array suitable for MODE_PWM
        
        Example
        --------
        ```python
            >>> # Servo-style pattern: 1ms, 1.5ms, 2ms pulses
            >>> # At 1MHz: 1000, 1500, 2000 cycles
            >>> pattern = PioWaveform.generate_pwm_pattern([
            ...     (1000, 19000),   # 1ms high, 19ms low
            ...     (1500, 18500),   # 1.5ms high
            ...     (2000, 18000),   # 2ms high
            ... ])
        ```
        """
