"""
Relay - Multi-channel relay controller with software interlock.

Standard GPIO-based relay control with support for normally-open
and normally-closed contacts, software interlock between pairs,
and convenient View-based indexing.
"""

from typing import overload


class Relay:
    """Multi-channel relay controller.
    
    Supports single or multiple relays with unified interface using _View pattern.
    
    Single relay:
        relay = Relay(pin=16)
        relay[0].state = Relay.ON
        relay[0].toggle()
    
    Multiple relays:
        relays = Relay(pins=[16, 17, 18, 19])
        relays[0].state = Relay.ON      # Single relay
        relays[:].state = Relay.OFF     # All relays
        relays[0:2].toggle()            # First two
    
    With interlock (mutually exclusive):
        relays = Relay(pins=[16, 17], interlock_pairs=[(0, 1)])
        relays[0].state = Relay.ON      # Turns ON relay 0
        relays[1].state = Relay.ON      # Auto turns OFF relay 0, then ON relay 1
    
    :param pins: Relay pin number(s) - int for single, list for multiple
    :param contact_type: NORMALLY_OPEN (default) or NORMALLY_CLOSED
    :param interlock_pairs: List of relay index pairs that are mutually exclusive
    
    Example
    -------
    ```python
    from relay import Relay
    
    # Basic usage
    relay = Relay(pins=[16, 17])
    relay[0].state = Relay.ON
    relay[:].state = Relay.OFF
    
    # With pulse
    relay[0].pulse(500)  # ON for 500ms, then OFF
    
    # Interlock (motor direction)
    motor = Relay(pins=[16, 17], interlock_pairs=[(0, 1)])
    motor[0].state = Relay.ON  # Forward
    motor[1].state = Relay.ON  # Reverse (auto stops forward first)
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
        interlock_pairs: list[tuple[int, int]] | None = None
    ) -> None: ...

    def deinit(self) -> None:
        """Release GPIO resources and turn off all relays."""
        ...

    def __enter__(self) -> "Relay": ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
    def __len__(self) -> int: ...

    @overload
    def __getitem__(self, idx: int) -> "_View": ...
    @overload
    def __getitem__(self, idx: slice) -> "_View": ...

    def all_off(self) -> None:
        """Turn off all relays immediately."""
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
            """Set contact type for selected relays.
            
            :param ct: NORMALLY_OPEN or NORMALLY_CLOSED
            """
            ...

        def toggle(self) -> None:
            """Toggle state of selected relays (ON→OFF, OFF→ON)."""
            ...

        def pulse(self, duration_ms: int, state: int = 1) -> None:
            """Output a pulse on selected relays.
            
            :param duration_ms: Pulse duration in milliseconds
            :param state: Pulse state (default ON=1)
            """
            ...

        def all_off(self) -> None:
            """Turn off selected relays."""
            ...
