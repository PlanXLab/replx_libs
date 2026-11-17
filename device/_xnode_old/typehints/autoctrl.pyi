"""
AutoCtrl Hardware Control Library

Comprehensive hardware abstraction for XNode automation control peripherals including
DIO ports, relay control, PWM outputs, and specialized device interfaces for building
automation and IoT applications. Designed for industrial control systems, smart home
automation, and facility management solutions.

This library provides a unified interface for controlling various actuators and reading
sensor states commonly used in building automation scenarios, including door locks,
gas detection systems, fans, and lighting controls.

Core Features:

- Digital I/O port configuration with multiple modes
- Multi-channel relay control with terminal board support
- PWM signal generation via PCA9685 controller
- Door lock control with position feedback sensing
- Gas detector monitoring and breaker integration
- Flexible fan and light control abstractions

Hardware Support:

- DIO Ports: P8 (3V3 IN/OUT), P17 (Active-Low input), P18 (Active-High with voltage divider), P23 (3V3 IN/OUT)
- Relay Outputs: D0, D5, D6 channels for AC/DC load switching
- PWM Controller: PCA9685-based 16-channel PWM with configurable frequency
- Gas Breaker: Dual-wire motor control for gas valve operation

Author: PlanXLab Development Team
"""

import machine

class Dio:
    """
    Digital I/O port configuration class for AutoCtrl peripherals.
    
    This class provides static methods and constants for configuring DIO port pins
    used in the AutoCtrl system. It abstracts the pin mapping and provides a
    consistent interface for accessing the various I/O ports.
    
    Key Features:
    
        - Standard pin mode constants (IN, OUT)
        - Pull resistor configuration (PULL_UP, PULL_DOWN)
        - Relay pin mapping dictionary
        - Factory methods for specific port types
    """
    
    IN: int
    OUT: int
    PULL_UP: int
    PULL_DOWN: int
    LOW: int
    HIGH: int

    class Device:
        """
        Device type enumeration for actuator selection.
        
        Used to specify whether a controlled device (fan, light, etc.) should
        use relay switching or PWM control.
        """
        RELAY: int
        PWM: int
    
    P_RELAYS: dict

    @staticmethod
    def Relays(value: int = 0) -> list: ...
    
    @staticmethod
    def P18() -> machine.Pin:
        """
        Create a pin object for the P18 input port.
        
        P18 is configured as an input for active-high devices operating at 5V-6V,
        such as gas detectors. The port includes a built-in voltage divider that
        halves the input voltage, allowing safe connection of 12V signal sources.
        
        :return: Configured Pin object for P18 input
        
        Example
        --------
        ```python
            >>> # Gas detector input
            >>> gas_input = DIO.P18()
            >>> if gas_input.value():
            ...     print("Gas detected!")
            >>> 
            >>> # Polling loop for gas detection
            >>> while True:
            ...     if DIO.P18().value():
            ...         trigger_alarm()
            ...         break
            ...     utime.sleep_ms(100)
        ```
        """
    
    @staticmethod
    def P17() -> machine.Pin:
        """
        Create a pin object for the P17 input port.
        
        P17 is configured as an input for active-low devices that signal by
        pulling the line to ground, such as PIR motion sensors, limit switches,
        and push buttons.
        
        :return: Configured Pin object for P17 input
        
        Example
        --------
        ```python
            >>> # PIR sensor input
            >>> pir = DIO.P17()
            >>> if pir.value() == 0:  # Active-low
            ...     print("Motion detected!")
            >>> 
            >>> # Limit switch monitoring
            >>> limit = DIO.P17()
            >>> while limit.value():  # Wait for switch activation
            ...     utime.sleep_ms(10)
            >>> print("Limit reached!")
        ```
        """
     
    @staticmethod
    def P8(mode: int, *, pull: int | None = None, value: int = 0) -> machine.Pin:
        """
        Create a pin object for the P8 bidirectional port.
        
        P8 is a 3.3V compatible bidirectional port that can be configured
        as either input or output with optional pull resistor configuration.
        
        :param mode: Pin mode (DIO.IN for input, DIO.OUT for output)
        :param pull_value: Pull resistor configuration (DIO.PULL_UP or DIO.PULL_DOWN, optional)
        :return: Configured Pin object for P8
        
        Example
        --------
        ```python
            >>> # Configure as input with pull-up
            >>> sensor = DIO.P8(DIO.IN, DIO.PULL_UP)
            >>> state = sensor.value()
            >>> 
            >>> # Configure as output
            >>> indicator = DIO.P8(DIO.OUT)
            >>> indicator.value(1)  # Set high
            >>> 
            >>> # Toggle output
            >>> led = DIO.P8(DIO.OUT)
            >>> for _ in range(10):
            ...     led.toggle()
            ...     utime.sleep_ms(500)
        ```
        """
    
    @staticmethod
    def P23(mode: int, *, pull: int | None = None, value: int = 0) -> machine.Pin:
        """
        Create a pin object for the P23 bidirectional port.
        
        P23 is a 3.3V compatible bidirectional port that can be configured
        as either input or output with optional pull resistor configuration.
        
        :param mode: Pin mode (DIO.IN for input, DIO.OUT for output)
        :param pull_value: Pull resistor configuration (DIO.PULL_UP or DIO.PULL_DOWN, optional)
        :return: Configured Pin object for P23
        
        Example
        --------
        ```python
            >>> # Configure as input with pull-down
            >>> button = DIO.P23(DIO.IN, DIO.PULL_DOWN)
            >>> if button.value():
            ...     print("Button pressed!")
            >>> 
            >>> # Configure as output for LED
            >>> led = DIO.P23(DIO.OUT)
            >>> led.value(1)  # Turn on
            >>> utime.sleep(1)
            >>> led.value(0)  # Turn off
        ```
        """

