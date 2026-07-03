"""
Relay - PIO-based high-performance relay controller for RP2040/RP2350.

Advanced relay control with PIO state machines, hardware watchdog,
interlock safety, and feedback verification for industrial applications.
"""

from typing import overload


class Relay:
    """PIO-based multi-channel relay controller with safety features.
    
    High-performance relay control using PIO state machines with:
    - Hardware-level watchdog for fail-safe operation
    - Software interlock between relay pairs
    - Feedback pin verification for relay state confirmation
    - Emergency stop functionality
    
    Single relay:
        relay = Relay(pin=16, watchdog_ms=5000)
        relay.enable_watchdog()
        relay[0].state = Relay.ON
        relay.feed()  # Must call periodically
    
    Multiple relays with interlock:
        relays = Relay(
            pins=[16, 17, 18, 19],
            interlock_pairs=[(0, 1), (2, 3)],
            feedback_pins=[20, 21, 22, 23]
        )
        relays[0].state = Relay.ON
        relays[0].feedback  # Verify relay actually switched
    
    :param pins: Relay pin number(s) - int for single, list for multiple
    :param contact_type: NORMALLY_OPEN (default) or NORMALLY_CLOSED
    :param interlock_pairs: List of relay index pairs that are mutually exclusive
    :param feedback_pins: Optional feedback pins to verify relay state
    :param watchdog_ms: Watchdog timeout in ms (0=disabled)
    
    Note
    ----
    Uses len(pins) PIO State Machines (1 per relay). Call deinit() to release.
    
    Example
    -------
    ```python
    from relay import Relay
    
    # Industrial motor control with safety
    motor = Relay(
        pins=[16, 17],          # Forward, Reverse
        interlock_pairs=[(0, 1)],
        feedback_pins=[18, 19],
        watchdog_ms=5000
    )
    motor.enable_watchdog()
    
    # Forward
    motor[0].state = Relay.ON
    if not motor[0].feedback[0]:
        motor.emergency_stop()
        raise RuntimeError("Relay feedback mismatch!")
    
    # Must feed watchdog periodically
    while running:
        motor.feed()
        time.sleep_ms(1000)
    ```
    """
    
    ON: int
    OFF: int
    NORMALLY_OPEN: bool
    NORMALLY_CLOSED: bool

    def __init__(
        self,
        pins: int | list[int] | tuple[int, ...],
        *,
        contact_type: bool = ...,
        interlock_pairs: list[tuple[int, int]] | None = None,
        feedback_pins: list[int] | None = None,
        watchdog_ms: int = 0
    ) -> None: ...

    def enable_watchdog(self, timeout_ms: int | None = None) -> "Relay":
        """Enable hardware watchdog.
        
        :param timeout_ms: Timeout override (uses constructor value if None)
        :return: Self for chaining
        """
        ...

    def feed(self) -> None:
        """Feed the watchdog to prevent system reset.
        
        Must be called periodically when watchdog is enabled.
        """
        ...

    def deinit(self) -> None:
        """Release PIO resources and turn off all relays."""
        ...

    def __enter__(self) -> "Relay": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
    def __len__(self) -> int: ...

    @overload
    def __getitem__(self, idx: int) -> "_View": ...
    @overload
    def __getitem__(self, idx: slice) -> "_View": ...

    def verify_feedback(self, idx: int) -> bool | None:
        """Verify relay feedback for a single channel.
        
        :param idx: Relay index
        :return: True if feedback matches, False if mismatch, None if no feedback pin
        """
        ...

    def verify_all_feedback(self) -> list[bool | None]:
        """Verify feedback for all relays.
        
        :return: List of verification results
        """
        ...

    def all_off(self) -> None:
        """Turn off all relay channels."""
        ...

    def emergency_stop(self) -> None:
        """Immediately turn off all relays (PIO direct write)."""
        ...

    class _View:
        """View for accessing relay channels by index."""

        def __getitem__(self, idx: int | slice) -> "Relay._View": ...
        def __len__(self) -> int: ...

        @property
        def state(self) -> list[int]:
            """Get logical state of selected relays (ON=1, OFF=0)."""
            ...

        @state.setter
        def state(self, value: int | list[int]) -> None:
            """Set state of selected relays.
            
            :param value: Single value for all, or list matching count
            """
            ...

        @property
        def contact_type(self) -> list[bool]:
            """Get contact type of selected relays."""
            ...

        @contact_type.setter
        def contact_type(self, ct: bool) -> None:
            """Set contact type for selected relays."""
            ...

        @property
        def feedback(self) -> list[bool | None]:
            """Verify feedback for selected relays.
            
            :return: List of verification results (True/False/None)
            """
            ...

        def toggle(self) -> None:
            """Toggle state of selected relays."""
            ...

        def pulse(self, duration_ms: int, state: int = 1) -> None:
            """Output a pulse on selected relays.
            
            :param duration_ms: Pulse duration in milliseconds
            :param state: Pulse state (default ON=1)
            """
            ...

        def all_off(self) -> None:
            """Turn off all channels in this view."""
            ...

        def emergency_stop(self) -> None:
            """Immediately turn off selected relays."""
            ...
