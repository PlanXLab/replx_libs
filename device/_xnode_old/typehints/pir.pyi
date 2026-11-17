"""
XNode Extension Modules Library

Comprehensive driver library for external sensor and peripheral modules compatible with
the XNode (XBee-based IoT node) platform. Provides high-level interfaces for motion
detection, temperature sensing, orientation tracking, GPS positioning, and basic I/O
expansion modules commonly used in IoT and automation applications.

This library abstracts the complexities of sensor communication protocols (I2C, UART)
and provides intuitive Python interfaces for rapid prototyping and deployment of
sensor-based applications including security systems, environmental monitoring,
navigation solutions, and educational projects.

Supported Modules:

- PIR Motion Sensor: Edge detection with configurable timeout and enter/leave state tracking
- IR Thermometer (MLX90614): Non-contact ambient and object temperature measurement
- IMU (BNO055): 9-DOF absolute orientation with sensor fusion (accelerometer, gyroscope, magnetometer)
- GPS Module: NMEA sentence parsing with configurable update rates and multiple output formats
- Basic I/O Board: PCA9535-based LED array, button matrix, and buzzer control

Key Features:

- Plug-and-play sensor initialization with sensible defaults
- Configurable measurement parameters for application-specific tuning
- Real-time data acquisition with efficient polling patterns
- Low-power operation support for battery-powered deployments
- I2C and UART communication abstraction

Author: PlanXLab Development Team
"""


class Pir:
    """
    PIR (Passive Infrared) motion sensor controller.
    
    This class provides an interface for PIR motion sensors with edge detection
    capabilities. Supports simple motion detection, state change monitoring,
    and configurable detection with timeout for debouncing.
    
    Key Features:
    
        - Simple binary motion detection
        - Edge detection (enter/leave states)
        - Configurable debounce timeout
        - Low-power polling support
    """
    
    NONE: int
    DETECT: int
    ENTER: int
    LEAVE: int
    
    def __init__(self) -> None:
        """
        Initialize the PIR motion sensor.
        
        Sets up the PIR sensor on the P2 input pin with appropriate
        configuration for motion detection.
        
        Example
        --------
        ```python
            >>> pir = Pir()
            >>> 
            >>> # Simple motion check
            >>> if pir.read():
            ...     print("Motion detected!")
            >>> 
            >>> # Continuous monitoring
            >>> while True:
            ...     if pir.read():
            ...         print("Movement!")
            ...     utime.sleep_ms(100)
        ```
        """
        
    def read(self) -> int:
        """
        Read the current PIR sensor state.
        
        Returns the raw sensor output indicating whether motion is
        currently being detected.
        
        :return: Pir.DETECT (1) if motion is detected, Pir.NONE (0) otherwise
        
        Example
        --------
        ```python
            >>> pir = Pir()
            >>> 
            >>> # Simple detection
            >>> motion = pir.read()
            >>> print(f"Motion: {'Yes' if motion else 'No'}")
            >>> 
            >>> # Count motion events
            >>> count = 0
            >>> for _ in range(100):
            ...     if pir.read():
            ...         count += 1
            ...     utime.sleep_ms(100)
            >>> print(f"Motion detected {count} times")
            >>> 
            >>> # Security alarm
            >>> while True:
            ...     if pir.read():
            ...         trigger_alarm()
            ...         break
            ...     utime.sleep_ms(50)
        ```
        """

    def state(self, timeout: int = 1) -> int:
        """
        Get the edge state of the PIR sensor.
        
        Compares current and previous sensor states to detect transitions
        (entering or leaving detection zone). Useful for counting entries
        or triggering on state changes.
        
        :param timeout: Time in milliseconds between state samples (default: 1)
        :return: ENTER (2) for rising edge, LEAVE (3) for falling edge, or current state if no change
        
        Example
        --------
        ```python
            >>> pir = Pir()
            >>> 
            >>> # Detect entry/exit
            >>> while True:
            ...     state = pir.state()
            ...     if state == Pir.ENTER:
            ...         print("Someone entered!")
            ...     elif state == Pir.LEAVE:
            ...         print("Someone left!")
            ...     utime.sleep_ms(10)
            >>> 
            >>> # Entry counter
            >>> entries = 0
            >>> while True:
            ...     if pir.state() == Pir.ENTER:
            ...         entries += 1
            ...         print(f"Total entries: {entries}")
            ...     utime.sleep_ms(10)
            >>> 
            >>> # Presence detection with hysteresis
            >>> present = False
            >>> while True:
            ...     state = pir.state(timeout=50)
            ...     if state == Pir.ENTER:
            ...         present = True
            ...         print("Presence detected")
            ...     elif state == Pir.LEAVE:
            ...         present = False
            ...         print("Area cleared")
        ```
        """
    
    def detect(self, timeout: int = 1500) -> bool:
        """
        Detect sustained motion within timeout period.
        
        Returns True only if motion has been continuously detected for
        at least the specified timeout duration. Useful for filtering
        out brief false positives.
        
        :param timeout: Minimum detection duration in milliseconds (default: 1500)
        :return: True if sustained motion detected, False otherwise
        
        Example
        --------
        ```python
            >>> pir = Pir()
            >>> 
            >>> # Detect sustained presence
            >>> if pir.detect():
            ...     print("Confirmed presence!")
            >>> 
            >>> # Occupancy detection with 2-second threshold
            >>> while True:
            ...     if pir.detect(timeout=2000):
            ...         print("Room occupied")
            ...         turn_on_lights()
            ...     else:
            ...         print("Room empty")
            ...         turn_off_lights()
            ...     utime.sleep(1)
            >>> 
            >>> # Security with confirmation
            >>> if pir.detect(timeout=3000):
            ...     print("Intruder confirmed!")
            ...     trigger_alarm()
        ```
        """
