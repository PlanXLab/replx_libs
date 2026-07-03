"""
Async Terminal I/O module for MicroPython.

Provides async wrappers for KeyReader and ReplSerial with non-blocking
read operations that yield to other asyncio tasks.
"""


from termio import KeyReader, ReplSerial, Key


class _KeysIter:
    """Async iterator returned by ``AsyncKeyReader.keys()``.

    Implements ``__aiter__`` / ``__anext__`` so that ``async for`` works on
    MicroPython, which does not support async generators.
    """

    def __init__(self, reader: KeyReader) -> None: ...
    def __aiter__(self) -> "_KeysIter": ...
    async def __anext__(self) -> str: ...


class AsyncKeyReader:
    """
    Async wrapper for KeyReader.
    
    Provides async key reading that yields to other tasks
    while waiting for user input.

    Example
    -------
    ```python
        >>> from termio import KeyReader, Key
        >>> from termio_async import AsyncKeyReader
        >>> 
        >>> with KeyReader() as reader:
        ...     areader = AsyncKeyReader(reader)
        ...     key = await areader.wait_key(timeout_ms=5000)
        ...     if key == Key.ENTER:
        ...         print("Enter pressed!")
    ```
    """
    
    def __init__(self, reader: KeyReader) -> None:
        """
        Initialize async key reader wrapper.
        
        :param reader: Synchronous KeyReader object to wrap

        Example
        -------
        ```python
            >>> with KeyReader() as reader:
            ...     areader = AsyncKeyReader(reader)
        ```
        """
        ...

    def __enter__(self) -> "AsyncKeyReader":
        """Enter context manager - initializes underlying KeyReader."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - cleans up underlying KeyReader."""
        ...

    @property
    def reader(self) -> KeyReader:
        """
        Access underlying synchronous KeyReader object.
        
        :return: The wrapped KeyReader instance
        """
        ...

    @property
    def key(self) -> str | None:
        """
        Get key if available (non-blocking).
        
        :return: Key string or None if no key available
        """
        ...

    async def wait_key(self, timeout_ms: int = 0) -> str | None:
        """
        Wait for a key press asynchronously.
        
        Yields to other tasks while waiting for input.
        
        :param timeout_ms: Maximum wait time in milliseconds.
            0 means wait forever (default: 0)
        
        :return: Key string, or None if timeout occurred

        Example
        -------
        ```python
            >>> # Wait up to 5 seconds for a key
            >>> key = await areader.wait_key(timeout_ms=5000)
            >>> if key is None:
            ...     print("Timeout!")
            >>> elif key == Key.ESC:
            ...     print("Escape pressed")
            >>> 
            >>> # Wait forever
            >>> key = await areader.wait_key()
        ```
        """
        ...

    def keys(self) -> "_KeysIter":
        """
        Return an async iterator that yields keys as they are pressed.

        MicroPython does not support async generators, so this method returns
        a ``_KeysIter`` instance that implements ``__aiter__`` / ``__anext__``.
        Use with ``async for`` to receive each key in order.

        :return: Async iterator yielding key strings

        Example
        -------
        ```python
            >>> async for key in areader.keys():
            ...     print(f"Key: {key}")
            ...     if key == Key.ESC:
            ...         break
        ```
        """
        ...

    async def wait_for_key(self, target: str, timeout_ms: int = 0) -> bool:
        """
        Wait until a specific key is pressed.
        
        :param target: The key to wait for (e.g., Key.ENTER, 'a')
        :param timeout_ms: Maximum wait time. 0 means wait forever (default: 0)
        
        :return: True if key was pressed, False if timeout

        Example
        -------
        ```python
            >>> # Wait for Enter key
            >>> if await areader.wait_for_key(Key.ENTER, timeout_ms=10000):
            ...     print("Enter pressed!")
            >>> else:
            ...     print("Timeout")
        ```
        """
        ...

    async def wait_for_any(self, keys: list[str], timeout_ms: int = 0) -> str | None:
        """
        Wait until any of the specified keys is pressed.
        
        :param keys: List of keys to wait for
        :param timeout_ms: Maximum wait time. 0 means wait forever (default: 0)
        
        :return: The key that was pressed, or None if timeout

        Example
        -------
        ```python
            >>> # Wait for Y or N
            >>> key = await areader.wait_for_any(['y', 'Y', 'n', 'N'])
            >>> if key in ('y', 'Y'):
            ...     print("Yes!")
            >>> 
            >>> # Wait for arrow keys
            >>> key = await areader.wait_for_any([Key.UP, Key.DOWN, Key.LEFT, Key.RIGHT])
        ```
        """
        ...


