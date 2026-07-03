"""
XNode Board Control Library

Comprehensive hardware abstraction and control library for the XNode (XBee-based IoT node) board.
This library provides high-level interfaces for all onboard peripherals and sensors, enabling rapid
prototyping and development of IoT applications with professional-grade functionality on the
Silicon Labs EFR32MG (XBee 3) platform.

The XNode board is designed for low-power IoT applications with integrated Zigbee/DigiMesh networking
capabilities. This library abstracts the hardware complexity and provides intuitive Python interfaces
for seamless development in building automation, sensor networks, and industrial IoT applications.

Core Features:

- Complete hardware abstraction for XNode board peripherals
- XBee Zigbee/DigiMesh networking integration
- Digital input/output control with pull resistor configuration
- I2C communication interface with comprehensive register access
- System monitoring and diagnostics capabilities
- Memory and filesystem information utilities
- Low-power operation support

Hardware Interfaces:

- GPIO Control: Digital input/output with configurable pull resistors
- I2C Communication: Single-bus I2C with automatic device detection
- Serial Interface: REPL integration for interactive development
- Built-in Components: LED control and supply voltage monitoring
- Environmental Sensors: Illuminance, temperature, pressure, humidity, and gas sensing

Author: PlanXLab Development Team
"""

import machine


# Constants
XNODE_LED_PIN: str
XNODE_SUPPLY_VOLTAGE_PIN: str
XNODE_I2C_ID1_SCL_PIN: str
XNODE_I2C_ID1_SDA_PIN: str

def get_sys_info() -> tuple:
    """
    Get system information including core frequency and temperature.
    
    This function retrieves the current CPU frequency and internal temperature
    of the XNode board using XBee AT commands for temperature sensing.
    
    :return: tuple of (frequency, temperature) where frequency is in Hz and temperature is in Celsius
    
    Example
    --------
    ```python
        >>> freq, temp = get_sys_info()
        >>> print(f"CPU Frequency: {freq/1000000:.1f} MHz")
        >>> print(f"Temperature: {temp}°C")
        >>> # Output: CPU Frequency: 40.0 MHz
        >>> # Output: Temperature: 25°C
        >>> 
        >>> # System health monitoring
        >>> freq, temp = get_sys_info()
        >>> if temp > 60:
        ...     print("Warning: High temperature detected!")
        >>> 
        >>> # Periodic monitoring
        >>> import utime
        >>> while True:
        ...     freq, temp = get_sys_info()
        ...     print(f"Temp: {temp}°C")
        ...     utime.sleep(10)
    ```
    """

def get_mem_info() -> tuple:
    """
    Get memory usage information of XNode.
    
    This function performs garbage collection and returns detailed memory
    statistics including free, used, and total memory in bytes.
    
    :return: tuple of (free, used, total) memory in bytes
    
    Example
    --------
    ```python
        >>> free, used, total = get_mem_info()
        >>> print(f"Free memory: {free/1024:.1f} KB")
        >>> print(f"Used memory: {used/1024:.1f} KB")
        >>> print(f"Total memory: {total/1024:.1f} KB")
        >>> print(f"Memory usage: {used/total*100:.1f}%")
        >>> 
        >>> # Memory monitoring
        >>> free, used, total = get_mem_info()
        >>> if used / total > 0.9:
        ...     print("Warning: Low memory!")
        ...     import gc
        ...     gc.collect()
        >>> 
        >>> # Track memory allocation
        >>> before = get_mem_info()
        >>> data = [i for i in range(100)]
        >>> after = get_mem_info()
        >>> print(f"Memory used: {after[1] - before[1]} bytes")
    ```
    """

def get_fs_info(path: str = '/') -> tuple:
    """
    Get filesystem information for the given path.
    
    This function retrieves detailed filesystem statistics including total,
    used, and free space along with usage percentage for the specified path.
    
    :param path: Path to check filesystem info for (default: '/')
    :return: tuple of (total, used, free, usage_percentage)
    
    Example
    --------
    ```python
        >>> total, used, free, usage = get_fs_info()
        >>> print(f"Total space: {total/1024:.1f} KB")
        >>> print(f"Used space: {used/1024:.1f} KB")
        >>> print(f"Free space: {free/1024:.1f} KB")
        >>> print(f"Usage: {usage:.1f}%")
        >>> 
        >>> # Storage monitoring
        >>> total, used, free, usage = get_fs_info()
        >>> if usage > 80:
        ...     print("Warning: Low storage space!")
        >>> 
        >>> # Check before file write
        >>> total, used, free, usage = get_fs_info()
        >>> file_size = 1024  # bytes to write
        >>> if free > file_size:
        ...     print("Sufficient space available")
    ```
    """