class DoorLock:
    """
    Door lock controller with optional position feedback.
    
    This class provides control for electric door locks through relay actuation.
    When configured with a feedback sensor, it supports intelligent open/close
    operations that verify the current lock state before acting.
    
    Key Features:
    
        - Basic work (toggle) operation for simple locks
        - Position feedback sensing for smart operation
        - Automatic state verification before actuation
        - Configurable active-low/active-high feedback
    """
    
    def __init__(self, relay, *, feedback=None, active_low: bool = True) -> None:
        """
        Initialize the door lock controller.
        
        Creates a door lock controller that uses a relay for actuation and
        optionally monitors position feedback for intelligent operation.
        
        :param relay: Relay object for controlling the lock mechanism
        :param dio: Feedback pin object for reading lock state (optional, enables open/close/is_opened methods)
        :param active_low: If True, feedback pin reads LOW when lock is open (default: True)
        
        Example
        --------
        ```python
            >>> # Simple lock without feedback
            >>> relay = Relay(DIO.P_RELAY[0])
            >>> lock = DoorLock(relay)
            >>> lock.work()  # Toggle lock state
            >>> 
            >>> # Lock with position feedback
            >>> relay = Relay(DIO.P_RELAY[0])
            >>> feedback = DIO.P17()
            >>> lock = DoorLock(relay, dio=feedback, active_low=True)
            >>> 
            >>> # Now can use smart operations
            >>> lock.open()   # Only opens if currently closed
            >>> lock.close()  # Only closes if currently open
            >>> print(f"Lock is {'open' if lock.is_opened() else 'closed'}")
        ```
        """

    def open(self) -> bool:
        """
        Open the door lock if currently closed.
        
        Checks the current lock state via feedback and only actuates if
        the lock is currently closed. Only available when feedback pin is configured.
        
        :return: True if action was taken (lock was closed), False if already open
        
        Example
        --------
        ```python
            >>> lock = DoorLock(relay, dio=feedback)
            >>> 
            >>> # Open the lock
            >>> if lock.open():
            ...     print("Lock opened successfully")
            >>> else:
            ...     print("Lock was already open")
            >>> 
            >>> # Entry sequence
            >>> if not lock.is_opened():
            ...     lock.open()
            ...     print("Access granted")
        ```
        """
    
    def close(self) -> bool:
        """
        Close the door lock if currently open.
        
        Checks the current lock state via feedback and only actuates if
        the lock is currently open. Only available when feedback pin is configured.
        
        :return: True if action was taken (lock was open), False if already closed
        
        Example
        --------
        ```python
            >>> lock = DoorLock(relay, dio=feedback)
            >>> 
            >>> # Close the lock
            >>> if lock.close():
            ...     print("Lock closed successfully")
            >>> else:
            ...     print("Lock was already closed")
            >>> 
            >>> # Auto-lock after timeout
            >>> utime.sleep(5)
            >>> lock.close()
        ```
        """

    def is_opened(self) -> bool:
        """
        Check if the door lock is currently open.
        
        Reads the feedback pin state to determine current lock position.
        Only available when feedback pin is configured.
        
        :return: True if lock is open, False if closed
        
        Example
        --------
        ```python
            >>> lock = DoorLock(relay, dio=feedback)
            >>> 
            >>> # Check lock state
            >>> if lock.is_opened():
            ...     print("Door is unlocked")
            >>> else:
            ...     print("Door is locked")
            >>> 
            >>> # Monitor lock state
            >>> while True:
            ...     state = "OPEN" if lock.is_opened() else "CLOSED"
            ...     print(f"Lock state: {state}")
            ...     utime.sleep(1)
        ```
        """
    
    def work(self) -> None:
        """
        Toggle the door lock state.
        
        Activates the lock relay for a brief period to change the lock state.
        This is the basic operation available for all lock configurations,
        regardless of feedback sensor presence.
        
        Example
        --------
        ```python
            >>> lock = DoorLock(relay)
            >>> 
            >>> # Toggle lock
            >>> lock.work()
            >>> print("Lock toggled")
            >>> 
            >>> # Simple unlock/lock cycle
            >>> lock.work()  # Unlock
            >>> utime.sleep(5)
            >>> lock.work()  # Lock
        ```
        """

