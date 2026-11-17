
"""
Basic I/O expansion board controller.

This class provides interfaces for the Basic I/O expansion board featuring
a PCA9535 GPIO expander. Includes buzzer control, LED array, and button
matrix for educational and prototyping applications.

Components:

    - Buzzer: Audio feedback with on/off and beep patterns
    - Leds: 8-channel LED array with individual and group control
    - Buttons: 8-channel button matrix with individual and group read

Author: PlanXLab Development Team
"""

class Buzzer:
    """
    Buzzer controller for audio feedback.
    
    Provides simple on/off control and pattern-based beeping
    for audio alerts and notifications.
    """

    def on(self) -> None:
        """
        Turn on the buzzer.
        
        Example
        --------
        ```python
            >>> buzzer = Buzzer()
            >>> buzzer.on()
            >>> utime.sleep(0.5)
            >>> buzzer.off()
        ```
        """

    def off(self) -> None:
        """
        Turn off the buzzer.
        
        Example
        --------
        ```python
            >>> buzzer = Buzzer()
            >>> buzzer.off()
        ```
        """
        
    def beep(self, count: int, on: int = 50, off: int = 10) -> None:
        """
        Generate a beep pattern.
        
        Produces a series of beeps with configurable on/off timing.
        
        :param count: Number of beeps to generate
        :param on: Duration of each beep in milliseconds (default: 50)
        :param off: Duration of silence between beeps in milliseconds (default: 10)
        
        Example
        --------
        ```python
            >>> buzzer = Buzzer()
            >>> 
            >>> # Single beep
            >>> buzzer.beep(1)
            >>> 
            >>> # Triple beep for alert
            >>> buzzer.beep(3)
            >>> 
            >>> # Long beeps for warning
            >>> buzzer.beep(2, on=200, off=100)
            >>> 
            >>> # Rapid beeping
            >>> buzzer.beep(10, on=20, off=20)
            >>> 
            >>> # Confirmation sound
            >>> buzzer.beep(2, on=100, off=50)
        ```
        """

class _I2CtoGPIO:
    """
    Base class for PCA9535 GPIO expander communication.
    
    Provides low-level I2C read/write methods for the GPIO expander.
    """
    PCA9535_ADDR: int
            
    def read(self) -> int:
        """
        Read GPIO register values.
        
        :return: Bytes containing GPIO register values
        
        Example
        --------
        ```python
            >>> gpio = _I2CtoGPIO()
            >>> data = gpio.read()
            >>> print(f"GPIO state: {data.hex()}")
        ```
        """

    def write(self, n: int | bytes) -> None:
        """
        Write to GPIO registers.
        
        :param n: Value(s) to write to the GPIO expander
        
        Example
        --------
        ```python
            >>> gpio = _I2CtoGPIO()
            >>> gpio.write(0xFF)  # Set all outputs high
        ```
        """
    
class _LedIter:
    """
    LED iterator element for indexed LED access.
    
    Represents a single LED in the array with on/off control.
    """
        
    def on(self) -> None:
        """
        Turn on this LED.
        
        Example
        --------
        ```python
            >>> leds = Leds()
            >>> for led in leds:
            ...     led.on()
            ...     utime.sleep_ms(100)
        ```
        """
                
    def off(self) -> None:
        """
        Turn off this LED.
        
        Example
        --------
        ```python
            >>> leds = Leds()
            >>> for led in leds:
            ...     led.off()
        ```
        """
        
