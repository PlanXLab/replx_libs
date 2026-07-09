"""
AS5600 Magnetic Angle Encoder Driver

12-bit magnetic rotary position sensor with I2C interface.
Provides angle, velocity, and multi-turn tracking with filtering support.

Features:

- 12-bit resolution (4096 steps per revolution)
- Continuous angle measurement with EMA filtering
- Velocity calculation with low-pass and slew-rate limiting
- Multi-turn tracking with net/path accumulation
- Soft-zero calibration with persistence
- Magnet status monitoring (presence, field strength)
- Configurable hysteresis and filtering

"""

from typing import Tuple
from i2c import I2CController


def to_deg(rad: float) -> float:
    """
    Convert radians to degrees (0-360 range).
    
    :param rad: Angle in radians
    :return: Angle in degrees, wrapped to 0-360
    
    Example
    -------
    ```python
        >>> from as5600 import to_deg
        >>> to_deg(3.14159)  # ~180°
        180.0
    ```
    """
    ...


def to_deg_signed(rad: float) -> float:
    """
    Convert radians to signed degrees (-180 to +180 range).
    
    :param rad: Angle in radians
    :return: Angle in degrees, wrapped to -180 to +180
    
    Example
    -------
    ```python
        >>> from as5600 import to_deg_signed
        >>> to_deg_signed(3.5)  # ~200° -> -160°
        -159.3...
    ```
    """
    ...