class Din:
    """
    Digital input pin controller for reading external signals.
    
    This class provides a high-level interface for configuring and reading
    digital input pins with optional pull-up or pull-down resistor configuration.
    The input value is inverted for active-low device compatibility.
    
    Key Features:
    
        - Configurable pull-up/pull-down resistors
        - Active-low compatible value reading
        - Simple pin state access
    """
    
    LOW: int
    HIGH: int
    PULL_DOWN: int
    PULL_UP: int
    
    def __init__(self, pin: str, *, pull: int | None = None):
        """
        Initialize the digital input pin.
        
        Creates a new digital input pin with optional pull resistor configuration
        for reading external signals like switches, sensors, or other digital devices.
        
        :param pin: The pin identifier string (e.g., 'D0', 'P2')
        :param pull: Pull resistor configuration (PULL_UP, PULL_DOWN, or None for no pull)
        
        Example
        --------
        ```python
            >>> # Basic input with pull-up
            >>> button = Din('P2', pull=Din.PULL_UP)
            >>> if button.value() == Din.LOW:
            ...     print("Button pressed!")
            >>> 
            >>> # Limit switch with pull-down
            >>> limit = Din('D7', pull=Din.PULL_DOWN)
            >>> while limit.value() == Din.LOW:
            ...     print("Waiting for switch...")
            ...     utime.sleep_ms(100)
            >>> 
            >>> # PIR sensor input
            >>> pir = Din('P2', pull=Din.PULL_DOWN)
            >>> if pir.value() == Din.HIGH:
            ...     print("Motion detected!")
        ```
        """

    def value(self) -> int:
        """
        Read the current value of the digital input pin.
        
        Returns the inverted pin state for active-low device compatibility.
        
        :return: Current pin state (0 for LOW, 1 for HIGH)
        
        Example
        --------
        ```python
            >>> button = Din('P2', pull=Din.PULL_UP)
            >>> 
            >>> # Simple state check
            >>> state = button.value()
            >>> print(f"Button state: {'pressed' if state else 'released'}")
            >>> 
            >>> # Polling loop
            >>> while True:
            ...     if button.value() == Din.HIGH:
            ...         print("Button pressed!")
            ...         break
            ...     utime.sleep_ms(10)
            >>> 
            >>> # Edge detection
            >>> last_state = button.value()
            >>> while True:
            ...     current = button.value()
            ...     if current != last_state:
            ...         if current == Din.HIGH:
            ...             print("Button pressed")
            ...         else:
            ...             print("Button released")
            ...         last_state = current
            ...     utime.sleep_ms(10)
        ```
        """

