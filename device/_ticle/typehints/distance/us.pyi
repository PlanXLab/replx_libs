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
- _std-compatible single-sensor API: read(), trigger(), ready(), result(), last

Distance unit: metres (float)

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
        >>> from ticle_lite.us import SR04 as UltraSonic
        >>> 
        >>> # _std-compatible single-sensor usage
        >>> sonic = UltraSonic(trig=10, echo=11)
        >>> dist_m = sonic.read()  # blocking read, returns float (metres)
        >>> 
        >>> # Non-blocking
        >>> sonic.trigger()
        >>> while not sonic.ready():
        ...     pass
        >>> dist_m = sonic.result()
        >>> 
        >>> # Multi-sensor (original API)
        >>> sensors = SR04([(2, 3), (4, 5)])  # [(trig, echo), ...]
        >>> sensors[:].temperature = 25.0
        >>> distances = sensors[:].value  # list[float | None] in metres
        >>> 
        >>> # Continuous non-blocking
        >>> def on_distance(args):
        ...     trig_pin, dist = args
        ...     if dist is not None:
        ...         print(f"{dist:.3f} m")
        >>> sensors[:].callback = on_distance
        >>> sensors[:].measurement = True
        >>> # ... measurements arrive via callback ...
        >>> sensors[:].measurement = False
        >>> sensors.deinit()
    ```
    """

    def __init__(
        self,
        sensor_configs: list[tuple[int, int]] | None = None,
        *,
        trig: int | list[int] | None = None,
        echo: int | list[int] | None = None,
        temp_c: float = 20.0,
        R: int = 25,
        Q: int = 4,
        pio: int | list[int] | tuple[int, ...] | None = 2
    ) -> None:
        """
        Initialize multi-channel SR04 driver with PIO State Machines.

        Accepts either the multi-sensor list form or the single-sensor
        keyword form compatible with the _std SR04 API.

        :param sensor_configs: List of (trig_pin, echo_pin) tuples. If omitted,
            use ``trig`` and ``echo`` keyword arguments instead.
        :param trig: Trigger pin(s) — used when sensor_configs is None
        :param echo: Echo pin(s) — used when sensor_configs is None
        :param temp_c: Initial ambient temperature in Celsius (default: 20.0)
        :param R: Kalman measurement noise covariance in cm² (default: 25, range 10-100)
        :param Q: Kalman process noise covariance in cm² (default: 4, range 1-10)
        :param pio: PIO block selection (default: 2). Can be:
            - int (e.g., 2): single PIO block
            - list/tuple (e.g., [0, 2]): search free SMs within specified PIO blocks
            - None or [0, 1, 2]: search across all PIO blocks using default preferred order

        :raises ValueError: If neither sensor_configs nor trig/echo provided,
            or sensor_configs is empty, or temperature out of range
        :raises RuntimeError: If no free state machines available
        :raises OSError: If PIO initialization fails

        Note
        ----
        Uses len(sensor_configs) PIO State Machines (1 per sensor). Call deinit() to release.

        Example
        -------
        ```python
            >>> # Single sensor, _std-compatible
            >>> sonic = SR04(trig=10, echo=11)
            >>> dist_m = sonic.read()
            >>> 
            >>> # Multi-sensor list form
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> 
            >>> # With custom Kalman and specific PIO block
            >>> sonic = SR04(trig=10, echo=11, R=16, Q=1, pio=1)
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Access sensor(s) by index or slice.

        :param idx: Integer index or slice.
        :return: ``_View`` for the selected sensor(s).

        :raises IndexError: If index is out of range.
        :raises TypeError: If *idx* is not int or slice.

        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5), (6, 7)])
            >>> sensors[0].value              # single sensor
            >>> sensors[1:].temperature = 22.0  # last two sensors
            >>> sensors[:].measurement = True   # all sensors
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return the number of configured sensors.

        :return: Sensor count.

        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> len(sensors)
            2
        ```
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
            >>> sonic = SR04(trig=10, echo=11)
            >>> sonic.deinit()
        ```
        """
        ...

    # ---- _std-compatible single-sensor API ----

    def read(self, timeout_us: int | None = None) -> float:
        """
        Blocking read for sensor 0. Returns distance in metres, or nan.

        :param timeout_us: Echo timeout in microseconds (default: _TIMEOUT_US).
        :return: Distance in metres, or ``float('nan')`` on timeout/invalid.

        Example
        -------
        ```python
            >>> sonic = SR04(trig=10, echo=11)
            >>> dist_m = sonic.read()
            >>> if dist_m == dist_m:  # nan check
            ...     print(f"{dist_m:.3f} m")
        ```
        """
        ...

    @property
    def last(self) -> float:
        """
        Last valid distance in metres for sensor 0.

        :return: Last measurement in metres, or -1.0 if none yet.

        Example
        -------
        ```python
            >>> sonic = SR04(trig=10, echo=11)
            >>> sonic.read()
            >>> print(sonic.last)
        ```
        """
        ...

    def trigger(self) -> None:
        """
        Fire trigger pulse for sensor 0 (non-blocking).

        Follow with ``ready()`` polling and ``result()`` to retrieve value.

        Example
        -------
        ```python
            >>> sonic = SR04(trig=10, echo=11)
            >>> sonic.trigger()
            >>> while not sonic.ready():
            ...     pass
            >>> dist_m = sonic.result()
        ```
        """
        ...

    def ready(self) -> bool:
        """
        True if echo result is waiting in the FIFO for sensor 0.

        :return: ``True`` when ``result()`` can be called without blocking.

        Example
        -------
        ```python
            >>> sonic.trigger()
            >>> while not sonic.ready():
            ...     pass  # or do other work
            >>> dist_m = sonic.result()
        ```
        """
        ...

    def result(self) -> float:
        """
        Read pending echo result for sensor 0.

        :return: Distance in metres, or ``float('nan')`` if not ready or invalid.

        Example
        -------
        ```python
            >>> sonic.trigger()
            >>> while not sonic.ready():
            ...     pass
            >>> print(f"{sonic.result():.3f} m")
        ```
        """
        ...

    def reset_filter(self) -> None:
        """
        Reset Kalman filter state for all sensors.

        Example
        -------
        ```python
            >>> sonic = SR04(trig=10, echo=11)
            >>> sonic.reset_filter()
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
        Further narrow the view by index or slice.

        :param idx: Integer index or slice (relative to this view).
        :return: New ``_View`` containing the selected sensors.

        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5), (6, 7)])
            >>> sensors[:][0].value     # first sensor via nested view
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return the number of sensors in this view.

        :return: Sensor count.

        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> len(sensors[:])
            2
        ```
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
        Enable or disable timer-based non-blocking measurement.

        When enabled, measurements are taken automatically via an internal
        timer.  Results are delivered to the registered callback if set.

        :param enable: Single bool applied to all selected sensors, or a list
            with one value per sensor.

        :raises ValueError: If list length does not match sensor count.

        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> sensors[:].callback = my_callback
            >>> sensors[:].measurement = True    # start timer
            >>> sensors[:].measurement = False   # stop timer
        ```
        """
        ...

    @property
    def value(self) -> list[float | None]:
        """
        Read distance values in metres.
        
        In blocking mode: triggers measurement and waits for result.
        In continuous mode: returns latest result from IRQ.
        Returns None for invalid readings or timeout.
        
        :return: List of distances in metres (float), or None per sensor.
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> distances = sensors[:].value
            >>> for i, d in enumerate(distances):
            ...     if d is not None:
            ...         print(f"Sensor {i}: {d:.3f} m")
        ```
        """
        ...

    @property
    def last(self) -> list[float]:
        """
        Get last measured distance values in metres.
        
        Returns the most recent valid measurement for each sensor.
        Returns -1.0 if no valid measurement has been taken yet.
        
        :return: List of last measured distances in metres.
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> sensors[:].value
            >>> print(sensors[:].last)  # e.g. [0.235, 1.048]
        ```
        """
        ...

    @property
    def temperature(self) -> list[float]:
        """
        Get the temperature setting for selected sensors in Celsius.

        :return: List of temperatures.

        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> print(sensors[:].temperature)
            [20.0, 20.0]
        ```
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
        Get Kalman filter parameters in cm² scale.
        
        :return: List of dicts with keys: R (measurement noise), Q (process noise)
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3)])
            >>> print(sensors[0].filter)  # [{'R': 25, 'Q': 4}]
        ```
        """
        ...

    @filter.setter
    def filter(self, params: dict) -> None:
        """
        Set Kalman filter parameters in cm² scale.
        
        R: Measurement noise covariance (higher = trust predictions more, range 10-100)
        Q: Process noise covariance (higher = faster response, more noise, range 1-10)
        
        :param params: Dict with optional keys 'R' and 'Q'
        
        :raises TypeError: If params is not a dict
        :raises ValueError: If R is not in range 10-100 or Q is not in range 1-10
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3)])
            >>> # Smoother tracking
            >>> sensors[:].filter = {'R': 40, 'Q': 1}
            >>> # Faster response
            >>> sensors[:].filter = {'R': 15, 'Q': 9}
        ```
        """
        ...

    @property
    def filter_states(self) -> list[dict]:
        """
        Get Kalman filter internal states.
        
        :return: List of dicts with keys: position, velocity, covariance,
                 measurement_noise (in cm²), process_noise (in cm²)
        
        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3)])
            >>> state = sensors[0].filter_states[0]
            >>> print(f"Position: {state['position']:.3f} m")
            >>> print(f"Velocity: {state['velocity']:.3f} m/s")
        ```
        """
        ...

    @property
    def callback(self) -> list[Callable | None]:
        """
        Get the registered measurement callbacks for selected sensors.

        :return: List of callables or ``None`` for each sensor.

        Example
        -------
        ```python
            >>> sensors = SR04([(2, 3)])
            >>> print(sensors[0].callback)
            [None]
        ```
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
            ...         print(f"Pin {trig_pin}: {distance:.3f} m")
            ...     else:
            ...         print(f"Pin {trig_pin}: timeout")
            >>> 
            >>> sensors = SR04([(2, 3), (4, 5)])
            >>> sensors[:].callback = on_distance
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