class AsyncReplSerial:
    """
    Async wrapper for ReplSerial.
    
    Provides async read operations that yield to other tasks
    while waiting for data from REPL serial interface.

    Example
    -------
    ```python
        >>> from termio import ReplSerial
        >>> from termio_async import AsyncReplSerial
        >>> 
        >>> with ReplSerial(timeout=1.0) as serial:
        ...     aserial = AsyncReplSerial(serial)
        ...     data = await aserial.read_until(b'\\n', timeout_ms=5000)
    ```
    """
    
    def __init__(self, serial: ReplSerial) -> None:
        """
        Initialize async serial wrapper.
        
        :param serial: Synchronous ReplSerial object to wrap

        Example
        -------
        ```python
            >>> with ReplSerial() as serial:
            ...     aserial = AsyncReplSerial(serial)
        ```
        """
        ...

    def __enter__(self) -> "AsyncReplSerial":
        """Enter context manager."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - calls close()."""
        ...

    @property
    def serial(self) -> ReplSerial:
        """
        Access underlying synchronous ReplSerial object.
        
        :return: The wrapped ReplSerial instance
        """
        ...

    @property
    def timeout(self) -> float | None:
        """
        Get timeout for synchronous operations.
        
        :return: Timeout in seconds, or None for no timeout
        """
        ...

    @timeout.setter
    def timeout(self, value: float | None) -> None:
        """
        Set timeout for synchronous operations.
        
        :param value: Timeout in seconds, or None for no timeout
        """
        ...

    @property
    def in_waiting(self) -> int:
        """
        Number of bytes in receive buffer.
        
        :return: Number of bytes available to read
        """
        ...

    def write(self, data: bytes) -> int:
        """
        Write data (synchronous - writes are fast).
        
        :param data: Bytes to write
        
        :return: Number of bytes written
        
        :raises TypeError: If data is not bytes or bytearray
        """
        ...

    async def read(self, size: int = 1, timeout_ms: int = 0) -> bytes:
        """
        Read bytes asynchronously.
        
        Yields to other tasks while waiting for data.
        
        :param size: Number of bytes to read (default: 1)
        :param timeout_ms: Maximum wait time. 0 means wait forever (default: 0)
        
        :return: Bytes read (may be less than size if timeout)

        Example
        -------
        ```python
            >>> data = await aserial.read(10, timeout_ms=1000)
            >>> print(f"Read {len(data)} bytes")
        ```
        """
        ...

    async def read_until(self, expected: bytes = b'\r', timeout_ms: int = 0, max_size: int | None = None) -> bytes:
        """
        Read until expected pattern is found.
        
        Yields to other tasks while waiting for pattern.
        
        :param expected: Pattern to look for (default: b'\\r')
        :param timeout_ms: Maximum wait time. 0 means wait forever (default: 0)
        :param max_size: Maximum bytes to read (default: None = unlimited)
        
        :return: Bytes read including the pattern, or partial data if timeout

        Example
        -------
        ```python
            >>> # Read until newline
            >>> line = await aserial.read_until(b'\\n', timeout_ms=5000)
            >>> 
            >>> # Read until specific marker
            >>> data = await aserial.read_until(b'END', timeout_ms=10000)
        ```
        """
        ...

    def close(self) -> None:
        """
        Close the serial connection.
        
        Releases resources and stops background polling.
        """
        ...
