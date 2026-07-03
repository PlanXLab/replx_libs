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
        
        :return: 1 if motion is detected, 0 otherwise
        
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

class IRThermometer: 
    """
    Infrared thermometer sensor controller for MLX90614.
    
    This class provides an interface for the MLX90614 non-contact infrared
    thermometer sensor, capable of measuring both ambient temperature and
    object surface temperature without physical contact.
    
    Key Features:
    
        - Non-contact temperature measurement
        - Ambient and object temperature modes
        - High accuracy (±0.5°C typical)
        - Wide measurement range (-40°C to +125°C ambient, -70°C to +380°C object)
    """

    def __init__(self) -> None:
        """
        Initialize the IR thermometer sensor.
        
        Sets up I2C communication with the MLX90614 sensor at address 0x5A.
        Uses 50kHz I2C frequency for reliable communication.
        
        Example
        --------
        ```python
            >>> thermo = IRThermometer()
            >>> 
            >>> # Read object temperature
            >>> temp = thermo.object()
            >>> print(f"Object temperature: {temp}°C")
            >>> 
            >>> # Read ambient temperature
            >>> ambient = thermo.ambient()
            >>> print(f"Ambient temperature: {ambient}°C")
        ```
        """

    def read(self, object: bool = True, eeprom: bool = False) -> int:
        """
        Read raw temperature data from the sensor.
        
        Returns the raw 16-bit temperature value from the sensor.
        Use ambient() or object() methods for converted temperature values.
        
        :param object: If True, read object temperature; if False, read ambient temperature
        :param eeprom: If True, read from EEPROM; if False, read from RAM
        :return: Raw 16-bit temperature value
        
        Example
        --------
        ```python
            >>> thermo = IRThermometer()
            >>> 
            >>> # Read raw object temperature
            >>> raw = thermo.read(object=True)
            >>> print(f"Raw value: {raw}")
            >>> 
            >>> # Read raw ambient temperature
            >>> raw_ambient = thermo.read(object=False)
            >>> 
            >>> # Convert raw to Celsius
            >>> temp_c = raw * 0.02 - 273.15
            >>> print(f"Temperature: {temp_c:.1f}°C")
        ```
        """

    def ambient(self) -> float:
        """
        Read the ambient temperature.
        
        Returns the temperature of the sensor's surrounding environment
        (not the target object).
        
        :return: Ambient temperature in degrees Celsius (rounded to 1 decimal)
        
        Example
        --------
        ```python
            >>> thermo = IRThermometer()
            >>> 
            >>> # Read ambient temperature
            >>> ambient = thermo.ambient()
            >>> print(f"Room temperature: {ambient}°C")
            >>> 
            >>> # Monitor ambient over time
            >>> while True:
            ...     temp = thermo.ambient()
            ...     print(f"Ambient: {temp}°C")
            ...     utime.sleep(60)
            >>> 
            >>> # Temperature logging
            >>> readings = []
            >>> for _ in range(10):
            ...     readings.append(thermo.ambient())
            ...     utime.sleep(1)
            >>> avg = sum(readings) / len(readings)
            >>> print(f"Average ambient: {avg:.1f}°C")
        ```
        """

    def object(self) -> float:
        """
        Read the object (target) temperature.
        
        Returns the temperature of the object in the sensor's field of view
        using non-contact infrared measurement.
        
        :return: Object temperature in degrees Celsius (rounded to 1 decimal)
        
        Example
        --------
        ```python
            >>> thermo = IRThermometer()
            >>> 
            >>> # Read object temperature
            >>> temp = thermo.object()
            >>> print(f"Object temperature: {temp}°C")
            >>> 
            >>> # Fever detection
            >>> body_temp = thermo.object()
            >>> if body_temp > 37.5:
            ...     print("Elevated temperature detected!")
            >>> 
            >>> # Surface temperature monitoring
            >>> while True:
            ...     obj = thermo.object()
            ...     amb = thermo.ambient()
            ...     diff = obj - amb
            ...     print(f"Object: {obj}°C, Ambient: {amb}°C, Diff: {diff:+.1f}°C")
            ...     utime.sleep(1)
            >>> 
            >>> # Hot spot detection
            >>> threshold = 50.0
            >>> if thermo.object() > threshold:
            ...     print(f"Warning: Temperature exceeds {threshold}°C!")
        ```
        """