class Dout:
    """
    Digital output pin controller for driving external devices.
    
    This class provides a high-level interface for configuring and controlling
    digital output pins with optional pull resistor configuration. Supports
    setting, reading, and toggling the output state.
    
    Key Features:
    
        - Configurable initial output value
        - Optional pull-up/pull-down resistors
        - Toggle functionality for easy state switching
    """
    
    LOW: int
    HIGH: int
    PULL_DOWN: int
    PULL_UP: int
    
    def __init__(self, pin: str, *, pull: int | None = None, value: int | None = None):
        """
        Initialize the digital output pin.
        
        Creates a new digital output pin with optional pull resistor and initial
        value configuration for controlling LEDs, relays, or other digital devices.
        
        :param pin: The pin identifier string (e.g., 'D0', 'D5')
        :param pull: Pull resistor configuration (PULL_UP, PULL_DOWN, or None)
        :param value: Initial output value (LOW or HIGH, default is LOW)
        
        Example
        --------
        ```python
            >>> # LED control
            >>> led = Dout('D9', value=Dout.LOW)
            >>> led.value(Dout.HIGH)  # Turn on
            >>> 
            >>> # Relay control with initial state
            >>> relay = Dout('D0', value=Dout.LOW)
            >>> relay.value(Dout.HIGH)  # Activate relay
            >>> 
            >>> # Multiple outputs
            >>> outputs = [Dout(f'D{i}') for i in range(3)]
            >>> for out in outputs:
            ...     out.value(Dout.HIGH)
        ```
        """

    def value(self, n: int | None = None) -> int | None:
        """
        Read or set the value of the digital output pin.
        
        :param n: If None, returns current output state (0=LOW, 1=HIGH). If given, sets the output.
        :return: Current output state when called without argument, None when setting
        
        Example
        --------
        ```python
            >>> led = Dout('D9')
            >>> print(f"LED state: {'on' if led.value() else 'off'}")
            >>> led.value(Dout.HIGH)  # Turn on
            >>> utime.sleep(1)
            >>> led.value(Dout.LOW)   # Turn off
        ```
        """

    def toggle(self) -> None:
        """
        Toggle the current value of the digital output pin.
        
        Switches the output from HIGH to LOW or LOW to HIGH.
        
        Example
        --------
        ```python
            >>> led = Dout('D9')
            >>> 
            >>> # Simple blink using toggle
            >>> while True:
            ...     led.toggle()
            ...     utime.sleep_ms(500)
            >>> 
            >>> # Toggle on button press
            >>> button = Din('P2', pull=Din.PULL_UP)
            >>> while True:
            ...     if button.value() == Din.HIGH:
            ...         led.toggle()
            ...         utime.sleep_ms(200)  # Debounce
        ```
        """

def Wdt(timeout: int) -> machine.WDT:
    """
    Create a watchdog timer with the specified timeout.
    
    Creates and returns a watchdog timer that will reset the device if not
    fed within the specified timeout period. Useful for recovering from
    software hangs in unattended deployments.
    
    :param timeout: Watchdog timeout in milliseconds
    :return: A configured WDT object
    
    Example
    --------
    ```python
        >>> # Create 5-second watchdog
        >>> wdt = Wdt(5000)
        >>> 
        >>> # Main loop with watchdog feed
        >>> while True:
        ...     # Do work
        ...     process_sensors()
        ...     send_data()
        ...     
        ...     # Feed the watchdog
        ...     wdt.feed()
        ...     utime.sleep(1)
        >>> 
        >>> # If the loop hangs, device resets after 5 seconds
    ```
    """

def i2cdetect(show: bool = False) -> list | None:
    """
    Detect I2C devices on the bus.
    
    Scans the I2C bus for connected devices and optionally displays
    a formatted table showing all addresses with detected devices highlighted.
    
    :param show: If True, prints formatted I2C address table; if False, returns list
    :return: List of detected device addresses (0-127), or None if show=True
    
    Example
    --------
    ```python
        >>> # Get list of devices
        >>> devices = i2cdetect()
        >>> print(f"Found {len(devices)} devices: {[hex(d) for d in devices]}")
        >>> # Output: Found 2 devices: ['0x28', '0x5a']
        >>> 
        >>> # Display formatted table
        >>> i2cdetect(show=True)
        >>>      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
        >>> 00: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
        >>> 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
        >>> 20: -- -- -- -- -- -- -- -- 28 -- -- -- -- -- -- --
        >>> ...
        >>> 
        >>> # Check for specific device
        >>> devices = i2cdetect()
        >>> BME680_ADDR = 0x77
        >>> if BME680_ADDR in devices:
        ...     print("BME680 sensor found!")
        >>> else:
        ...     print("BME680 not detected")
    ```
    """

