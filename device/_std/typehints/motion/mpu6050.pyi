"""
MPU6050 6-DoF IMU Driver with DMP Support

A comprehensive driver for the InvenSense MPU6050 6-axis motion tracking
device with onboard Digital Motion Processor (DMP). Combines 3-axis
accelerometer and 3-axis gyroscope with hardware sensor fusion for
quaternion and Euler-angle output.

Features:
- Bias-corrected accelerometer and gyroscope data access
- Mounting remap with signed axis permutations such as "xyz" and "x-zy"
- Output coordinate modes: raw, ENU, ROS FLU body frame, and NED
- DMP-based quaternion/Euler output and accel-based tilt computation
- Frame-synchronized linear acceleration (gravity-compensated)
- Auto-calibration with hardware offsets for DMP mode
- Multiple operating modes (DMP/RAW, various sample rates)

Sensor Type: D (Immediate) - Property-based data access
Interface: I2C (400kHz)
"""
from i2c import I2CController

class MPU6050:
    """
    MPU6050 6-axis IMU driver with DMP (Digital Motion Processor) support.

    The MPU6050 combines a 3-axis accelerometer and 3-axis gyroscope with an
    onboard DMP that can compute quaternion orientation. This driver supports
    bias-corrected PCB-frame data access, signed axis remapping for mounting,
    and ENU/FLU/NED output coordinates.

    Features
    --------
    - Accelerometer: +/-8g range, outputs in m/s^2
    - Gyroscope: +/-2000 dps range, outputs in rad/s
    - coord='raw', 'enu', 'flu', or 'ned'
    - remap strings such as 'xyz', 'x-zy', or 'yx-z'
    - Configurable I2C frequency for bus troubleshooting
    - DMP quaternion and Euler output transformed by coord and remap
        - Auto-calibration: Quick bias estimation, DMP hardware offsets, and
            residual gyro bias correction

    Coordinate Model
    ----------------
    The MPU6050 chip/PCB frame is the fixed physical sensor frame. ``remap``
    maps that PCB frame directly into the selected output frame using a signed
    permutation. The mapping is written as output X, output Y, output Z.

    For TiCLE Lite's Basic-board orientation, ``coord='flu', remap='x-zy'``
    means output X = PCB X, output Y = -PCB Z, and output Z = PCB Y. Accel,
    gyro, DMP quaternion, tilt, Euler, and linear acceleration all use this
    same final output-frame transform.

    If ``remap`` is omitted, ``coord`` selects a conventional default mapping:
    ``'raw'`` and ``'enu'`` use ``'xyz'``, ``'flu'`` uses ``'y-xz'``, and
    ``'ned'`` uses ``'yx-z'``. When ``remap`` is supplied explicitly, it is
    already the final output-frame mapping and is not transformed a second time.

    ``remap`` must use x, y, and z exactly once and preserve a right-handed
    coordinate frame. DMP quaternion, tilt, linear acceleration, accel,
    and gyro all use the same transformed output frame. ``raw_accel`` and
    ``raw_gyro`` always return bias-corrected IMU PCB-frame values.

    Example
    -------
    ```python
        >>> import math
        >>> import time
        >>> from i2c import I2CController
        >>> from mpu6050 import MPU6050

        >>> i2c = I2CController(sda=12, scl=13)
        >>> imu = MPU6050(i2c,
        ...               mode=MPU6050.Mode.DMP_STABLE,
        ...               coord='flu',
        ...               remap='x-zy')
        >>> t0 = time.ticks_ms()
        >>> while time.ticks_diff(time.ticks_ms(), t0) < 1_000:
        ...     roll, pitch = imu.tilt
        ...     time.sleep_ms(100)
        >>> roll, pitch = imu.tilt
        >>> print(math.degrees(roll), math.degrees(pitch))
        >>> imu.deinit()

        >>> raw = MPU6050(i2c, mode=MPU6050.Mode.RAW_FAST,
        ...               coord='raw', remap='xyz')
        >>> ax, ay, az = raw.accel
        >>> pcb_ax, pcb_ay, pcb_az = raw.raw_accel
        >>> raw.deinit()
    ```
    """

    DLPF_DIV8K_256HZ: int
    DLPF_DIV1K_98HZ: int
    DLPF_DIV1K_42HZ: int
    SIMPLERT_DIV8K_1KHz: int
    SIMPLERT_DIV1K_200Hz: int
    SIMPLERT_DIV1K_100Hz: int

    class Mode:
        """Operating mode presets for the MPU6050."""
        DMP_STABLE: str
        DMP_FAST: str
        RAW_BALANCED: str
        RAW_FAST: str

    def __init__(
        self,
        i2c: I2CController,
        *,
        addr: int = 0x68,
        mode: str = Mode.RAW_BALANCED,
        coord: str = 'raw',
        remap: str | None = None,
    ) -> None:
        """
        Initialize the MPU6050 IMU.

        :param i2c: Shared I2CController instance.
        :param addr: I2C address (0x68 default, 0x69 if AD0 high).
        :param mode: Operating mode preset.
        :param coord: Output coordinate convention: 'raw', 'enu', 'flu', or 'ned'.
            'raw' applies only remap. 'enu' uses the same axis order as the
            remapped base frame as an ENU world-style frame. 'flu' converts
            the remapped ENU-style base frame to the ROS robot body frame
            (Forward-Left-Up) using (x, y, z) -> (y, -x, z). 'ned' converts
            the remapped ENU-style base frame to NED using (x, y, z) ->
            (y, x, -z).
        :param remap: Signed axis permutation from IMU PCB frame directly to
            the selected output frame. It must use x, y, and z exactly once and
            must preserve a right-handed frame. Examples: 'xyz', 'x-zy',
            'yx-z'. If omitted, coord selects a conventional default remap.
        :raises RuntimeError: If I2C scan fails, the MPU6050 address is not
            found, the WHO_AM_I value is not valid, or DMP mode cannot locate
            responsive accelerometer offset registers.
        :raises ValueError: If mode, coord, or remap is invalid.

        Example
        -------
        ```python
            >>> import time
            >>> from i2c import I2CController
            >>> from mpu6050 import MPU6050
            >>> i2c = I2CController(sda=12, scl=13)
            >>> imu = MPU6050(i2c,
            ...               mode=MPU6050.Mode.DMP_STABLE,
            ...               coord='flu', remap='x-zy')
            >>> t0 = time.ticks_ms()
            >>> while time.ticks_diff(time.ticks_ms(), t0) < 30_000:
            ...     roll, pitch, yaw = imu.euler
            ...     time.sleep_ms(100)
            >>> imu.deinit()
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Deinitialize the sensor and enter sleep mode.

        Disables interrupts, FIFO, and DMP, then puts the device in low-power
        sleep mode.
        """
        ...

    @property
    def accel(self) -> tuple[float, float, float]:
        """
        Read acceleration values in the configured coord/remap frame.

        Values are converted to m/s^2 and bias-corrected. In DMP mode this
        property performs a fresh register read; async DMP streams use the DMP
        packet acceleration transformed with the same coord/remap rules.

        :return: Tuple of (ax, ay, az) in m/s^2.
        """
        ...

    @property
    def raw_accel(self) -> tuple[float, float, float]:
        """
        Read acceleration values in the IMU PCB frame.

        These values are converted to m/s^2 and bias-corrected, but coord and
        remap are not applied. Use this when inspecting the physical sensor axes
        directly.

        :return: Tuple of (ax, ay, az) in m/s^2 using the IMU PCB frame.
        """
        ...

    @property
    def gyro(self) -> tuple[float, float, float]:
        """
        Read angular velocity values in the configured coord/remap frame.

        Values are converted to rad/s and bias-corrected.

        :return: Tuple of (gx, gy, gz) in rad/s.
        """
        ...

    @property
    def raw_gyro(self) -> tuple[float, float, float]:
        """
        Read angular velocity values in the IMU PCB frame.

        These values are converted to rad/s and bias-corrected, but coord and
        remap are not applied.

        :return: Tuple of (gx, gy, gz) in rad/s using the IMU PCB frame.
        """
        ...

    @property
    def quat(self) -> tuple[float, float, float, float]:
        """
        Read quaternion orientation from DMP in the configured coord/remap frame.

        Returns identity quaternion (1, 0, 0, 0) if DMP is not enabled. In DMP
        mode, temporary FIFO overflow or packet gaps are recovered internally
        and the last valid quaternion is returned if no fresh packet is
        available after recovery. Implausible quaternion packets are ignored to
        avoid single-sample orientation jumps. During DMP startup, the driver
        measures accelerometer offset-register sensitivity on the current chip
        writes accelerometer/gyroscope hardware offsets, and measures residual
        gyro bias before enabling DMP.

        :return: Tuple of (w, x, y, z) normalized quaternion.
        """
        ...

    @property
    def tilt(self) -> tuple[float, float]:
        """
        Read two-axis tilt from the gravity vector.

        Returns roll and pitch tilt angles computed from acceleration after the
        configured coord/remap transform, using Right-Hand Rule (RHR) signs:
        - Roll: positive rotation about body +X, left side rises and right side lowers in FLU
        - Pitch: positive rotation about body +Y, front lowers in FLU

        In DMP mode, the frame-synchronized DMP packet acceleration is used with the
        DMP packet scale; in RAW mode, a fresh accelerometer register read is used.
        This output is suitable for tilt detection and small-angle control, but it
        is not a full 3D Euler orientation and it does not include yaw.

        Near-zero angles are normalized to 0.0 to avoid signed zero output.

        :return: Tuple of (roll, pitch) in radians adhering to the standard Right-Hand Rule.
        """
        ...

    @property
    def euler(self) -> tuple[float, float, float]:
        """
        Read DMP-derived Euler angles in radians.

        Roll and pitch are computed from the frame-synchronized DMP packet
        acceleration after coord/remap correction using Right-Hand Rule signs
        (positive roll about body +X, positive pitch about body +Y), so they are usable immediately after startup and are not 
        affected by the slow DMP quaternion gravity-axis convergence on rotated mounts.
        Yaw is reported as a relative heading from bias-corrected body-frame gyroscope
        integration with a small stationary deadband, and may drift because
        MPU6050 has no magnetometer. Call ``zero_heading()`` to reset the yaw
        reference.

        Returns (0.0, 0.0, 0.0) when DMP is not enabled.

        :return: Tuple of (roll, pitch, yaw) in radians.

        Example
        -------
        ```python
            >>> from i2c import I2CController
            >>> from mpu6050 import MPU6050

            >>> i2c = I2CController(sda=12, scl=13)
            >>> imu = MPU6050(i2c,
            ...               mode=MPU6050.Mode.DMP_STABLE,
            ...               coord='flu', remap='x-zy')
            >>> for _ in range(20):
            ...     roll, pitch, yaw = imu.euler
            ...     print(math.degrees(roll), math.degrees(pitch), math.degrees(yaw))
            ...     time.sleep_ms(100)
            >>> imu.zero_heading()
            >>> imu.deinit()
        ```
        """
        ...

    @property
    def linear(self) -> tuple[float, float, float]:
        """
        Read gravity-compensated linear acceleration from DMP.

        Uses the transformed quaternion orientation and DMP packet acceleration
        to remove gravity. Returns (0, 0, 0) if DMP is not enabled.

        :return: Tuple of (ax, ay, az) in m/s^2 in the configured world coord
            frame, with gravity removed.
        """
        ...

    def zero_heading(self) -> None:
        """
        Reset yaw reference to current heading.

        Sets the current transformed yaw angle as the zero reference point.
        Only effective when DMP is enabled.
        """
        ...
