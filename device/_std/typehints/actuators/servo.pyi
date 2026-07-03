"""
Dual-mode servo controller supporting positional and continuous rotation Servo.

This module provides unified control for both standard positional servos (0-180°)
and continuous rotation servos (360°) with a consistent API.

Features:
    - Positional mode: angle control with non-blocking smooth movement
    - Continuous mode: speed control (-100% to +100%)
    - Easing functions: linear, quad, cubic for smooth acceleration
    - Home position: configurable home angle with home() method
    - Per-servo calibration (pulse width tuning)
    - Timer-based smooth interpolation
    - Unified indexing/slicing API

Example
-------
```python
    >>> from servo import Servo
    >>> arm = Servo([16, 17], mode='positional', home_angle=90)
    >>> arm[0].move_to(45)
    >>> arm[0].wait()
    >>> arm.deinit()

    >>> wheels = Servo([18, 19], mode='continuous')
    >>> wheels[:].speed = [60, -60]
    >>> wheels[:].stop()
    >>> wheels.deinit()
```
"""



class Servo:
    """
    Dual-mode multi-channel servo controller.

    Supports both positional (0-180°) and continuous rotation (360°) servos
    through a unified API with mode selection at initialization.

    :param pins: GPIO pin numbers for servo signal lines
    :param mode: 'positional' for standard servos, 'continuous' for 360° Servo
    :param freq: PWM frequency in Hz (default 50Hz)
    :param min_us: Minimum pulse width in microseconds (0° or full reverse)
    :param max_us: Maximum pulse width in microseconds (180° or full forward)
    :param center_us: Center pulse width for continuous mode (stop point)
    :param home_angle: Home position angle for positional mode (default 90°)
    
    :raises ValueError: If pins are empty, mode is invalid, frequency is not
        positive, or pulse-width calibration values are inconsistent.
    
    Example
    -------
    ```python
        >>> from servo import Servo
        >>> arm = Servo([16, 17], mode='positional', home_angle=45)
        >>> wheels = Servo([18, 19], mode='continuous')
        >>> arm.deinit()
        >>> wheels.deinit()
    ```
    """

    MODE_POSITIONAL: str
    MODE_CONTINUOUS: str

    EASE_LINEAR: str
    EASE_QUAD: str
    EASE_CUBIC: str

    def __init__(
        self,
        pins: int | list[int] | tuple[int, ...],
        *,
        mode: str = 'positional',
        freq: int = 50,
        min_us: int = 500,
        max_us: int = 2500,
        center_us: int = 1500,
        home_angle: float = 90.0
    ) -> None: ...

    def deinit(self) -> None:
        """
        Release PWM resources and stop timers.

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16])
            >>> srv.deinit()
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return number of controlled servos.
        
        :return: Total number of servos
        
        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16, 17, 18])
            >>> len(srv)
            3
            >>> srv.deinit()
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Access servo(s) by index or slice.

        :param idx: Single index or slice.
        :return: _View for controlling selected servo(s).

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> arm = Servo([16, 17], mode='positional')
            >>> arm[0].angle = 90       # Single servo
            >>> arm[:].home()           # All positional servos
            >>> arm.deinit()

            >>> wheels = Servo([18, 19], mode='continuous')
            >>> wheels[:].speed = 50    # Range
            >>> wheels[:].stop()        # All continuous servos
            >>> wheels.deinit()
        ```
        """
        ...