class PCA9685:
    """
    PWM controller for PCA9685-based signal generation.
    
    This class provides control for the PCA9685 16-channel PWM controller,
    commonly used for LED dimming, motor speed control, and servo positioning
    in automation applications.
    
    Key Features:
    
        - 16-channel PWM output
        - Configurable frequency (up to 1526 Hz)
        - Duty cycle and raw PWM control
        - 12-bit resolution (0-4095)
    """
    
    def __init__(self, freq: int = 100) -> None:
        """
        Initialize the PWM controller.
        
        Sets up the PCA9685 PWM controller with the specified frequency.
        The controller provides 16 channels of PWM output with 12-bit resolution.
        
        :param freq: PWM frequency in Hz (default: 100, max: 1526)
        
        Example
        --------
        ```python
            >>> # Initialize with default 100Hz
            >>> pwm = Pwm()
            >>> 
            >>> # Initialize with 500Hz for motor control
            >>> pwm = Pwm(freq=500)
            >>> 
            >>> # Set duty cycle on channel 0
            >>> pwm.duty(0, 50)  # 50% duty cycle
        ```
        """
     
    def freq(self, freq: int) -> None:
        """
        Set the PWM frequency.
        
        Changes the PWM frequency for all channels. Note that very high
        frequencies may result in reduced resolution.
        
        :param freq: PWM frequency in Hz (maximum: 1526 Hz)
        
        Example
        --------
        ```python
            >>> pwm = Pwm()
            >>> 
            >>> # Change to 200Hz for LED dimming
            >>> pwm.freq(200)
            >>> 
            >>> # Change to 50Hz for servo control
            >>> pwm.freq(50)
        ```
        """

    def pwm(self, ch: int, on: int, off: int) -> None:
        """
        Set raw PWM timing values.
        
        Directly sets the ON and OFF timing values for a channel.
        This provides full 12-bit control over the PWM waveform.
        
        :param ch: Channel number (0-15)
        :param on: Count value when output goes HIGH (0-4095)
        :param off: Count value when output goes LOW (0-4095)
        
        Example
        --------
        ```python
            >>> pwm = Pwm()
            >>> 
            >>> # 0% duty cycle (always off)
            >>> pwm.pwm(0, 0, 4096)
            >>> 
            >>> # 100% duty cycle (always on)
            >>> pwm.pwm(0, 4096, 0)
            >>> 
            >>> # 50% duty cycle
            >>> pwm.pwm(0, 0, 2048)
            >>> 
            >>> # Phase-shifted output
            >>> pwm.pwm(1, 1024, 3072)
        ```
        """

    def duty(self, ch: int, value: int) -> None:
        """
        Set the duty cycle percentage for a channel.
        
        Convenience method to set PWM duty cycle as a percentage (0-100).
        
        :param ch: Channel number (0-15)
        :param value: Duty cycle percentage (0-100)
        
        Example
        --------
        ```python
            >>> pwm = Pwm()
            >>> 
            >>> # Set 50% brightness on LED
            >>> pwm.duty(0, 50)
            >>> 
            >>> # Fade LED up
            >>> for i in range(0, 101, 5):
            ...     pwm.duty(0, i)
            ...     utime.sleep_ms(50)
            >>> 
            >>> # Fade LED down
            >>> for i in range(100, -1, -5):
            ...     pwm.duty(0, i)
            ...     utime.sleep_ms(50)
            >>> 
            >>> # Motor speed control
            >>> pwm.duty(2, 75)  # 75% speed
        ```
        """

