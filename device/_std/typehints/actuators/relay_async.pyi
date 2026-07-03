"""
Async Wrapper for GPIO-based Relay Controller

This module provides an asyncio-compatible wrapper for the Relay class,
enabling non-blocking pulse operations in async applications.

Features:

- Non-blocking pulse operations using asyncio.sleep_ms
- Full access to underlying Relay instance
- View pattern for channel selection (same as Relay)
- Compatible with asyncio event loop

Example
-------
```python
import asyncio
from actuators.relay import Relay
from actuators.relay_async import RelayAsync

relay = Relay([16, 17, 18])
async_relay = RelayAsync(relay)

async def main():
    # Non-blocking pulse
    await async_relay[0].pulse(500)  # 500ms ON pulse
    
    # Immediate operations (no await needed)
    async_relay[1].state = Relay.ON
    async_relay[2].toggle()
    
    # Multiple concurrent pulses
    await asyncio.gather(
        async_relay[0].pulse(1000),
        async_relay[1].pulse(500),
    )

asyncio.run(main())
```

"""

from .relay import Relay


class RelayAsync:
    """
    Async wrapper for Relay controller.
    
    Provides non-blocking pulse operations while maintaining immediate
    access to state changes through the underlying Relay instance.
    
    :param relay: Relay instance to wrap.
    
    Example
    -------
    ```python
    relay = Relay([16, 17])
    async_relay = RelayAsync(relay)
    
    # Access underlying relay for immediate operations
    async_relay.relay[0].state = Relay.ON
    
    # Use async pulse
    await async_relay[0].pulse(1000)
    ```
    """

    def __init__(self, relay: Relay) -> None: ...

    def __len__(self) -> int:
        """Return number of relay channels."""
        ...

    def __getitem__(self, idx: int | slice) -> "_View":
        """
        Access relay channel(s) by index or slice.
        
        :param idx: Channel index or slice.
        :return: View for selected channels.
        
        Example
        -------
        ```python
        async_relay[0]      # Single channel
        async_relay[1:3]    # Channels 1, 2
        async_relay[:]      # All channels
        ```
        """
        ...

    @property
    def relay(self) -> Relay:
        """
        Access underlying Relay instance.
        
        Use this for immediate (non-async) operations.
        
        :return: Underlying Relay instance.
        """
        ...

    def all_off(self) -> None:
        """
        Turn off all relay channels immediately.
        
        This is a synchronous operation (no await needed).
        """
        ...

    class _View:
        """
        View for accessing selected relay channels.
        
        Provides both sync (state, toggle) and async (pulse) operations.
        """

        def __getitem__(self, idx: int | slice) -> "RelayAsync._View":
            """Sub-select from current view."""
            ...

        def __len__(self) -> int:
            """Number of channels in this view."""
            ...

        @property
        def state(self) -> list[int]:
            """
            Get logical state of selected channels.
            
            :return: List of states (Relay.ON or Relay.OFF).
            """
            ...

        @state.setter
        def state(self, value: int | list[int]) -> None:
            """
            Set state of selected channels (immediate, no await).
            
            :param value: Single state for all, or list matching channel count.
            
            Example
            -------
            ```python
            async_relay[0].state = Relay.ON
            async_relay[0:2].state = [Relay.ON, Relay.OFF]
            ```
            """
            ...

        def toggle(self) -> None:
            """
            Toggle state of selected channels (immediate, no await).
            
            Example
            -------
            ```python
            async_relay[0].toggle()  # ON -> OFF or OFF -> ON
            ```
            """
            ...

        @property
        def contact_type(self) -> list[bool]:
            """
            Get contact type of selected channels.
            
            :return: List of contact types (NORMALLY_OPEN or NORMALLY_CLOSED).
            """
            ...

        @contact_type.setter
        def contact_type(self, ct: bool) -> None:
            """
            Set contact type of selected channels.
            
            :param ct: Contact type to set (NORMALLY_OPEN or NORMALLY_CLOSED).
            """
            ...

        async def pulse(self, duration_ms: int, state: int = ...) -> None:
            """
            Non-blocking pulse operation.
            
            Turns relay ON (or specified state), waits asynchronously,
            then turns OFF (or opposite state).
            
            :param duration_ms: Pulse duration in milliseconds.
            :param state: State during pulse (default: Relay.ON).
            
            Example
            -------
            ```python
            # Simple pulse
            await async_relay[0].pulse(500)
            
            # Concurrent pulses
            await asyncio.gather(
                async_relay[0].pulse(1000),
                async_relay[1].pulse(500),
            )
            ```
            """
            ...

        def all_off(self) -> None:
            """Turn off all channels in this view (immediate)."""
            ...