class _View:
    """
    View for accessing and controlling selected servo(s).

    Provides mode-appropriate properties and methods. Using wrong
    property for the mode raises RuntimeError.
    """

    def __len__(self) -> int:
        """
        Return number of servos in view.
        
        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16, 17, 18])
            >>> len(srv[0:2])
            2
            >>> srv.deinit()
        ```
        """
        ...
    
    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Create sub-view from current view.
        
        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16, 17])
            >>> srv[:][0].angle = 90
            >>> srv.deinit()
        ```
        """
        ...

    @property
    def angle(self) -> list[float]:
        """
        Current angle(s) in degrees (positional mode only).

        :return: List of angles (0.0-180.0)
        
        :raises RuntimeError: If called in continuous mode

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].angle
            [90.0]
            >>> srv.deinit()
        ```
        """
        ...

    @angle.setter
    def angle(self, value: float | list[float]) -> None:
        """
        Set angle immediately (positional mode only).

        For smooth movement, use `move_to()` instead.

        :param value: Target angle(s) in degrees (0-180)
        
        :raises RuntimeError: If called in continuous mode

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16, 17, 18], mode='positional')
            >>> srv[0].angle = 45
            >>> srv[:].angle = [0, 90, 180]
            >>> srv.deinit()
        ```
        """
        ...

    def move_to(self, deg: float, ms: int | None = None, easing: str = 'linear') -> None:
        """
        Start smooth non-blocking movement (positional mode only).

        The servo interpolates from current to target angle over
        the specified duration with optional easing. If ``ms`` is omitted,
        duration is calculated from angular travel so short feedback-loop
        movements respond quickly. Use `wait()` to block.

        :param deg: Target angle in degrees (0-180)
        :param ms: Movement duration in milliseconds (min 50). If None,
            auto duration is based on angular travel.
        :param easing: Easing function - 'linear', 'quad', or 'cubic'
        
        :raises RuntimeError: If called in continuous mode

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].move_to(120)                       # Auto duration
            >>> srv[0].move_to(180, ms=2000)              # Explicit duration
            >>> srv[0].move_to(180, ms=2000, easing='quad')   # Smooth
            >>> srv[0].wait()
            >>> srv.deinit()
        ```
        """
        ...

    def home(self, ms: int | None = None, easing: str = 'quad') -> None:
        """
        Move to home position (positional mode only).

        Returns servo(s) to their configured home angle with easing.
        Home angle defaults to 90° and can be set per-servo.

        :param ms: Movement duration in milliseconds (min 50). If None,
            auto duration is based on angular travel to home.
        :param easing: Easing function - 'linear', 'quad' (default), or 'cubic'
        
        :raises RuntimeError: If called in continuous mode

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> arm = Servo([16, 17], home_angle=45)
            >>> arm[:].angle = [0, 180]           # Move away
            >>> arm[:].home()                     # Auto duration
            >>> arm[:].home(ms=1500)              # Explicit duration
            >>> arm[:].wait()
            >>> 
            >>> arm[0].home_angle = 90            # Change home for servo 0
            >>> arm[0].home()                     # Servo 0 goes to 90°
            >>> arm.deinit()
        ```
        """
        ...

    @property
    def home_angle(self) -> list[float]:
        """
        Home position angle(s) in degrees.

        :return: List of home angles (0.0-180.0)

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].home_angle
            [90.0]
            >>> srv.deinit()
        ```
        """
        ...

    @home_angle.setter
    def home_angle(self, value: float | list[float]) -> None:
        """
        Set home position angle(s).

        :param value: Home angle(s) in degrees (0-180)

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16, 17, 18], mode='positional')
            >>> srv[0].home_angle = 45
            >>> srv[:].home_angle = [0, 90, 180]
            >>> srv.deinit()
        ```
        """
        ...

    @property
    def speed(self) -> list[float]:
        """
        Current speed(s) as percentage (continuous mode only).

        :return: List of speeds (-100.0 to +100.0, 0 = stopped)
        
        :raises RuntimeError: If called in positional mode

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> wheels = Servo([18, 19], mode='continuous')
            >>> wheels[0].speed = 50
            >>> wheels[0].speed
            [50.0]
            >>> wheels.deinit()
        ```
        """
        ...

    @speed.setter
    def speed(self, value: float | list[float]) -> None:
        """
        Set rotation speed (continuous mode only).

        :param value: Speed as percentage (-100 to +100, 0 = stop)
        
        :raises RuntimeError: If called in positional mode

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> wheels = Servo([18, 19], mode='continuous')
            >>> wheels[:].speed = 50         # All forward 50%
            >>> wheels[0].speed = -30        # First reverse 30%
            >>> wheels[:].speed = 0          # All stop
            >>> wheels.deinit()
        ```
        """
        ...

    @property
    def duty_us(self) -> list[int]:
        """
        Raw PWM pulse width in microseconds.

        For advanced users who need direct PWM control.

        :return: List of pulse widths in microseconds

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].duty_us
            [1500]
            >>> srv.deinit()
        ```
        """
        ...

    @duty_us.setter
    def duty_us(self, value: int | list[int]) -> None:
        """
        Set raw PWM pulse width directly.

        Bypasses angle/speed conversion for advanced control.

        :param value: Pulse width in microseconds

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].duty_us = 1500  # Direct PWM control
            >>> srv.deinit()
        ```
        """
        ...

    @property
    def is_moving(self) -> list[bool]:
        """
        Check if servo(s) are in non-blocking movement.

        Only meaningful in positional mode with `move_to()`.

        :return: List of movement status flags

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].move_to(180, ms=2000)
            >>> srv[0].is_moving
            [True]
            >>> srv[0].stop()
            >>> srv.deinit()
        ```
        """
        ...

    @property
    def calibration(self) -> list[dict]:
        """
        Get pulse width calibration.

        :return: Positional mode: [{'min_us': int, 'max_us': int}, ...], Continuous mode: [{'center_us': int, 'min_us': int, 'max_us': int}, ...]

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].calibration
            [{'min_us': 500, 'max_us': 2500}]
            >>> srv.deinit()
        ```
        """
        ...

    @calibration.setter
    def calibration(self, params: dict) -> None:
        """
        Set pulse width calibration.

        :param params: Dict with 'min_us', 'max_us', and/or 'center_us' (continuous mode)

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> # Positional servo calibration
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].calibration = {'min_us': 600, 'max_us': 2400}
            >>> srv.deinit()
            >>> 
            >>> # Continuous servo - adjust stop point
            >>> wheels = Servo([18], mode='continuous')
            >>> wheels[0].calibration = {'center_us': 1520}
            >>> wheels.deinit()
        ```
        """
        ...

    def wait(self, timeout_ms: int = 10000) -> bool:
        """
        Block until movement completes (positional mode).

        :param timeout_ms: Maximum wait time in milliseconds
        
        :return: True if completed, False if timeout

        Example
        -------
        ```python
            >>> from servo import Servo
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].move_to(180, ms=2000)
            >>> if not srv[0].wait(5000):
            ...     print("Timeout!")
            >>> srv.deinit()
        ```
        """
        ...

    def stop(self) -> None:
        """
        Stop servo(s) immediately.

        Positional mode: Cancels ongoing move_to(), stays at current position.
        Continuous mode: Sets speed to 0 (stops rotation).

        Example
        -------
        ```python
            >>> import time
            >>> from servo import Servo
            >>> srv = Servo([16], mode='positional')
            >>> srv[0].move_to(180, ms=5000)
            >>> time.sleep_ms(1000)
            >>> srv[0].stop()  # Stop mid-movement
            >>> srv.deinit()
            >>> 
            >>> wheels = Servo([18, 19], mode='continuous')
            >>> wheels[:].speed = 100
            >>> wheels[:].stop()  # Emergency stop
            >>> wheels.deinit()
        ```
        """
        ...
