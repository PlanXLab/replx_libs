"""
Utility Tools Library

Essential utility functions for MicroPython embedded development.
Provides commonly used mathematical functions, color conversion, and
timing utilities optimized for resource-constrained environments.

Features:

- Mathematical utility functions (clamp, map, xrange)
- HSV to RGB color conversion
- Random number generation with specified byte size
- Interval timing and scheduling utilities
- Memory-efficient implementations for embedded systems
- Cross-platform compatibility for MicroPython devices

Mathematical Functions:

- clamp: Constrain values within specified bounds
- map: Linear interpolation between value ranges  
- xrange: Floating-point range generator with precision control

Color Functions:

- hsv_to_rgb: Convert HSV color space to RGB values

Utility Functions:

- rand: Cryptographically secure random number generation
- intervalChecker: Non-blocking interval timing

"""

import micropython


__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


@micropython.native
def clamp(val: float, lo: float, hi: float) -> float:
    """
    Constrain a value within the inclusive range [lo, hi].
    
    This function ensures that the input value falls within the specified bounds
    by returning the lower bound if the value is too small, the upper bound if
    the value is too large, or the value itself if it's within range.
    
    :param val: Value to be clamped (numeric type)
    :param lo: Lower bound (inclusive)
    :param hi: Upper bound (inclusive)
    :return: Clamped value within [lo, hi] range
    
    :raises TypeError: If arguments are not numeric
    :raises ValueError: If lo > hi
    
    Example
    -------
    ```python
        >>> # Basic clamping operations
        >>> clamp(15, 0, 10)     # Returns 10 (clamped to upper bound)
        >>> clamp(-5, 0, 10)     # Returns 0 (clamped to lower bound)
        >>> clamp(7, 0, 10)      # Returns 7 (within range, unchanged)
        >>> 
        >>> # Practical application: Limiting sensor values
        >>> adc_value = adc.read_u16()
        >>> normalized = clamp(adc_value, 1000, 64000)  # Clamp to valid range
        >>> percentage = (normalized - 1000) / (64000 - 1000) * 100
        >>> 
        >>> # Input validation
        >>> try:
        ...     clamp(5, 10, 5)  # Invalid: lower bound > upper bound
        >>> except ValueError as e:
        ...     print(f"Error: {e}")
    ```
    """

@micropython.native
def map(x: float, min_i: float, max_i: float, min_o: float, max_o: float) -> float:
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
    :raises TypeError: If arguments are not numeric
    
    Example
    -------
    ```python
        >>> # Basic range mapping
        >>> map(50, 0, 100, 0, 255)  # Returns 127.5 (50% of 255)
        >>> 
        >>> # ADC to voltage conversion
        >>> adc_value = adc.read_u16()  # 0-65535 range
        >>> voltage = map(adc_value, 0, 65535, 0, 3.3)
        >>> print(f"Voltage: {voltage:.3f}V")
        >>> 
        >>> # Servo control - angle to pulse width
        >>> angle = 45  # degrees (-90 to +90)
        >>> pulse_width = map(angle, -90, 90, 1000, 2000)  # microseconds
        >>> servo.duty_us(int(pulse_width))
    ```
    """

@micropython.native
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
    :raises TypeError: If arguments are not numeric
    
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
        >>> # Practical application: PWM sweep
        >>> for duty in xrange(0, 100, 5):  # 0% to 100% in 5% steps
        ...     pwm.duty(duty)
        ...     utime.sleep_ms(100)  # Smooth transition
    ```
    """


def rand(size: int = 4) -> int:
    """
    Generate a cryptographically secure random number of specified byte size.
    
    This function uses the system's random number generator to create secure
    random numbers suitable for cryptographic applications, session tokens,
    and other security-sensitive uses.
    
    :param size: The size of the random number in bytes (default: 4 bytes)
    
        - 1 byte: 0 to 255
        - 2 bytes: 0 to 65,535  
        - 4 bytes: 0 to 4,294,967,295
        - 8 bytes: 0 to 18,446,744,073,709,551,615
    
    :return: Random number as integer within the range for specified byte size
    
    :raises ValueError: If size <= 0 or size > 8
    :raises OSError: If system random generator is not available
    
    Example
    -------
    ```python
        >>> # Generate random numbers of different sizes
        >>> rand(1)  # 8-bit random number (0-255)
        >>> rand(4)  # 32-bit random number (default)
        >>> 
        >>> # Generate random identifier
        >>> device_id = rand(4)
        >>> print(f"Device ID: 0x{device_id:08X}")
        >>> 
        >>> # Randomized timing for anti-collision
        >>> jitter_ms = rand(1) % 100  # Random delay 0-99ms
        >>> utime.sleep_ms(base_delay + jitter_ms)
        >>> 
        >>> # Input validation
        >>> try:
        ...     rand(10)  # Invalid: size > 8
        >>> except ValueError as e:
        ...     print(f"Error: {e}")
    ```
    """

