"""
Async Servo Control module for MicroPython.

Provides async wrappers for Servo with non-blocking wait operations
that yield to other asyncio tasks during movement.
"""


from servo import Servo


class ServoAsync:
    """
    Async wrapper for Servo controller.
    
    Provides async methods for servo movement that yield
    to other tasks while waiting for motion to complete.

    Example
    -------
    ```python
        >>> from servo import Servo
        >>> from servo_async import ServoAsync
        >>> 
        >>> servo = Servo([15, 16])
        >>> aservo = ServoAsync(servo)
        >>> 
        >>> # Move and wait asynchronously
        >>> await aservo[0].move_to(90)
        >>> await aservo[1].move_to(45, ms=500)
    ```
    """
    
    def __init__(self, servo: Servo) -> None:
        """
        Initialize async servo wrapper.
        
        :param servo: Synchronous Servo object to wrap

        Example
        -------
        ```python
            >>> servo = Servo([15, 16])
            >>> aservo = ServoAsync(servo)
        ```
        """
        ...

    def __enter__(self) -> "ServoAsync":
        """Enter context manager."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - calls deinit()."""
        ...

    def __len__(self) -> int:
        """
        Return number of servo channels.
        
        :return: Total number of servos
        
        Example
        -------
        ```python
            >>> len(aservo)
            2
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "ServoAsyncView":
        """
        Access servo(s) by index or slice.
        
        :param idx: Channel index (0-based) or slice object
        
        :return: ServoAsyncView for controlling servo(s)

        Example
        -------
        ```python
            >>> aservo[0]      # Single servo
            >>> aservo[1:3]    # Servos 1-2
            >>> aservo[:]      # All servos
        ```
        """
        ...

    @property
    def device(self) -> Servo:
        """
        Access underlying synchronous Servo object.

        :return: The wrapped Servo instance

        Example
        -------
        ```python
            >>> aservo.device.deinit()
        ```
        """
        ...

    @property
    def servo(self) -> Servo:
        """
        Access underlying synchronous Servo object.
        
        Compatibility alias for ``device``.
        
        Example
        -------
        ```python
            >>> aservo.servo.deinit()
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Deinitialize servo controller and release resources.
        
        Example
        -------
        ```python
            >>> aservo.deinit()
        ```
        """
        ...


class ServoAsyncView:
    """
    Async wrapper for Servo._View.
    
    Provides async versions of blocking methods like wait(),
    and combined move + wait operations.
    """
    
    def __init__(self, view: object) -> None:
        """
        Initialize async view wrapper.
        
        :param view: Synchronous _View object to wrap
        """
        ...

    def __len__(self) -> int:
        """
        Return number of servos in this view.
        
        :return: Number of servos accessible through this view
        
        Example
        -------
        ```python
            >>> len(aservo[0:2])
            2
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "ServoAsyncView":
        """
        Create sub-view from current view.
        
        :param idx: Index or slice relative to current view
        
        :return: New AsyncServoView with selected servos
        
        Example
        -------
        ```python
            >>> aservo[:][0].angle = 90
        ```
        """
        ...

    # ===== Synchronous properties (pass-through) =====

    @property
    def angle(self) -> list[float]:
        """
        Get current angle(s) in degrees (positional mode).
        
        :return: List of current angles
        
        Example
        -------
        ```python
            >>> aservo[0].angle
            [90.0]
        ```
        """
        ...

    @angle.setter
    def angle(self, val: float | list[float]) -> None:
        """
        Set angle immediately without easing (positional mode).
        
        :param val: Angle or list of angles in degrees (0-180)
        
        :raises RuntimeError: If called in continuous mode
        
        Example
        -------
        ```python
            >>> aservo[0].angle = 90
        ```
        """
        ...

    @property
    def speed(self) -> list[float]:
        """
        Get current speed(s) as percentage (continuous mode).
        
        :return: List of current speeds (-100 to 100)
        
        Example
        -------
        ```python
            >>> aservo[0].speed
            [50.0]
        ```
        """
        ...

    @speed.setter
    def speed(self, val: float | list[float]) -> None:
        """
        Set speed (continuous mode).
        
        :param val: Speed or list of speeds as percentage (-100 to 100)
        
        :raises RuntimeError: If called in positional mode
        
        Example
        -------
        ```python
            >>> aservo[0].speed = 50
        ```
        """
        ...

    @property
    def duty_us(self) -> list[int]:
        """
        Get raw pulse width in microseconds.
        
        :return: List of pulse widths
        
        Example
        -------
        ```python
            >>> aservo[0].duty_us
            [1500]
        ```
        """
        ...

    @duty_us.setter
    def duty_us(self, val: int | list[int]) -> None:
        """
        Set raw pulse width in microseconds.
        
        :param val: Pulse width or list of pulse widths
        
        Example
        -------
        ```python
            >>> aservo[0].duty_us = 1500
        ```
        """
        ...

    @property
    def is_moving(self) -> list[bool]:
        """
        Check if servo(s) are currently moving.
        
        :return: List of boolean moving states
        
        Example
        -------
        ```python
            >>> aservo[0].is_moving
            [True]
        ```
        """
        ...

    @property
    def home_angle(self) -> list[float]:
        """
        Get home angle(s).
        
        :return: List of home angles
        
        Example
        -------
        ```python
            >>> aservo[0].home_angle
            [90.0]
        ```
        """
        ...

    @home_angle.setter
    def home_angle(self, val: float | list[float]) -> None:
        """
        Set home angle(s).
        
        :param val: Home angle or list of home angles
        
        Example
        -------
        ```python
            >>> aservo[0].home_angle = 45
        ```
        """
        ...

    @property
    def calibration(self) -> list[dict]:
        """
        Get calibration parameters.
        
        :return: List of calibration dicts with min_us, max_us, center_us
        
        Example
        -------
        ```python
            >>> aservo[0].calibration
            [{'min_us': 500, 'max_us': 2500}]
        ```
        """
        ...

    @calibration.setter
    def calibration(self, params: dict) -> None:
        """
        Set calibration parameters.
        
        :param params: Dict with min_us, max_us, and/or center_us
        
        Example
        -------
        ```python
            >>> aservo[0].calibration = {'min_us': 600, 'max_us': 2400}
        ```
        """
        ...

    def stop(self) -> None:
        """
        Stop all movement immediately.
        
        Example
        -------
        ```python
            >>> aservo[:].stop()
        ```
        """
        ...

    # ===== Async methods =====

    async def wait(self, timeout_ms: int = 10000) -> bool:
        """
        Wait for servo movement to complete asynchronously.
        
        Yields to other tasks while waiting for motion to finish.
        
        :param timeout_ms: Maximum wait time in milliseconds (default: 10000)
        
        :return: True if movement completed, False if timeout

        Example
        -------
        ```python
            >>> aservo[0].angle = 0  # Start position
            >>> aservo[0]._view.move_to(90, 1000)  # Start movement
            >>> await aservo[0].wait()  # Wait for completion
        ```
        """
        ...

    async def move_to(self, deg: float, ms: int | None = None, easing: str = 'linear', *, wait: bool = True, timeout_ms: int = 10000) -> bool:
        """
        Move servo to angle and optionally wait for completion.
        
        Starts the movement and yields to other tasks while waiting.
        
        :param deg: Target angle in degrees (0-180)
        :param ms: Duration of movement in milliseconds. If None, auto
            duration is based on angular travel.
        :param easing: Easing function - 'linear', 'quad', 'cubic' (default: 'linear')
        :param wait: If True, wait for movement to complete (default: True)
        :param timeout_ms: Maximum wait time in milliseconds (default: 10000)
        
        :return: True if movement completed (or started if wait=False), False if timeout
        
        :raises RuntimeError: If called in continuous mode

        Example
        -------
        ```python
            >>> # Move to 90° with automatic duration
            >>> await aservo[0].move_to(90)
            >>> 
            >>> # Move with easing
            >>> await aservo[0].move_to(180, ms=2000, easing='quad')
            >>> 
            >>> # Start movement without waiting
            >>> await aservo[0].move_to(45, wait=False)
            >>> # Do other work...
            >>> await aservo[0].wait()  # Wait later
        ```
        """
        ...

    async def home(self, ms: int | None = None, easing: str = 'quad', *, wait: bool = True, timeout_ms: int = 10000) -> bool:
        """
        Move servo to home position and optionally wait for completion.
        
        :param ms: Duration of movement in milliseconds. If None, auto
            duration is based on angular travel to home.
        :param easing: Easing function - 'linear', 'quad', 'cubic' (default: 'quad')
        :param wait: If True, wait for movement to complete (default: True)
        :param timeout_ms: Maximum wait time in milliseconds (default: 10000)
        
        :return: True if movement completed (or started if wait=False), False if timeout
        
        :raises RuntimeError: If called in continuous mode

        Example
        -------
        ```python
            >>> # Move all servos to home
            >>> await aservo[:].home(ms=1500)
        ```
        """
        ...

    async def sweep(self, start: float, end: float, ms: int | None = None, easing: str = 'linear', *, repeat: int = 1) -> None:
        """
        Sweep servo between two angles.
        
        :param start: Starting angle in degrees
        :param end: Ending angle in degrees
        :param ms: Duration for each direction in milliseconds. If None,
            auto duration is based on angular travel.
        :param easing: Easing function (default: 'linear')
        :param repeat: Number of complete cycles (default: 1). 0 = infinite

        Example
        -------
        ```python
            >>> # Sweep between 0° and 180° three times
            >>> await aservo[0].sweep(0, 180, ms=1000, repeat=3)
            >>> 
            >>> # Continuous sweep (cancel with task.cancel())
            >>> await aservo[0].sweep(45, 135, repeat=0)
        ```
        """
        ...

    async def sequence(self, positions: list[tuple[float, int | None]], easing: str = 'linear') -> None:
        """
        Execute a sequence of movements.
        
        :param positions: List of (angle, duration_ms) tuples
        :param easing: Easing function to use (default: 'linear')

        Example
        -------
        ```python
            >>> await aservo[0].sequence([
            ...     (0, 500),    # Move to 0° in 500ms
            ...     (90, 1000),  # Move to 90° in 1000ms
            ...     (180, 500),  # Move to 180° in 500ms
            ... ])
        ```
        """
        ...


AsyncServo = ServoAsync
AsyncServoView = ServoAsyncView