class I2c:
    """
    I2C communication interface for peripheral devices.
    
    This class provides a comprehensive interface for I2C communication with
    external devices, including convenient methods for reading and writing
    8-bit and 16-bit values, as well as low-level memory access operations.
    
    Key Features:
    
        - Automatic address handling
        - 8-bit and 16-bit register read/write
        - Configurable byte order (little/big endian)
        - Low-level memory access methods
        - Configurable bus frequency
    """

    def __init__(self, addr: int, freq: int = 400_000):
        """
        Initialize the I2C interface for a specific device.
        
        Creates an I2C interface configured for communication with a device
        at the specified address using the XNode's I2C bus (bus 1).
        
        :param addr: I2C device address (7-bit, 0x00-0x7F)
        :param freq: I2C bus frequency in Hz (default: 400000)
        
        Example
        --------
        ```python
            >>> # Initialize sensor at address 0x28
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Initialize with lower frequency for compatibility
            >>> eeprom = I2c(0x50, freq=100_000)
            >>> 
            >>> # Read device ID
            >>> device_id = sensor.read_u8(0x00)
            >>> print(f"Device ID: 0x{device_id:02X}")
        ```
        """

    def read_u8(self, reg: int) -> int:
        """
        Read an unsigned 8-bit value from a register.
        
        :param reg: Register address to read from
        :return: 8-bit value (0-255)
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Read single register
            >>> status = sensor.read_u8(0x00)
            >>> print(f"Status: 0x{status:02X}")
            >>> 
            >>> # Check flag bits
            >>> flags = sensor.read_u8(0x01)
            >>> data_ready = (flags & 0x01) != 0
            >>> if data_ready:
            ...     print("Data ready!")
        ```
        """

    def read_u16(self, reg: int, *, little_endian: bool = True) -> int:
        """
        Read an unsigned 16-bit value from a register.
        
        :param reg: Register address to read from
        :param little_endian: If True, read in little-endian format; if False, big-endian
        :return: 16-bit value (0-65535)
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Read 16-bit value (little-endian)
            >>> raw_temp = sensor.read_u16(0x20)
            >>> temperature = raw_temp / 100.0
            >>> print(f"Temperature: {temperature}°C")
            >>> 
            >>> # Read big-endian value
            >>> raw_pressure = sensor.read_u16(0x22, little_endian=False)
            >>> pressure = raw_pressure / 10.0
            >>> print(f"Pressure: {pressure} hPa")
        ```
        """

    def write_u8(self, reg: int, val: int) -> None:
        """
        Write an unsigned 8-bit value to a register.
        
        :param reg: Register address to write to
        :param val: Value to write (0-255)
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Write configuration register
            >>> sensor.write_u8(0x00, 0x01)  # Enable sensor
            >>> 
            >>> # Set measurement mode
            >>> MODE_CONTINUOUS = 0x03
            >>> sensor.write_u8(0x01, MODE_CONTINUOUS)
        ```
        """

    def write_u16(self, reg: int, val: int, *, little_endian: bool = True) -> None:
        """
        Write an unsigned 16-bit value to a register.
        
        :param reg: Register address to write to
        :param val: Value to write (0-65535)
        :param little_endian: If True, write in little-endian format; if False, big-endian
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Write 16-bit threshold value
            >>> THRESHOLD = 1000
            >>> sensor.write_u16(0x10, THRESHOLD)
            >>> 
            >>> # Write big-endian value
            >>> sensor.write_u16(0x12, 0x1234, little_endian=False)
        ```
        """

    def readfrom(self, nbytes: int, *, stop: bool = True) -> bytes:
        """
        Read bytes directly from the I2C device.
        
        :param nbytes: Number of bytes to read
        :param stop: If True, send stop condition after reading
        :return: Bytes read from the device
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Read raw data block
            >>> data = sensor.readfrom(6)
            >>> x, y, z = ustruct.unpack('<hhh', data)
            >>> print(f"X={x}, Y={y}, Z={z}")
        ```
        """

    def readinto(self, buf: bytearray, *, stop: bool = True) -> int:
        """
        Read bytes from the I2C device into a buffer.
        
        :param buf: Buffer to read data into
        :param stop: If True, send stop condition after reading
        :return: Number of bytes read
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Pre-allocated buffer for efficiency
            >>> buf = bytearray(6)
            >>> sensor.readinto(buf)
            >>> print(f"Data: {buf.hex()}")
        ```
        """

    def readfrom_mem(self, reg: int, nbytes: int, *, addrsize: int = 8) -> bytes:
        """
        Read bytes from a specific register address.
        
        :param reg: Register address to read from
        :param nbytes: Number of bytes to read
        :param addrsize: Address size in bits (default: 8)
        :return: Bytes read from the register
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Read calibration data
            >>> cal_data = sensor.readfrom_mem(0x88, 26)
            >>> print(f"Calibration: {cal_data.hex()}")
            >>> 
            >>> # Read with 16-bit address
            >>> eeprom = I2c(0x50)
            >>> data = eeprom.readfrom_mem(0x0100, 32, addrsize=16)
        ```
        """

    def readfrom_mem_into(self, reg: int, buf: bytearray, *, addrsize: int = 8) -> int:
        """
        Read bytes from a register into a buffer.
        
        :param reg: Register address to read from
        :param buf: Buffer to read data into
        :param addrsize: Address size in bits (default: 8)
        :return: Number of bytes read
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Efficient repeated reads
            >>> buf = bytearray(6)
            >>> while True:
            ...     sensor.readfrom_mem_into(0x20, buf)
            ...     x, y, z = ustruct.unpack('<hhh', buf)
            ...     print(f"X={x}, Y={y}, Z={z}")
            ...     utime.sleep_ms(100)
        ```
        """

    def writeto(self, buf: bytes, *, stop: bool = True) -> int:
        """
        Write bytes directly to the I2C device.
        
        :param buf: Bytes to write
        :param stop: If True, send stop condition after writing
        :return: Number of bytes written
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Write command sequence
            >>> sensor.writeto(bytes([0x00, 0x01, 0x02]))
        ```
        """

    def writeto_mem(self, reg: int, buf: bytes, *, addrsize: int = 8) -> int:
        """
        Write bytes to a specific register address.
        
        :param reg: Register address to write to
        :param buf: Bytes to write
        :param addrsize: Address size in bits (default: 8)
        :return: Number of bytes written
        
        Example
        --------
        ```python
            >>> sensor = I2c(0x28)
            >>> 
            >>> # Write configuration block
            >>> config = bytes([0x01, 0x02, 0x03, 0x04])
            >>> sensor.writeto_mem(0x10, config)
            >>> 
            >>> # Write to EEPROM with 16-bit address
            >>> eeprom = I2c(0x50)
            >>> eeprom.writeto_mem(0x0100, b'Hello', addrsize=16)
        ```
        """

