"""
Console Input/Output Library for MicroPython

Unified console handling module providing keyboard input, line editing,
and buffered serial communication for MicroPython environments.

This module combines functionality for:

    - Non-blocking keyboard reading (KeyReader)
    - Line input with editing support (input)
    - Buffered console I/O with timeouts (ReplSerial)

The module provides a consistent interface for terminal interaction,
with support for special keys (arrows, function keys, etc.) and
UTF-8 characters.

Key Features:

    - Unified ESC sequence handling for all terminal keys
    - Non-blocking key reading for interactive applications
    - Line editing with cursor movement and character deletion
    - Buffered I/O with timeout and pattern matching support
    - Full UTF-8 character support

Usage:

    ```python
    from termio import KeyReader, input, ReplSerial
    K = KeyReader.Key
    
    # Non-blocking key reading
    with KeyReader() as kr:
        while True:
            key = kr.key
            if key == K.ESC:
                break
            elif key:
                print(f"Pressed: {key}")
    
    # Line input with editing
    name = input("Enter name: ")
    
    # Buffered console I/O
    rs = ReplSerial(timeout=1.0)
    data = rs.read_until(b'\\n')
    rs.close()
    ```

"""

from typing import Callable


class KeyReader:
    """
    Non-blocking keyboard reader for interactive applications.
    
    Provides asynchronous key reading for game loops, UI interactions,
    and other scenarios requiring non-blocking input. Handles special
    keys (arrows, enter, tab, etc.) and UTF-8 characters.
    
    Must be used as a context manager to ensure proper resource cleanup.
    
    Key Features:
    
        - Non-blocking key polling via `key` property
        - Blocking wait with timeout via `wait_key()` method
        - Automatic ESC sequence parsing
        - UTF-8 character support
    
    Example
    --------
    ```python
        >>> from termio import KeyReader
        >>> import time
        >>> K = KeyReader.Key
        >>> 
        >>> # Game loop pattern
        >>> with KeyReader() as kr:
        ...     x, y = 0, 0
        ...     while True:
        ...         key = kr.key
        ...         if key == K.UP:
        ...             y -= 1
        ...         elif key == K.DOWN:
        ...             y += 1
        ...         elif key == K.LEFT:
        ...             x -= 1
        ...         elif key == K.RIGHT:
        ...             x += 1
        ...         elif key == K.ESC:
        ...             break
        ...         elif key:
        ...             print(f"Key: {key}")
        ...         time.sleep_ms(50)
    ```
    """

    class Key:
        """Key code constants for special keys supported by KeyReader."""

        ESC: str
        UP: str
        DOWN: str
        LEFT: str
        RIGHT: str
        TAB: str
        ENTER: str
        SPACE: str
        BACKSPACE: str
        UNKNOWN: str
    
    def __init__(self, esc_timeout_ms: int = 50) -> None:
        """
        Initialize KeyReader.
        
        :param esc_timeout_ms: Timeout in milliseconds to wait for ESC sequence
                               completion. Increase if ESC sequences are not
                               being detected properly on slow connections.
        
        Example
        --------
        ```python
            >>> # Default timeout (50ms)
            >>> kr = KeyReader()
            >>> 
            >>> # Longer timeout for slow serial connections
            >>> kr = KeyReader(esc_timeout_ms=100)
        ```
        """
        ...
    
    def __enter__(self) -> "KeyReader":
        """
        Enter the context manager.
        
        Sets up polling for stdin and returns the KeyReader instance.
        
        :return: The KeyReader instance
        
        Example
        --------
        ```python
            >>> with KeyReader() as kr:
            ...     key = kr.key
            ...     print(f"Current key: {key}")
        ```
        """
        ...
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit the context manager and release resources.
        
        Unregisters stdin from polling.
        
        :param exc_type: Exception type if an exception occurred
        :param exc_val: Exception value if an exception occurred
        :param exc_tb: Exception traceback if an exception occurred
        """
        ...
    
    @property
    def key(self) -> str | None:
        """
        Read currently pressed key without blocking.
        
        Returns the key as a string:
        - Single character for regular keys (e.g., 'a', '1', '@')
        - Key constant string for special keys (e.g., KeyReader.Key.UP, KeyReader.Key.ENTER)
        - None if no key is currently pressed
        
        Special keys are returned as Key class constant values, which can
        be compared using == operator.
        
        :return: Key string or None if no key pressed
        
        :raises RuntimeError: If called outside of 'with' statement
        
        Example
        --------
        ```python
            >>> from termio import KeyReader
            >>> K = KeyReader.Key
            >>> 
            >>> with KeyReader() as kr:
            ...     while True:
            ...         key = kr.key
            ...         if key is None:
            ...             continue  # No key pressed
            ...         elif key == K.ESC:
            ...             break
            ...         elif key == K.ENTER:
            ...             print("Enter pressed!")
            ...         elif len(key) == 1:
            ...             print(f"Character: {key}")
            ...         else:
            ...             print(f"Special key: {key}")
        ```
        """
        ...
    
    def wait_key(self, timeout_ms: int = 0) -> str | None:
        """
        Wait for a key press with optional timeout.
        
        Blocks until a key is pressed or timeout expires. Use timeout_ms=0
        to wait indefinitely.
        
        :param timeout_ms: Maximum wait time in milliseconds (0 = wait forever)
        :return: Key string, or None if timeout occurred
        
        :raises RuntimeError: If called outside of 'with' statement
        
        Example
        --------
        ```python
            >>> from termio import KeyReader
            >>> 
            >>> with KeyReader() as kr:
            ...     # Wait forever for a key
            ...     key = kr.wait_key()
            ...     print(f"Pressed: {key}")
            ...     
            ...     # Wait up to 5 seconds
            ...     key = kr.wait_key(timeout_ms=5000)
            ...     if key is None:
            ...         print("Timeout - no key pressed")
            ...     else:
            ...         print(f"Pressed: {key}")
        ```
        """
        ...


def input(prompt: str = "", mask: str | None = None) -> str:
    """
    Read a line of input with editing support.
    
    Provides a full-featured line editor supporting:
    
        - Left/Right arrows for cursor movement
        - Home/End keys to jump to line start/end
        - Backspace to delete character before cursor
        - Delete key to delete character at cursor
        - UTF-8 character input
    
    This function blocks until Enter is pressed.

    If `mask` is provided, typed characters are echoed using the mask
    character (e.g. `'*'`) instead of the original character. The returned
    string is still the original input.
    
    :param prompt: Optional prompt string to display before input
    :param mask: Optional single-character mask for echo (e.g. '*')
    :return: The entered line without trailing newline
    
    Example
    --------
    ```python
        >>> from termio import input
        >>> 
        >>> # Simple input
        >>> name = input()
        >>> print(f"Hello, {name}!")
        >>> 
        >>> # With prompt
        >>> age = input("Enter your age: ")
        >>> print(f"You are {age} years old")
        >>> 
        >>> # Multi-line input
        >>> lines = []
        >>> print("Enter text (empty line to finish):")
        >>> while True:
        ...     line = input("> ")
        ...     if not line:
        ...         break
        ...     lines.append(line)
    ```
    """
    ...


class ReplSerial:
    """
    Buffered serial I/O with timeout support.
    
    Provides buffered reading with timeout and pattern matching,
    suitable for serial communication and protocol handling.
    Uses an internal ring buffer and timer-based polling for
    efficient non-blocking I/O.
    
    Key Features:
    
        - Configurable read timeout
        - Pattern-based reading (read_until)
        - Internal buffering with configurable size
        - Timer-based background polling
    
    Example
    --------
    ```python
        >>> from termio import ReplSerial
        >>> 
        >>> # Create console with 1 second timeout
        >>> con = ReplSerial(timeout=1.0)
        >>> 
        >>> # Read single byte
        >>> byte = con.read(1)
        >>> 
        >>> # Read until newline
        >>> line = con.read_until(b'\\n')
        >>> 
        >>> # Read with max size limit
        >>> data = con.read_until(b'\\r\\n', max_size=1024)
        >>> 
        >>> # Clean up
        >>> con.close()
    ```
    """
    
    def __init__(
        self,
        timeout: float | None = None,
        *,
        bufsize: int = 512,
        poll_ms: int = 10
    ) -> None:
        """
        Initialize Console.
        
        :param timeout: Read timeout in seconds. None means blocking read,
                        0 means non-blocking (return immediately).
        :param bufsize: Internal buffer size in bytes (default: 512)
        :param poll_ms: Polling interval in milliseconds (default: 10)
        
        Example
        --------
        ```python
            >>> # Blocking console (waits forever for data)
            >>> con = ReplSerial()
            >>> 
            >>> # Non-blocking console (returns immediately)
            >>> con = ReplSerial(timeout=0)
            >>> 
            >>> # 2 second timeout
            >>> con = ReplSerial(timeout=2.0)
            >>> 
            >>> # Large buffer for high-throughput
            >>> con = ReplSerial(timeout=1.0, bufsize=4096)
            >>> 
            >>> # Faster polling for low-latency
            >>> con = ReplSerial(timeout=1.0, poll_ms=5)
        ```
        """
        ...
    
    @property
    def timeout(self) -> float | None:
        """
        Get current read timeout.
        
        :return: Timeout in seconds, or None for blocking
        
        Example
        --------
        ```python
            >>> con = ReplSerial(timeout=1.0)
            >>> print(con.timeout)  # 1.0
        ```
        """
        ...
    
    @timeout.setter
    def timeout(self, value: float | None) -> None:
        """
        Set read timeout.
        
        :param value: Timeout in seconds, None for blocking, 0 for non-blocking
        
        Example
        --------
        ```python
            >>> con = ReplSerial()
            >>> con.timeout = 2.0   # 2 second timeout
            >>> con.timeout = None  # Blocking mode
            >>> con.timeout = 0     # Non-blocking mode
        ```
        """
        ...
    
    def read(self, size: int = 1) -> bytes:
        """
        Read up to size bytes from console.
        
        Waits for data according to timeout setting. May return fewer
        bytes than requested if timeout occurs or less data is available.
        
        :param size: Maximum number of bytes to read
        :return: Bytes read (may be empty if timeout with no data)
        
        Example
        --------
        ```python
            >>> con = ReplSerial(timeout=1.0)
            >>> 
            >>> # Read single byte
            >>> b = con.read(1)
            >>> if b:
            ...     print(f"Got byte: {b[0]}")
            >>> 
            >>> # Read multiple bytes
            >>> data = con.read(100)
            >>> print(f"Read {len(data)} bytes")
        ```
        """
        ...
    
    def read_until(self, expected: bytes = b'\r', max_size: int | None = None) -> bytes:
        """
        Read until expected pattern is found.
        
        Reads bytes until the expected pattern is encountered or max_size
        is reached. The returned data includes the pattern.
        
        :param expected: Byte pattern to read until (default: carriage return)
        :param max_size: Maximum bytes to read (None = no limit)
        :return: Bytes read including pattern, or empty bytes if timeout
        
        Example
        --------
        ```python
            >>> con = ReplSerial(timeout=5.0)
            >>> 
            >>> # Read a line (until newline)
            >>> line = con.read_until(b'\\n')
            >>> print(line.decode('utf-8').strip())
            >>> 
            >>> # Read until CR-LF
            >>> response = con.read_until(b'\\r\\n')
            >>> 
            >>> # Read until pattern with size limit
            >>> data = con.read_until(b'END', max_size=1024)
            >>> 
            >>> # Protocol example: read until OK or ERROR
            >>> con.write(b'AT\\r\\n')
            >>> response = con.read_until(b'\\r\\n', max_size=256)
            >>> if b'OK' in response:
            ...     print("Command succeeded")
        ```
        """
        ...
    
    def write(self, data: bytes) -> None:
        """
        Write bytes to console output.
        
        :param data: Bytes or bytearray to write
        :return: None
        
        :raises TypeError: If data is not bytes or bytearray
        
        Example
        --------
        ```python
            >>> con = ReplSerial()
            >>> 
            >>> # Write bytes
            >>> con.write(b'Hello, World!\\n')
            >>> 
            >>> # Write encoded string
            >>> message = "Hello"
            >>> con.write(message.encode('utf-8'))
            >>> 
            >>> # Protocol command
            >>> con.write(b'AT+GMR\\r\\n')
            >>> response = con.read_until(b'\\r\\n')
        ```
        """
        ...
    
    def close(self) -> None:
        """
        Close console and release resources.
        
        Stops the internal polling timer. Should be called when done
        using the ReplSerial instance.
        
        Example
        --------
        ```python
            >>> con = ReplSerial(timeout=1.0)
            >>> try:
            ...     data = con.read_until(b'\\n')
            ...     print(data)
            ... finally:
            ...     con.close()
        ```
        """
        ...


# Legacy alias for backward compatibility
Console = ReplSerial
