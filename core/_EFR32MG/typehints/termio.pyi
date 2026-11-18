"""
Terminal I/O Library for EFR32MG

Buffered REPL serial I/O for the XBee 3 (EFR32MG) MicroPython platform.
Use `termio_xbee` instead of the standard `termio` module on XBee to
avoid loading the standard module's unsupported dependencies.

Unlike the standard `termio`, the EFR32MG platform has no `machine.Timer`,
`select.poll`, or `micropython.schedule`, so incoming data is pumped from
the firmware stdin buffer synchronously whenever `read()`, `read_until()`,
or `in_waiting` is used, using the non-blocking
`sys.stdin.buffer.read(-1)` pattern documented by Digi.

Features:

- Internal ring buffer that preserves excess received bytes between calls
- Timeout semantics identical to termio@_std (None=blocking, 0=non-blocking)
- Pattern-based reading across chunk boundaries (read_until)
- Unread data stays buffered on timeout (no data loss)
- Memory-efficient implementation for the EFR32MG heap (default 128-byte buffer)

Notes:

- stdin access requires ATAP=4 (MicroPython REPL mode)
- Ctrl-C (0x03) in the input stream raises KeyboardInterrupt unless
  disabled with micropython.kbd_intr(-1)
"""

class ReplSerial:
    """
    Buffered serial I/O over REPL stdin/stdout with timeout support.

    Provides buffered reading with timeout and pattern matching, suitable
    for serial communication and protocol handling. Uses an internal ring
    buffer which is filled synchronously (call-driven pumping) from the
    XBee firmware stdin buffer; bytes received in excess of a read request
    remain buffered for subsequent calls.

    Key Features:

        - Configurable read timeout
        - Pattern-based reading (read_until)
        - Internal ring buffering with configurable size
        - Unread data preserved across calls

    Example
    -------
    ```python
        >>> from termio_xbee import ReplSerial
        >>>
        >>> # Create serial with 1 second timeout
        >>> con = ReplSerial(timeout=1.0)
        >>>
        >>> # Read single byte
        >>> byte = con.read(1)
        >>>
        >>> # Read until newline
        >>> line = con.read_until(b'\\n')
        >>>
        >>> # Clean up
        >>> con.close()
    ```
    """

    def __init__(self, timeout: float | None = None, *, bufsize: int = 128) -> None:
        """
        Initialize the REPL serial interface.

        :param timeout: Read timeout in seconds. None means blocking read,
                        0 means non-blocking (return immediately).
        :param bufsize: Internal ring buffer size in bytes (default: 128).
                        One byte is reserved internally, so the usable
                        capacity is bufsize - 1.

        Example
        -------
        ```python
            >>> # Blocking serial (waits forever for data)
            >>> con = ReplSerial()
            >>>
            >>> # Non-blocking serial (returns immediately)
            >>> con = ReplSerial(timeout=0)
            >>>
            >>> # 2 second timeout with a larger buffer
            >>> con = ReplSerial(timeout=2.0, bufsize=256)
        ```
        """
        ...

    def __enter__(self) -> "ReplSerial":
        """
        Enter a context manager block.

        :return: This ReplSerial instance.

        Example
        -------
        ```python
            >>> with ReplSerial(timeout=1.0) as con:
            ...     line = con.read_until(b'\\n')
        ```
        """
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit a context manager block, closing the instance.

        Example
        -------
        ```python
            >>> with ReplSerial(timeout=1.0) as con:
            ...     con.write(b'ping\\r\\n')
        ```
        """
        ...

    @property
    def timeout(self) -> float | None:
        """
        Get current read timeout.

        :return: Timeout in seconds, or None for blocking.

        Example
        -------
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

        :param value: Timeout in seconds, None for blocking, 0 for non-blocking.

        Example
        -------
        ```python
            >>> con = ReplSerial()
            >>> con.timeout = 2.0   # 2 second timeout
            >>> con.timeout = None  # Blocking mode
            >>> con.timeout = 0     # Non-blocking mode
        ```
        """
        ...

    @property
    def in_waiting(self) -> int:
        """
        Get the number of buffered bytes available to read.

        Pumps pending stdin data into the ring buffer before counting.

        :return: Number of bytes currently buffered.

        Example
        -------
        ```python
            >>> con = ReplSerial(timeout=0)
            >>> if con.in_waiting:
            ...     data = con.read(con.in_waiting)
        ```
        """
        ...

    def read(self, size: int = 1) -> bytes:
        """
        Read up to size bytes.

        Waits for data according to the timeout setting. May return fewer
        bytes than requested if a timeout occurs or less data is available.
        Excess received bytes remain buffered for the next call.

        :param size: Maximum number of bytes to read.
        :return: Bytes read (may be empty if timeout with no data).

        Example
        -------
        ```python
            >>> con = ReplSerial(timeout=1.0)
            >>>
            >>> # Read single byte
            >>> b = con.read(1)
            >>> if b:
            ...     print("Got byte:", b[0])
            >>>
            >>> # Read multiple bytes
            >>> data = con.read(32)
            >>> print("Read", len(data), "bytes")
        ```
        """
        ...

    def read_until(self, expected: bytes = b'\r', max_size: int | None = None) -> bytes:
        """
        Read until the expected pattern is found.

        Reads bytes until the expected pattern is encountered or max_size
        is reached. The returned data includes the pattern. On timeout,
        empty bytes are returned and partially received data stays in the
        internal buffer so a later call can complete the frame.

        :param expected: Byte pattern to read until (default: carriage return).
        :param max_size: Maximum bytes to read (None = no limit).
        :return: Bytes read including pattern, or empty bytes if timeout.

        Example
        -------
        ```python
            >>> con = ReplSerial(timeout=5.0)
            >>>
            >>> # Read a line (until newline)
            >>> line = con.read_until(b'\\n')
            >>> print(line.decode('utf-8').strip())
            >>>
            >>> # Protocol example: command and response
            >>> con.write(b'AT\\r\\n')
            >>> response = con.read_until(b'\\r\\n', max_size=256)
            >>> if b'OK' in response:
            ...     print("Command succeeded")
        ```
        """
        ...

    def write(self, data: bytes) -> None:
        """
        Write bytes to stdout in binary mode.

        :param data: Bytes or bytearray to write.

        :raises TypeError: If data is not bytes or bytearray.

        Example
        -------
        ```python
            >>> con = ReplSerial()
            >>>
            >>> # Write bytes
            >>> con.write(b'Hello, World!\\n')
            >>>
            >>> # Write encoded string
            >>> message = "Hello"
            >>> con.write(message.encode('utf-8'))
        ```
        """
        ...

    def close(self) -> None:
        """
        Close the instance.

        Example
        -------
        ```python
            >>> con = ReplSerial(timeout=1.0)
            >>> try:
            ...     data = con.read_until(b'\\n')
            ... finally:
            ...     con.close()
        ```
        """
        ...
