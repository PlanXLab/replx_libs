"""
Utility Tools Library for EFR32MG

Essential utility functions for XBee3 MicroPython embedded development.
Provides commonly used mathematical functions, color conversion, and
timing utilities optimized for resource-constrained EFR32MG environments.

Features:

- Mathematical utility functions (clamp, map, xrange)
- HSV to RGB color conversion
- Random number generation with specified byte size
- Interval timing and scheduling utilities
- Memory-efficient implementations for embedded systems
- Compatible with XBee3 MicroPython

Mathematical Functions:

- clamp: Constrain values within specified bounds
- map: Linear interpolation between value ranges  
- xrange: Floating-point range generator with precision control

Color Functions:

- hsv_to_rgb: Convert HSV color space to RGB values
- rgb_to_hsv: Convert RGB color values to HSV color space

Utility Functions:

- rand: Random number generation using uos.urandom
- intervalChecker: Non-blocking interval timing

"""

from typing import Callable

def clamp(val: int | float, lo: int | float, hi: int | float) -> int | float:
    """
    Constrain a value within the inclusive range [lo, hi].
    
    This function ensures that the input value falls within the specified bounds
    by returning the lower bound if the value is too small, the upper bound if
    the value is too large, or the value itself if it's within range.
    
    :param val: Value to be clamped (numeric type)
    :param lo: Lower bound (inclusive)
    :param hi: Upper bound (inclusive)
    :return: Clamped value within [lo, hi] range
    
    :raises ValueError: If lo > hi
    
    Example
    -------
    ```python
        >>> # Basic clamping operations
        >>> clamp(15, 0, 10)     # Returns 10 (clamped to upper bound)
        >>> clamp(-5, 0, 10)     # Returns 0 (clamped to lower bound)
        >>> clamp(7, 0, 10)      # Returns 7 (within range, unchanged)
        >>> 
        >>> # XBee ADC reading example
        >>> import xbee
        >>> adc_value = xbee.atcmd('%V')  # Read supply voltage
        >>> normalized = clamp(adc_value, 2700, 3600)  # Clamp to valid mV range
        >>> 
        >>> # PWM duty cycle limiting
        >>> duty = clamp(user_input, 0, 100)
        >>> set_pwm_duty(duty)
    ```
    """
    
def map(x: int | float, min_i: int | float, max_i: int | float, min_o: int | float, max_o: int | float) -> int | float:
    """
    Map a value from one range to another using linear interpolation.
    
    This function performs linear interpolation to map a value from an input range
    [min_i, max_i] to an output range [min_o, max_o]. It's commonly used for
    scaling sensor readings, converting between units, and normalizing data.
    
    :param x: Input value to be mapped
    :param min_i: Minimum value of input range
    :param max_i: Maximum value of input range
    :param min_o: Minimum value of output range
    :param max_o: Maximum value of output range
    :return: Mapped value in the output range
    
    :raises ZeroDivisionError: If input range is zero (min_i == max_i)
    
    Example
    -------
    ```python
        >>> # Basic range mapping
        >>> map(50, 0, 100, 0, 255)  # Returns 127.5 (50% of 255)
        >>> 
        >>> # XBee supply voltage to percentage
        >>> import xbee
        >>> mv = xbee.atcmd('%V')  # Read supply voltage in mV
        >>> battery_pct = map(mv, 2700, 3600, 0, 100)  # Convert to percentage
        >>> print(f"Battery: {battery_pct:.0f}%")
        >>> 
        >>> # RSSI to signal strength indicator (0-5 bars)
        >>> rssi = xbee.atcmd('DB')  # Read last RSSI
        >>> bars = map(-rssi, 30, 90, 5, 0)  # Higher RSSI = lower dBm = more bars
        >>> bars = int(clamp(bars, 0, 5))
        >>> print(f"Signal: {'█' * bars}{'░' * (5-bars)}")
    ```
    """

