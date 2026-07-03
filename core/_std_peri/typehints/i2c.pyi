"""
I2C Master Module

Platform-independent I2C master implementation with retry support,
validation, and convenience methods for common operations.

Features:

- Robust I2C communication with automatic retry on bus errors
- Address validation and error status tracking
- Typed register access methods (read_u8, read_u16, write_u8, write_u16)
- Scoped frequency change for mixed-speed peripherals
- Context manager support for resource cleanup
- I2CTarget support for slave device implementation

Classes:

- I2CController: High-level I2C controller (formerly I2CMaster)
- I2CTarget: I2C target device (formerly slave, platform dependent)

Functions:

- i2cdetect: Linux-style I2C bus scanner with formatted output

"""

from typing import overload


class I2CController:
    """
    I2C Controller with retry support and validation.
    
    Provides a robust interface to I2C peripherals with automatic
    retry on communication errors, address validation, and convenience
    methods for common read/write patterns.

    Example
    -------
    ```python
        >>> i2c = I2CController(sda=4, scl=5, id=0, freq=400_000)
        >>> 
        >>> # Scan for devices
        >>> devices = i2c.scan()
        >>> print(f"Found: {[hex(a) for a in devices]}")
        >>> 
        >>> # Read/write registers
        >>> val = i2c.read_u8(0x68, 0x75)  # WHO_AM_I register
        >>> i2c.write_u8(0x68, 0x6B, 0x00)  # Wake up MPU6050
        >>> 
        >>> # Context manager
        >>> with I2CController(sda=4, scl=5, id=0) as i2c:
        ...     i2c.probe(0x3C)
    ```
    """
    
    STAT_OK: int
    """No error."""

    STAT_TIMEOUT: int
    """Operation timed out."""

    STAT_BUS_ERR: int
    """Bus communication error."""

    STAT_NO_DEVICE: int
    """Device not responding."""

    def __init__(
        self,
        *,
        sda: int,
        scl: int,
        id: int = 0,
        freq: int = 400_000
    ) -> None:
        """
        Initialize I2C master.
        
        :param sda: GPIO pin number for SDA (data line)
        :param scl: GPIO pin number for SCL (clock line)
        :param id: I2C peripheral ID (0 or 1, platform dependent)
        :param freq: Clock frequency in Hz (default: 400kHz)
        
        :raises ValueError: If pin numbers are invalid
        :raises OSError: If I2C initialization fails

        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5, id=0)
            >>> i2c = I2CController(sda=0, scl=1, id=0, freq=100_000)
        ```
        """
        ...

    @property
    def bus_id(self) -> int:
        """I2C peripheral ID (0 or 1)."""
        ...

    @property
    def pins(self) -> tuple[int, int]:
        """Tuple of (sda_pin, scl_pin)."""
        ...

    @property
    def freq(self) -> int:
        """Current clock frequency in Hz."""
        ...

    @property
    def last_error(self) -> int:
        """Last error status (STAT_OK, STAT_BUS_ERR, etc.)."""
        ...

    def __repr__(self) -> str: ...
    def __enter__(self) -> "I2CController": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...

    def deinit(self) -> None:
        """
        Release I2C peripheral resources.

        Example
        -------
        ```python
            >>> i2c.deinit()
        ```
        """
        ...

    def set_retry_policy(
        self,
        *,
        retries: int | None = None,
        delay_us: int | None = None
    ) -> None:
        """
        Configure retry behavior for I2C operations.
        
        :param retries: Number of retry attempts on error (default: 1)
        :param delay_us: Delay between retries in microseconds (default: 200)

        Example
        -------
        ```python
            >>> i2c.set_retry_policy(retries=3, delay_us=500)
        ```
        """
        ...

    def set_freq(self, freq: int) -> None:
        """
        Set clock frequency.
        
        :param freq: Frequency in Hz (must be > 0)
        
        :raises ValueError: If freq <= 0

        Example
        -------
        ```python
            >>> i2c.set_freq(100_000)  # 100kHz for long wires
        ```
        """
        ...

    def scoped_freq(self, freq: int) -> "_FreqContext":
        """
        Context manager for temporary frequency change.
        
        Restores original frequency on exit.
        
        :param freq: Temporary frequency in Hz
        :return: Context manager that yields self

        Example
        -------
        ```python
            >>> # Temporarily use 100kHz for a slow device
            >>> with i2c.scoped_freq(100_000):
            ...     data = i2c.readfrom(0x50, 256)
            >>> # Back to original frequency
        ```
        """
        ...

    def scan(self) -> list[int]:
        """
        Scan bus for responding devices.
        
        :return: List of 7-bit addresses that responded

        Example
        -------
        ```python
            >>> addrs = i2c.scan()
            >>> print([hex(a) for a in addrs])
            ['0x3c', '0x68']
        ```
        """
        ...

    def probe(self, addr: int) -> bool:
        """
        Check if device responds at address.
        
        :param addr: 7-bit I2C address (0x00-0x7F)
        :return: True if device acknowledged, False otherwise

        Example
        -------
        ```python
            >>> if i2c.probe(0x3C):
            ...     print("OLED display found")
        ```
        """
        ...

    def readfrom(self, addr: int, nbytes: int, *, stop: bool = True) -> bytes:
        """
        Read bytes from device.
        
        :param addr: 7-bit I2C address
        :param nbytes: Number of bytes to read
        :param stop: Generate STOP condition (default: True)
        :return: Bytes read from device
        
        :raises ValueError: If address is invalid
        :raises OSError: If communication fails

        Example
        -------
        ```python
            >>> data = i2c.readfrom(0x50, 16)
        ```
        """
        ...

    def readfrom_into(self, addr: int, buf: bytearray, *, stop: bool = True) -> None:
        """
        Read bytes from device into existing buffer.
        
        :param addr: 7-bit I2C address
        :param buf: Buffer to read into
        :param stop: Generate STOP condition (default: True)
        
        :raises ValueError: If address is invalid
        :raises OSError: If communication fails

        Example
        -------
        ```python
            >>> buf = bytearray(16)
            >>> i2c.readfrom_into(0x50, buf)
        ```
        """
        ...

    def writeto(self, addr: int, buf: bytes | bytearray, *, stop: bool = True) -> int:
        """
        Write bytes to device.
        
        :param addr: 7-bit I2C address
        :param buf: Data to write
        :param stop: Generate STOP condition (default: True)
        :return: Number of bytes written
        
        :raises ValueError: If address is invalid
        :raises OSError: If communication fails

        Example
        -------
        ```python
            >>> i2c.writeto(0x3C, bytes([0x00, 0xAF]))  # Display ON
        ```
        """
        ...

    def readfrom_mem(
        self,
        addr: int,
        reg: int,
        nbytes: int,
        *,
        addrsize: int = 8
    ) -> bytes:
        """
        Read from device memory/register.
        
        :param addr: 7-bit I2C address
        :param reg: Register address
        :param nbytes: Number of bytes to read
        :param addrsize: Register address size in bits (8 or 16)
        :return: Bytes read from register

        Example
        -------
        ```python
            >>> # Read 6 bytes from MPU6050 accelerometer
            >>> data = i2c.readfrom_mem(0x68, 0x3B, 6)
        ```
        """
        ...

    def readfrom_mem_into(
        self,
        addr: int,
        reg: int,
        buf: bytearray,
        *,
        addrsize: int = 8
    ) -> None:
        """
        Read from device memory into existing buffer.
        
        :param addr: 7-bit I2C address
        :param reg: Register address
        :param buf: Buffer to read into
        :param addrsize: Register address size in bits (8 or 16)

        Example
        -------
        ```python
            >>> buf = bytearray(6)
            >>> i2c.readfrom_mem_into(0x68, 0x3B, buf)
        ```
        """
        ...

    def writeto_mem(
        self,
        addr: int,
        reg: int,
        buf: bytes | bytearray,
        *,
        addrsize: int = 8
    ) -> None:
        """
        Write to device memory/register.
        
        :param addr: 7-bit I2C address
        :param reg: Register address
        :param buf: Data to write
        :param addrsize: Register address size in bits (8 or 16)

        Example
        -------
        ```python
            >>> # Write config to BME280
            >>> i2c.writeto_mem(0x76, 0xF4, bytes([0x27]))
        ```
        """
        ...

    def read_u8(self, addr: int, reg: int, *, addrsize: int = 8) -> int:
        """
        Read unsigned 8-bit value from register.
        
        :param addr: 7-bit I2C address
        :param reg: Register address
        :param addrsize: Register address size in bits
        :return: Unsigned 8-bit value (0-255)

        Example
        -------
        ```python
            >>> who_am_i = i2c.read_u8(0x68, 0x75)
            >>> print(f"Device ID: 0x{who_am_i:02X}")
        ```
        """
        ...

    def read_u16(
        self,
        addr: int,
        reg: int,
        *,
        little_endian: bool = True,
        addrsize: int = 8
    ) -> int:
        """
        Read unsigned 16-bit value from register.
        
        :param addr: 7-bit I2C address
        :param reg: Register address
        :param little_endian: Byte order (default: True for LE)
        :param addrsize: Register address size in bits
        :return: Unsigned 16-bit value (0-65535)

        Example
        -------
        ```python
            >>> temp_raw = i2c.read_u16(0x76, 0xFA, little_endian=False)
        ```
        """
        ...

    def write_u8(self, addr: int, reg: int, val: int, *, addrsize: int = 8) -> None:
        """
        Write unsigned 8-bit value to register.
        
        :param addr: 7-bit I2C address
        :param reg: Register address
        :param val: Value to write (0-255)
        :param addrsize: Register address size in bits

        Example
        -------
        ```python
            >>> i2c.write_u8(0x68, 0x6B, 0x00)  # Wake MPU6050
        ```
        """
        ...

    def write_u16(
        self,
        addr: int,
        reg: int,
        val: int,
        *,
        little_endian: bool = True,
        addrsize: int = 8
    ) -> None:
        """
        Write unsigned 16-bit value to register.
        
        :param addr: 7-bit I2C address
        :param reg: Register address
        :param val: Value to write (0-65535)
        :param little_endian: Byte order (default: True for LE)
        :param addrsize: Register address size in bits

        Example
        -------
        ```python
            >>> i2c.write_u16(0x40, 0x06, 4096)  # PCA9685 prescale
        ```
        """
        ...

    def write_mem_ex(
        self,
        addr: int,
        reg_bytes: bytes,
        payload: bytes,
        *,
        stop: bool = True
    ) -> None:
        """
        Write with custom register address bytes.
        
        Useful for devices with non-standard register addressing.
        
        :param addr: 7-bit I2C address
        :param reg_bytes: Register address as raw bytes
        :param payload: Data to write
        :param stop: Generate STOP after payload

        Example
        -------
        ```python
            >>> # 24-bit address EEPROM
            >>> i2c.write_mem_ex(0x50, bytes([0x00, 0x01, 0x00]), data)
        ```
        """
        ...

    def read_mem_ex(
        self,
        addr: int,
        reg_bytes: bytes,
        n: int,
        out: bytearray | None = None
    ) -> bytes | None:
        """
        Read with custom register address bytes.
        
        :param addr: 7-bit I2C address
        :param reg_bytes: Register address as raw bytes
        :param n: Number of bytes to read
        :param out: Optional buffer to read into
        :return: Bytes read if out is None, otherwise None

        Example
        -------
        ```python
            >>> data = i2c.read_mem_ex(0x50, bytes([0x00, 0x01, 0x00]), 256)
        ```
        """
        ...


