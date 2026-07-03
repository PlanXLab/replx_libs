"""
Async Wrapper for Multi-Button Input Driver.

Provides asyncio-compatible interface for Button class with non-blocking
wait methods and async event streaming.

Features:

- Non-blocking wait for press/release/click
- Async event generator for continuous monitoring
- Cooperative multitasking with asyncio event loop
- Full access to underlying Button device

Examples:
    Basic async usage:

    >>> from input.button import Button
    >>> from input.button_async import ButtonAsync
    >>> 
    >>> btns = Button([15, 16, 17], active_high=False)
    >>> async_btns = ButtonAsync(btns)
    >>> 
    >>> # Non-blocking wait
    >>> await async_btns.wait_for_click(0)

    Event streaming:

    >>> async for idx, event in async_btns.events():
    ...     print(f"Button {idx}: {event}")

    With timeout:

    >>> if await async_btns.wait_for_press(0, timeout_ms=5000):
    ...     print("Pressed!")
    ... else:
    ...     print("Timeout")

    Concurrent with other tasks:

    >>> async def button_task():
    ...     async for idx, event in async_btns.events():
    ...         handle_event(idx, event)
    >>> 
    >>> async def main():
    ...     await asyncio.gather(
    ...         button_task(),
    ...         other_task(),
    ...     )

"""

from typing import AsyncIterator
from .button import Button


class ButtonAsync:
    """
    Async wrapper for Button class.
    
    Wraps a Button instance to provide asyncio-compatible methods.
    Does not own the underlying device - caller manages lifecycle.
    
    :param device: Button instance to wrap
    
    Example
    -------
    ```python
        >>> btns = Button([15, 16, 17], active_high=False)
        >>> async_btns = ButtonAsync(btns)
        >>> 
        >>> # Use async methods
        >>> await async_btns.wait_for_click(0)
        >>> 
        >>> # Cleanup is caller's responsibility
        >>> btns.deinit()
    ```
    """
    
    def __init__(self, device: Button) -> None: ...
    
    def __enter__(self) -> "ButtonAsync":
        """
        Enter context manager.
        
        :return: Self
        
        Example
        -------
        ```python
            >>> with ButtonAsync(btns) as async_btns:
            ...     await async_btns.wait_for_click(0)
        ```
        """
        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit context manager.
        
        Does NOT call device.deinit() - wrapper does not own device.
        
        Example
        -------
        ```python
            >>> with ButtonAsync(btns) as async_btns:
            ...     pass
            >>> # btns still valid, must call btns.deinit() separately
        ```
        """
        ...
    
    def __len__(self) -> int:
        """
        Get number of buttons.
        
        :return: Number of buttons in wrapped device
        
        Example
        -------
        ```python
            >>> len(async_btns)
            3
        ```
        """
        ...
    
    def __getitem__(self, idx: int | slice) -> "Button._View":
        """
        Access button view from underlying device.
        
        :param idx: Button index or slice
        :return: View for accessing button(s)
        
        Example
        -------
        ```python
            >>> async_btns[0].on_click = lambda idx: print(f"Click {idx}")
        ```
        """
        ...
    
    @property
    def device(self) -> Button:
        """
        Get underlying Button device.
        
        :return: Wrapped Button instance
        
        Example
        -------
        ```python
            >>> async_btns.device.pins
            [15, 16, 17]
        ```
        """
        ...
    
    async def wait_for_press(
        self,
        idx: int = 0,
        timeout_ms: int = 0,
        poll_ms: int = 10
    ) -> bool:
        """
        Wait for button press asynchronously.
        
        Yields to event loop between polls, allowing other tasks to run.
        
        :param idx: Button index (default: 0)
        :param timeout_ms: Timeout in milliseconds. 0 for no timeout
        :param poll_ms: Polling interval in milliseconds (default: 10)
        :return: True if pressed, False on timeout
        
        Example
        -------
        ```python
            >>> # Wait indefinitely
            >>> await async_btns.wait_for_press(0)
            >>> 
            >>> # Wait with timeout
            >>> if await async_btns.wait_for_press(1, timeout_ms=5000):
            ...     print("Button 1 pressed")
        ```
        """
        ...
    
    async def wait_for_release(
        self,
        idx: int = 0,
        timeout_ms: int = 0,
        poll_ms: int = 10
    ) -> bool:
        """
        Wait for button release asynchronously.
        
        :param idx: Button index (default: 0)
        :param timeout_ms: Timeout in milliseconds. 0 for no timeout
        :param poll_ms: Polling interval in milliseconds (default: 10)
        :return: True if released, False on timeout
        
        Example
        -------
        ```python
            >>> await async_btns.wait_for_release(0)
        ```
        """
        ...
    
    async def wait_for_click(
        self,
        idx: int = 0,
        timeout_ms: int = 0,
        poll_ms: int = 10
    ) -> bool:
        """
        Wait for button click (press + release) asynchronously.
        
        :param idx: Button index (default: 0)
        :param timeout_ms: Timeout in milliseconds. 0 for no timeout
        :param poll_ms: Polling interval in milliseconds (default: 10)
        :return: True if click detected, False on timeout
        
        Example
        -------
        ```python
            >>> if await async_btns.wait_for_click(0, timeout_ms=10000):
            ...     print("Clicked!")
        ```
        """
        ...
    
    async def wait_for_event(
        self,
        idx: int = 0,
        event: str = 'click',
        timeout_ms: int = 0,
        poll_ms: int = 10
    ) -> bool:
        """
        Wait for specific gesture event asynchronously.
        
        :param idx: Button index (default: 0)
        :param event: Event type to wait for ('press', 'release', 'click', 
            'double_click', 'long_press')
        :param timeout_ms: Timeout in milliseconds. 0 for no timeout
        :param poll_ms: Polling interval in milliseconds (default: 10)
        :return: True if event detected, False on timeout
        
        Example
        -------
        ```python
            >>> # Wait for double click
            >>> if await async_btns.wait_for_event(0, 'double_click', 5000):
            ...     print("Double clicked!")
            >>> 
            >>> # Wait for long press
            >>> await async_btns.wait_for_event(1, 'long_press')
        ```
        """
        ...
    
    def events(self, poll_ms: int = 10) -> AsyncIterator[tuple[int, str]]:
        """
        Async generator yielding all button events.
        
        Continuously monitors all buttons and yields events as they occur.
        Also fires registered callbacks on the underlying Button device.
        
        :param poll_ms: Polling interval in milliseconds (default: 10)
        :yields: Tuple of (button_index, event_name)
        
        Example
        -------
        ```python
            >>> async for idx, event in async_btns.events():
            ...     print(f"Button {idx}: {event}")
            ...     if event == 'long_press' and idx == 0:
            ...         break  # Exit on button 0 long press
        ```
        """
        ...
    
    def events_for(
        self,
        indices: list[int] | None = None,
        poll_ms: int = 10
    ) -> AsyncIterator[tuple[int, str]]:
        """
        Async generator yielding events for specific buttons only.
        
        :param indices: List of button indices to monitor. None for all buttons
        :param poll_ms: Polling interval in milliseconds (default: 10)
        :yields: Tuple of (button_index, event_name)
        
        Example
        -------
        ```python
            >>> # Monitor only buttons 0 and 2
            >>> async for idx, event in async_btns.events_for([0, 2]):
            ...     print(f"Button {idx}: {event}")
        ```
        """
        ...
