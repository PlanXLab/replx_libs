"""
BNO055 9-DoF Absolute Orientation IMU Driver

A comprehensive driver for the Bosch BNO055 intelligent 9-axis absolute
orientation sensor with sensor fusion. The sensor combines accelerometer,
gyroscope, and magnetometer data to provide accurate orientation in
quaternion, Euler angles, and other formats.

Features:

- Automatic sensor fusion (NDOF mode) for accurate orientation
- Multiple output formats: quaternion, Euler angles, raw sensor data
- Hardware-calibrated accelerometer, gyroscope, and magnetometer
- Linear acceleration (gravity removed) and gravity vector
- Automatic calibration file save/load
- Interactive calibration wizard with 6-face accelerometer calibration
- Axis remapping for flexible mounting orientations

Sensor Type: D (Immediate) - Property-based data access

Output Data:

- Quaternion: Normalized (w, x, y, z) for 3D rotation
- Euler angles: Roll, pitch, yaw in radians
- Accelerometer: m/s² (raw acceleration including gravity)
- Gyroscope: rad/s (angular velocity)
- Magnetometer: μT (magnetic field)
- Linear acceleration: m/s² (gravity removed)
- Gravity vector: m/s² (gravity direction)
- Temperature: °C (die temperature)

Calibration:

The BNO055 requires calibration for accurate readings. Use
`run_calibration_wizard()` for interactive calibration, which saves
offsets to a file for automatic restoration on startup.

Example
-------
```python
from bno055 import BNO055

# Initialize with I2C pins
imu = BNO055(sda=4, scl=5)

# Wait for full calibration
if imu.wait_ready(timeout_s=30):
    print("Calibration complete")

# Read orientation as quaternion
w, x, y, z = imu.quat

# Read Euler angles (roll, pitch, yaw in radians)
roll, pitch, yaw = imu.euler

# Read all sensor data
accel, gyro, mag, quat, euler, linear, gravity, temp = imu.read()

# Check calibration status
diag = imu.diagnostics
print(f"Calibration: sys={diag['calib'][0]}, gyro={diag['calib'][1]}, "
      f"accel={diag['calib'][2]}, mag={diag['calib'][3]}")

# Clean up
imu.deinit()
```
"""
from typing import Tuple

READ_TYPE_ACCEL: int
READ_TYPE_GYRO: int
READ_TYPE_MAG: int
READ_TYPE_QUAT: int
READ_TYPE_EULER: int
READ_TYPE_LINEAR: int
READ_TYPE_GRAVITY: int
READ_TYPE_ALL: int


