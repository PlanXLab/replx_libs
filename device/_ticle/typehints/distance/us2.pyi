"""
Ultrasonic Distance Sensor Driver for ticle (RP2040/RP2350)

PIO-based multi-channel ultrasonic distance sensor driver with Kalman filtering
and timer-based non-blocking operation. Uses PIO State Machines for precise
pulse timing (1µs resolution).

Features:

- PIO-based pulse generation and echo timing (up to 12 sensors)
- Multi-sensor support with _View pattern for indexed access
- 1D Kalman filter for accurate tracking with velocity estimation
- Timer-based non-blocking measurement with callbacks
- Temperature-compensated sound speed calculation
- Configurable filter parameters (R: measurement noise, Q: process noise)

"""

from typing import Callable, Optional


class SR04:
    """
    Multi-channel HC-SR04 driver with Kalman filtering for ticle platform.
    
    Supports multiple sensors with indexed access via _View pattern.
    Provides both blocking reads and timer-based non-blocking operation.
    
    Example
    -------
    ```python
        >>> from ticle.us2 import SR04
        >>> 
        >>> # Initialize with two sensors
        >>> sensors = SR04([(2, 3), (4, 5)])  # [(trig, echo), ...]
        >>> 
        >>> # Set temperature for all sensors
        >>> sensors[:].temperature = 25.0
        >>> 
        >>> # Blocking read from first sensor
        >>> print(sensors[0].value)  # Returns [distance_cm] or [None]
        >>> 
        >>> # Non-blocking with callback
        >>> def on_distance(trig_pin, distance):
        ...     if distance is not None:
        ...         print(f"Sensor {trig_pin}: {distance} cm")
        >>> 
        >>> sensors[:].callback = on_distance
        >>> sensors[:].nonblocking = True
        >>> sensors[:].measurement = True
        >>> 
        >>> # ... measurements arrive via callback ...
        >>> 
        >>> sensors[:].measurement = False
        >>> sensors.deinit()
    ```
    """

    def __init__(
        self, 
        sensor_configs: list[tuple[int, int]], 
        *, 
        temp_c: float = 20.0, 
        R: float = 25.0, 
        Q: float = 4.0
    ) -> None:
        """
        Initialize multi-channel SR04 driver with PIO State Machines.
        
        :param sensor_configs: List of (trig_pin, echo_pin) tuples
        :param temp_c: Initial ambient temperature in Celsius (default: 20.0)
        :param R: Kalman measurement noise covariance (default: 25.0)
        :param Q: Kalman process noise covariance (default: 4.0)
        
        :raises ValueError: If sensor_configs is empty or temperature out of range
        :raises RuntimeError: If no free state machines available
        :raises OSError: If PIO initialization fails
        
        Note
        ----
        Uses len(sensor_configs) PIO State Machines (1 per sensor). Call deinit() to release.
        
        Example
        -------
        ```python
            >>> # Single sensor (uses 1 SM)
            >>> sensor = SR04([(14, 15)])
            >>> 
            >>> # 3 sensors (uses 3 SMs)
            >>> sensors = SR04([(2, 3), (4, 5), (6, 7)])
            >>> 
            >>> # With custom Kalman parameters
            >>> sensors = SR04(
            ...     [(2, 3), (4, 5)],
            ...     temp_c=25.0,
            ...     R=16.0,  # Lower = trust measurements more
            ...     Q=1.0    # Lower = smoother, slower response
            ... )
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Access sensor(s) by index or slice.
        
        :param idx: Integer index or slice
        :return: _View for accessing sensor properties
        
        :raises IndexError: If index out of range
        :raises TypeError: If idx is not int or slice
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5), (6, 7)])
            >>> 
            >>> # Single sensor access
            >>> sensors[0].value
            >>> 
            >>> # Slice access
            >>> sensors[1:].temperature = 22.0
            >>> 
            >>> # All sensors
            >>> sensors[:].nonblocking = True
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Get number of sensors.
        
        :return: Number of configured sensors
        """
        ...

    def deinit(self) -> None:
        """
        Release all hardware resources.
        
        Stops timer, disables measurements, and releases GPIO pins.
        Safe to call multiple times.
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> # ... use sensors ...
            >>> sensors.deinit()
        ```
        """
        ...