class Leds(_I2CtoGPIO):
    """
    LED array controller.
    
    Provides control for an 8-LED array with individual and group
    access methods including iteration and indexed access.
    
    Key Features:
    
        - Individual LED control via indexing
        - Group status reading
        - Iterator support for sequential operations
        - Bulk write and clear operations
    """
        
    def __call__(self) -> tuple:
        """
        Get the status of all LEDs.
        
        :return: Tuple of LED states (0 or 1 for each LED)
        
        Example
        --------
        ```python
            >>> leds = Leds()
            >>> states = leds()
            >>> print(f"LED states: {states}")
            >>> 
            >>> # Count lit LEDs
            >>> lit = sum(leds())
            >>> print(f"{lit} LEDs are on")
        ```
        """
    
    def __getitem__(self, index: int) -> bool:
        """
        Get the status of a specific LED.
        
        :param index: LED index (0-7)
        :return: True if LED is on, False if off
        
        Example
        --------
        ```python
            >>> leds = Leds()
            >>> 
            >>> # Check LED 0
            >>> if leds[0]:
            ...     print("LED 0 is on")
            >>> 
            >>> # Check all LEDs
            >>> for i in range(8):
            ...     state = "ON" if leds[i] else "OFF"
            ...     print(f"LED {i}: {state}")
        ```
        """
    
    def __setitem__(self, index: int, value: bool) -> None:
        """
        Set the status of a specific LED.
        
        :param index: LED index (0-7)
        :param value: True to turn on, False to turn off
        
        Example
        --------
        ```python
            >>> leds = Leds()
            >>> 
            >>> # Turn on LED 0
            >>> leds[0] = True
            >>> 
            >>> # Turn off LED 3
            >>> leds[3] = False
            >>> 
            >>> # Binary pattern
            >>> pattern = 0b10101010
            >>> for i in range(8):
            ...     leds[i] = bool(pattern & (1 << i))
        ```
        """
        
    def __iter__(self):
        """
        Get an iterator over all LEDs.
        
        :return: LED iterator
        
        Example
        --------
        ```python
            >>> leds = Leds()
            >>> 
            >>> # Turn on all LEDs sequentially
            >>> for led in leds:
            ...     led.on()
            ...     utime.sleep_ms(100)
            >>> 
            >>> # Turn off all LEDs
            >>> for led in leds:
            ...     led.off()
        ```
        """
    
    def __next__(self):
        """
        Get the next LED in iteration.
        
        :return: Next LED iterator element
        """

    def write(self, n: int) -> None:
        """
        Write a value to all LEDs at once.
        
        Sets all 8 LEDs based on the bits of the input value.
        
        :param n: 8-bit value where each bit controls one LED
        
        Example
        --------
        ```python
            >>> leds = Leds()
            >>> 
            >>> # All LEDs on
            >>> leds.write(0xFF)
            >>> 
            >>> # All LEDs off
            >>> leds.write(0x00)
            >>> 
            >>> # Alternating pattern
            >>> leds.write(0b10101010)
            >>> 
            >>> # Binary counter display
            >>> for i in range(256):
            ...     leds.write(i)
            ...     utime.sleep_ms(100)
        ```
        """
        
    def clear(self) -> None:
        """
        Turn off all LEDs.
        
        Example
        --------
        ```python
            >>> leds = Leds()
            >>> 
            >>> # Clear all LEDs
            >>> leds.clear()
            >>> 
            >>> # Reset after pattern
            >>> leds.write(0xFF)
            >>> utime.sleep(1)
            >>> leds.clear()
        ```
        """

class Buttons(_I2CtoGPIO):
    """
    Button matrix controller.
    
    Provides read access for an 8-button matrix with individual
    and group reading capabilities.
    """
    
    def __getitem__(self, index: int) -> int | None:
        """
        Get the status of a specific button.
        
        :param index: Button index (0-7)
        :return: True if button is pressed, False if released
        
        Example
        --------
        ```python
            >>> buttons = Buttons()
            >>> 
            >>> # Check button 0
            >>> if buttons[0]:
            ...     print("Button 0 pressed!")
            >>> 
            >>> # Wait for button press
            >>> while not buttons[0]:
            ...     utime.sleep_ms(10)
            >>> print("Button 0 was pressed!")
            >>> 
            >>> # Check multiple buttons
            >>> for i in range(8):
            ...     if buttons[i]:
            ...         print(f"Button {i} pressed")
        ```
        """
    
    def __call__(self) -> tuple:
        """
        Get the status of all buttons.
        
        :return: Tuple of button states (True=pressed, False=released)
        
        Example
        --------
        ```python
            >>> buttons = Buttons()
            >>> 
            >>> # Read all button states
            >>> states = buttons()
            >>> print(f"Button states: {states}")
            >>> 
            >>> # Count pressed buttons
            >>> pressed = sum(buttons())
            >>> print(f"{pressed} buttons pressed")
            >>> 
            >>> # Interactive button display
            >>> while True:
            ...     states = buttons()
            ...     print(f"Buttons: {states}")
            ...     utime.sleep_ms(100)
        ```
        """

