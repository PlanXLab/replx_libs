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
    The MPU6050 chip/PCB frame is the fixed physical sensor frame: +X points
    right, +Y points upward on the chip, and +Z points upward from the chip
    surface when the chip is lying flat. ``remap`` first maps that PCB frame
    into the mounted local frame using a signed permutation. The mapping is
    written as output X, output Y, output Z.

    For a board mounted by rotating the chip/PCB 90 degrees counterclockwise
    around the +X axis, the mounted local frame is right/up/sky = +X/-Z/+Y,
    so ``remap='x-zy'`` means output X = PCB X, output Y = -PCB Z, and output
    Z = PCB Y.

    ``coord`` is applied after remap:
    - ``'raw'``: remap only
    - ``'enu'``: ENU world-style output, numerically the same base frame as raw
    - ``'flu'``: ROS robot body frame, converted as (x, y, z) -> (y, -x, z)
    - ``'ned'``: NED output converted from ENU as (x, y, z) -> (y, x, -z)

    ``remap`` must use x, y, and z exactly once and preserve a right-handed
    coordinate frame. DMP quaternion, tilt, linear acceleration, accel,
    and gyro all use the same transformed output frame. ``raw_accel`` and
    ``raw_gyro`` always return bias-corrected IMU PCB-frame values.

    Example
    -------
    ```python
        >>> import math
        >>> import time
        >>> from mpu6050 import MPU6050

        >>> imu = MPU6050(sda=12, scl=13,
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

        >>> raw = MPU6050(sda=12, scl=13, mode=MPU6050.Mode.RAW_FAST,
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
        sda: int,
        scl: int,
        *,
        addr: int = 0x68,
        mode: str = Mode.RAW_BALANCED,
        coord: str = 'raw',
        remap: str = 'xyz',
        freq: int = 400_000
    ) -> None:
        """
        Initialize the MPU6050 IMU.

        :param sda: I2C SDA pin number.
        :param scl: I2C SCL pin number.
        :param addr: I2C address (0x68 default, 0x69 if AD0 high).
        :param mode: Operating mode preset.
        :param coord: Output coordinate convention: 'raw', 'enu', 'flu', or 'ned'.
            'raw' applies only remap. 'enu' uses the same axis order as the
            remapped base frame as an ENU world-style frame. 'flu' converts
            the remapped ENU-style base frame to the ROS robot body frame
            (Forward-Left-Up) using (x, y, z) -> (y, -x, z). 'ned' converts
            the remapped ENU-style base frame to NED using (x, y, z) ->
            (y, x, -z).
        :param remap: Signed axis permutation from IMU PCB frame to the mounted
            base frame. It must use x, y, and z exactly once and must preserve
            a right-handed frame. Examples: 'xyz', 'x-zy', 'yx-z'.
        :param freq: I2C bus frequency in Hz. Default is 400000. Try 100000 if
            the sensor is visible in scans but register reads or writes fail.
        :raises RuntimeError: If I2C scan fails, the MPU6050 address is not
            found, the WHO_AM_I value is not valid, or DMP mode cannot locate
            responsive accelerometer offset registers.
        :raises ValueError: If mode, coord, or remap is invalid.

        Example
        -------
        ```python
            >>> import time
            >>> from mpu6050 import MPU6050
            >>> imu = MPU6050(sda=12, scl=13,
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

        Returns roll-like and pitch-like tilt angles computed from acceleration
        after the configured coord/remap transform. In DMP mode, the
        frame-synchronized DMP packet acceleration is used with the DMP packet
        scale; in RAW mode, a fresh accelerometer register read is used. This
        output is suitable for tilt
        detection and small-angle control, but it is not a full 3D Euler
        orientation and it does not include yaw.

        Near-zero angles are normalized to 0.0 to avoid signed zero output.

        :return: Tuple of (roll, pitch) in radians.
        """
        ...

    @property
    def euler(self) -> tuple[float, float, float]:
        """
        Read DMP-derived Euler angles in radians.

        Roll and pitch are computed from the frame-synchronized DMP packet
        acceleration after coord/remap correction, so they are usable
        immediately after startup and are not affected by the slow DMP
        quaternion gravity-axis convergence on rotated mounts. Yaw is reported
        as a relative heading from bias-corrected body-frame gyroscope
        integration with a small stationary deadband, and may drift because
        MPU6050 has no magnetometer. Call ``zero_heading()`` to reset the yaw
        reference.

        Returns (0.0, 0.0, 0.0) when DMP is not enabled.

        :return: Tuple of (roll, pitch, yaw) in radians.

        Example
        -------
        ```python
            >>> import math
            >>> import time
            >>> from mpu6050 import MPU6050

            >>> imu = MPU6050(sda=12, scl=13,
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