def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int,int,int]:
    """
    Convert HSV (Hue, Saturation, Value) color values to RGB format.
    
    This function converts HSV color space to RGB color space, commonly used
    for color manipulation, LED control, and graphics applications. HSV is
    often more intuitive for color selection as it separates color (hue),
    intensity (saturation), and brightness (value).
    
    :param h: Hue value in degrees (0-360)
        - 0° = Red
        - 60° = Yellow  
        - 120° = Green
        - 180° = Cyan
        - 240° = Blue
        - 300° = Magenta
    :param s: Saturation value (0.0-1.0)
        - 0.0 = Grayscale (no color)
        - 1.0 = Full color saturation
    :param v: Value/brightness (0.0-1.0)
        - 0.0 = Black (no brightness)
        - 1.0 = Full brightness
    :return: RGB values as tuple of integers (red, green, blue) in range 0-255
    
    :raises TypeError: If parameters are not numeric
    
    Example
    -------
    ```python
        >>> # Primary colors
        >>> hsv_to_rgb(0, 1.0, 1.0)    # Red: (255, 0, 0)
        >>> hsv_to_rgb(120, 1.0, 1.0)  # Green: (0, 255, 0)
        >>> hsv_to_rgb(240, 1.0, 1.0)  # Blue: (0, 0, 255)
        >>> 
        >>> # Color variations
        >>> hsv_to_rgb(60, 1.0, 1.0)   # Yellow: (255, 255, 0)
        >>> hsv_to_rgb(180, 1.0, 1.0)  # Cyan: (0, 255, 255)
        >>> hsv_to_rgb(300, 1.0, 1.0)  # Magenta: (255, 0, 255)
        >>> 
        >>> # Brightness control (varying value)
        >>> hsv_to_rgb(0, 1.0, 0.5)    # Dim red: (127, 0, 0)
        >>> hsv_to_rgb(0, 1.0, 0.25)   # Dark red: (63, 0, 0)
        >>> 
        >>> # Saturation control (color intensity)
        >>> hsv_to_rgb(0, 0.5, 1.0)    # Pale red: (255, 127, 127)
        >>> hsv_to_rgb(0, 0.0, 1.0)    # White: (255, 255, 255)
        >>> 
        >>> # Rainbow effect for RGB LEDs
        >>> import neopixel
        >>> np = neopixel.NeoPixel(machine.Pin(18), 8)
        >>> 
        >>> def rainbow_cycle():
        ...     for i in range(8):  # 8 LEDs
        ...         hue = (i * 360) / 8  # Distribute hues across LEDs
        ...         r, g, b = hsv_to_rgb(hue, 1.0, 0.5)  # Full saturation, half brightness
        ...         np[i] = (r, g, b)
        ...     np.write()
        >>> 
        >>> # Color breathing effect
        >>> def breathing_effect(hue, duration_ms=2000):
        ...     steps = 50
        ...     for i in range(steps):
        ...         # Sine wave for smooth breathing
        ...         import math
        ...         brightness = (math.sin(2 * math.pi * i / steps) + 1) / 2
        ...         r, g, b = hsv_to_rgb(hue, 1.0, brightness)
        ...         set_led_color(r, g, b)
        ...         utime.sleep_ms(duration_ms // steps)
        >>> 
        >>> # Temperature-based color indication
        >>> def temp_to_color(temp_celsius):
        ...     # Map temperature to hue: blue (cold) to red (hot)
        ...     if temp_celsius < 0:
        ...         hue = 240  # Blue for very cold
        ...     elif temp_celsius > 40:
        ...         hue = 0    # Red for very hot
        ...     else:
        ...         hue = 240 - (temp_celsius / 40) * 240  # Blue to red gradient
        ...     
        ...     return hsv_to_rgb(hue, 1.0, 1.0)
        >>> 
        >>> # Status indication with color coding
        >>> STATUS_COLORS = {
        ...     'idle': hsv_to_rgb(0, 0, 0.3),      # Dim white
        ...     'working': hsv_to_rgb(60, 1.0, 1.0), # Yellow
        ...     'success': hsv_to_rgb(120, 1.0, 1.0), # Green
        ...     'error': hsv_to_rgb(0, 1.0, 1.0),     # Red
        ...     'warning': hsv_to_rgb(30, 1.0, 1.0)   # Orange
        ... }
    ```
    """

def intervalChecker(interval_ms: int) -> callable:
    """
    Create a function that checks if a specified time interval has elapsed.
    
    This function returns a closure that tracks time and indicates when the
    specified interval has passed since the last positive check. It's useful
    for implementing periodic operations without blocking execution.
    
    :param interval_ms: The interval in milliseconds to check
    :return: Function that returns True when interval has elapsed, False otherwise
    
    :raises ValueError: If interval_ms <= 0
    :raises TypeError: If interval_ms is not an integer
    
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
        ...         sensor_value = read_sensor()
        ...         print(f"Sensor value: {sensor_value}")
        ...     
        ...     # Other operations continue without delay
        ...     process_input()
        ...     update_display()
        ...     utime.sleep_ms(10)
        >>> 
        >>> # Multiple independent timers
        >>> fast_check = intervalChecker(100)    # Fast operations (100ms)
        >>> slow_check = intervalChecker(5000)   # Slow operations (5s)
        >>> 
        >>> while True:
        ...     if fast_check():
        ...         update_leds()
        ...     
        ...     if slow_check():
        ...         log_data()
        ...     
        ...     # No blocking delays needed
        ...     utime.sleep_ms(10)
    ```
    """