class GasDetector:
    """
    Gas detector sensor interface.
    
    This class provides an interface for reading the state of a gas detector
    (such as ND-102D) connected to the P18 active-high input port.
    
    Typical Wiring:
    
        - Red wire: 12V power
        - Black wire: GND
        - White wire: P18 signal output
    """
    
    def __init__(self):
        """
        Initialize the gas detector interface.
        
        Sets up the P18 input port for reading the gas detector state.
        
        Example
        --------
        ```python
            >>> detector = GasDetector()
            >>> if detector.read():
            ...     print("Gas detected! Take action!")
        ```
        """
    
    def read(self) -> int:
        """
        Read the current gas detection state.
        
        :return: Detection state (1 if gas detected, 0 if clear)
        
        Example
        --------
        ```python
            >>> detector = GasDetector()
            >>> 
            >>> # Simple check
            >>> if detector.read():
            ...     activate_alarm()
            ...     close_gas_valve()
            >>> 
            >>> # Continuous monitoring
            >>> while True:
            ...     if detector.read():
            ...         print("GAS LEAK DETECTED!")
            ...         emergency_shutdown()
            ...         break
            ...     utime.sleep_ms(500)
            >>> 
            >>> # Status logging
            >>> state = "ALARM" if detector.read() else "NORMAL"
            >>> print(f"Gas detector status: {state}")
        ```
        """

class GasBreaker: 
    """
    Gas breaker (valve) controller.
    
    This class provides control for motorized gas breakers (such as SV-20H)
    using dual PWM channels for bidirectional motor control. The breaker
    can be opened, closed, or stopped mid-operation.
    
    Typical Wiring:
    
        - Red wire: PWM channel A
        - Black wire: PWM channel B
    """    
    
    def __init__(self, red: int, black: int) -> None:
        """
        Initialize the gas breaker controller.
        
        Sets up PWM control for bidirectional motor operation.
        
        :param red: PWM channel number for the red wire (motor direction A)
        :param black: PWM channel number for the black wire (motor direction B)
        
        Example
        --------
        ```python
            >>> # Initialize with PWM channels 0 and 1
            >>> breaker = GasBreaker(0, 1)
            >>> 
            >>> # Initialize to closed position
            >>> breaker.close(init=True)
            >>> 
            >>> # Normal operation
            >>> breaker.open()   # Open gas valve
            >>> breaker.close()  # Close gas valve
        ```
        """        
        
    def init(self) -> None:
        """
        Initialize the gas breaker to the closed position.
        """
        
    def open(self) -> None:
        """
        Open the gas breaker (valve).
        
        Drives the motor in the opening direction to allow gas flow.
        
        Example
        --------
        ```python
            >>> breaker = GasBreaker(0, 1)
            >>> 
            >>> # Open gas valve
            >>> breaker.open()
            >>> print("Gas valve opened")
            >>> 
            >>> # Timed operation
            >>> breaker.open()
            >>> utime.sleep(2)
            >>> breaker.stop()  # Stop motor after 2 seconds
        ```
        """
            
    def close(self, init: bool = False) -> None:
        """
        Close the gas breaker (valve).
        
        Drives the motor in the closing direction to stop gas flow.
        Use init=True for initial positioning after power-up.
        
        :param init: If True, performs initialization sequence (default: False)
        
        Example
        --------
        ```python
            >>> breaker = GasBreaker(0, 1)
            >>> 
            >>> # Normal close
            >>> breaker.close()
            >>> print("Gas valve closed")
            >>> 
            >>> # Initialization close (on startup)
            >>> breaker.close(init=True)
            >>> 
            >>> # Emergency shutdown
            >>> if gas_detected:
            ...     breaker.close()
            ...     print("Emergency: Gas valve closed!")
        ```
        """
    
    def stop(self) -> None:
        """
        Stop the gas breaker motor.
        
        Immediately stops motor operation, useful for precise positioning
        or emergency stop scenarios.
        
        Example
        --------
        ```python
            >>> breaker = GasBreaker(0, 1)
            >>> 
            >>> # Stop motor
            >>> breaker.stop()
            >>> 
            >>> # Partial open operation
            >>> breaker.open()
            >>> utime.sleep_ms(500)  # Partial travel
            >>> breaker.stop()
            >>> 
            >>> # Emergency stop
            >>> breaker.stop()
            >>> print("Motor stopped")
        ```
        """
    