class ReplSerial:
    """
    Serial communication interface for REPL interaction.
    
    This class provides methods for reading and writing data through the
    REPL UART interface with configurable timeout support. Useful for
    implementing custom serial protocols and interactive applications.
    
    Key Features:
    
        - Configurable read timeout
        - Byte-level and pattern-based reading
        - Direct write access to serial output
    """
    
    def __init__(self, timeout: int | float | None = None):
        """
        Initialize the REPL serial interface.
        
        :param timeout: Read timeout in seconds (None for blocking)
        
        Example
        --------
        ```python
            >>> # Non-blocking serial
            >>> serial = ReplSerial(timeout=1.0)
            >>> 
            >>> # Blocking serial
            >>> serial = ReplSerial()
        ```
        """

    @property
    def timeout(self) -> int | float | None:
        """
        Get the current timeout value.
        
        :return: Timeout in seconds, or None if blocking
        """
    
    @timeout.setter
    def timeout(self, n: int | float | None):
        """
        Set the read timeout.
        
        :param n: Timeout in seconds, or None for blocking
        """

    def read(self, size: int = 1) -> bytes: 
        """
        Read bytes from the serial interface.
        
        :param size: Number of bytes to read (default: 1)
        :return: Bytes read from the interface
        
        Example
        --------
        ```python
            >>> serial = ReplSerial(timeout=1.0)
            >>> 
            >>> # Read single byte
            >>> b = serial.read()
            >>> 
            >>> # Read multiple bytes
            >>> data = serial.read(10)
            >>> print(f"Received: {data}")
        ```
        """
        
    def read_until(self, expected: bytes = b'\n', size: int | None = None) -> bytes:
        """
        Read until a pattern is found or size limit reached.
        
        :param expected: Byte pattern to stop at (default: newline)
        :param size: Maximum bytes to read (None for no limit)
        :return: Bytes read including the pattern
        
        Example
        --------
        ```python
            >>> serial = ReplSerial(timeout=5.0)
            >>> 
            >>> # Read line
            >>> line = serial.read_until(b'\\n')
            >>> print(f"Line: {line.decode()}")
            >>> 
            >>> # Read until custom delimiter
            >>> data = serial.read_until(b'\\r\\n', size=100)
        ```
        """
                    
    def write(self, data: bytes) -> int:
        """
        Write bytes to the serial interface.
        
        :param data: Bytes to write
        :return: Number of bytes written
        
        Example
        --------
        ```python
            >>> serial = ReplSerial()
            >>> 
            >>> # Write string
            >>> serial.write(b"Hello, World!\\n")
            >>> 
            >>> # Write formatted data
            >>> temp = 25.5
            >>> serial.write(f"Temperature: {temp}°C\\n".encode())
        ```
        """

