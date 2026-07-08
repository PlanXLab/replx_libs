"""
Async Wrapper for PIO-based Relay Controller (RP2350)

This module provides an asyncio-compatible wrapper for the _ticle Relay class,
enabling non-blocking pulse operations in async applications.

Features:

- Non-blocking pulse operations using asyncio.sleep_ms
- Full access to underlying PIO-based Relay instance
- View pattern for channel selection
- Emergency stop support
- Compatible with asyncio event loop

Example
-------
```python
import asyncio
from actuators.relay import Relay
from actuators.relay_async import RelayAsync

relay = Relay([16, 17, 18], watchdog_ms=5000)
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
    
    # Emergency stop (immediate)
    async_relay.emergency_stop()

asyncio.run(main())
```

"""

from .relay import Relay


class RelayAsync:
    """
    Async wrapper for PIO-based Relay controller.
    
    Provides non-blocking pulse operations while maintaining immediate
    access to state changes and emergency stop through the underlying
    Relay instance.
    
    :param relay: Relay instance to wrap.
    
    Example
    -------
    ```python
    relay = Relay([16, 17], watchdog_ms=5000)
    async_relay = RelayAsync(relay)
    
    # Access underlying relay for immediate operations
    async_relay.relay[0].state = Relay.ON
    
    # Use async pulse
    await async_relay[0].pulse(1000)
    ```
    """

    def __init__(self, relay: Relay) -> None:
        """
        Create an async wrapper around an existing ``Relay`` instance.

        :param relay: An already-initialised ``Relay`` object to wrap.

        Example
        -------
        ```python
            >>> from ticle_lite.relay import Relay
            >>> from ticle_lite.relay_async import RelayAsync
            >>> relay = Relay(pins=[16, 17], watchdog_ms=5000)
            >>> async_relay = RelayAsync(relay)
        ```
        """
        ...

    def __len__(self) -> int:
        """
        Return the number of relay channels.

        :return: Channel count.

        Example
        -------
        ```python
            >>> relay = Relay(pins=[16, 17, 18])
            >>> async_relay = RelayAsync(relay)
            >>> len(async_relay)
            3
        ```
        """
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
        
        Use this for immediate (non-async) operations or hardware-specific
        features like watchdog and feedback.
        
        :return: Underlying Relay instance.
        """
        ...

    def all_off(self) -> None:
        """
        Turn off all relay channels immediately.
        
        This is a synchronous operation (no await needed).
        """
        ...

    def emergency_stop(self) -> None:
        """
        Immediately disable all outputs and halt PIO state machines.
        
        Call this in safety-critical situations. After emergency stop,
        the relay controller must be re-initialized.
        
        Example
        -------
        ```python
        try:
            await async_relay[0].pulse(10000)
        except SomeError:
            async_relay.emergency_stop()  # Immediate halt
        ```
        """
        ...

    class _View:
        """
        View for accessing selected relay channels.
        
        Provides both sync (state, toggle) and async (pulse) operations.
        """

        def __getitem__(self, idx: int | slice) -> "RelayAsync._View":
            """
            Return a narrower view from this view.

            :param idx: View-local index or slice.
            :return: A narrower ``_View``.

            Example
            -------
            ```python
                >>> async_relay[0:2][0].state = Relay.ON
            ```
            """
            ...

        def __len__(self) -> int:
            """
            Return the number of channels in this view.

            :return: Channel count.

            Example
            -------
            ```python
                >>> len(async_relay[:])
                3
            ```
            """
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

        @property
        def feedback(self) -> list[bool | None]:
            """
            Verify feedback status of selected channels.
            
            :return: List of feedback results (True=match, False=mismatch, None=no feedback pin).
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
            
            # Concurrent pulses on different channels
            await asyncio.gather(
                async_relay[0].pulse(1000),
                async_relay[1].pulse(500),
            )
            ```
            """
            ...

        def all_off(self) -> None:
            """
            De-energise all channels in this view (immediate, no await).

            Example
            -------
            ```python
                >>> async_relay[:].all_off()
            ```
            """
            ...

        def emergency_stop(self) -> None:
            """
            Immediately de-energise selected relays via direct PIO writes
            (no await needed).

            Example
            -------
            ```python
                >>> async_relay[:].emergency_stop()
            ```
            """
            ...