def Fan(type: int, ch: int, value: int = 0) -> object:
    """
    Create a fan control object.
    
    Factory function to create either a relay-controlled or PWM-controlled
    fan interface, depending on the type parameter.
    
    :param type: Device type (DIO.Device.RELAY for on/off, DIO.Device.PWM for variable speed)
    :param ch: Channel number (relay index or PWM channel)
    :param value: Initial value (0 for off)
    :return: Configured Relay or PWM channel object
    
    Example
    --------
    ```python
        >>> # Relay-controlled fan (on/off)
        >>> fan = Fan(DIO.Device.RELAY, 0)
        >>> fan.value(1)  # Turn on
        >>> fan.value(0)  # Turn off
        >>> 
        >>> # PWM-controlled fan (variable speed)
        >>> fan = Fan(DIO.Device.PWM, 2)
        >>> fan.duty(50)  # 50% speed
        >>> fan.duty(100) # Full speed
        >>> fan.duty(0)   # Off
        >>> 
        >>> # Speed ramping
        >>> fan = Fan(DIO.Device.PWM, 2)
        >>> for speed in range(0, 101, 10):
        ...     fan.duty(speed)
        ...     utime.sleep(1)
    ```
    """
     
def Light(type: int, ch: int, value: int = 0) -> object:
    """
    Create a light control object.
    
    Factory function to create either a relay-controlled or PWM-controlled
    light interface, depending on the type parameter.
    
    :param type: Device type (DIO.Device.RELAY for on/off, DIO.Device.PWM for dimming)
    :param ch: Channel number (relay index or PWM channel)
    :param value: Initial value (0 for off)
    :return: Configured Relay or PWM channel object
    
    Example
    --------
    ```python
        >>> # Relay-controlled light (on/off)
        >>> light = Light(DIO.Device.RELAY, 1)
        >>> light.value(1)  # Turn on
        >>> light.value(0)  # Turn off
        >>> 
        >>> # PWM-controlled light (dimmable)
        >>> light = Light(DIO.Device.PWM, 0)
        >>> light.duty(100)  # Full brightness
        >>> light.duty(50)   # Half brightness
        >>> light.duty(10)   # Night light level
        >>> 
        >>> # Smooth dimming
        >>> light = Light(DIO.Device.PWM, 0)
        >>> for brightness in range(0, 101, 2):
        ...     light.duty(brightness)
        ...     utime.sleep_ms(20)
        >>> 
        >>> # Sunset simulation
        >>> light = Light(DIO.Device.PWM, 0, value=100)
        >>> for brightness in range(100, -1, -1):
        ...     light.duty(brightness)
        ...     utime.sleep_ms(100)
    ```
    """
