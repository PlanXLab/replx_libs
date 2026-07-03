"""
Digital GPIO Driver.

Provides digital input, digital output, and bidirectional GPIO helpers with
scalar methods and reusable multi-pin views.

Example
-------
```python
    >>> from dio import Din, Dout
    >>> btn = Din(17, pull=Din.PULL_DOWN)
    >>> led = Dout(25)
    >>> led.write(btn.read())
    >>> btn.deinit(); led.deinit()
```
"""

from typing import Callable

LOW: int
"""Logical low constant."""
HIGH: int
"""Logical high constant."""

class Din:
    """Digital input pins.

    Example
    -------
    ```python
        >>> sw = Din([17, 19], pull=Din.PULL_DOWN)
        >>> sw[:].value
    ```
    """
    PULL_DOWN: int
    PULL_UP: int
    OPEN_DRAIN: int
    CB_FALLING: int
    CB_RISING: int
    CB_BOTH: int

    def __init__(self, pins: int | list[int] | tuple[int, ...], *, pull: int | None = None) -> None:
        """Initialize input pin(s).

        :param pins: GPIO pin number or sequence.
        :param pull: Pull resistor mode.
        
        Example
        -------
        ```python
            >>> sw = Din(17, pull=Din.PULL_DOWN)
        ```
        """
        ...

    def __enter__(self) -> "Din":
        """Enter context manager.

        :return: Self.
        
        Example
        -------
        ```python
            >>> with Din(17) as sw:
            ...     sw.read()
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and release IRQ handlers.

        Example
        -------
        ```python
            >>> with Din(17) as sw:
            ...     pass
        ```
        """
        ...

    def __len__(self) -> int:
        """Return input pin count.

        :return: Number of pins.
        
        Example
        -------
        ```python
            >>> len(Din([17, 19]))
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "Din._View":
        """Get reusable view for input pin(s).

        :param idx: Pin index or slice.
        :return: Input view.
        :raises IndexError: If index is out of range.
        
        Example
        -------
        ```python
            >>> sw = Din([17, 19])
            >>> sw[0].value
            >>> sw[:].pull = Din.PULL_UP
        ```
        """
        ...

    @property
    def pins(self):
        """Get underlying machine.Pin objects.

        :return: Pin object list.
        
        Example
        -------
        ```python
            >>> sw.pins[0]
        ```
        """
        ...

    def deinit(self) -> None:
        """Disable IRQ handlers.

        Example
        -------
        ```python
            >>> sw.deinit()
        ```
        """
        ...

    def read(self, idx: int = 0) -> int:
        """Read one input pin.

        :param idx: Pin index.
        :return: 0 or 1.
        
        Example
        -------
        ```python
            >>> sw.read()
        ```
        """
        ...

    def read_into(self, buf):
        """Read all input pins into an existing buffer.

        :param buf: Mutable buffer.
        :return: The same buffer.
        
        Example
        -------
        ```python
            >>> buf = [0, 0]
            >>> sw.read_into(buf)
        ```
        """
        ...

    def set_pull(self, idx: int, pull: int | None) -> None:
        """Set pull mode for one pin.

        :param idx: Pin index.
        :param pull: Pull mode or None.
        
        Example
        -------
        ```python
            >>> sw.set_pull(0, Din.PULL_UP)
        ```
        """
        ...

    def set_pull_all(self, pull: int | None) -> None:
        """Set pull mode for all pins.

        :param pull: Pull mode or None.
        
        Example
        -------
        ```python
            >>> sw.set_pull_all(Din.PULL_DOWN)
        ```
        """
        ...

    def set_debounce_us(self, idx: int, us: int) -> None:
        """Set IRQ debounce for one pin.

        :param idx: Pin index.
        :param us: Debounce time in microseconds.
        
        Example
        -------
        ```python
            >>> sw.set_debounce_us(0, 50000)
        ```
        """
        ...

    def set_debounce_all(self, us: int) -> None:
        """Set IRQ debounce for all pins.

        :param us: Debounce time in microseconds.
        
        Example
        -------
        ```python
            >>> sw.set_debounce_all(50000)
        ```
        """
        ...

    def irq(self, idx: int, callback: Callable[[int, int], None] | None = None, *, trigger: int = ..., debounce_us: int = 0, hard: bool = True) -> None:
        """Register an IRQ callback for one pin.

        :param idx: Pin index.
        :param callback: Function receiving (pin_number, value).
        :param trigger: IRQ trigger mask.
        :param debounce_us: Debounce time.
        :param hard: Request hard IRQ when supported.
        
        Example
        -------
        ```python
            >>> sw.irq(0, lambda pin, value: print(pin, value), trigger=Din.CB_RISING)
        ```
        """
        ...

    def measure_pulse_width(self, idx: int = 0, level: int = 1, timeout_us: int = 1000000) -> int:
        """Measure pulse width with machine.time_pulse_us.

        :param idx: Pin index.
        :param level: Pulse level to measure.
        :param timeout_us: Timeout in microseconds.
        :return: Pulse width or platform error code.
        
        Example
        -------
        ```python
            >>> width = echo.measure_pulse_width(level=1)
        ```
        """
        ...

    def start_pulse_capture(self, idx: int = 0, level: int = 1) -> None:
        """Start IRQ-based pulse capture.

        :param idx: Pin index.
        :param level: Active pulse level.
        
        Example
        -------
        ```python
            >>> echo.start_pulse_capture(level=1)
        ```
        """
        ...

    def stop_pulse_capture(self, idx: int = 0) -> None:
        """Stop pulse capture IRQ.

        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> echo.stop_pulse_capture()
        ```
        """
        ...

    def pulse_ready(self, idx: int = 0) -> bool:
        """Return whether a captured pulse is ready.

        :param idx: Pin index.
        :return: True when pulse width is available.
        
        Example
        -------
        ```python
            >>> if echo.pulse_ready(): print(echo.pulse_width_us())
        ```
        """
        ...

    def pulse_width_us(self, idx: int = 0) -> int:
        """Return captured pulse width.

        :param idx: Pin index.
        :return: Width in microseconds, or -1 if not ready.
        
        Example
        -------
        ```python
            >>> width = echo.pulse_width_us()
        ```
        """
        ...

    def wait_pulse_ready(self, idx: int = 0, timeout_ms: int = 50) -> bool:
        """Wait until pulse capture is ready.

        :param idx: Pin index.
        :param timeout_ms: Timeout in milliseconds.
        :return: True if ready, False on timeout.
        
        Example
        -------
        ```python
            >>> echo.wait_pulse_ready(0, 50)
        ```
        """
        ...

    def wait_for_value(self, idx: int = 0, target: int = 1, timeout_ms: int = 0) -> bool:
        """Wait for a pin to reach a value.

        :param idx: Pin index.
        :param target: Target value.
        :param timeout_ms: Timeout, or 0 for no timeout.
        :return: True if reached, False on timeout.
        
        Example
        -------
        ```python
            >>> sw.wait_for_value(target=1, timeout_ms=1000)
        ```
        """
        ...

    def wait_for_edge(self, idx: int = 0, edge: int = ..., timeout_ms: int = 0) -> bool:
        """Wait for a pin edge.

        :param idx: Pin index.
        :param edge: Edge mask.
        :param timeout_ms: Timeout, or 0 for no timeout.
        :return: True if edge occurs, False on timeout.
        
        Example
        -------
        ```python
            >>> sw.wait_for_edge(edge=Din.CB_RISING, timeout_ms=1000)
        ```
        """
        ...

    class _View:
        """Reusable input view.

        Example
        -------
        ```python
            >>> values = sw[:].value
        ```
        """
        __slots__ = ("_p", "_i", "_cache")
        def __len__(self) -> int:
            """Return view pin count.

            :return: Number of pins in view.
            
            Example
            -------
            ```python
                >>> len(sw[:])
            ```
            """
            ...

        def __getitem__(self, idx: int | slice) -> "Din._View":
            """Narrow input view.

            :param idx: View-relative index or slice.
            :return: Narrowed view.
            
            Example
            -------
            ```python
                >>> sw[:][0].value
            ```
            """
            ...

        def read(self) -> int:
            """Read a single-pin view.

            :return: Pin value.
            
            Example
            -------
            ```python
                >>> sw[0].read()
            ```
            """
            ...

        def read_into(self, buf):
            """Read view pins into a buffer.

            :param buf: Mutable buffer.
            :return: The same buffer.
            
            Example
            -------
            ```python
                >>> sw[:].read_into([0, 0])
            ```
            """
            ...

        @property
        def value(self) -> list[int]:
            """Get view values as a reused list.

            :return: Reused list of 0/1 values.
            
            Example
            -------
            ```python
                >>> values = sw[:].value.copy()
            ```
            """
            ...

        @property
        def pull(self) -> list[int | None]:
            """Get pull modes.

            :return: Reused list of pull modes.
            
            Example
            -------
            ```python
                >>> pulls = sw[:].pull.copy()
            ```
            """
            ...

        @pull.setter
        def pull(self, value: int | None) -> None:
            """Set pull mode for view pins.

            :param value: Pull mode or None.
            
            Example
            -------
            ```python
                >>> sw[:].pull = Din.PULL_UP
            ```
            """
            ...

        @property
        def debounce_us(self) -> list[int]:
            """Get debounce settings.

            :return: Reused list of debounce times.
            
            Example
            -------
            ```python
                >>> sw[:].debounce_us
            ```
            """
            ...

        @debounce_us.setter
        def debounce_us(self, us: int) -> None:
            """Set debounce for view pins.

            :param us: Debounce time in microseconds.
            
            Example
            -------
            ```python
                >>> sw[:].debounce_us = 50000
            ```
            """
            ...

        @property
        def callback(self) -> list[Callable[[int, int], None] | None]:
            """Get IRQ callbacks.

            :return: Reused list of callbacks.
            
            Example
            -------
            ```python
                >>> callbacks = sw[:].callback.copy()
            ```
            """
            ...

        @callback.setter
        def callback(self, fn: Callable[[int, int], None] | None) -> None:
            """Set callback for view pins.

            :param fn: Callback receiving (pin_number, value), or None.
            
            Example
            -------
            ```python
                >>> sw[:].callback = lambda pin, value: print(pin, value)
            ```
            """
            ...

        def set_pull(self, pull: int | None) -> None:
            """Set pull mode for view pins.

            :param pull: Pull mode or None.
            
            Example
            -------
            ```python
                >>> sw[:].set_pull(Din.PULL_DOWN)
            ```
            """
            ...

        def set_debounce_us(self, us: int) -> None:
            """Set debounce for view pins.

            :param us: Debounce time in microseconds.
            
            Example
            -------
            ```python
                >>> sw[:].set_debounce_us(50000)
            ```
            """
            ...

        def irq(self, callback: Callable[[int, int], None] | None = None, *, trigger: int | None = None, debounce_us: int = 0, hard: bool = True) -> None:
            """Register IRQ for view pins.

            :param callback: Callback receiving (pin_number, value).
            :param trigger: Edge trigger mask.
            
            Example
            -------
            ```python
                >>> sw[:].irq(lambda pin, value: print(pin, value))
            ```
            """
            ...

        def start_pulse_capture(self, level: int = 1) -> None:
            """Start pulse capture for a single-pin view.

            :param level: Active pulse level.
            
            Example
            -------
            ```python
                >>> echo[0].start_pulse_capture()
            ```
            """
            ...

        def stop_pulse_capture(self) -> None:
            """Stop pulse capture for a single-pin view.

            Example
            -------
            ```python
                >>> echo[0].stop_pulse_capture()
            ```
            """
            ...

        def pulse_ready(self) -> bool:
            """Return pulse capture readiness.

            :return: True if ready.
            
            Example
            -------
            ```python
                >>> echo[0].pulse_ready()
            ```
            """
            ...

        def pulse_width_us(self) -> int:
            """Return captured pulse width.

            :return: Width in microseconds.
            
            Example
            -------
            ```python
                >>> echo[0].pulse_width_us()
            ```
            """
            ...

        def wait_pulse_ready(self, timeout_ms: int = 50) -> bool:
            """Wait for pulse capture readiness.

            :param timeout_ms: Timeout in milliseconds.
            :return: True if ready.
            
            Example
            -------
            ```python
                >>> echo[0].wait_pulse_ready(50)
            ```
            """
            ...

class Dout:
    """Digital output pins.

    Example
    -------
    ```python
        >>> led = Dout([25, 26])
        >>> led[:].value = [1, 0]
    ```
    """
    LOGIC_HIGH: bool
    LOGIC_LOW: bool
    PULL_DOWN: int
    PULL_UP: int
    OPEN_DRAIN: int
    def __init__(self, pins: int | list[int] | tuple[int, ...], *, value: int = 0, active_high: bool = True, mode: int = ...) -> None:
        """Initialize output pin(s).

        :param pins: GPIO pin number or sequence.
        :param value: Initial logical value.
        :param active_high: True for active-high logic.
        :param mode: Pin output mode.
        
        Example
        -------
        ```python
            >>> led = Dout(25, value=0)
        ```
        """
        ...

    def __enter__(self) -> "Dout":
        """Enter context manager.

        :return: Self.
        
        Example
        -------
        ```python
            >>> with Dout(25) as led:
            ...     led.write(1)
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and deinitialize pins.

        Example
        -------
        ```python
            >>> with Dout(25) as led:
            ...     pass
        ```
        """
        ...

    def __len__(self) -> int:
        """Return output pin count.

        :return: Number of pins.
        
        Example
        -------
        ```python
            >>> len(Dout([25, 26]))
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "Dout._View":
        """Get output view.

        :param idx: Pin index or slice.
        :return: Reusable output view.
        
        Example
        -------
        ```python
            >>> led[0].value = 1
            >>> led[:].value = [1, 0]
        ```
        """
        ...

    @property
    def pins(self):
        """Get underlying pin objects.

        :return: Pin object list.
        
        Example
        -------
        ```python
            >>> led.pins[0]
        ```
        """
        ...

    def deinit(self) -> None:
        """Release output pins.

        Example
        -------
        ```python
            >>> led.deinit()
        ```
        """
        ...

    def write(self, value: int = 1, idx: int = 0) -> None:
        """Write logical value to one pin.

        :param value: Logical value.
        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> led.write(1)
        ```
        """
        ...

    def read(self, idx: int = 0) -> int:
        """Read logical output value.

        :param idx: Pin index.
        :return: Logical value.
        
        Example
        -------
        ```python
            >>> led.read()
        ```
        """
        ...

    def read_physical(self, idx: int = 0) -> int:
        """Read physical pin level.

        :param idx: Pin index.
        :return: Physical 0/1 level.
        
        Example
        -------
        ```python
            >>> led.read_physical()
        ```
        """
        ...

    def write_all(self, value: int) -> None:
        """Write logical value to all pins.

        :param value: Logical value.
        
        Example
        -------
        ```python
            >>> led.write_all(0)
        ```
        """
        ...

    def read_into(self, buf):
        """Read all logical values into a buffer.

        :param buf: Mutable buffer.
        :return: The same buffer.
        
        Example
        -------
        ```python
            >>> led.read_into([0, 0])
        ```
        """
        ...

    def set_active(self, idx: int, active_high: bool = True) -> None:
        """Set active logic for one output.

        :param idx: Pin index.
        :param active_high: True for active-high logic.
        
        Example
        -------
        ```python
            >>> relay.set_active(0, False)
        ```
        """
        ...

    def toggle(self, idx: int = 0) -> None:
        """Toggle one output.

        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> led.toggle()
        ```
        """
        ...

    def pulse(self, value: int = 1, *, idx: int = 0, duration_us: int = 10) -> None:
        """Output a short pulse.

        :param value: Pulse logical value.
        :param idx: Pin index.
        :param duration_us: Pulse duration.
        
        Example
        -------
        ```python
            >>> trig.pulse(1, duration_us=10)
        ```
        """
        ...

    class _View:
        """Reusable output view.

        Example
        -------
        ```python
            >>> led[:].value = [1, 0]
        ```
        """
        __slots__ = ("_p", "_i", "_cache")
        def __len__(self) -> int:
            """Return view pin count.

            :return: Number of pins.
            
            Example
            -------
            ```python
                >>> len(led[:])
            ```
            """
            ...

        def __getitem__(self, idx: int | slice) -> "Dout._View":
            """Narrow output view.

            :param idx: View-relative index or slice.
            :return: Narrowed view.
            
            Example
            -------
            ```python
                >>> led[:][0].value = 1
            ```
            """
            ...

        def write(self, value: int) -> None:
            """Write value to all view pins.

            :param value: Logical value.
            
            Example
            -------
            ```python
                >>> led[:].write(1)
            ```
            """
            ...

        def read(self) -> int:
            """Read a single-pin view.

            :return: Logical value.
            
            Example
            -------
            ```python
                >>> led[0].read()
            ```
            """
            ...

        def read_into(self, buf):
            """Read view values into a buffer.

            :param buf: Mutable buffer.
            :return: The same buffer.
            
            Example
            -------
            ```python
                >>> led[:].read_into([0, 0])
            ```
            """
            ...

        @property
        def value(self) -> list[int]:
            """Get logical values as reused list.

            :return: Reused list of logical values.
            
            Example
            -------
            ```python
                >>> values = led[:].value.copy()
            ```
            """
            ...

        @value.setter
        def value(self, val: int | list[int] | tuple[int, ...]) -> None:
            """Set logical values.

            :param val: Scalar or sequence matching view length.
            
            Example
            -------
            ```python
                >>> led[:].value = [1, 0]
            ```
            """
            ...

        @property
        def physical_value(self) -> list[int]:
            """Get physical levels as reused list.

            :return: Reused list of physical levels.
            
            Example
            -------
            ```python
                >>> physical = led[:].physical_value.copy()
            ```
            """
            ...

        @property
        def active(self) -> list[bool]:
            """Get active-high states.

            :return: Reused list of active-high flags.
            
            Example
            -------
            ```python
                >>> states = led[:].active.copy()
            ```
            """
            ...

        @active.setter
        def active(self, value: bool | list[bool] | tuple[bool, ...]) -> None:
            """Set active-high states.

            :param value: Scalar or sequence matching view length.
            
            Example
            -------
            ```python
                >>> relay[:].active = False
            ```
            """
            ...

        def toggle(self) -> None:
            """Toggle all view pins.

            Example
            -------
            ```python
                >>> led[:].toggle()
            ```
            """
            ...

        def pulse(self, value: int = 1, duration_us: int = 10) -> None:
            """Pulse all view pins.

            :param value: Pulse logical value.
            :param duration_us: Pulse duration.
            
            Example
            -------
            ```python
                >>> trig[:].pulse(1, 10)
            ```
            """
            ...

class Dio:
    """Bidirectional digital pins.

    Example
    -------
    ```python
        >>> pins = Dio([16, 17], mode=Dio.MODE_OUT)
        >>> pins[:].value = [1, 0]
    ```
    """
    MODE_IN: int
    MODE_OUT: int
    MODE_OPEN_DRAIN: int
    PULL_DOWN: int
    PULL_UP: int
    OPEN_DRAIN: int
    CB_FALLING: int
    CB_RISING: int
    CB_BOTH: int
    def __init__(self, pins: int | list[int] | tuple[int, ...], *, mode: int = ..., pull: int | None = None, value: int = 0) -> None:
        """Initialize bidirectional pin(s).

        :param pins: GPIO pin number or sequence.
        :param mode: Initial pin mode.
        :param pull: Pull mode for input/open-drain modes.
        :param value: Initial output value.
        
        Example
        -------
        ```python
            >>> pins = Dio([16, 17], mode=Dio.MODE_OUT)
        ```
        """
        ...

    def __enter__(self) -> "Dio":
        """Enter context manager.

        :return: Self.
        
        Example
        -------
        ```python
            >>> with Dio(16) as pin:
            ...     pin.read()
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and release pins.

        Example
        -------
        ```python
            >>> with Dio(16) as pin:
            ...     pass
        ```
        """
        ...

    def __len__(self) -> int:
        """Return pin count.

        :return: Number of pins.
        
        Example
        -------
        ```python
            >>> len(Dio([16, 17]))
        ```
        """
        ...

    def __getitem__(self, idx: int | slice) -> "Dio._View":
        """Get bidirectional pin view.

        :param idx: Pin index or slice.
        :return: Reusable view.
        
        Example
        -------
        ```python
            >>> pins[0].value = 1
        ```
        """
        ...

    def deinit(self) -> None:
        """Release pins.

        Example
        -------
        ```python
            >>> pins.deinit()
        ```
        """
        ...

    def set_mode(self, idx: int = 0, mode: int = ..., *, pull: int | None = None) -> None:
        """Set mode for one pin.

        :param idx: Pin index.
        :param mode: Dio mode constant.
        :param pull: Pull mode.
        
        Example
        -------
        ```python
            >>> pins.set_mode(0, Dio.MODE_IN, pull=Dio.PULL_UP)
        ```
        """
        ...

    def read(self, idx: int = 0) -> int:
        """Read one pin.

        :param idx: Pin index.
        :return: 0 or 1.
        
        Example
        -------
        ```python
            >>> pins.read()
        ```
        """
        ...

    def write(self, value: int = 1, idx: int = 0) -> None:
        """Write one output-capable pin.

        :param value: Output value.
        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> pins.write(1)
        ```
        """
        ...

    def toggle(self, idx: int = 0) -> None:
        """Toggle one output-capable pin.

        :param idx: Pin index.
        
        Example
        -------
        ```python
            >>> pins.toggle()
        ```
        """
        ...

    def irq(self, idx: int, callback: Callable[[int, int], None] | None = None, *, trigger: int = ..., debounce_us: int = 0, hard: bool = True) -> None:
        """Register IRQ for an input-mode pin.

        :param idx: Pin index.
        :param callback: Callback receiving (pin_number, value).
        
        Example
        -------
        ```python
            >>> pins.irq(0, lambda pin, value: print(value))
        ```
        """
        ...

    class _View:
        """Reusable bidirectional pin view.

        Example
        -------
        ```python
            >>> pins[:].mode = Dio.MODE_OUT
        ```
        """
        __slots__ = ("_p", "_i", "_cache")
        def __len__(self) -> int:
            """Return view pin count.

            :return: Number of pins.
            
            Example
            -------
            ```python
                >>> len(pins[:])
            ```
            """
            ...

        def __getitem__(self, idx: int | slice) -> "Dio._View":
            """Narrow bidirectional pin view.

            :param idx: View-relative index or slice.
            :return: Narrowed view.
            
            Example
            -------
            ```python
                >>> pins[:][0].value = 1
            ```
            """
            ...

        def read(self) -> int:
            """Read a single-pin view.

            :return: Pin value.
            
            Example
            -------
            ```python
                >>> pins[0].read()
            ```
            """
            ...

        def write(self, value: int = 1) -> None:
            """Write all output-capable view pins.

            :param value: Output value.
            
            Example
            -------
            ```python
                >>> pins[:].write(1)
            ```
            """
            ...

        @property
        def value(self) -> list[int]:
            """Get pin values as reused list.

            :return: Reused list of pin values.
            
            Example
            -------
            ```python
                >>> values = pins[:].value.copy()
            ```
            """
            ...

        @value.setter
        def value(self, val: int | list[int] | tuple[int, ...]) -> None:
            """Set pin values.

            :param val: Scalar or sequence matching view length.
            
            Example
            -------
            ```python
                >>> pins[:].value = [1, 0]
            ```
            """
            ...

        @property
        def mode(self) -> list[int]:
            """Get pin modes as reused list.

            :return: Reused list of mode constants.
            
            Example
            -------
            ```python
                >>> modes = pins[:].mode.copy()
            ```
            """
            ...

        @mode.setter
        def mode(self, value: int | list[int] | tuple[int, ...]) -> None:
            """Set pin modes.

            :param value: Scalar mode or sequence matching view length.
            
            Example
            -------
            ```python
                >>> pins[:].mode = Dio.MODE_OUT
            ```
            """
            ...

        def toggle(self) -> None:
            """Toggle output-capable view pins.

            Example
            -------
            ```python
                >>> pins[:].toggle()
            ```
            """
            ...
