"""
Ultrasonic Distance Sensor Driver

Supports single or multiple sensors with unified interface.
Uses machine.time_pulse_us for reliable bounded blocking reads.

Features:

- Direct machine.time_pulse_us measurement for reliable bounded blocking reads
- Single and multi-sensor support with View pattern
- Configurable sound speed for temperature compensation
- Optional median filter for noise reduction
- Optional low-pass filter for smoothing
- Interference delay setting for multi-sensor sequential measurement
- Valid range checking (default: 2cm - 4.5m)

"""

from typing import Optional
from dio import Din, Dout
from ufilter import Median, TauLowPass, FilterChain


class SR04:
    """
    HC-SR04 ultrasonic distance sensor driver.
    
    Supports single or multiple sensors with unified interface.
    Uses io.py Din/Dout for GPIO management and machine.time_pulse_us for
    reliable bounded blocking reads.
    
    Example
    -------
    ```python
        >>> from ticle.us import SR04
        >>> 
        >>> # Single sensor
        >>> sensor = SR04(echo=15, trig=14)
        >>> distance = sensor.read()
        >>> print(f"Distance: {distance:.3f} m")
        >>> 
        >>> # Multiple sensors
        >>> sensors = SR04(echo=[15, 17, 19], trig=[14, 16, 18])
        >>> sensors[0].trigger()           # Single sensor
        >>> d0 = sensors[0].result()[0]
        >>> sensors[:].trigger()           # All sensors
        >>> distances = sensors[:].result() # All results
        >>> 
        >>> # With interference delay (sequential measurement)
        >>> sensors = SR04(
        ...     echo=[15, 17], trig=[14, 16],
        ...     interference_delay_ms=60
        ... )
        >>> distances = sensors[:].read()  # Measured sequentially
    ```
    """

    def __init__(
        self, 
        *, 
        echo: int | list[int], 
        trig: int | list[int],
        sound_speed_ms: float = 343.2,
        min_valid_m: float = 0.02, 
        max_valid_m: float = 4.5,
        interference_delay_ms: int = 0,
        median: int | None = None, 
        lpf: float | None = None
    ) -> None:
        """
        Initialize HC-SR04 sensor(s).
        
        :param echo: Echo pin number(s) - int for single, list for multiple
        :param trig: Trigger pin number(s) - int for single, list for multiple
        :param sound_speed_ms: Speed of sound in m/s (default: 343.2 at 20°C)
        :param min_valid_m: Minimum valid distance in meters (default: 0.02)
        :param max_valid_m: Maximum valid distance in meters (default: 4.5)
        :param interference_delay_ms: Delay between sequential measurements to avoid
                                      ultrasonic interference (0=simultaneous allowed)
        :param median: Median filter window size, None to disable
        :param lpf: Low-pass filter tau in seconds, None to disable
        
        :raises ValueError: If echo and trig have different lengths
        :raises OSError: If GPIO initialization fails
        
        Example
        -------
        ```python
            >>> # Single sensor
            >>> sensor = SR04(echo=15, trig=14)
            >>> 
            >>> # Multiple sensors, simultaneous measurement
            >>> sensors = SR04(echo=[15, 17], trig=[14, 16])
            >>> 
            >>> # Multiple sensors with interference protection
            >>> sensors = SR04(
            ...     echo=[15, 17, 19], trig=[14, 16, 18],
            ...     interference_delay_ms=60,
            ...     median=5
            ... )
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Release hardware resources.
        
        Example
        -------
        ```python
            >>> sensor = SR04(echo=15, trig=14)
            >>> sensor.deinit()
        ```
        """
        ...

    def __enter__(self) -> "SR04":
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    def __len__(self) -> int:
        """Return number of sensors."""
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Get view for selected sensor(s).
        
        :param idx: Sensor index or slice
        :return: View for selected sensors
        
        Example
        -------
        ```python
            >>> sensors = SR04(echo=[15, 17, 19], trig=[14, 16, 18])
            >>> sensors[0].read()      # First sensor
            >>> sensors[1:3].read()    # Second and third
            >>> sensors[:].read()      # All sensors
        ```
        """
        ...

    @property
    def last(self) -> float:
        """
        Get last measured distance (single sensor only).
        
        :return: Last distance in meters, or NaN if no valid reading
        :raises RuntimeError: If called on multi-sensor instance
        """
        ...

    def trigger(self) -> None:
        """
        Trigger measurement (single sensor only).
        
        :raises RuntimeError: If called on multi-sensor instance
        """
        ...

    def ready(self) -> bool:
        """
        Check if measurement ready (single sensor only).
        
        :raises RuntimeError: If called on multi-sensor instance
        """
        ...

    def result(self, timeout_ms: int = 50) -> float:
        """
        Get measurement result (single sensor only).
        
        :param timeout_ms: Maximum wait time in milliseconds
        :return: Distance in meters, or NaN on timeout
        :raises RuntimeError: If called on multi-sensor instance
        """
        ...

    def read(self, timeout_ms: int = 50) -> float:
        """
        Trigger and read distance (single sensor only).
        
        :param timeout_ms: Maximum wait time in milliseconds
        :return: Distance in meters, or NaN on timeout
        :raises RuntimeError: If called on multi-sensor instance
        """
        ...

    def reset_filter(self) -> None:
        """Reset all filters."""
        ...

    class _View:
        """View for selected sensor(s)."""
        
        def __len__(self) -> int:
            ...

        def __getitem__(self, idx: int | slice) -> "SR04._View":
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

        def result(self, timeout_ms: int = 50) -> list[float]:
            """
            Wait for and calculate distances.
            
            :param timeout_ms: Maximum wait time in milliseconds
            :return: List of distances in meters
            """
            ...

        def read(self, timeout_ms: int = 50) -> list[float]:
            """
            Trigger and read distances.
            
            If interference_delay_ms > 0, measurements are sequential.
            
            :param timeout_ms: Maximum wait time in milliseconds
            :return: List of distances in meters
            """
            ...

        @property
        def sound_speed(self) -> float:
            """Get sound speed (m/s)."""
            ...

        @sound_speed.setter
        def sound_speed(self, value: float) -> None:
            """Set sound speed (m/s)."""
            ...

        def reset_filter(self) -> None:
            """Reset filters for selected sensors."""
            ...
