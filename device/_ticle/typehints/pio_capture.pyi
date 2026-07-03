"""
PIO Capture Module

High-speed GPIO capture using RP2040/RP2350 PIO (Programmable I/O) and DMA.
Captures edge events or continuous samples at rates up to 125MHz.

Key Features:

    - Edge detection: rising, falling, or both edges
    - Continuous sampling at configurable rate
    - Parallel capture of up to 8 pins simultaneously
    - DMA transfer for zero-CPU-load capture
    - Async callback on capture complete

Use Cases:

    - Logic analyzer functionality
    - Protocol decoding (UART, SPI bit-banging)
    - Pulse width measurement
    - Frequency measurement
    - High-speed event logging

Author: PlanXLab Development Team
"""

import array
from typing import Callable


class PioCapture:
    """
    PIO-based high-speed GPIO capture.
    
    Uses RP2040/RP2350 PIO state machine and DMA for capturing GPIO
    events or continuous samples with minimal CPU overhead.
    
    Capture Modes:
    
        - RISING: Capture on rising edge
        - FALLING: Capture on falling edge  
        - BOTH: Capture on any edge change
        - CONTINUOUS: Sample at fixed rate
        - PARALLEL: Capture 8 pins simultaneously
    
    Example
    --------
    Basic edge capture::
    
        >>> from pio_capture import PioCapture
        >>> import array
        >>> 
        >>> cap = PioCapture(pin=15, mode=PioCapture.RISING)
        >>> buf = array.array('I', [0] * 1000)
        >>> cap.start(buf)
        >>> cap.wait(timeout_ms=5000)
        >>> cap.stop()
        >>> print(f"Captured {cap.bytes_captured()} bytes")
    """
    
    RISING: int
    """Capture on rising edge (low to high transition)."""
    
    FALLING: int
    """Capture on falling edge (high to low transition)."""
    
    BOTH: int
    """Capture on any edge (both rising and falling)."""
    
    CONTINUOUS: int
    """Continuous sampling at fixed rate."""
    
    PARALLEL: int
    """Parallel capture of multiple pins (up to 8)."""

    def __init__(
        self,
        pin: int | list[int],
        *,
        mode: int = 0
    ):
        """
        Initialize PIO capture.
        
        :param pin: GPIO pin number, or list of pins for parallel mode
        :param mode: Capture mode (RISING, FALLING, BOTH, CONTINUOUS, PARALLEL)
        
        :raises ValueError: If pin is invalid or mode is unsupported
        :raises RuntimeError: If no free state machines available
        
        Note
        ----
        Uses 1 PIO State Machine. Call deinit() to release.
        
        Example
        --------
        ```python
            >>> # Single pin edge capture
            >>> cap = PioCapture(pin=15, mode=PioCapture.RISING)
            
            >>> # Parallel 8-bit capture
            >>> cap = PioCapture(pin=[0,1,2,3,4,5,6,7], mode=PioCapture.PARALLEL)
        ```
        """

    def deinit(self) -> None:
        """
        Release PIO and DMA resources.
        
        Stops any active capture and frees hardware resources.
        Called automatically when using context manager.
        
        Example
        --------
        ```python
            >>> cap = PioCapture(pin=15)
            >>> # ... use capture ...
            >>> cap.deinit()
        ```
        """

    def __enter__(self) -> "PioCapture":
        """Enter context manager."""

    def __exit__(self, *args) -> None:
        """Exit context manager, calls deinit()."""

    def set_freq(self, freq: int) -> None:
        """
        Set PIO state machine frequency.
        
        Controls the capture sample rate for CONTINUOUS mode,
        or the edge detection resolution for edge modes.
        
        :param freq: Frequency in Hz (1 to 125000000)
        
        :raises ValueError: If frequency is out of range
        :raises RuntimeError: If state machine not initialized
        
        Example
        --------
        ```python
            >>> cap = PioCapture(pin=15, mode=PioCapture.CONTINUOUS)
            >>> cap.set_freq(1_000_000)  # 1MHz sample rate
        ```
        """

    def start(
        self,
        buffer: array.array,
        *,
        count: int = None,
        callback: Callable[[array.array], None] = None
    ) -> bool:
        """
        Start capturing to buffer.
        
        Begins DMA transfer from PIO RX FIFO to the provided buffer.
        Capture continues until buffer is full or stop() is called.
        
        :param buffer: Target buffer, must be array('I', ...)
        :param count: Number of words to capture (default: buffer length)
        :param callback: Optional callback when capture completes
        
        :return: True if started, False if already running
        
        :raises ValueError: If buffer type is not array('I')
        
        Example
        --------
        ```python
            >>> buf = array.array('I', [0] * 1000)
            >>> cap.start(buf)
            >>> # ... capture runs in background ...
            
            >>> # With callback
            >>> def on_done(data):
            ...     print(f"Captured {len(data)} samples")
            >>> cap.start(buf, callback=on_done)
        ```
        """

    def stop(self) -> None:
        """
        Stop capture.
        
        Immediately halts DMA and PIO state machine.
        Partial data remains in buffer up to bytes_captured().
        
        Example
        --------
        ```python
            >>> cap.start(buf)
            >>> time.sleep_ms(100)
            >>> cap.stop()
            >>> print(f"Got {cap.bytes_captured()} bytes")
        ```
        """

    @property
    def is_running(self) -> bool:
        """
        Check if capture is active.
        
        :return: True if capture in progress
        
        Example
        --------
        ```python
            >>> if cap.is_running:
            ...     print("Still capturing...")
        ```
        """

    @property
    def is_complete(self) -> bool:
        """
        Check if capture completed (buffer full).
        
        :return: True if DMA transfer finished
        
        Example
        --------
        ```python
            >>> cap.start(buf)
            >>> while not cap.is_complete:
            ...     time.sleep_ms(10)
        ```
        """

    def bytes_captured(self) -> int:
        """
        Get number of bytes captured so far.
        
        :return: Bytes written to buffer
        
        Example
        --------
        ```python
            >>> cap.start(buf)
            >>> # ... later ...
            >>> print(f"Progress: {cap.bytes_captured()} bytes")
        ```
        """

    def wait(self, timeout_ms: int = None) -> bool:
        """
        Wait for capture to complete.
        
        Blocks until buffer is full or timeout expires.
        
        :param timeout_ms: Maximum wait time (None = infinite)
        
        :return: True if completed, False if timeout
        
        Example
        --------
        ```python
            >>> cap.start(buf)
            >>> if cap.wait(timeout_ms=5000):
            ...     print("Capture complete")
            ... else:
            ...     print("Timeout!")
            ...     cap.stop()
        ```
        """

    def read_blocking(
        self,
        count: int,
        *,
        timeout_ms: int = 5000
    ) -> array.array:
        """
        Capture fixed number of samples (blocking).
        
        Convenience method that allocates buffer, captures, and returns data.
        
        :param count: Number of 32-bit words to capture
        :param timeout_ms: Maximum wait time
        
        :return: Array of captured data
        
        :raises TimeoutError: If capture doesn't complete in time
        
        Example
        --------
        ```python
            >>> cap = PioCapture(pin=15, mode=PioCapture.RISING)
            >>> data = cap.read_blocking(1000, timeout_ms=10000)
            >>> print(f"Got {len(data)} edge events")
        ```
        """