class IMU:
    """
    Inertial Measurement Unit controller for BNO055 sensor.
    
    This class provides an interface for the BNO055 9-DOF absolute orientation
    sensor with on-chip sensor fusion. The sensor combines accelerometer,
    gyroscope, and magnetometer data to provide accurate orientation data.
    
    Key Features:
    
        - 9-DOF sensor fusion (accelerometer, gyroscope, magnetometer)
        - Absolute orientation output (Euler angles, quaternions)
        - Linear acceleration (gravity-compensated)
        - Gravity vector measurement
        - Temperature sensing
        - Calibration status monitoring
    
    Data Types:
    
        - ACCELERATION: Raw accelerometer data (m/s²)
        - MAGNETIC: Magnetometer data (µT)
        - GYROSCOPE: Gyroscope data (rad/s)
        - EULER: Orientation as Euler angles (degrees)
        - QUATERNION: Orientation as quaternion
        - ACCEL_LINEAR: Linear acceleration without gravity (m/s²)
        - ACCEL_GRAVITY: Gravity vector (m/s²)
        - TEMPERATURE: Sensor temperature (°C)
    """
    
    ACCELERATION: int
    MAGNETIC: int
    GYROSCOPE: int
    EULER: int
    QUATERNION: int
    ACCEL_LINEAR: int
    ACCEL_GRAVITY: int
    TEMPERATURE: int
    
    def __init__(self) -> None:
        """
        Initialize the IMU sensor.
        
        Sets up I2C communication with the BNO055 at address 0x28 and
        configures the sensor for NDOF (Nine Degrees of Freedom) fusion mode
        with external crystal for improved accuracy.
        
        Example
        --------
        ```python
            >>> imu = IMU()
            >>> 
            >>> # Read orientation
            >>> heading, roll, pitch = imu.read(IMU.EULER)
            >>> print(f"Heading: {heading}°, Roll: {roll}°, Pitch: {pitch}°")
            >>> 
            >>> # Check calibration
            >>> sys, gyro, accel, mag = imu.calibration()
            >>> print(f"Calibration: Sys={sys}, Gyro={gyro}, Accel={accel}, Mag={mag}")
        ```
        """
    
    def calibration(self) -> tuple:
        """
        Read the calibration status of all sensors.
        
        Returns calibration levels (0-3) for each sensor component.
        A value of 3 indicates fully calibrated.
        
        :return: Tuple of (system, gyroscope, accelerometer, magnetometer) calibration levels (0-3 each)
        
        Example
        --------
        ```python
            >>> imu = IMU()
            >>> 
            >>> # Check calibration
            >>> sys, gyro, accel, mag = imu.calibration()
            >>> print(f"System: {sys}/3")
            >>> print(f"Gyroscope: {gyro}/3")
            >>> print(f"Accelerometer: {accel}/3")
            >>> print(f"Magnetometer: {mag}/3")
            >>> 
            >>> # Wait for full calibration
            >>> while True:
            ...     sys, gyro, accel, mag = imu.calibration()
            ...     if sys == 3 and gyro == 3 and accel == 3 and mag == 3:
            ...         print("Fully calibrated!")
            ...         break
            ...     print(f"Calibrating... S:{sys} G:{gyro} A:{accel} M:{mag}")
            ...     utime.sleep(1)
            >>> 
            >>> # Calibration quality check
            >>> sys, _, _, _ = imu.calibration()
            >>> if sys < 2:
            ...     print("Warning: Low calibration quality")
        ```
        """

    def read(self, target: int) -> tuple | int:
        """
        Read data from the specified sensor output.
        
        Reads and returns processed sensor data based on the target type.
        Vector data is returned as tuples, scalar data as integers.
        
        :param target: Data type to read (ACCELERATION, MAGNETIC, GYROSCOPE, EULER, QUATERNION, ACCEL_LINEAR, ACCEL_GRAVITY, or TEMPERATURE)
        :return: Tuple of values for vector data, integer for temperature
        
        Example
        --------
        ```python
            >>> imu = IMU()
            >>> 
            >>> # Read Euler angles (heading, roll, pitch)
            >>> heading, roll, pitch = imu.read(IMU.EULER)
            >>> print(f"Heading: {heading:.1f}°")
            >>> print(f"Roll: {roll:.1f}°")
            >>> print(f"Pitch: {pitch:.1f}°")
            >>> 
            >>> # Read quaternion orientation
            >>> w, x, y, z = imu.read(IMU.QUATERNION)
            >>> print(f"Quaternion: ({w:.3f}, {x:.3f}, {y:.3f}, {z:.3f})")
            >>> 
            >>> # Read acceleration
            >>> ax, ay, az = imu.read(IMU.ACCELERATION)
            >>> print(f"Acceleration: X={ax:.2f}, Y={ay:.2f}, Z={az:.2f} m/s²")
            >>> 
            >>> # Read linear acceleration (without gravity)
            >>> lx, ly, lz = imu.read(IMU.ACCEL_LINEAR)
            >>> 
            >>> # Read gravity vector
            >>> gx, gy, gz = imu.read(IMU.ACCEL_GRAVITY)
            >>> 
            >>> # Read gyroscope
            >>> gx, gy, gz = imu.read(IMU.GYROSCOPE)
            >>> print(f"Angular velocity: {gx:.3f}, {gy:.3f}, {gz:.3f} rad/s")
            >>> 
            >>> # Read magnetometer
            >>> mx, my, mz = imu.read(IMU.MAGNETIC)
            >>> 
            >>> # Read temperature
            >>> temp = imu.read(IMU.TEMPERATURE)
            >>> print(f"IMU Temperature: {temp}°C")
            >>> 
            >>> # Real-time orientation display
            >>> while True:
            ...     h, r, p = imu.read(IMU.EULER)
            ...     print(f"H:{h:6.1f}° R:{r:6.1f}° P:{p:6.1f}°")
            ...     utime.sleep_ms(100)
        ```
        """

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
    UPDATE_10HZ: str

    GPGGA: str
    GPVTG: str
    GPRMC: str
    
    BAUD_9600: str
    BAUD_19200: str
    BAUD_38400: str
    BAUD_115200: str
                
    def __init__(self, first_update: bool = True, gps_mode: str = None,
                 baudrate: str = None) -> None:
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

    def setBaudrate(self, baudrate: str) -> None:
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
    def timestamp(self) -> str:
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

class Basic:
    """
    Basic I/O expansion board controller.
    
    This class provides interfaces for the Basic I/O expansion board featuring
    a PCA9535 GPIO expander. Includes buzzer control, LED array, and button
    matrix for educational and prototyping applications.
    
    Components:
    
        - Buzzer: Audio feedback with on/off and beep patterns
        - Leds: 8-channel LED array with individual and group control
        - Buttons: 8-channel button matrix with individual and group read
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
                >>> buzzer = Basic.Buzzer()
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
                >>> buzzer = Basic.Buzzer()
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
                >>> buzzer = Basic.Buzzer()
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
                >>> gpio = Basic._I2CtoGPIO()
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
                >>> gpio = Basic._I2CtoGPIO()
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
                >>> leds = Basic.Leds()
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
                >>> leds = Basic.Leds()
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
                >>> leds = Basic.Leds()
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
                >>> leds = Basic.Leds()
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
                >>> leds = Basic.Leds()
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
                >>> leds = Basic.Leds()
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
                >>> leds = Basic.Leds()
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
                >>> leds = Basic.Leds()
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
                >>> buttons = Basic.Buttons()
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
                >>> buttons = Basic.Buttons()
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

