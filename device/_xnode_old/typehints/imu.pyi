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