def xrange(start: float, stop: float | None = None, step: float | None = None) -> iter[float]:
    """
    Create a generator that yields floating-point numbers in a specified range.
    
    This function is a floating-point equivalent of Python's range() function,
    allowing precise control over decimal increments. It uses string formatting
    to maintain precision and avoid floating-point arithmetic errors.
    
    :param start: Starting value of the range
    :param stop: Ending value of the range (exclusive). If None, start becomes stop and start becomes 0.0
    :param step: Step size for the range. If None, defaults to 1.0 or -1.0 based on direction
    :return: Generator yielding floating-point values
    
    :raises ValueError: If step is zero
    
    Example
    -------
    ```python
        >>> # Basic floating-point range
        >>> list(xrange(0.0, 1.0, 0.2))
        [0.0, 0.2, 0.4, 0.6, 0.8]
        >>> 
        >>> # Single argument (stop only)
        >>> list(xrange(3.0))  # Equivalent to xrange(0.0, 3.0, 1.0)
        [0.0, 1.0, 2.0]
        >>> 
        >>> # Descending range
        >>> list(xrange(5.0, 0.0, -1.0))
        [5.0, 4.0, 3.0, 2.0, 1.0]
        >>> 
        >>> # Temperature calibration sweep
        >>> for temp in xrange(20.0, 30.0, 0.5):
        ...     calibrate_sensor(temp)
        ...     utime.sleep(1)
    ```
    """

def rand(size: int = 4) -> int:
    """
    Generate a random number of specified byte size.
    
    This function uses uos.urandom to create random numbers suitable for
    various applications. Note: XBee3's urandom may not be cryptographically
    secure for all use cases.
    
    :param size: The size of the random number in bytes (default: 4 bytes)
    
        - 1 byte: 0 to 255
        - 2 bytes: 0 to 65,535  
        - 4 bytes: 0 to 4,294,967,295
        - 8 bytes: 0 to 18,446,744,073,709,551,615
    
    :return: Random number as integer within the range for specified byte size
    
    :raises ValueError: If size <= 0 or size > 8
    
    Example
    -------
    ```python
        >>> # Generate random numbers of different sizes
        >>> rand(1)  # 8-bit random number (0-255)
        >>> rand(4)  # 32-bit random number (default)
        >>> 
        >>> # Random XBee network identifier
        >>> network_id = rand(2)  # Random 16-bit ID
        >>> xbee.atcmd('ID', network_id)
        >>> 
        >>> # Randomized transmission backoff
        >>> jitter_ms = rand(1) % 100  # Random delay 0-99ms
        >>> utime.sleep_ms(base_delay + jitter_ms)
        >>> 
        >>> # Generate random session token
        >>> token = rand(4)
        >>> print(f"Session: 0x{token:08X}")
    ```
    """

def intervalChecker(interval_ms: int) -> Callable[[], bool]:
    """
    Create a function that checks if a specified time interval has elapsed.
    
    This function returns a closure that tracks time and indicates when the
    specified interval has passed since the last positive check. It's useful
    for implementing periodic operations without blocking execution.
    
    :param interval_ms: The interval in milliseconds to check
    :return: Function that returns True when interval has elapsed, False otherwise
    
    :raises ValueError: If interval_ms <= 0 or not an integer
    
    Example
    -------
    ```python
        >>> # Basic periodic operation without blocking
        >>> check_sensor = intervalChecker(1000)  # Check every 1 second
        >>> 
        >>> # Main loop with non-blocking timing
        >>> while True:
        ...     if check_sensor():
        ...         # This executes approximately every 1 second
        ...         temp = xbee.atcmd('TP')  # Read temperature
        ...         print(f"Temperature: {temp}°C")
        ...     
        ...     # Other operations continue without delay
        ...     process_xbee_messages()
        >>> 
        >>> # Multiple independent timers for XBee operations
        >>> check_network = intervalChecker(5000)   # Network check every 5s
        >>> send_heartbeat = intervalChecker(10000) # Heartbeat every 10s
        >>> 
        >>> while True:
        ...     if check_network():
        ...         ai = xbee.atcmd('AI')
        ...         if ai != 0:
        ...             print("Network lost, rejoining...")
        ...     
        ...     if send_heartbeat():
        ...         xbee.transmit(xbee.ADDR_COORDINATOR, b'ALIVE')
        ...     
        ...     utime.sleep_ms(100)
    ```
    """