class Led:
    """
    Built-in LED controller for XNode board.
    
    This class provides simple on/off/toggle control for the XNode's
    onboard LED (connected to D9), useful for status indication and debugging.
    """
    
    def __init__(self):
        """
        Initialize the LED controller.
        
        Sets up the LED pin for output control.
        
        Example
        --------
        ```python
            >>> led = Led()
            >>> led.on()   # Turn on
            >>> led.off()  # Turn off
        ```
        """

    def on(self) -> None:
        """
        Turn the LED on.
        
        Example
        --------
        ```python
            >>> led = Led()
            >>> led.on()
            >>> print("LED is now on")
        ```
        """
        
    def off(self) -> None:
        """
        Turn the LED off.
        
        Example
        --------
        ```python
            >>> led = Led()
            >>> led.off()
            >>> print("LED is now off")
        ```
        """

    def toggle(self) -> None:
        """
        Toggle the LED state.
        
        Switches the LED from on to off or off to on.
        
        Example
        --------
        ```python
            >>> led = Led()
            >>> 
            >>> # Blink pattern
            >>> for _ in range(10):
            ...     led.toggle()
            ...     utime.sleep_ms(500)
        ```
        """
        
    def value(self, n: int | None = None) -> int | None:
        """
        Get or set the LED state.
        
        :param n: If None, returns current state (0=off, 1=on). If given, sets state (1=on, 0=off).
        :return: Current LED state when called without argument, None when setting
        
        Example
        --------
        ```python
            >>> led = Led()
            >>> state = led.value()
            >>> print(f"LED is {'on' if state else 'off'}")
            >>> led.value(1)  # Turn on
            >>> led.value(0)  # Turn off
        ```
        """

class SupplyVoltage(machine.ADC):
    """
    Supply voltage monitor for XNode board.
    
    This class provides access to the XNode's supply voltage through
    the ADC interface, useful for battery monitoring and power management.
    """
 
    def __init__(self):
        """
        Initialize the supply voltage monitor.
        
        Sets up the ADC on the supply voltage sensing pin (D2).
        
        Example
        --------
        ```python
            >>> vsupply = SupplyVoltage()
            >>> voltage = vsupply.read()
            >>> print(f"Supply voltage: {voltage}V")
        ```
        """
        
    def read(self) -> float:
        """
        Read the current supply voltage.
        
        :return: Supply voltage in volts (rounded to 1 decimal place)
        
        Example
        --------
        ```python
            >>> vsupply = SupplyVoltage()
            >>> 
            >>> # Check voltage level
            >>> voltage = vsupply.read()
            >>> print(f"Supply: {voltage}V")
            >>> 
            >>> # Low battery warning
            >>> if voltage < 3.3:
            ...     print("Warning: Low battery!")
            >>> 
            >>> # Periodic monitoring
            >>> while True:
            ...     v = vsupply.read()
            ...     print(f"Voltage: {v}V")
            ...     utime.sleep(60)
        ```
        """

class Illuminance:
    """
    Illuminance sensor interface for BH1750 ambient light sensor.
    
    This class provides methods to read ambient light levels from a BH1750
    digital light sensor connected via I2C, with configurable measurement
    modes and scaling factors.
    """
    
    def __init__(self, *, mode: int = 0x10) -> None:
        """
        Initialize the illuminance sensor.
        
        :param mode: Measurement mode (CONT_HIGH_RES=0x10, CONT_HIGH_RES_2=0x11, CONT_LOW_RES=0x13)
        
        Example
        --------
        ```python
            >>> lux_sensor = Illuminance()
            >>> lux = lux_sensor.read()
            >>> print(f"Illuminance: {lux} lux")
        ```
        """

    def init(self, mode: int) -> None:
        """
        Re-initialize the sensor with a new mode.
        
        :param mode: Measurement mode constant
        """

    def deinit(self) -> None:
        """
        Power off the sensor.
        """

    def read(self) -> int:
        """
        Read the current illuminance raw count value.
        
        :return: Raw sensor count ((data[0] << 8) | data[1])
        
        Example
        --------
        ```python
            >>> sensor = Illuminance()
            >>> 
            >>> # Continuous reading
            >>> while True:
            ...     lux = sensor.read()
            ...     print(f"Light level: {lux} lux")
            ...     utime.sleep(1)
            >>> 
            >>> # One-time low-power reading
            >>> lux = sensor.read(continuous=False)
            >>> 
            >>> # Light level classification
            >>> lux = sensor.read()
            >>> if lux < 50:
            ...     print("Dark")
            >>> elif lux < 200:
            ...     print("Dim")
            >>> elif lux < 500:
            ...     print("Normal indoor")
            >>> else:
            ...     print("Bright")
        ```
        """ 

