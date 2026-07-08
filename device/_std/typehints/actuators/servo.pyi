"""
Dual-mode servo controller supporting positional and continuous rotation servos.

Two initialization styles are supported:

- ``Servo(pin)`` — single-servo mode: all control methods are available
  directly on the ``Servo`` instance (``s.home()``, ``s.angle = 90``, etc.).
- ``Servo([pin0, pin1, ...])`` — multi-servo mode: individual servos are
  accessed via index subscript (``s[0].home()``, ``s[:].angle = 90``, etc.).

Both forms support ``s.deinit()`` and ``len(s)``.

Features:
    - Positional mode: angle control with non-blocking smooth movement
    - Continuous mode: speed control (-100% to +100%)
    - Easing functions: linear, quad, cubic for smooth acceleration
    - Home position: configurable home angle with home() method
    - Per-servo calibration (pulse width tuning)
    - Timer-based smooth interpolation
    - Unified indexing/slicing API for multi-servo

Example
-------
```python
    >>> from servo import Servo

    >>> # Single-servo mode — direct method access
    >>> s = Servo(16, mode='positional', home_angle=90)
    >>> s.move_to(45)
    >>> s.wait()
    >>> s.home()
    >>> s.deinit()

    >>> # Multi-servo mode — index access
    >>> arm = Servo([16, 17], mode='positional', home_angle=90)
    >>> arm[0].move_to(45)
    >>> arm[0].wait()
    >>> arm[:].home()
    >>> arm.deinit()

    >>> # Continuous rotation
    >>> wheels = Servo([18, 19], mode='continuous')
    >>> wheels[:].speed = [60, -60]
    >>> wheels[:].stop()
    >>> wheels.deinit()
```
"""


