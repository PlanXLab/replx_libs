"""
Multi-Button Input Driver with Gesture Detection.

Provides debounced multi-button input with press/release detection and gesture
recognition including click, double-click, and long-press.

Features:

- Multi-button support with shared Din instance
- Active-high or active-low configuration
- Hardware debouncing via Din
- Basic events: press, release
- Gesture detection: click, double_click, long_press
- Callback-based event handling with button index
- _View pattern for indexed access
- Configurable timing parameters

Examples:
    Single button (backward compatible):

    >>> from input.button import Button
    >>> btn = Button(15, active_high=False)
    >>> if btn[0].pressed[0]:
    ...     print("Pressed")

    Multiple buttons:

    >>> btns = Button([15, 16, 17], active_high=False)
    >>> 
    >>> # Individual access
    >>> if btns[0].pressed[0]:
    ...     print("Button 0 pressed")
    >>> 
    >>> # Individual callbacks (receives button index)
    >>> btns[0].on_click = lambda idx: print(f"Btn {idx} click")
    >>> btns[1].on_long_press = lambda idx: print(f"Btn {idx} long")
    >>> 
    >>> # Shared callback for all buttons
    >>> btns[:].on_press = lambda idx: print(f"Btn {idx} pressed")
    >>> 
    >>> btns.start()  # Enable IRQ detection

    Polling mode:

    >>> btns = Button([15, 16, 17], active_high=False)
    >>> btns[0].on_click = lambda idx: print(f"Click {idx}")
    >>> while True:
    ...     events = btns.update()
    ...     for idx, event in events:
    ...         print(f"Btn {idx}: {event}")
    ...     time.sleep_ms(10)

"""

from typing import Callable

ACTIVE_HIGH: int
"""Active-high constant (1). Button press reads HIGH."""

ACTIVE_LOW: int
"""Active-low constant (0). Button press reads LOW."""