class _View:
    """
    View into subset of SR04 sensors.
    
    Provides property-based access to sensor configuration and readings.
    Returned by SR04.__getitem__(), not instantiated directly.
    
    Example
    -------
    ```python
        >>> sensors = SR04([(2, 3), (4, 5)])
        >>> view = sensors[0]      # Single sensor view
        >>> view = sensors[:]      # All sensors view
        >>> view = sensors[0:2]    # Range view
    ```
    """

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Further slice the view.
        
        :param idx: Integer index or slice
        :return: New _View with selected sensors
        """
        ...

    def __len__(self) -> int:
        """
        Get number of sensors in this view.
        
        :return: Number of sensors
        """
        ...

    def reset_filter(self) -> None:
        """
        Reset Kalman filter state for selected sensors.
        
        Clears position, velocity estimates and resets covariance matrix.
        Call after sensor repositioning or significant condition changes.
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> # Take some readings
            >>> for _ in range(10):
            ...     sensors[:].value
            >>> 
            >>> # Sensors moved, reset filters
            >>> sensors[:].reset_filter()
        ```
        """
        ...

    @property
    def measurement(self) -> list[bool]:
        """
        Get measurement enabled state for selected sensors.
        
        :return: List of enabled states
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> print(sensors[:].measurement)  # [False, False]
        ```
        """
        ...

    @measurement.setter
    def measurement(self, enable: bool | list[bool]) -> None:
        """
        Enable/disable timer-based non-blocking measurement.
        
        When enabled, measurements are taken automatically at period_ms intervals.
        Results are delivered via callback if set.
        
        :param enable: Single bool for all, or list per sensor
        
        :raises ValueError: If list length doesn't match sensor count
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> sensors[:].callback = my_callback
            >>> sensors[:].nonblocking = True
            >>> sensors[:].measurement = True   # Start timer
            >>> sensors[:].measurement = False  # Stop timer
        ```
        """
        ...

    @property
    def value(self) -> list[int | None]:
        """
        Read distance values.
        
        In blocking mode: triggers measurement and waits for result.
        In nonblocking mode: returns last pending result from timer callback.
        Returns distance in centimeters, rounded to integer.
        Returns None for invalid readings or timeout.
        
        :return: List of distances in cm, or None for each sensor
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> # Blocking read
            >>> distances = sensors[:].value
            >>> for i, d in enumerate(distances):
            ...     if d is not None:
            ...         print(f"Sensor {i}: {d} cm")
        ```
        """
        ...

    @property
    def last(self) -> list[float]:
        """
        Get last measured distance values.
        
        Returns the most recent valid measurement for each sensor.
        Returns -1.0 if no valid measurement has been taken yet.
        
        :return: List of last measured distances in cm
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> sensors[:].value  # Take measurement
            >>> print(sensors[:].last)  # Get last values
        ```
        """
        ...

    @property
    def temperature(self) -> list[float]:
        """
        Get temperature setting in Celsius.
        
        :return: List of temperatures
        """
        ...

    @temperature.setter
    def temperature(self, temp_c: float | list[float]) -> None:
        """
        Set temperature for sound speed calculation.
        
        Sound speed: v = 331.3 + 0.606 * T (m/s)
        
        :param temp_c: Temperature in Celsius (-40 to +85)
        
        :raises ValueError: If temperature out of range
        :raises ValueError: If list length doesn't match sensor count
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> sensors[:].temperature = 25.0  # All sensors
            >>> sensors[0].temperature = 22.0  # First only
        ```
        """
        ...

    @property
    def filter(self) -> list[dict]:
        """
        Get Kalman filter parameters.
        
        :return: List of dicts with keys: R (measurement noise), Q (process noise)
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3)])
            >>> print(sensors[0].filter)  # [{'R': 25.0, 'Q': 4.0}]
        ```
        """
        ...

    @filter.setter
    def filter(self, params: dict) -> None:
        """
        Set Kalman filter parameters.
        
        R: Measurement noise covariance (higher = trust predictions more)
        Q: Process noise covariance (higher = faster response, more noise)
        
        :param params: Dict with optional keys 'R' and 'Q'
        
        :raises TypeError: If params is not a dict
        :raises ValueError: If R or Q <= 0
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3)])
            >>> # Smoother tracking
            >>> sensors[:].filter = {'R': 16.0, 'Q': 1.0}
            >>> # Faster response
            >>> sensors[:].filter = {'R': 4.0, 'Q': 9.0}
        ```
        """
        ...

    @property
    def filter_states(self) -> list[dict]:
        """
        Get Kalman filter internal states.
        
        :return: List of dicts with keys: position, velocity, covariance,
                 measurement_noise, process_noise
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3)])
            >>> state = sensors[0].filter_states[0]
            >>> print(f"Position: {state['position']:.1f} cm")
            >>> print(f"Velocity: {state['velocity']:.1f} cm/s")
        ```
        """
        ...

    @property
    def callback(self) -> list[Callable | None]:
        """
        Get registered measurement callbacks.
        
        :return: List of callbacks or None
        """
        ...

    @callback.setter
    def callback(self, fn: Callable | list[Callable] | None) -> None:
        """
        Set measurement callback(s).
        
        Callback receives a tuple: (trig_pin: int, distance: float | None)
        Called from timer ISR context via micropython.schedule().
        
        :param fn: Single callback for all, list per sensor, or None
        
        :raises ValueError: If list length doesn't match sensor count
        :raises TypeError: If element is not callable or None
        
        Example
        -------
        ```python
            >>> def on_distance(args):
            ...     trig_pin, distance = args
            ...     if distance is not None:
            ...         print(f"Pin {trig_pin}: {distance} cm")
            ...     else:
            ...         print(f"Pin {trig_pin}: timeout")
            >>> 
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> sensors[:].callback = on_distance
            >>> sensors[:].nonblocking = True
            >>> sensors[:].measurement = True
        ```
        """
        ...

    @property
    def sm_ids(self) -> list[int]:
        """
        Get PIO State Machine IDs for selected sensors.
        
        :return: List of State Machine IDs (0-11)
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)], sm=4)
            >>> print(sensors[:].sm_ids)  # [4, 5]
        ```
        """
        ...