class Servo:
    """
    Dual-mode servo controller.

    Pass a single ``int`` pin to enable single-servo mode, where all
    ``_View`` methods are accessible directly on the instance.  Pass a list
    or tuple of pins for multi-servo mode, where channels are accessed via
    ``[idx]`` subscript.

    :param pins: Single GPIO pin number **or** list/tuple of GPIO pin numbers.
    :param mode: ``'positional'`` for standard servos, ``'continuous'`` for
        360-degree servos.
    :param freq: PWM frequency in Hz (default: 50).
    :param min_us: Minimum pulse width in microseconds (0° or full reverse,
        default: 500).
    :param max_us: Maximum pulse width in microseconds (180° or full forward,
        default: 2500).
    :param center_us: Center pulse width for continuous mode stop point
        (default: 1500).
    :param home_angle: Home position in degrees for positional mode
        (default: 90.0).

    :raises ValueError: If pins are empty, mode is invalid, frequency is not
        positive, or pulse-width calibration values are inconsistent.

    Example
    -------
    ```python
        >>> from servo import Servo

        >>> # Single-servo: direct method access
        >>> s = Servo(16, mode='positional', home_angle=90)
        >>> s.move_to(45)
        >>> s.wait()
        >>> s.deinit()

        >>> # Multi-servo: index access
        >>> arm = Servo([16, 17], mode='positional', home_angle=45)
        >>> arm[0].move_to(90)
        >>> arm[:].home()
        >>> arm.deinit()
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
    ) -> None:
        """
        Initialize servo controller.

        :param pins: Single GPIO pin number or list/tuple of pin numbers.
        :param mode: ``'positional'`` or ``'continuous'``.
        :param freq: PWM frequency in Hz (default: 50).
        :param min_us: Minimum pulse width in microseconds (default: 500).
        :param max_us: Maximum pulse width in microseconds (default: 2500).
        :param center_us: Continuous-mode stop pulse width (default: 1500).
        :param home_angle: Default home angle in degrees (default: 90.0).

        :raises ValueError: On invalid arguments.

        Example
        -------
        ```python
            >>> s = Servo(16)                          # single, positional
            >>> s = Servo([16, 17], mode='continuous') # multi, continuous
        ```
        """
        ...

    def deinit(self) -> None:
        """
        Release PWM resources and stop timers.

        Always call this when done, regardless of single or multi-servo mode.

        Example
        -------
        ```python
            >>> s = Servo(16)
            >>> s.deinit()

            >>> arm = Servo([16, 17])
            >>> arm.deinit()
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return the total number of controlled servos.

        :return: Servo count.

        Example
        -------
        ```python
            >>> len(Servo(16))
            1
            >>> len(Servo([16, 17, 18]))
            3
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Access servo(s) by index or slice (multi-servo mode).

        :param idx: Channel index or slice.
        :return: ``_View`` for the selected channel(s).

        :raises IndexError: If index is out of range.

        Example
        -------
        ```python
            >>> arm = Servo([16, 17], mode='positional')
            >>> arm[0].angle = 90
            >>> arm[:].home()
            >>> arm.deinit()
        ```
        """
        ...

    @property
    def angle(self) -> list[float]:
        """
        Current angle(s) in degrees (positional mode, single-servo only).

        :return: List containing the current angle (0.0–180.0).
        :raises RuntimeError: If called in continuous mode.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16, mode='positional')
            >>> s.angle
            [90.0]
            >>> s.deinit()
        ```
        """
        ...

    @angle.setter
    def angle(self, value: float | list[float]) -> None:
        """
        Set angle immediately (positional mode, single-servo only).

        :param value: Target angle in degrees (0–180).
        :raises RuntimeError: If called in continuous mode.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16, mode='positional')
            >>> s.angle = 45
            >>> s.deinit()
        ```
        """
        ...

    def move_to(self, deg: float, ms: int | None = None, easing: str = 'linear') -> None:
        """
        Start smooth non-blocking movement (positional mode, single-servo only).

        :param deg: Target angle in degrees (0–180).
        :param ms: Duration in milliseconds (min 50). Auto if ``None``.
        :param easing: ``'linear'``, ``'quad'``, or ``'cubic'``.
        :raises RuntimeError: If called in continuous mode.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16, mode='positional')
            >>> s.move_to(120)
            >>> s.move_to(180, ms=2000, easing='quad')
            >>> s.wait()
            >>> s.deinit()
        ```
        """
        ...

    def home(self, ms: int | None = None, easing: str = 'quad') -> None:
        """
        Move to home position (positional mode, single-servo only).

        :param ms: Duration in milliseconds (min 50). Auto if ``None``.
        :param easing: ``'linear'``, ``'quad'`` (default), or ``'cubic'``.
        :raises RuntimeError: If called in continuous mode.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16, mode='positional', home_angle=90)
            >>> s.angle = 0
            >>> s.home()
            >>> s.wait()
            >>> s.deinit()
        ```
        """
        ...

    @property
    def home_angle(self) -> list[float]:
        """
        Home position angle(s) in degrees (single-servo only).

        :return: List containing the configured home angle.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16, home_angle=45)
            >>> s.home_angle
            [45.0]
            >>> s.deinit()
        ```
        """
        ...

    @home_angle.setter
    def home_angle(self, value: float | list[float]) -> None:
        """
        Set home position angle (single-servo only).

        :param value: Home angle in degrees (0–180).
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16)
            >>> s.home_angle = 45
            >>> s.home()
            >>> s.deinit()
        ```
        """
        ...

    @property
    def speed(self) -> list[float]:
        """
        Current speed as percentage (continuous mode, single-servo only).

        :return: List containing the current speed (−100.0 to +100.0).
        :raises RuntimeError: If called in positional mode.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(18, mode='continuous')
            >>> s.speed = 50
            >>> s.speed
            [50.0]
            >>> s.deinit()
        ```
        """
        ...

    @speed.setter
    def speed(self, value: float | list[float]) -> None:
        """
        Set rotation speed (continuous mode, single-servo only).

        :param value: Speed as percentage (−100 to +100, 0 = stop).
        :raises RuntimeError: If called in positional mode.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(18, mode='continuous')
            >>> s.speed = 75
            >>> s.stop()
            >>> s.deinit()
        ```
        """
        ...

    @property
    def duty_us(self) -> list[int]:
        """
        Raw PWM pulse width in microseconds (single-servo only).

        :return: List containing the current pulse width.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16)
            >>> s.duty_us
            [1500]
            >>> s.deinit()
        ```
        """
        ...

    @duty_us.setter
    def duty_us(self, value: int | list[int]) -> None:
        """
        Set raw PWM pulse width directly (single-servo only).

        :param value: Pulse width in microseconds.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16)
            >>> s.duty_us = 1800
            >>> s.deinit()
        ```
        """
        ...

    @property
    def is_moving(self) -> list[bool]:
        """
        Movement status flag (single-servo only).

        :return: List containing ``True`` while a ``move_to()`` is in progress.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16)
            >>> s.move_to(180, ms=2000)
            >>> s.is_moving
            [True]
            >>> s.wait()
            >>> s.deinit()
        ```
        """
        ...

    @property
    def calibration(self) -> list[dict]:
        """
        Pulse-width calibration dictionary (single-servo only).

        Positional: ``[{'min_us': int, 'max_us': int}]``.
        Continuous: ``[{'center_us': int, 'min_us': int, 'max_us': int}]``.

        :return: List containing calibration parameters.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16)
            >>> s.calibration
            [{'min_us': 500, 'max_us': 2500}]
            >>> s.deinit()
        ```
        """
        ...

    @calibration.setter
    def calibration(self, params: dict) -> None:
        """
        Set pulse-width calibration (single-servo only).

        :param params: Dict with any of ``'min_us'``, ``'max_us'``,
            ``'center_us'`` keys.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16)
            >>> s.calibration = {'min_us': 600, 'max_us': 2400}
            >>> s.deinit()
        ```
        """
        ...

    def wait(self, timeout_ms: int = 10000) -> bool:
        """
        Block until movement completes (single-servo only).

        :param timeout_ms: Maximum wait time in milliseconds (default: 10000).
        :return: ``True`` if movement finished, ``False`` on timeout.
        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(16)
            >>> s.move_to(180, ms=2000)
            >>> s.wait()
            >>> s.deinit()
        ```
        """
        ...

    def stop(self) -> None:
        """
        Stop immediately (single-servo only).

        Positional mode: cancel any ongoing ``move_to()`` and hold current
        position.  Continuous mode: set speed to zero.

        :raises AttributeError: If called on a multi-servo instance.

        Example
        -------
        ```python
            >>> s = Servo(18, mode='continuous')
            >>> s.speed = 60
            >>> s.stop()
            >>> s.deinit()
        ```
        """
        ...


class _View:
    """
    View for accessing and controlling one or more servo channels.

    Returned by ``Servo[idx]`` or ``Servo[slice]``.  Provides mode-appropriate
    properties and methods.  Using the wrong property for the current mode
    raises ``RuntimeError``.

    Example
    -------
    ```python
        >>> arm = Servo([16, 17], mode='positional')
        >>> arm[0].move_to(90)      # single channel
        >>> arm[:].home()           # all channels
        >>> arm.deinit()
    ```
    """

    def __len__(self) -> int:
        """
        Return the number of servos in this view.

        :return: Channel count.

        Example
        -------
        ```python
            >>> arm = Servo([16, 17, 18])
            >>> len(arm[0:2])
            2
            >>> arm.deinit()
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Create a sub-view from this view.

        :param idx: View-local index or slice.
        :return: Narrower ``_View``.

        Example
        -------
        ```python
            >>> arm = Servo([16, 17])
            >>> arm[:][0].angle = 90
            >>> arm.deinit()
        ```
        """
        ...

    @property
    def angle(self) -> list[float]:
        """
        Current angle(s) in degrees (positional mode only).

        :return: List of current angles (0.0–180.0).
        :raises RuntimeError: If called in continuous mode.

        Example
        -------
        ```python
            >>> arm = Servo([16, 17], mode='positional')
            >>> arm[0].angle
            [90.0]
            >>> arm.deinit()
        ```
        """
        ...

    @angle.setter
    def angle(self, value: float | list[float]) -> None:
        """
        Set angle(s) immediately (positional mode only).

        :param value: Target angle or list of angles in degrees (0–180).
        :raises RuntimeError: If called in continuous mode.

        Example
        -------
        ```python
            >>> arm = Servo([16, 17, 18], mode='positional')
            >>> arm[0].angle = 45
            >>> arm[:].angle = [0, 90, 180]
            >>> arm.deinit()
        ```
        """
        ...

    def move_to(self, deg: float, ms: int | None = None, easing: str = 'linear') -> None:
        """
        Start smooth non-blocking movement (positional mode only).

        :param deg: Target angle in degrees (0–180).
        :param ms: Duration in milliseconds (min 50). Auto if ``None``.
        :param easing: ``'linear'``, ``'quad'``, or ``'cubic'``.
        :raises RuntimeError: If called in continuous mode.

        Example
        -------
        ```python
            >>> arm = Servo([16], mode='positional')
            >>> arm[0].move_to(120)
            >>> arm[0].move_to(180, ms=2000, easing='quad')
            >>> arm[0].wait()
            >>> arm.deinit()
        ```
        """
        ...

    def home(self, ms: int | None = None, easing: str = 'quad') -> None:
        """
        Move to home position (positional mode only).

        :param ms: Duration in milliseconds (min 50). Auto if ``None``.
        :param easing: ``'linear'``, ``'quad'`` (default), or ``'cubic'``.
        :raises RuntimeError: If called in continuous mode.

        Example
        -------
        ```python
            >>> arm = Servo([16, 17], home_angle=45)
            >>> arm[:].angle = [0, 180]
            >>> arm[:].home()
            >>> arm[:].wait()
            >>> arm.deinit()
        ```
        """
        ...

    @property
    def home_angle(self) -> list[float]:
        """
        Home position angle(s) in degrees.

        :return: List of home angles (0.0–180.0).

        Example
        -------
        ```python
            >>> arm = Servo([16], home_angle=45)
            >>> arm[0].home_angle
            [45.0]
            >>> arm.deinit()
        ```
        """
        ...

    @home_angle.setter
    def home_angle(self, value: float | list[float]) -> None:
        """
        Set home position angle(s).

        :param value: Home angle or list of angles in degrees (0–180).

        Example
        -------
        ```python
            >>> arm = Servo([16, 17], mode='positional')
            >>> arm[0].home_angle = 45
            >>> arm[:].home_angle = [0, 180]
            >>> arm.deinit()
        ```
        """
        ...

    @property
    def speed(self) -> list[float]:
        """
        Current speed(s) as percentage (continuous mode only).

        :return: List of speeds (−100.0 to +100.0, 0 = stopped).
        :raises RuntimeError: If called in positional mode.

        Example
        -------
        ```python
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

        :param value: Speed as percentage (−100 to +100, 0 = stop).
        :raises RuntimeError: If called in positional mode.

        Example
        -------
        ```python
            >>> wheels = Servo([18, 19], mode='continuous')
            >>> wheels[:].speed = [60, -60]
            >>> wheels[:].stop()
            >>> wheels.deinit()
        ```
        """
        ...

    @property
    def duty_us(self) -> list[int]:
        """
        Raw PWM pulse width(s) in microseconds.

        :return: List of current pulse widths.

        Example
        -------
        ```python
            >>> arm = Servo([16], mode='positional')
            >>> arm[0].duty_us
            [1500]
            >>> arm.deinit()
        ```
        """
        ...

    @duty_us.setter
    def duty_us(self, value: int | list[int]) -> None:
        """
        Set raw PWM pulse width(s) directly.

        :param value: Pulse width or list of pulse widths in microseconds.

        Example
        -------
        ```python
            >>> arm = Servo([16], mode='positional')
            >>> arm[0].duty_us = 1800
            >>> arm.deinit()
        ```
        """
        ...

    @property
    def is_moving(self) -> list[bool]:
        """
        Movement status flag(s).

        :return: List of ``True`` for each servo currently executing
            a ``move_to()`` interpolation.

        Example
        -------
        ```python
            >>> arm = Servo([16], mode='positional')
            >>> arm[0].move_to(180, ms=2000)
            >>> arm[0].is_moving
            [True]
            >>> arm[0].stop()
            >>> arm.deinit()
        ```
        """
        ...

    @property
    def calibration(self) -> list[dict]:
        """
        Pulse-width calibration dictionary/dictionaries.

        Positional: ``[{'min_us': int, 'max_us': int}]``.
        Continuous: ``[{'center_us': int, 'min_us': int, 'max_us': int}]``.

        :return: List of calibration parameter dicts.

        Example
        -------
        ```python
            >>> arm = Servo([16], mode='positional')
            >>> arm[0].calibration
            [{'min_us': 500, 'max_us': 2500}]
            >>> arm.deinit()
        ```
        """
        ...

    @calibration.setter
    def calibration(self, params: dict) -> None:
        """
        Set pulse-width calibration for selected servos.

        :param params: Dict with any of ``'min_us'``, ``'max_us'``,
            ``'center_us'`` keys.

        Example
        -------
        ```python
            >>> arm = Servo([16], mode='positional')
            >>> arm[0].calibration = {'min_us': 600, 'max_us': 2400}
            >>> arm.deinit()
        ```
        """
        ...

    def wait(self, timeout_ms: int = 10000) -> bool:
        """
        Block until all selected servos finish their current movement.

        :param timeout_ms: Maximum wait time in milliseconds (default: 10000).
        :return: ``True`` if all movements finished; ``False`` on timeout.

        Example
        -------
        ```python
            >>> arm = Servo([16, 17], mode='positional')
            >>> arm[:].move_to(180, ms=2000)
            >>> arm[:].wait()
            >>> arm.deinit()
        ```
        """
        ...

    def stop(self) -> None:
        """
        Stop selected servos immediately.

        Positional: cancels any ongoing ``move_to()`` and holds current
        position.  Continuous: sets speed to zero (center pulse).

        Example
        -------
        ```python
            >>> wheels = Servo([18, 19], mode='continuous')
            >>> wheels[:].speed = 50
            >>> wheels[:].stop()
            >>> wheels.deinit()
        ```
        """
        ...