class Tphg:
    """
    Environmental sensor interface for BME680 sensor.
    
    This class provides comprehensive access to temperature, pressure, humidity,
    and gas resistance measurements from a BME680 environmental sensor. Includes
    Indoor Air Quality (IAQ) calculation with configurable weighting factors.
    
    Key Features:
    
        - Temperature measurement with correction support
        - Barometric pressure with altitude calculation
        - Relative humidity sensing
        - Gas resistance for air quality assessment
        - Indoor Air Quality (IAQ) scoring algorithm
        - Sensor burn-in monitoring for gas baseline
    """
        
    def __init__(self, temp_weighting: float = 0.10, pressure_weighting: float = 0.05,
                 humi_weighting: float = 0.20, gas_weighting: float = 0.65,
                 gas_ema_alpha: float = 0.1, temp_baseline: float = 23.0,
                 pressure_baseline: float = 1013.25, humi_baseline: float = 45.0,
                 gas_baseline: int = 450_000):
        """
        Initialize the environmental sensor.
        
        :param temp_weighting: Temperature weight in IAQ calculation (default: 0.10)
        :param pressure_weighting: Pressure weight in IAQ calculation (default: 0.05)
        :param humi_weighting: Humidity weight in IAQ calculation (default: 0.20)
        :param gas_weighting: Gas resistance weight in IAQ calculation (default: 0.65)
        :param gas_ema_alpha: Exponential moving average alpha for gas baseline (default: 0.1)
        :param temp_baseline: Reference temperature in Celsius (default: 23.0)
        :param pressure_baseline: Reference pressure in hPa (default: 1013.25)
        :param humi_baseline: Reference humidity percentage (default: 45.0)
        :param gas_baseline: Reference gas resistance in ohms (default: 450000)
        
        Example
        --------
        ```python
            >>> # Default initialization
            >>> sensor = Tphg()
            >>> 
            >>> # Custom IAQ weighting
            >>> sensor = Tphg(gas_weighting=0.70, humi_weighting=0.15)
            >>> 
            >>> # Read basic environmental data
            >>> temp, pressure, humidity = sensor.read()
            >>> print(f"T={temp}°C, P={pressure}hPa, H={humidity}%")
        ```
        """
            
    def set_temperature_correction(self, value: float) -> None:
        """
        Set temperature correction offset.
        
        Applies a correction value to all temperature readings to compensate
        for sensor self-heating or calibration errors.
        
        :param value: Correction value in Celsius (added to readings)
        
        Example
        --------
        ```python
            >>> sensor = Tphg()
            >>> 
            >>> # Compensate for 2°C self-heating
            >>> sensor.set_temperature_correction(-2.0)
            >>> 
            >>> # Now readings will be corrected
            >>> temp, _, _ = sensor.read()
        ```
        """

    def read(self, gas: bool = False) -> tuple:
        """
        Read environmental sensor data.
        
        :param gas: If True, also read gas resistance (slower measurement)
        :return: Tuple of (temperature, pressure, humidity) or (temperature, pressure, humidity, gas)
        
        Example
        --------
        ```python
            >>> sensor = Tphg()
            >>> 
            >>> # Basic reading (fast)
            >>> temp, pressure, humidity = sensor.read()
            >>> print(f"Temperature: {temp}°C")
            >>> print(f"Pressure: {pressure} hPa")
            >>> print(f"Humidity: {humidity}%")
            >>> 
            >>> # With gas resistance (slower)
            >>> temp, pressure, humidity, gas = sensor.read(gas=True)
            >>> print(f"Gas resistance: {gas} ohms")
            >>> 
            >>> # Weather station logging
            >>> while True:
            ...     t, p, h = sensor.read()
            ...     print(f"{t:.1f}°C, {p:.1f}hPa, {h:.1f}%")
            ...     utime.sleep(60)
        ```
        """
        
    def sealevel(self, altitude: float) -> tuple:
        """
        Calculate sea level pressure from current altitude.
        
        :param altitude: Current altitude in meters above sea level
        :return: Tuple of (sea_level_pressure, current_pressure) in hPa
        
        Example
        --------
        ```python
            >>> sensor = Tphg()
            >>> 
            >>> # Calculate sea level pressure at 500m altitude
            >>> sea_level, current = sensor.sealevel(500)
            >>> print(f"Sea level pressure: {sea_level} hPa")
            >>> print(f"Current pressure: {current} hPa")
        ```
        """
        
    def altitude(self, sealevel: float) -> tuple:
        """
        Calculate altitude from sea level pressure reference.
        
        :param sealevel: Sea level pressure reference in hPa
        :return: Tuple of (calculated_altitude, current_pressure)
        
        Example
        --------
        ```python
            >>> sensor = Tphg()
            >>> 
            >>> # Calculate altitude using standard sea level pressure
            >>> alt, pressure = sensor.altitude(1013.25)
            >>> print(f"Altitude: {alt:.1f} meters")
            >>> 
            >>> # Get altitude using local sea level pressure
            >>> local_sea_level = 1015.0  # From weather service
            >>> alt, _ = sensor.altitude(local_sea_level)
        ```
        """ 

    def iaq(self) -> tuple:
        """
        Calculate Indoor Air Quality score.
        
        Computes an IAQ score (0-500) based on temperature, pressure, humidity,
        and gas resistance readings with configurable weighting factors.
        
        :return: Tuple of (iaq_score, temperature, pressure, humidity, gas_resistance)
        
        Example
        --------
        ```python
            >>> sensor = Tphg()
            >>> 
            >>> # Get IAQ reading
            >>> iaq, temp, pressure, humidity, gas = sensor.iaq()
            >>> print(f"IAQ Score: {iaq}")
            >>> 
            >>> # IAQ classification
            >>> if iaq <= 50:
            ...     quality = "Excellent"
            >>> elif iaq <= 100:
            ...     quality = "Good"
            >>> elif iaq <= 150:
            ...     quality = "Moderate"
            >>> elif iaq <= 200:
            ...     quality = "Poor"
            >>> else:
            ...     quality = "Very Poor"
            >>> print(f"Air Quality: {quality}")
            >>> 
            >>> # Continuous monitoring with alerts
            >>> while True:
            ...     iaq, t, p, h, g = sensor.iaq()
            ...     if iaq > 150:
            ...         print(f"Warning: Poor air quality! IAQ={iaq}")
            ...     utime.sleep(60)
        ```
        """
        
    def burnIn(self, threshold: float = 0.01, count: int = 10,
               timeout_sec: int = 180) -> iter:
        """
        Monitor gas sensor stabilization during burn-in period.
        
        Yields status updates as the gas sensor stabilizes. The sensor is
        considered burned in when readings stabilize within the threshold
        for the specified count of consecutive readings.
        
        :param threshold: Relative change threshold for stability (default: 0.01 = 1%)
        :param count: Consecutive stable readings required (default: 10)
        :param timeout_sec: Maximum burn-in time in seconds (default: 180)
        :return: Generator yielding (is_burned_in, current_gas, gas_change) tuples
        
        Example
        --------
        ```python
            >>> sensor = Tphg()
            >>> 
            >>> # Wait for sensor burn-in
            >>> print("Warming up gas sensor...")
            >>> for done, gas, change in sensor.burnIn():
            ...     print(f"Gas: {gas}, Change: {change:.2%}")
            ...     if done:
            ...         print("Sensor ready!")
            ...         break
            >>> 
            >>> # Custom burn-in parameters
            >>> for done, gas, change in sensor.burnIn(threshold=0.005, count=20):
            ...     if done:
            ...         break
            >>> 
            >>> # Now take accurate readings
            >>> iaq, *_ = sensor.iaq()
        ```
        """
