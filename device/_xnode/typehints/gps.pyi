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

- GPS Module: NMEA sentence parsing with configurable update rates and multiple output formats

Key Features:

- Plug-and-play sensor initialization with sensible defaults
- Configurable measurement parameters for application-specific tuning
- Real-time data acquisition with efficient polling patterns
- Low-power operation support for battery-powered deployments
- I2C and UART communication abstraction

Author: PlanXLab Development Team
"""

SC16IS750_ADDR: int
RHR: int
THR: int
IER: int
FCR: int
IIR: int
LCR: int
MCR: int
LSR: int
MSR: int
SPR: int
TXLVL: int
RXLVL: int
IODIR: int
IOSTATE: int
IOINTENA: int
IOCTRL: int
EFCR: int
DLL: int
DLH: int
LSR_DR: int
LSR_OE: int
LSR_PE: int
LSR_FE: int
LSR_BI: int
LSR_THRE: int
LSR_TEMT: int
LSR_FIFOE: int
FCR_FIFO_ENABLE: int
FCR_FIFO_RCVR_RESET: int
FCR_FIFO_XMIT_RESET: int
FCR_FIFO_DMA_MODE: int
FCR_FIFO_64: int
FCR_FIFO_RCVR_TRIGGER_MASK: int
FCR_FIFO_RCVR_TRIGGER_8: int
FCR_FIFO_RCVR_TRIGGER_16: int
FCR_FIFO_RCVR_TRIGGER_32: int
FCR_FIFO_RCVR_TRIGGER_60: int
MCR_DTR: int
MCR_RTS: int
MCR_LOOP: int

class Gps:
    """
    GPS module controller with NMEA parsing.
    
    This class provides an interface for GPS modules with UART communication,
    supporting NMEA sentence parsing and various configuration options for
    update rate, output format, and baud rate.
    
    Key Features:
    
        - NMEA sentence parsing (GPGGA, GPRMC, GPVTG)
        - Configurable update rates (1Hz, 2Hz, 10Hz)
        - Position data (latitude, longitude, altitude)
        - Velocity data (speed, course)
        - Fix quality and satellite information
    
    Supported NMEA Sentences:
    
        - GPGGA: Position, altitude, fix quality
        - GPRMC: Position, velocity, timestamp
        - GPVTG: Velocity and course
    """

    UPDATE_1HZ: str
    UPDATE_2HZ: str
    UPDATE_5HZ: str
    UPDATE_10HZ: str

    GPGGA: str
    GPVTG: str
    GPRMC: str
    GPGGA_GPRMC: str
    ALL_NMEA: str
    
    BAUD_9600: str
    BAUD_19200: str
    BAUD_38400: str
    BAUD_115200: str
    latest_nmea: str
    gps_mode: str
    date: str | None
    speed_over_ground_knots: float
    speed_over_ground_kmh: float
    course_over_ground: float
                
    def __init__(self, fast_update: bool = True, gps_mode: str | None = None,
                 baudrate: str | int | None = None, *, first_update: bool | None = None) -> None:
        """
        Initialize the GPS module.
        
        Sets up UART communication with the GPS module and configures
        the output format and update rate.
        
        :param first_update: If True, set fast update rate initially (default: True)
        :param gps_mode: NMEA output mode (GPGGA, GPRMC, or GPVTG, default: GPGGA)
        :param baudrate: UART baud rate (default: BAUD_9600)
        
        Example
        --------
        ```python
            >>> # Basic initialization
            >>> gps = Gps()
            >>> 
            >>> # With specific configuration
            >>> gps = Gps(gps_mode=Gps.GPRMC, baudrate=Gps.BAUD_9600)
            >>> 
            >>> # Update and read position
            >>> if gps.update():
            ...     print(f"Lat: {gps.latitude}, Lon: {gps.longitude}")
        ```
        """

    def set_baudrate(self, baudrate: str | int) -> None: ...
    def set_update_rate(self, rate_cmd: str) -> None: ...
    def set_fast_update(self, fast_update: bool = True) -> None: ...
    def set_mode(self, gps_mode: str) -> None: ...
    @staticmethod
    def verify_checksum(sentence: str) -> bool: ...
    @property
    def has_fix(self) -> bool: ...
    @property
    def position(self) -> tuple[float, float, float]: ...
    @property
    def hdop(self) -> float: ...

    def setBaudrate(self, baudrate: str | int) -> None:
        """
        Set the GPS module baud rate.
        
        Changes the UART communication speed. Note: 38400 and 115200 baud
        rates may not be reliable with all GPS modules.
        
        :param baudrate: Baud rate command string (BAUD_9600, BAUD_19200, etc.)
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> 
            >>> # Change to 19200 baud
            >>> gps.setBaudrate(Gps.BAUD_19200)
        ```
        """
                
    def setFastUpdate(self, fast_update: bool) -> None:
        """
        Configure the GPS update rate.
        
        :param fast_update: If True, use faster update rate
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> 
            >>> # Enable fast updates
            >>> gps.setFastUpdate(True)
        ```
        """
    
    def setGpsMode(self, gps_mode: str) -> None:
        """
        Set the NMEA output mode.
        
        Configures which NMEA sentence type the GPS module outputs.
        
        :param gps_mode: NMEA mode command (GPGGA, GPRMC, or GPVTG)
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> 
            >>> # Switch to GPRMC for velocity data
            >>> gps.setGpsMode(Gps.GPRMC)
            >>> 
            >>> # Switch to GPGGA for altitude data
            >>> gps.setGpsMode(Gps.GPGGA)
        ```
        """

    def update(self, timeout_ms: int = 2000) -> bool:
        """
        Read and parse NMEA data from the GPS module.
        
        Reads NMEA sentences from the GPS and parses the data, updating
        all position and velocity properties.
        
        :param timeout_ms: Maximum time to wait for valid data in milliseconds (default: 2000)
        :return: True if valid NMEA sentence was parsed, False on timeout or error
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> 
            >>> # Simple position read
            >>> if gps.update():
            ...     print(f"Position: {gps.latitude}, {gps.longitude}")
            >>> else:
            ...     print("No GPS fix")
            >>> 
            >>> # Continuous tracking
            >>> while True:
            ...     if gps.update(timeout_ms=1000):
            ...         print(f"Lat: {gps.latitude:.6f}")
            ...         print(f"Lon: {gps.longitude:.6f}")
            ...         print(f"Alt: {gps.altitude:.1f}m")
            ...         print(f"Satellites: {gps.satellites_in_use}")
            ...     else:
            ...         print("Waiting for fix...")
            ...     utime.sleep(1)
            >>> 
            >>> # With custom timeout
            >>> if gps.update(timeout_ms=5000):
            ...     print("Got fix!")
        ```
        """    
        
    @property
    def latitude(self) -> float:
        """
        Get the current latitude.
        
        :return: Latitude in decimal degrees (positive = North, negative = South)
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> print(f"Latitude: {gps.latitude:.6f}°")
        ```
        """
       
    @property
    def longitude(self) -> float:
        """
        Get the current longitude.
        
        :return: Longitude in decimal degrees (positive = East, negative = West)
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> print(f"Longitude: {gps.longitude:.6f}°")
        ```
        """
    
    @property
    def altitude(self) -> float:
        """
        Get the current altitude.
        
        :return: Altitude above mean sea level in meters
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> print(f"Altitude: {gps.altitude:.1f}m")
        ```
        """
    
    @property
    def fix_quality(self) -> int:
        """
        Get the GPS fix quality indicator.
        
        :return: Fix quality (0=invalid, 1=GPS fix, 2=DGPS fix, etc.)
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> quality = gps.fix_quality
            >>> if quality == 0:
            ...     print("No fix")
            >>> elif quality == 1:
            ...     print("GPS fix")
            >>> elif quality == 2:
            ...     print("DGPS fix")
        ```
        """

    @property
    def satellites_in_use(self) -> int:
        """
        Get the number of satellites used for the fix.
        
        :return: Number of satellites in use
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> sats = gps.satellites_in_use
            >>> print(f"Tracking {sats} satellites")
            >>> if sats < 4:
            ...     print("Warning: Weak signal")
        ```
        """

    @property
    def timestamp(self) -> str | None:
        """
        Get the timestamp of the last fix.
        
        :return: UTC timestamp in HHMMSS.sss format
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> print(f"Time: {gps.timestamp}")
        ```
        """
    
    @property
    def fix_status(self) -> str:
        """
        Get the fix status from GPRMC sentence.
        
        :return: 'A' for Active (valid fix), 'V' for Void (invalid)
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> if gps.fix_status == 'A':
            ...     print("Valid fix")
            >>> else:
            ...     print("Invalid fix")
        ```
        """

    @property
    def speed_knots(self) -> float:
        """
        Get the speed over ground in knots.
        
        :return: Speed in knots
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> print(f"Speed: {gps.speed_knots:.1f} knots")
        ```
        """

    @property
    def speed_kmh(self) -> float:
        """
        Get the speed over ground in km/h.
        
        :return: Speed in kilometers per hour
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> print(f"Speed: {gps.speed_kmh:.1f} km/h")
            >>> 
            >>> # Speed monitoring
            >>> while True:
            ...     if gps.update():
            ...         speed = gps.speed_kmh
            ...         if speed > 50:
            ...             print(f"Speed limit warning: {speed:.0f} km/h")
            ...     utime.sleep(1)
        ```
        """

    @property
    def course(self) -> float:
        """
        Get the course over ground.
        
        :return: Course in degrees (0-360, 0=North, 90=East)
        
        Example
        --------
        ```python
            >>> gps = Gps()
            >>> gps.update()
            >>> course = gps.course
            >>> print(f"Heading: {course:.1f}°")
            >>> 
            >>> # Cardinal direction
            >>> if 315 <= course or course < 45:
            ...     direction = "North"
            >>> elif 45 <= course < 135:
            ...     direction = "East"
            >>> elif 135 <= course < 225:
            ...     direction = "South"
            >>> else:
            ...     direction = "West"
            >>> print(f"Direction: {direction}")
        ```
        """