class BNO055:
    """
    BNO055 9-DoF Absolute Orientation IMU Driver.

    The BNO055 is a System in Package (SiP) integrating a triaxial 14-bit
    accelerometer, a triaxial 16-bit gyroscope, a triaxial geomagnetic sensor,
    and a 32-bit Cortex M0+ microcontroller running Bosch Sensortec sensor
    fusion software.
    """

    READ_TYPE_ACCEL: int
    READ_TYPE_GYRO: int
    READ_TYPE_MAG: int
    READ_TYPE_QUAT: int
    READ_TYPE_EULER: int
    READ_TYPE_LINEAR: int
    READ_TYPE_GRAVITY: int
    READ_TYPE_ALL: int
    CAL_FILE_NAME: str

    @staticmethod
    def run_calibration_wizard(
        sda: int,
        scl: int,
        *,
        addr: int = 0x28,
        accel_samples: int = 200,
        settle_ms: int = 500,
        savefile: str = ...,
    ) -> None:
        """
        Run interactive calibration wizard.

        Guides the user through a complete calibration procedure including
        gyroscope, 6-face accelerometer, and magnetometer calibration.
        Results are saved to a file for automatic restoration.

        :param sda: I2C SDA pin number
        :param scl: I2C SCL pin number
        :param addr: I2C address (default 0x28)
        :param accel_samples: Number of samples for accelerometer calibration
        :param settle_ms: Settling time in ms before sampling
        :param savefile: Path to save calibration data

        :raises RuntimeError: If calibration fails or sensor error occurs

        Example
        -------
        ```python
        # Run calibration (follow on-screen instructions)
        BNO055.run_calibration_wizard(sda=4, scl=5)

        # Then create instance (will auto-load calibration)
        imu = BNO055(sda=4, scl=5)
        ```
        """

    def __init__(
        self,
        sda: int,
        scl: int,
        *,
        addr: int = 0x28,
        calfile: str = ...,
    ) -> None:
        """
        Initialize BNO055 sensor.

        Resets the sensor, configures it for NDOF (Nine Degrees of Freedom)
        fusion mode with SI units, and loads calibration data if available.

        :param sda: I2C SDA pin number
        :param scl: I2C SCL pin number
        :param addr: I2C address (default 0x28, alternate 0x29)
        :param calfile: Path to calibration file to load

        :raises RuntimeError: If sensor is not found or not ready

        Example
        -------
        ```python
        # Basic initialization
        imu = BNO055(sda=4, scl=5)

        # With alternate address
        imu = BNO055(sda=4, scl=5, addr=0x29)

        # Without loading calibration
        imu = BNO055(sda=4, scl=5, calfile=None)
        ```
        """

    def deinit(self) -> None:
        """
        Deinitialize the sensor.

        Puts the sensor into suspend mode to minimize power consumption.
        The I2C connection is released.
        """

    def set_axis_remap(
        self,
        x: str = 'X',
        y: str = 'Y',
        z: str = 'Z',
        sx: int = 1,
        sy: int = 1,
        sz: int = 1,
    ) -> None:
        """
        Remap sensor axes for different mounting orientations.

        Allows remapping of physical sensor axes to logical axes, useful
        when the sensor is mounted in a non-standard orientation.

        :param x: Physical axis to map to X ('X', 'Y', or 'Z')
        :param y: Physical axis to map to Y ('X', 'Y', or 'Z')
        :param z: Physical axis to map to Z ('X', 'Y', or 'Z')
        :param sx: X axis sign (+1 or -1)
        :param sy: Y axis sign (+1 or -1)
        :param sz: Z axis sign (+1 or -1)

        :raises ValueError: If axis mapping is invalid

        Example
        -------
        ```python
        # Rotate 90° around Z axis
        imu.set_axis_remap(x='Y', y='X', z='Z', sx=-1, sy=1, sz=1)

        # Flip upside down
        imu.set_axis_remap(x='X', y='Y', z='Z', sx=1, sy=-1, sz=-1)
        ```
        """

    def wait_ready(self, timeout_s: int = 15) -> bool:
        """
        Wait for full sensor calibration.

        Blocks until all sensors (system, gyroscope, accelerometer,
        magnetometer) reach calibration level 3, or timeout expires.

        :param timeout_s: Maximum wait time in seconds
        :return: True if fully calibrated, False if timeout

        Example
        -------
        ```python
        imu = BNO055(sda=4, scl=5)
        if imu.wait_ready(timeout_s=30):
            print("Ready for use")
        else:
            print("Calibration incomplete, readings may be inaccurate")
        ```
        """

    def read(
        self,
    ) -> Tuple[
        Tuple[float, float, float],  # accel
        Tuple[float, float, float],  # gyro
        Tuple[float, float, float],  # magnetic
        Tuple[float, float, float, float],  # quat
        Tuple[float, float, float],  # euler
        Tuple[float, float, float],  # linear
        Tuple[float, float, float],  # gravity
        int,  # temp
    ]:
        """
        Read all sensor data at once.

        Convenience method to retrieve all sensor readings in a single call.

        :return: Tuple of (accel, gyro, magnetic, quat, euler, linear, gravity, temp)

        Example
        -------
        ```python
        accel, gyro, mag, quat, euler, linear, gravity, temp = imu.read()
        ```
        """

    @property
    def diagnostics(self) -> dict:
        """
        Get diagnostic information.

        :return: Dictionary with chip_id, sys_stat, sys_err, and calib tuple

        Example
        -------
        ```python
        diag = imu.diagnostics
        sys, gyro, accel, mag = diag['calib']
        print(f"Calibration: sys={sys}, gyro={gyro}, accel={accel}, mag={mag}")
        ```
        """

    @property
    def accel(self) -> Tuple[float, float, float]:
        """
        Raw accelerometer reading including gravity.

        :return: (x, y, z) acceleration in m/s²
        """

    @property
    def gyro(self) -> Tuple[float, float, float]:
        """
        Gyroscope reading (angular velocity).

        :return: (x, y, z) angular velocity in rad/s
        """

    @property
    def magnetic(self) -> Tuple[float, float, float]:
        """
        Magnetometer reading (magnetic field).

        :return: (x, y, z) magnetic field in μT (microtesla)
        """

    @property
    def euler(self) -> Tuple[float, float, float]:
        """
        Euler angles computed from quaternion.

        Returns orientation as Euler angles using the aerospace
        convention (roll-pitch-yaw / X-Y-Z rotation order).

        :return: (roll, pitch, yaw) angles in radians

        Note
        ----
        Euler angles are computed from quaternion to avoid gimbal lock
        issues inherent in the sensor's native Euler output.
        """

    @property
    def quat(self) -> Tuple[float, float, float, float]:
        """
        Quaternion orientation (most accurate).

        Returns the fused orientation as a unit quaternion, which is
        the most accurate and gimbal-lock-free representation.

        :return: (w, x, y, z) normalized quaternion components
        """

    @property
    def linear(self) -> Tuple[float, float, float]:
        """
        Linear acceleration with gravity removed.

        Returns acceleration due to motion only, with the gravity
        component removed by the fusion algorithm.

        :return: (x, y, z) linear acceleration in m/s²
        """

    @property
    def gravity(self) -> Tuple[float, float, float]:
        """
        Gravity vector direction.

        Returns the direction and magnitude of gravity as sensed
        by the accelerometer, useful for determining "down" direction.

        :return: (x, y, z) gravity vector in m/s² (magnitude ~9.81)
        """

    @property
    def temp(self) -> int:
        """
        Die temperature.

        :return: Temperature in °C (signed integer)
        """