class Button:
    """...
    See class docstring below.
    """

    ALL: int
    """Event filter: return all events as (index, event_name) tuples (default)."""
    PRESS: int
    """Event filter: return only press events as index list."""
    RELEASE: int
    """Event filter: return only release events as index list."""
    CLICK: int
    """Event filter: return only click events as index list."""
    DBCLICK: int
    """Event filter: return only double-click events as index list."""
    LPRESS: int
    """Event filter: return only long-press events as index list."""
    """
    Multi-button input driver with gesture detection.
    
    Uses Din for GPIO input with configurable active level and debouncing.
    Supports multiple buttons with _View pattern for indexed access.
    
    :param pins: Single GPIO pin number or list/tuple of pin numbers
    :param active_high: True if button press reads HIGH (default: True)
    
        - ACTIVE_HIGH (True): pressed = HIGH, released = LOW (uses pull-down)
        - ACTIVE_LOW (False): pressed = LOW, released = HIGH (uses pull-up)
    
    :param pull: Pull resistor configuration. None for auto-detect based on active_high
    :param debounce_ms: Debounce time in milliseconds (default: 20)
    :param long_press_ms: Long press threshold in milliseconds (default: 500)
    :param double_click_gap_ms: Maximum gap between clicks for double-click (default: 300)
    
    Example
    -------
    ```python
        >>> # Single button
        >>> btn = Button(15, active_high=False)
        >>> 
        >>> # Multiple buttons
        >>> btns = Button([15, 16, 17], active_high=False)
        >>> 
        >>> # Custom timing
        >>> btns = Button(
        ...     [15, 16],
        ...     active_high=False,
        ...     debounce_ms=30,
        ...     long_press_ms=1000,
        ...     double_click_gap_ms=400
        ... )
    ```
    """
    
    def __init__(
        self,
        pins: int | list[int] | tuple[int, ...],
        *,
        active_high: bool = True,
        pull: int | None = None,
        debounce_ms: int = 5,
        long_press_ms: int = 400,
        double_click_gap_ms: int = 200
    ) -> None:
        """
        Initialize button input channel(s).

        :param pins: Single GPIO pin number or list/tuple of pin numbers
        :param active_high: True if pressed state reads HIGH
        :param pull: Pull resistor configuration. None selects a default
            based on active_high
        :param debounce_ms: Debounce time in milliseconds
        :param long_press_ms: Long press threshold in milliseconds
        :param double_click_gap_ms: Double-click gap threshold in milliseconds

        Example
        -------
        ```python
            >>> btn = Button(15, active_high=False)
            >>> btns = Button([15, 16], debounce_ms=30)
        ```
        """
        ...
    
    def __enter__(self) -> "Button":
        """
        Enter context manager.
        
        :return: Self
        
        Example
        -------
        ```python
            >>> with Button([15, 16], active_high=False) as btns:
            ...     if btns[0].pressed[0]:
            ...         print("Btn 0 pressed")
        ```
        """
        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context manager.
        
        Calls deinit() to release resources.
        
        Example
        -------
        ```python
            >>> with Button([15, 16], active_high=False) as btns:
            ...     pass
            >>> # deinit() called automatically
        ```
        """
        ...
    
    def __len__(self) -> int:
        """
        Get number of buttons.
        
        :return: Number of buttons
        
        Example
        -------
        ```python
            >>> btns = Button([15, 16, 17])
            >>> len(btns)
            3
        ```
        """
        ...
    
    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Get view for button(s) by index or slice.
        
        :param idx: Button index or slice
        :return: View for accessing the specified button(s)
        
        :raises IndexError: If index out of range
        :raises TypeError: If index is not int or slice
        
        Example
        -------
        ```python
            >>> btns = Button([15, 16, 17])
            >>> btns[0].pressed         # Single button
            [False]
            >>> btns[1:3].pressed       # Slice
            [True, False]
            >>> btns[:].on_click = cb   # All buttons
        ```
        """
        ...
    
    def deinit(self) -> None:
        """
        Release hardware resources.
        
        Stops event detection and releases the underlying Din instance.
        Safe to call multiple times.
        
        Example
        -------
        ```python
            >>> btns = Button([15, 16])
            >>> # ... use buttons ...
            >>> btns.deinit()
        ```
        """
        ...
    
    @property
    def pins(self) -> list[int]:
        """
        Get list of GPIO pin numbers.
        
        :return: Copy of pin number list
        
        Example
        -------
        ```python
            >>> btns = Button([15, 16, 17])
            >>> btns.pins
            [15, 16, 17]
        ```
        """
        ...
    
    @property
    def active_high(self) -> bool:
        """
        Get active level configuration.
        
        :return: True if active-high, False if active-low
        
        Example
        -------
        ```python
            >>> btns = Button([15, 16], active_high=False)
            >>> btns.active_high
            False
        ```
        """
        ...
    
    @property
    def debounce_ms(self) -> int:
        """
        Get debounce time in milliseconds.
        
        :return: Debounce time in ms
        
        Example
        -------
        ```python
            >>> btns.debounce_ms
            20
        ```
        """
        ...
    
    @debounce_ms.setter
    def debounce_ms(self, ms: int) -> None:
        """
        Set debounce time for all buttons.
        
        :param ms: Debounce time in milliseconds
        
        Example
        -------
        ```python
            >>> btns.debounce_ms = 30
        ```
        """
        ...
    
    @property
    def long_press_ms(self) -> int:
        """
        Get long press threshold in milliseconds.
        
        :return: Long press threshold in ms
        
        Example
        -------
        ```python
            >>> btns.long_press_ms
            500
        ```
        """
        ...
    
    @long_press_ms.setter
    def long_press_ms(self, ms: int) -> None:
        """
        Set long press threshold for all buttons.
        
        :param ms: Long press threshold in milliseconds
        
        Example
        -------
        ```python
            >>> btns.long_press_ms = 1000
        ```
        """
        ...
    
    @property
    def double_click_gap_ms(self) -> int:
        """
        Get double-click gap threshold in milliseconds.
        
        :return: Maximum gap between clicks for double-click detection
        
        Example
        -------
        ```python
            >>> btns.double_click_gap_ms
            300
        ```
        """
        ...
    
    @double_click_gap_ms.setter
    def double_click_gap_ms(self, ms: int) -> None:
        """
        Set double-click gap threshold for all buttons.

        :param ms: Maximum gap between clicks for double-click detection

        Example
        -------
        ```python
            >>> btns.double_click_gap_ms = 400
        ```
        """
        ...

    def is_pressed(self, idx: int = 0) -> bool:
        """
        Check if a button is currently pressed, bypassing the state machine.

        Zero-latency direct pin read. Use instead of update() when only the
        instantaneous button state is needed.

        :param idx: Button index. Defaults to 0.
        :return: True if the button is pressed.

        Example
        -------
        ```python
            >>> while True:
            ...     if btn.is_pressed(0):
            ...         motor.run()
            ...     time.sleep_ms(5)
        ```
        """
        ...

    def is_released(self, idx: int = 0) -> bool:
        """
        Check if a button is currently released, bypassing the state machine.

        Zero-latency direct pin read.

        :param idx: Button index. Defaults to 0.
        :return: True if the button is released.

        Example
        -------
        ```python
            >>> if btn.is_released(0):
            ...     motor.stop()
        ```
        """
        ...

    def start(self) -> None:
        """
        Start IRQ-based event detection for all buttons.
        
        Enables hardware interrupt for edge detection. Callbacks are called
        automatically when events occur. Call this after setting up callbacks.
        
        Example
        -------
        ```python
            >>> btns[0].on_press = lambda idx: print(f"Btn {idx}!")
            >>> btns.start()
        ```
        """
        ...
    
    def stop(self) -> None:
        """
        Stop IRQ-based event detection for all buttons.
        
        Disables hardware interrupt. Callbacks will no longer fire automatically.
        
        Example
        -------
        ```python
            >>> btns.stop()
        ```
        """
        ...
    
    def update(self, type: int = ...) -> list:
        """
        Poll and process all button states (polling mode).

        :param type: Event filter constant. Default ``ALL``.

            - ``Button.ALL``     — all events; returns ``list[tuple[int, str]]``
            - ``Button.PRESS``   — press only; returns ``list[int]``
            - ``Button.RELEASE`` — release only; returns ``list[int]``
            - ``Button.CLICK``   — click only; returns ``list[int]``
            - ``Button.DBCLICK`` — double-click only; returns ``list[int]``
            - ``Button.LPRESS``  — long-press only; returns ``list[int]``

        :return: For ``ALL``: list of ``(button_index, event_name)`` tuples.
                 For specific types: list of ``button_index`` integers.

        Example
        -------
        ```python
            >>> # All events (original usage)
            >>> for idx, event in btn.update():
            ...     print(f"{idx}: {event}")
            >>> 
            >>> # Press only — no tuple unpacking needed
            >>> for idx in btn.update(Button.PRESS):
            ...     print(f"Button {idx} pressed")
            >>> 
            >>> # Long press detection — skips click/double-click processing
            >>> for idx in btn.update(Button.LPRESS):
            ...     print(f"Button {idx} long pressed")
        ```
        """
        ...
    
    def wait_for_press(self, idx: int = 0, timeout_ms: int = 0) -> bool:
        """
        Wait for specific button press (blocking).
        
        :param idx: Button index (default: 0)
        :param timeout_ms: Timeout in milliseconds. 0 for no timeout
        :return: True if pressed, False on timeout
        
        Example
        -------
        ```python
            >>> btns.wait_for_press(0)       # Wait for button 0
            >>> btns.wait_for_press(1, 5000) # Wait for button 1, 5s timeout
        ```
        """
        ...
    
    def wait_for_release(self, idx: int = 0, timeout_ms: int = 0) -> bool:
        """
        Wait for specific button release (blocking).
        
        :param idx: Button index (default: 0)
        :param timeout_ms: Timeout in milliseconds. 0 for no timeout
        :return: True if released, False on timeout
        
        Example
        -------
        ```python
            >>> btns.wait_for_release(0)
        ```
        """
        ...
    
    def wait_for_click(self, idx: int = 0, timeout_ms: int = 0) -> bool:
        """
        Wait for specific button click (blocking).
        
        :param idx: Button index (default: 0)
        :param timeout_ms: Timeout in milliseconds. 0 for no timeout
        :return: True if click detected, False on timeout
        
        Example
        -------
        ```python
            >>> if btns.wait_for_click(0, 10000):
            ...     print("Button 0 clicked")
        ```
        """
        ...
    
    class _View:
        """
        View for accessing subset of buttons.
        
        Provides indexed access to button properties and callbacks.
        View instances are reused - do not store references.
        
        Example
        -------
        ```python
            >>> # Correct usage (immediate use)
            >>> btns[0].pressed
            >>> btns[1:3].on_click = callback
            >>> 
            >>> # Incorrect (v1 and v2 are same object)
            >>> v1 = btns[0]
            >>> v2 = btns[1]  # v1 now also points to button 1
        ```
        """
        
        __slots__ = ('_p', '_i')
        
        def __len__(self) -> int:
            """
            Get number of buttons in this view.
            
            :return: Number of buttons
            
            Example
            -------
            ```python
                >>> len(btns[1:3])
                2
            ```
            """
            ...
        
        def __getitem__(self, idx: int | slice) -> "Button._View":
            """
            Further narrow the view.
            
            :param idx: Index or slice relative to current view
            :return: Narrowed view
            
            Example
            -------
            ```python
                >>> btns[1:4][0:2].pressed  # Buttons 1 and 2
            ```
            """
            ...
        
        @property
        def pin(self) -> list[int]:
            """
            Get GPIO pin number(s) for this view.
            
            :return: List of pin numbers
            
            Example
            -------
            ```python
                >>> btns[0].pin
                [15]
                >>> btns[:].pin
                [15, 16, 17]
            ```
            """
            ...
        
        @property
        def pressed(self) -> list[bool]:
            """
            Check if button(s) are currently pressed.
            
            :return: List of pressed states
            
            Example
            -------
            ```python
                >>> btns[0].pressed
                [True]
                >>> btns[:].pressed
                [True, False, False]
            ```
            """
            ...
        
        @property
        def released(self) -> list[bool]:
            """
            Check if button(s) are currently released.

            :return: List of released states

            Example
            -------
            ```python
                >>> btns[0].released
                [False]
            ```
            """
            ...

        def is_pressed(self, idx: int = 0) -> bool:
            """
            Check if the selected button is currently pressed.

            Zero-latency direct pin read for single or multi-channel views.

            :param idx: View-relative index. Defaults to 0.
            :return: True if pressed.

            Example
            -------
            ```python
                >>> if btn[0].is_pressed():
                ...     led.on()
            ```
            """
            ...

        def is_released(self, idx: int = 0) -> bool:
            """
            Check if the selected button is currently released.

            :param idx: View-relative index. Defaults to 0.
            :return: True if released.

            Example
            -------
            ```python
                >>> if btn[0].is_released():
                ...     led.off()
            ```
            """
            ...

        @property
        def on_press(self) -> list[Callable[[int], None] | None]:
            """
            Get press callback(s).
            
            :return: List of callbacks
            
            Example
            -------
            ```python
                >>> btns[0].on_press
                [<function>]
            ```
            """
            ...
        
        @on_press.setter
        def on_press(self, callback: Callable[[int], None] | list[Callable[[int], None]] | None) -> None:
            """
            Set press callback(s).
            
            Callback receives button index: callback(idx)
            Falls back to callback() if TypeError occurs.
            
            :param callback: Single callback for all buttons, or list of callbacks
            
            Example
            -------
            ```python
                >>> btns[0].on_press = lambda idx: print(f"Btn {idx}")
                >>> btns[:].on_press = lambda idx: print(f"Pressed {idx}")
            ```
            """
            ...
        
        @property
        def on_release(self) -> list[Callable[[int], None] | None]:
            """
            Get release callback(s).
            
            :return: List of callbacks
            
            Example
            -------
            ```python
                >>> btns[0].on_release
                [None]
            ```
            """
            ...
        
        @on_release.setter
        def on_release(self, callback: Callable[[int], None] | list[Callable[[int], None]] | None) -> None:
            """
            Set release callback(s).
            
            :param callback: Single callback for all buttons, or list of callbacks
            
            Example
            -------
            ```python
                >>> btns[:].on_release = lambda idx: print(f"Released {idx}")
            ```
            """
            ...
        
        @property
        def on_click(self) -> list[Callable[[int], None] | None]:
            """
            Get click callback(s).
            
            :return: List of callbacks
            
            Example
            -------
            ```python
                >>> btns[0].on_click
                [None]
            ```
            """
            ...
        
        @on_click.setter
        def on_click(self, callback: Callable[[int], None] | list[Callable[[int], None]] | None) -> None:
            """
            Set click callback(s).
            
            Called after press+release when double-click window expires.
            
            :param callback: Single callback for all buttons, or list of callbacks
            
            Example
            -------
            ```python
                >>> btns[0].on_click = lambda idx: print(f"Click {idx}")
            ```
            """
            ...
        
        @property
        def on_double_click(self) -> list[Callable[[int], None] | None]:
            """
            Get double-click callback(s).
            
            :return: List of callbacks
            
            Example
            -------
            ```python
                >>> btns[0].on_double_click
                [None]
            ```
            """
            ...
        
        @on_double_click.setter
        def on_double_click(self, callback: Callable[[int], None] | list[Callable[[int], None]] | None) -> None:
            """
            Set double-click callback(s).
            
            Called when two clicks occur within double_click_gap_ms.
            
            :param callback: Single callback for all buttons, or list of callbacks
            
            Example
            -------
            ```python
                >>> btns[0].on_double_click = lambda idx: print(f"DblClick {idx}")
            ```
            """
            ...
        
        @property
        def on_long_press(self) -> list[Callable[[int], None] | None]:
            """
            Get long-press callback(s).
            
            :return: List of callbacks
            
            Example
            -------
            ```python
                >>> btns[0].on_long_press
                [None]
            ```
            """
            ...
        
        @on_long_press.setter
        def on_long_press(self, callback: Callable[[int], None] | list[Callable[[int], None]] | None) -> None:
            """
            Set long-press callback(s).
            
            Called when button held for long_press_ms. Click event is suppressed.
            
            :param callback: Single callback for all buttons, or list of callbacks
            
            Example
            -------
            ```python
                >>> btns[0].on_long_press = lambda idx: print(f"Long {idx}")
            ```
            """
            ...
        
        def update(self, type: int = ...) -> list:
            """
            Poll and process button states for this view only.

            :param type: Event filter constant. See ``Button.update()``.
            :return: ``list[tuple[int, str]]`` for ALL; ``list[int]`` for specific types.

            Example
            -------
            ```python
                >>> for idx in btns[0:2].update(Button.CLICK):
                ...     print(f"Button {idx} clicked")
            ```
            """
            ...
