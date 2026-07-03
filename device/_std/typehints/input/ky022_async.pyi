"""
KY-022 Infrared Receiver Async Wrapper

Async wrapper for KY022 IR receiver providing non-blocking event retrieval
compatible with asyncio event loops.

Features:

- Non-blocking get() with await
- Async generator for continuous event streaming
- Cooperative multitasking friendly

"""

from typing import Tuple, AsyncIterator
from .ky022 import KY022


class KY022Async:
    """
    Async wrapper for KY022 IR receiver.
    
    Provides asyncio-compatible interface for IR event retrieval
    without blocking the event loop.
    
    Example
    -------
    ```python
        >>> import asyncio
        >>> from ky022 import KY022
        >>> from ky022_async import KY022Async
        >>> 
        >>> async def main():
        ...     ir = KY022(pin=15)
        ...     ir_async = KY022Async(ir)
        ...     
        ...     # Single event with timeout
        ...     evt = await ir_async.get(timeout_ms=5000)
        ...     if evt:
        ...         cmd, addr, ext = evt
        ...         print(f"Received: {cmd}")
        ...     
        ...     # Continuous event stream
        ...     async for cmd, addr, ext in ir_async.events():
        ...         print(f"Command: {cmd}, Address: {addr}")
        ...         if cmd == 0x45:  # Power button
        ...             break
        >>> 
        >>> asyncio.run(main())
    ```
    """

    def __init__(self, device: KY022) -> None:
        """
        Initialize async wrapper.
        
        :param device: KY022 instance to wrap
        
        Example
        -------
        ```python
            >>> ir = KY022(pin=15)
            >>> ir_async = KY022Async(ir)
        ```
        """
        ...

    async def get(self, timeout_ms: int = 1000) -> Tuple[int, int, int] | None:
        """
        Get next IR event asynchronously.
        
        Yields to event loop while waiting, allowing other coroutines to run.
        
        :param timeout_ms: Maximum wait time in milliseconds (default: 1000)
        :return: Tuple of (command, address, extended) or None on timeout
        
        Example
        -------
        ```python
            >>> async def handle_ir():
            ...     ir = KY022(pin=15)
            ...     ir_async = KY022Async(ir)
            ...     
            ...     while True:
            ...         evt = await ir_async.get(timeout_ms=5000)
            ...         if evt:
            ...             cmd, addr, _ = evt
            ...             print(f"Button: {cmd}")
            ...         else:
            ...             print("No IR signal")
        ```
        """
        ...

    def events(self, poll_ms: int = 10) -> AsyncIterator[Tuple[int, int, int]]:
        """
        Async generator for continuous IR event streaming.
        
        Yields events as they arrive, polling at specified interval.
        
        :param poll_ms: Polling interval in milliseconds (default: 10)
        :yields: Tuple of (command, address, extended) for each IR event
        
        Example
        -------
        ```python
            >>> async def ir_handler():
            ...     ir = KY022(pin=15)
            ...     ir_async = KY022Async(ir)
            ...     
            ...     async for cmd, addr, ext in ir_async.events():
            ...         if cmd == 0x45:  # Power
            ...             await power_toggle()
            ...         elif cmd == 0x46:  # Volume Up
            ...             await volume_up()
        ```
        """
        ...