class _FreqContext:
    """Context manager for scoped_freq()."""
    def __enter__(self) -> I2CController: ...
    def __exit__(self, et, ev, tb) -> None: ...


class I2CTarget:
    """
    I2C Target (Slave) device implementation.
    
    Allows the board to act as an I2C peripheral device, responding
    to read/write requests from an I2C master controller.
    
    Can operate in two modes:
    
    - Memory mode: Provide a `mem` buffer that acts as registers
    - Callback mode: Handle read/write requests via IRQ handlers
    
    Note: Not all platforms support I2CTarget. Use I2CTarget.available()
    to check before instantiation.

    Example
    -------
    ```python
        >>> # Memory mode - acts as register device
        >>> if I2CTarget.available():
        ...     mem = bytearray(16)
        ...     target = I2CTarget(0x42, mem=mem)
        ...     # Master can now read/write mem via I2C
        >>> 
        >>> # Callback mode - custom handling
        >>> def handler(target):
        ...     flags = target.irq().flags()
        ...     if flags & I2CTarget.IRQ_WRITE_REQ:
        ...         buf = bytearray(1)
        ...         target.readinto(buf)
        ...     if flags & I2CTarget.IRQ_READ_REQ:
        ...         target.write(b'\\x55')
        >>> target = I2CTarget(0x42)
        >>> target.irq(handler, hard=True)
    ```
    """

    IRQ_ADDR_MATCH_READ: int
    """Target addressed for read."""

    IRQ_ADDR_MATCH_WRITE: int
    """Target addressed for write."""

    IRQ_READ_REQ: int
    """Master requesting data (must respond with write())."""

    IRQ_WRITE_REQ: int
    """Master sent data (must read with readinto())."""

    IRQ_END_READ: int
    """Read transaction completed."""

    IRQ_END_WRITE: int
    """Write transaction completed."""

    def __init__(
        self,
        addr: int,
        *,
        id: int = 0,
        sda: int | None = None,
        scl: int | None = None,
        addrsize: int = 7,
        mem: bytearray | None = None,
        mem_addrsize: int = 8
    ) -> None:
        """
        Initialize I2C target device.
        
        :param addr: I2C address for this target (7-bit: 0x00-0x7F, 10-bit: 0x000-0x3FF)
        :param id: I2C peripheral ID (platform dependent)
        :param sda: GPIO pin for SDA (optional, uses default if None)
        :param scl: GPIO pin for SCL (optional, uses default if None)
        :param addrsize: Address size in bits (7 or 10)
        :param mem: Backing memory buffer for register mode
        :param mem_addrsize: Memory address size in bits (0, 8, 16, 24, 32)
        
        :raises NotImplementedError: If platform doesn't support I2CTarget
        :raises ValueError: If address is invalid

        Example
        -------
        ```python
            >>> # 7-bit address, 8 registers
            >>> target = I2CTarget(0x42, mem=bytearray(8))
            >>> 
            >>> # 10-bit address, custom pins
            >>> target = I2CTarget(0x123, addrsize=10, sda=4, scl=5)
        ```
        """
        ...

    @property
    def addr(self) -> int:
        """I2C address of this target."""
        ...

    @property
    def bus_id(self) -> int:
        """I2C peripheral ID."""
        ...

    @property
    def pins(self) -> tuple[int | None, int | None]:
        """Tuple of (sda_pin, scl_pin), None if using defaults."""
        ...

    @property
    def memaddr(self) -> int:
        """Most recent memory address selected by master."""
        ...

    def __repr__(self) -> str: ...
    def __enter__(self) -> "I2CTarget": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...

    def deinit(self) -> None:
        """
        Deinitialize I2C target.
        
        After calling, the target will no longer respond on the I2C bus.

        Example
        -------
        ```python
            >>> target.deinit()
        ```
        """
        ...

    def readinto(self, buf: bytearray) -> int:
        """
        Read pending bytes from master into buffer.
        
        Call this in IRQ handler when IRQ_WRITE_REQ is set.
        
        :param buf: Buffer to read data into
        :return: Number of bytes read

        Example
        -------
        ```python
            >>> buf = bytearray(4)
            >>> n = target.readinto(buf)
            >>> print(f"Received {n} bytes: {buf[:n]}")
        ```
        """
        ...

    def write(self, buf: bytes | bytearray) -> int:
        """
        Write bytes to be sent to master.
        
        Call this in IRQ handler when IRQ_READ_REQ is set.
        Most ports only accept one byte at a time.
        
        :param buf: Data to send to master
        :return: Number of bytes written

        Example
        -------
        ```python
            >>> target.write(b'\\x55')
        ```
        """
        ...

    def irq(
        self,
        handler: callable | None = None,
        trigger: int | None = None,
        hard: bool = False
    ):
        """
        Configure IRQ handler for I2C events.
        
        :param handler: Callback function(target) called on events
        :param trigger: Bitmask of IRQ_* constants (default: END_READ | END_WRITE)
        :param hard: Use hard IRQ (required for READ_REQ/WRITE_REQ events)
        
        Note: IRQ_ADDR_MATCH_*, IRQ_READ_REQ, IRQ_WRITE_REQ require hard=True
        due to strict timing requirements.

        Example
        -------
        ```python
            >>> def on_event(target):
            ...     flags = target.irq().flags()
            ...     print(f"Event: {flags:02X}")
            >>> target.irq(on_event, trigger=I2CTarget.IRQ_END_WRITE)
        ```
        """
        ...

    @staticmethod
    def available() -> bool:
        """
        Check if I2CTarget is available on this platform.
        
        :return: True if machine.I2CTarget exists

        Example
        -------
        ```python
            >>> if I2CTarget.available():
            ...     target = I2CTarget(0x42)
            ... else:
            ...     print("I2CTarget not supported")
        ```
        """
        ...


def i2cdetect(i2c: I2CController, *, color: bool = True) -> list[int]:
    """
    Print I2C device scan results in i2cdetect format.
    
    Displays a formatted table showing responding devices
    similar to Linux i2cdetect utility output.
    
    :param i2c: I2CController instance to scan
    :param color: Use ANSI color codes for highlighting (default: True)
    :return: List of 7-bit addresses that responded

    Example
    -------
    ```python
        >>> i2c = I2CController(sda=4, scl=5, id=0)
        >>> devices = i2cdetect(i2c)
        I2C id=0 SDA=4 SCL=5: 2 device(s)
             0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
        00:          -- -- -- -- -- -- -- -- -- -- -- -- --
        10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
        20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
        30: -- -- -- -- -- -- -- -- -- -- -- 3b 3c -- -- --
        40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
        50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
        60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
        70: -- -- -- -- -- -- -- --
        >>> print(devices)
        [59, 60, 104]
    ```
    """
    ...
