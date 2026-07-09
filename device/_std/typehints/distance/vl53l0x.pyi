"""
VL53L0X Time-of-Flight Distance Sensor Driver

I2C-based laser ranging sensor driver with configurable measurement modes.
Supports continuous and timed measurement with optional median and low-pass filtering.

Features:

- I2C communication via I2CController
- Multiple preset modes (Default, Long Range, High Accuracy, High Speed)
- Continuous (back-to-back) or timed measurement modes
- Type A sensor API: start() / ready() / result() pattern
- Optional median filter for noise reduction
- Optional low-pass filter for smoothing
- Valid range checking (default: 5cm - 1.2m)

"""
from i2c import I2CController


class VL53L0X:
    """
    VL53L0X Time-of-Flight distance sensor driver.
    
    Laser-based ranging sensor with I2C interface.
    Supports multiple measurement presets and filtering options.
    
    Implements Type A sensor pattern:
    
    - ``start()`` - Begin continuous measurement
    - ``ready()`` - Check if new data available
    - ``result()`` - Read measurement result
    - ``read()`` - Blocking convenience method
    
    Example
    -------
    ```python
        >>> from i2c import I2CController
        >>> from vl53l0x import VL53L0X
        >>> 
        >>> i2c = I2CController(sda=4, scl=5)
        >>> 
        >>> # Basic usage (continuous mode, auto-started)
        >>> sensor = VL53L0X(i2c)
        >>> distance = sensor.read()
        >>> print(f"Distance: {distance:.3f} m")
        >>> 
        >>> # Non-blocking polling
        >>> sensor = VL53L0X(i2c)
        >>> while True:
        ...     if sensor.ready():
        ...         d = sensor.result()
        ...         if d is not None:
        ...             print(f"{d:.3f} m")
        ...     # do other work
        >>> 
        >>> # High accuracy mode with filtering
        >>> sensor = VL53L0X(
        ...     i2c,
        ...     preset=VL53L0X.MODE_PRESET_HIGH_ACCURACY,
        ...     median=7, lpf=0.2
        ... )
    ```
    """

    MODE_PRESET_DEFAULT: int
    MODE_PRESET_LONG_RANGE: int
    MODE_PRESET_HIGH_ACCURACY: int
    MODE_PRESET_HIGH_SPEED: int

    def __init__(
        self,
        i2c: I2CController,
        *,
        addr: int = 0x29,
        preset: int = ...,
        period_ms: int = 0,
        timeout_ms: int = 250,
        min_valid_m: float = 0.05,
        max_valid_m: float | None = 1.2,
        median: int | None = 5,
        lpf: float | None = None
    ) -> None:
        """
        Initialize VL53L0X sensor.
        
        Automatically starts continuous measurement after initialization.
        
        :param i2c: Shared I2CController instance
        :param addr: I2C address (default: 0x29)
        :param preset: Measurement preset mode (default: MODE_PRESET_DEFAULT)
        :param period_ms: Measurement period in ms. 0 for back-to-back continuous (default: 0)
        :param timeout_ms: Read timeout in milliseconds (default: 250)
        :param min_valid_m: Minimum valid distance in meters (default: 0.05)
        :param max_valid_m: Maximum valid distance in meters, None for no limit (default: 1.2)
        :param median: Median filter window size, None to disable (default: 5)
        :param lpf: Low-pass filter time constant (tau) in seconds, None to disable (default: None)
        
        :raises RuntimeError: If sensor is not responding on I2C bus
        :raises ValueError: If invalid preset is specified
        
        Example
        -------
        ```python
            >>> from i2c import I2CController
            >>> from vl53l0x import VL53L0X
            >>> i2c = I2CController(sda=4, scl=5)
            >>> 
            >>> # Default mode (33ms timing budget)
            >>> sensor = VL53L0X(i2c)
            >>> 
            >>> # Long range mode (up to 2m, 200ms timing)
            >>> sensor = VL53L0X(
            ...     i2c,
            ...     preset=VL53L0X.MODE_PRESET_LONG_RANGE,
            ...     max_valid_m=2.0
            ... )
            >>> 
            >>> # High speed mode (20ms timing, less accurate)
            >>> sensor = VL53L0X(
            ...     i2c,
            ...     preset=VL53L0X.MODE_PRESET_HIGH_SPEED
            ... )
            >>> 
            >>> # Timed measurement at 100ms intervals
            >>> sensor = VL53L0X(i2c, period_ms=100)
            >>> 
            >>> # With filtering (median -> low-pass chain)
            >>> sensor = VL53L0X(i2c, median=7, lpf=0.1)
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Release hardware resources.
        
        Stops continuous measurement if running.
        Safe to call multiple times.
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> # ... use sensor ...
            >>> sensor.deinit()
        ```
        """
        ...

    @property
    def last(self) -> float:
        """
        Get the last measured distance.
        
        :return: Last distance in meters, or -1.0 if no valid reading yet
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> sensor.read()
            >>> print(f"Last: {sensor.last:.3f} m")
        ```
        """
        ...

    def start(self, period_ms: int = 0) -> None:
        """
        Start continuous measurement.
        
        Called automatically during initialization. Call manually after stop()
        to resume measurement.
        
        :param period_ms: Measurement period in ms. 0 for back-to-back continuous (default: 0)
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> sensor.stop()
            >>> # ... pause ...
            >>> sensor.start()  # Resume back-to-back
            >>> 
            >>> # Or start with timed interval
            >>> sensor.start(period_ms=100)
        ```
        """
        ...

    def stop(self) -> None:
        """
        Stop continuous measurement.
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> # ... use sensor ...
            >>> sensor.stop()
            >>> # Sensor is now idle, lower power consumption
        ```
        """
        ...

    def ready(self) -> bool:
        """
        Check if new measurement data is available.
        
        Use with result() for non-blocking operation.
        
        :return: True if new data available, False otherwise
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> while True:
            ...     if sensor.ready():
            ...         d = sensor.result()
            ...         if d is not None:
            ...             print(f"{d:.3f} m")
            ...     # do other tasks
            ...     time.sleep_ms(10)
        ```
        """
        ...

    def result(self) -> float | None:
        """
        Read measurement result (non-blocking).
        
        Call after ready() returns True. Returns None if data is invalid
        or out of range. Applies configured filters to valid readings.
        
        :return: Distance in meters, or None if invalid/out of range
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> if sensor.ready():
            ...     d = sensor.result()
            ...     if d is not None:
            ...         print(f"Distance: {d:.3f} m")
            ...     else:
            ...         print("Invalid reading")
        ```
        """
        ...

    def read(self, timeout_ms: int | None = None) -> float:
        """
        Measure distance (blocking).
        
        Waits for ready() then calls result(). Returns last valid reading
        on timeout or invalid data.
        
        :param timeout_ms: Maximum wait time in ms, None uses init value (default: None)
        :return: Distance in meters, or last valid reading on timeout
        
        :raises RuntimeError: If measurement not started
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> 
            >>> # Single reading
            >>> distance = sensor.read()
            >>> print(f"Distance: {distance:.3f} m")
            >>> 
            >>> # With custom timeout
            >>> distance = sensor.read(timeout_ms=500)
        ```
        """
        ...

    def reset_filter(self) -> None:
        """
        Reset filter state.
        
        Clears accumulated filter history. Call after sensor repositioning
        or when measurement conditions change significantly.
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c, median=5)
            >>> for _ in range(10):
            ...     sensor.read()
            >>> 
            >>> # Sensor moved, reset filter
            >>> sensor.reset_filter()
        ```
        """
        ...

    def set_signal_rate_limit_mcps(self, limit_mcps: float = 0.25) -> None:
        """
        Set signal rate limit.
        
        Lower values allow longer range but may increase noise.
        Higher values are more reliable but limit range.
        
        :param limit_mcps: Signal rate limit in MCPS (default: 0.25)
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> sensor.set_signal_rate_limit_mcps(0.1)  # Extended range
        ```
        """
        ...

    def get_measurement_timing_budget_us(self) -> int:
        """
        Get current measurement timing budget.
        
        :return: Timing budget in microseconds
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> budget = sensor.get_measurement_timing_budget_us()
            >>> print(f"Budget: {budget} us")
        ```
        """
        ...

    def set_measurement_timing_budget_us(self, budget_us: int) -> None:
        """
        Set measurement timing budget.
        
        Longer budget increases accuracy but slows measurement rate.
        Minimum value is 20000 (20ms).
        
        :param budget_us: Timing budget in microseconds (minimum: 20000)
        
        :raises ValueError: If budget is too small for current configuration
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> sensor = VL53L0X(i2c)
            >>> sensor.set_measurement_timing_budget_us(50000)  # 50ms for better accuracy
        ```
        """
        ...