class AS5600:
    """
    AS5600 magnetic rotary position sensor driver.
    
    High-resolution magnetic encoder using I2C interface.
    Provides angle, velocity, and multi-turn tracking with optional filtering.
    
    Example
    -------
    ```python
        >>> from i2c import I2CController
        >>> from as5600 import AS5600
        >>> 
        >>> i2c = I2CController(sda=4, scl=5)
        >>> # Basic usage
        >>> encoder = AS5600(i2c)
        >>> angle = encoder.angle()  # 0 to 2π radians
        >>> print(f"Angle: {angle:.3f} rad")
        >>> 
        >>> # With soft-zero calibration
        >>> encoder.set_soft_zero_now()
        >>> angle = encoder.angle()  # Now relative to zero position
        >>> 
        >>> # Velocity tracking
        >>> while True:
        ...     vel = encoder.velocity(filtered=True)
        ...     print(f"Velocity: {vel:.2f} rad/s")
    ```
    """
    
    # Class constants
    VELOCITY_UNIT_RAD_S_TO_RPM: float
    VELOCITY_UNIT_RAD_S_TO_RPS: float
    
    STATUS_NORMAL: int
    STATUS_NO_MAGNET: int
    STATUS_WEAK_MAGNET: int
    STATUS_STRONG_MAGNET: int
    STATUS_FIELD_RANGE: int
    
    CALIB_SOFT_ZERO_MODE_FIXED: int
    CALIB_SOFT_ZERO_MODE_ADAPTIVE: int
    
    DEFAULT_CAL_FILE: str

    def __init__(
        self,
        i2c: I2CController,
        *,
        addr: int = 0x36,
        ema_alpha: float = 0.25,
        vel_tau_s: float = 0.02,
        vel_slew_rise: float = 1e9,
        vel_slew_fall: float = 1e9,
        cal_file: str | None = None,
        apply_conf: bool = True,
        hysteresis: int = 1,
        slow_filter: int = 3,
        fast_filter_threshold: int = 4,
        watchdog: int = 0,
        cache_window_us: int = 500
    ) -> None:
        """
        Initialize AS5600 encoder.
        
        :param i2c: Shared I2CController instance
        :param addr: I2C address (default: 0x36)
        :param ema_alpha: EMA filter alpha for angle (0-1, default: 0.25)
        :param vel_tau_s: Velocity low-pass filter time constant in seconds (default: 0.02)
        :param vel_slew_rise: Velocity slew rate limit for rising (default: 1e9, no limit)
        :param vel_slew_fall: Velocity slew rate limit for falling (default: 1e9, no limit)
        :param cal_file: Calibration file path (default: "lib/ticle/as5600_zero.cal")
        :param apply_conf: Apply sensor configuration on init (default: True)
        :param hysteresis: Hysteresis setting 0-3 (default: 1)
        :param slow_filter: Slow filter setting 0-3 (default: 3)
        :param fast_filter_threshold: Fast filter threshold 0-6 (default: 4)
        :param watchdog: Enable watchdog 0/1 (default: 0)
        :param cache_window_us: Sample cache window in microseconds (default: 500)
        
        Example
        -------
        ```python
            >>> from i2c import I2CController
            >>> from as5600 import AS5600
            >>> i2c = I2CController(sda=4, scl=5)
            >>> 
            >>> # Basic initialization
            >>> encoder = AS5600(i2c)
            >>> 
            >>> # With custom filtering
            >>> encoder = AS5600(i2c, ema_alpha=0.1, vel_tau_s=0.05)
            >>> 
            >>> # With custom I2C address
            >>> encoder = AS5600(i2c, addr=0x36)
        ```
        """
        ...

    def reset_cache(self) -> None:
        """
        Clear the sample cache.
        
        Forces next read to fetch fresh data from sensor.
        """
        ...

    def status(self) -> int:
        """
        Get magnet status.
        
        :return: Status code:
            - STATUS_NORMAL (0): Magnet detected, field OK
            - STATUS_NO_MAGNET (1): No magnet detected
            - STATUS_WEAK_MAGNET (2): Magnet too weak
            - STATUS_STRONG_MAGNET (3): Magnet too strong
            - STATUS_FIELD_RANGE (4): Field out of range
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> status = encoder.status()
            >>> if status == AS5600.STATUS_NORMAL:
            ...     print("Magnet OK")
            >>> elif status == AS5600.STATUS_NO_MAGNET:
            ...     print("No magnet detected!")
        ```
        """
        ...

    def health_ok(self) -> bool:
        """
        Check if magnet status is normal.
        
        :return: True if status is STATUS_NORMAL
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> if encoder.health_ok():
            ...     angle = encoder.angle()
        ```
        """
        ...

    def set_conf(
        self,
        *,
        hysteresis: int = 1,
        slow_filter: int = 3,
        fast_filter_threshold: int = 4,
        watchdog: int = 0
    ) -> None:
        """
        Configure sensor hardware settings.
        
        :param hysteresis: Hysteresis setting 0-3
        :param slow_filter: Slow filter setting 0-3
        :param fast_filter_threshold: Fast filter threshold 0-6
        :param watchdog: Enable watchdog 0/1
        
        :raises ValueError: If parameters out of range
        """
        ...

    def agc(self) -> int:
        """
        Get AGC (Automatic Gain Control) value.
        
        :return: AGC value 0-255, indicates signal strength
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> agc = encoder.agc()
            >>> print(f"AGC: {agc}")  # ~128 is optimal
        ```
        """
        ...

    def magnitude(self) -> int:
        """
        Get magnetic field magnitude.
        
        :return: Magnitude value 0-4095
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> mag = encoder.magnitude()
            >>> print(f"Magnitude: {mag}")
        ```
        """
        ...

    def set_soft_zero_now(self) -> None:
        """
        Set current position as soft zero.
        
        Immediate zero calibration without motion detection.
        Does not save to file.
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> # Manually position to zero
            >>> encoder.set_soft_zero_now()
            >>> print(encoder.angle())  # Should be ~0
        ```
        """
        ...

    def calibrate_soft_zero(
        self,
        *,
        samples: int = 64,
        still_samples: int = 20,
        still_timeout_ms: int = 4000,
        still_thresh_lsb: int = 1,
        still_mode: int = 0,
        still_window: int = 16,
        still_k: float = 3.0,
        still_warmup: int = 8,
        verbose: bool = False,
        save_path: str | None = None
    ) -> bool:
        """
        Calibrate soft zero with motion detection.
        
        Waits for encoder to be still, then averages readings for calibration.
        Optionally saves to file for persistence.
        
        :param samples: Number of samples to average (default: 64)
        :param still_samples: Consecutive still samples required (default: 20)
        :param still_timeout_ms: Timeout waiting for stillness (default: 4000)
        :param still_thresh_lsb: Stillness threshold in LSB (default: 1)
        :param still_mode: CALIB_SOFT_ZERO_MODE_FIXED or ADAPTIVE (default: FIXED)
        :param still_window: Window size for adaptive mode (default: 16)
        :param still_k: Adaptive threshold multiplier (default: 3.0)
        :param still_warmup: Warmup samples for adaptive mode (default: 8)
        :param verbose: Print debug info (default: False)
        :param save_path: File path to save calibration (default: cal_file)
        :return: True if calibration file saved successfully
        
        :raises RuntimeError: If stillness timeout occurs
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> # Hold encoder still at zero position
            >>> success = encoder.calibrate_soft_zero(verbose=True)
            >>> if success:
            ...     print("Calibration saved!")
        ```
        """
        ...

    def angle(self, *, soft_zero: bool = True, filtered: bool = False) -> float:
        """
        Get current angle in radians.
        
        :param soft_zero: Apply soft zero offset (default: True)
        :param filtered: Apply EMA filter (default: False)
        :return: Angle in radians (0 to 2π)
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> 
            >>> # Raw angle
            >>> raw = encoder.angle(soft_zero=False)
            >>> 
            >>> # Calibrated angle
            >>> cal = encoder.angle()
            >>> 
            >>> # Filtered angle (smoother)
            >>> smooth = encoder.angle(filtered=True)
        ```
        """
        ...

    def angle_deg(self, *, soft_zero: bool = True, filtered: bool = False) -> float:
        """
        Get current angle in degrees.
        
        Convenience method that returns angle in degrees (0-360).
        
        :param soft_zero: Apply soft zero offset (default: True)
        :param filtered: Apply EMA filter (default: False)
        :return: Angle in degrees (0 to 360)
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> deg = encoder.angle_deg()
            >>> print(f"Angle: {deg:.1f}°")
        ```
        """
        ...

    def velocity_rpm(self, *, filtered: bool = False) -> float:
        """
        Get angular velocity in RPM.
        
        Convenience method that returns velocity in revolutions per minute.
        
        :param filtered: Apply low-pass and slew filters (default: False)
        :return: Angular velocity in RPM (positive=CCW)
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> rpm = encoder.velocity_rpm(filtered=True)
            >>> print(f"Speed: {rpm:.1f} RPM")
        ```
        """
        ...

    def velocity(
        self,
        *,
        filtered: bool = False,
        tick_emit: int = 4,
        tick_hold: int = 2,
        dt_min_s: float = 0.003,
        dt_max_s: float = 0.5,
        omega_clip: float | None = None
    ) -> float:
        """
        Get angular velocity in radians per second.
        
        :param filtered: Apply low-pass and slew filters (default: False)
        :param tick_emit: Minimum ticks to emit velocity (default: 4)
        :param tick_hold: Dead zone threshold in ticks (default: 2)
        :param dt_min_s: Minimum time delta in seconds (default: 0.003)
        :param dt_max_s: Maximum time delta before zero (default: 0.5)
        :param omega_clip: Optional velocity clipping limit (default: None)
        :return: Angular velocity in rad/s (positive=CCW)
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> 
            >>> while True:
            ...     vel = encoder.velocity(filtered=True)
            ...     rpm = vel * AS5600.VELOCITY_UNIT_RAD_S_TO_RPM
            ...     print(f"Speed: {rpm:.1f} RPM")
        ```
        """
        ...

    def reset_velocity(self) -> None:
        """
        Reset velocity tracking state.
        
        Clears internal state for velocity calculation.
        Call this when starting a new velocity measurement session.
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> encoder.reset_velocity()
            >>> # Start fresh velocity tracking
        ```
        """
        ...

    def reset_turn(self) -> None:
        """
        Reset multi-turn tracking.
        
        Clears accumulated turn count and path length.
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> encoder.reset_turn()
            >>> # Start tracking from zero
        ```
        """
        ...

    def turn(
        self,
        *,
        soft_zero: bool = True,
        filtered: bool = False,
        tick_thr: int = 2,
        confirm_samples: int = 3
    ) -> Tuple[float, float]:
        """
        Get multi-turn tracking data.
        
        Returns accumulated net turns and total path traveled.
        
        :param soft_zero: Apply soft zero offset (default: True)
        :param filtered: Apply EMA filter (default: False)
        :param tick_thr: Tick threshold for turn detection (default: 2)
        :param confirm_samples: Consecutive samples to confirm direction (default: 3)
        :return: Tuple of (net_turns, path_turns)
            - net_turns: Net rotation in turns (negative=CW)
            - path_turns: Total distance traveled in turns
        
        Example
        -------
        ```python
            >>> i2c = I2CController(sda=4, scl=5)
            >>> encoder = AS5600(i2c)
            >>> encoder.reset_turn()
            >>> 
            >>> while True:
            ...     net, path = encoder.turn()
            ...     print(f"Net: {net:.2f} turns, Path: {path:.2f} turns")
        ```
        """
        ...
