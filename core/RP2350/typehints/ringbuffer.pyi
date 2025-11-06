"""
Ring Buffer Implementation

High-performance circular buffer (ring buffer) for efficient byte data streaming
and buffering. Optimized for real-time data processing, protocol parsing, and
serial communication buffering in embedded systems.

Features:

- Fixed-size circular buffer with automatic wraparound
- Overflow protection with automatic overwrite of oldest data
- Efficient O(1) put and get operations
- Pattern searching and extraction capabilities
- Peek operations without data removal
- Memory-efficient implementation using bytearray
- Thread-safe for single producer/single consumer scenarios
- Support for variable-length data chunks

Buffer Management:

- Automatic wraparound when reaching buffer end
- FIFO (First In, First Out) behavior with overflow handling
- Maintains data ordering across wraparound boundaries
- Pre-allocated buffer for predictable memory usage
- Head and tail pointers for efficient circular indexing

Use Cases:

- UART/Serial communication buffering
- Protocol frame parsing and extraction
- Data stream processing and filtering
- Sensor data collection and aggregation
- Real-time data logging systems
- Circular logging with automatic rotation
- Message queue implementations

Pattern Matching:

- Search for byte patterns/delimiters in buffer
- Extract complete frames or messages
- Efficient pattern matching with early termination
- Support for maximum search limits
- Automatic frame boundary detection

"""

import micropython

__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class RingBuffer:
    """
    High-performance circular buffer implementation for byte data streaming.
    
    This class provides an efficient ring buffer (circular buffer) for managing
    byte streams with automatic overflow handling. It's designed for real-time
    data processing, protocol parsing, and buffering serial communication data.
    The buffer uses a fixed-size array with head and tail pointers for O(1)
    operations.
    
    Features:
    
        - Fixed-size circular buffer with automatic wraparound
        - Overflow protection (overwrites oldest data when full)
        - Efficient O(1) put and get operations
        - Pattern searching and extraction
        - Peek operations without data removal
        - Memory-efficient implementation using bytearray
        - Thread-safe for single producer/single consumer
    
    Buffer Management:
    
        - Automatic wraparound when reaching buffer end
        - Oldest data is overwritten when buffer is full
        - Maintains data ordering (FIFO behavior)
        - Efficient memory usage with pre-allocated buffer
    
    Use Cases:
    
        - Serial communication buffering
        - Protocol frame parsing
        - Data stream processing
        - Sensor data collection
        - Real-time data logging
        - Circular logging systems
    
    """
    
    def __init__(self, size: int) -> None:
        """
        Initialize the ring buffer with a specified size.
        
        Creates a circular buffer with the given capacity. The actual usable
        space is (size-1) bytes due to the implementation requiring one slot
        to distinguish between full and empty states.
        
        :param size: The total size of the ring buffer in bytes (minimum 2)
        
        :raises ValueError: If size < 2 (minimum required for ring buffer)
        :raises TypeError: If size is not an integer
        
        Example
        -------
        ```python
            >>> # Create buffers of different sizes for different purposes
            >>> cmd_buffer = RingBuffer(64)    # Small buffer for commands
            >>> data_buffer = RingBuffer(256)  # Medium buffer for sensor data
            >>> log_buffer = RingBuffer(2048)  # Large buffer for logging
            >>> 
            >>> # Buffer sizing based on data rate and latency
            >>> def calculate_buffer_size(data_rate_bps, latency_ms):
            ...     bytes_per_ms = data_rate_bps / 8 / 1000
            ...     min_size = int(bytes_per_ms * latency_ms * 2)  # 2x safety margin
            ...     return max(64, min_size)  # Minimum 64 bytes
            >>> 
            >>> # Create UART buffer based on baud rate
            >>> uart_buffer = RingBuffer(calculate_buffer_size(115200, 100))
        ```
        """
    
    @micropython.native
    def put(self, data: bytes) -> None:
        """
        Put data into the ring buffer with automatic overflow handling.
        
        Adds data to the buffer, automatically wrapping around when the end
        is reached. If the buffer becomes full, the oldest data is overwritten
        to make room for new data (FIFO with overflow).
        
        :param data: The byte data to put into the buffer
        
        :raises TypeError: If data is not bytes or bytearray
        
        Behavior:
        
            - Data is added byte by byte to the buffer
            - Buffer wraps around at the end (circular behavior)
            - Oldest data is overwritten when buffer is full
            - Operation is atomic for single bytes
        
        Example
        -------
        ```python
            >>> buffer = RingBuffer(10)
            >>> 
            >>> # Basic data insertion
            >>> buffer.put(b"Hello")
            >>> print(f"Available: {buffer.avail()}")  # 5 bytes
            >>> 
            >>> # Add more data (demonstrates overflow)
            >>> buffer.put(b" World")
            >>> print(f"Available: {buffer.avail()}")  # 9 bytes (limited by buffer size)
            >>> 
            >>> # Serial data buffering in an interrupt handler
            >>> def uart_irq_handler(pin):
            ...     # Buffer incoming data quickly
            ...     while uart.any():
            ...         chunk = uart.read()
            ...         if chunk:
            ...             buffer.put(chunk)  # Handles overflow automatically
        ```
        """

    @micropython.native
    def avail(self) -> int:
        """
        Get the number of bytes currently available in the buffer.
        
        Returns the count of bytes that can be read from the buffer without
        blocking. This represents the amount of data currently stored in
        the circular buffer.
        
        :return: Number of bytes available for reading (0 to size-1)
        
        Example
        -------
        ```python
            >>> buffer = RingBuffer(10)
            >>> print(f"Initial: {buffer.avail()}")  # 0
            >>> 
            >>> buffer.put(b"Hello")
            >>> print(f"After put: {buffer.avail()}")  # 5
            >>> 
            >>> data = buffer.get(2)
            >>> print(f"After get: {buffer.avail()}")  # 3
            >>> 
            >>> # Batch processing based on available data
            >>> def process_when_ready():
            ...     if buffer.avail() >= MIN_BATCH_SIZE:
            ...         batch = buffer.get(MIN_BATCH_SIZE)
            ...         process_data(batch)
            ...     elif buffer.avail() > 0 and timeout_occurred():
            ...         # Process whatever is available after timeout
            ...         process_data(buffer.get(buffer.avail()))
        ```
        """

    @micropython.native
    def get(self, n: int = 1) -> bytes:
        """
        Get and remove n bytes from the ring buffer.
        
        Retrieves up to n bytes from the buffer and removes them. If fewer
        than n bytes are available, returns only the available bytes.
        Data is returned in FIFO order (oldest data first).
        
        :param n: Number of bytes to retrieve (default: 1, minimum: 1)
        :return: Retrieved bytes (may be shorter than requested)
        
        :raises ValueError: If n < 1
        :raises TypeError: If n is not an integer
        
        Example
        -------
        ```python
            >>> buffer = RingBuffer(10)
            >>> buffer.put(b"Hello World")  # Note: only 9 bytes fit in a size-10 buffer
            >>> 
            >>> # Get specific number of bytes
            >>> data1 = buffer.get(5)
            >>> print(data1)  # b"Hello"
            >>> 
            >>> # Get remaining bytes
            >>> data2 = buffer.get(buffer.avail())
            >>> print(data2)  # b" Worl" (only what's available)
            >>> 
            >>> # Protocol parsing example
            >>> def parse_packet_header():
            ...     if buffer.avail() >= 4:  # Header size is 4 bytes
            ...         header = buffer.get(4)
            ...         msg_type = header[0]
            ...         msg_len = int.from_bytes(header[1:3], 'big')
            ...         checksum = header[3]
            ...         return msg_type, msg_len, checksum
            ...     return None, None, None
        ```
        """
    
    @micropython.native
    def peek(self, n: int = 1) -> bytes:
        """
        Peek at n bytes from the buffer without removing them.
        
        Returns up to n bytes from the buffer without modifying the buffer
        state. This allows inspection of data before deciding whether to
        consume it. Useful for protocol parsing and lookahead operations.
        
        :param n: Number of bytes to peek at (default: 1, minimum: 1)
        :return: Peeked bytes (may be shorter than requested)
        
        :raises ValueError: If n < 1
        :raises TypeError: If n is not an integer
        
        Example
        -------
        ```python
            >>> buffer = RingBuffer(10)
            >>> buffer.put(b"Hello")
            >>> 
            >>> # Peek without consuming
            >>> peeked = buffer.peek(3)
            >>> print(f"Peeked: {peeked}")  # b"Hel"
            >>> print(f"Available: {buffer.avail()}")  # Still 5 bytes
            >>> 
            >>> # Protocol header inspection
            >>> def inspect_header():
            ...     if buffer.avail() >= 2:
            ...         header = buffer.peek(2)
            ...         if header[0] == 0xAA and header[1] == 0x55:
            ...             # Valid header, consume it and process packet
            ...             buffer.get(2)  # Remove header
            ...             process_packet()
            ...         else:
            ...             # Invalid header, skip one byte and try again
            ...             buffer.get(1)
        ```
        """
    
    def get_until(self, pattern: bytes, max_size: int | None = None) -> bytes | None:
        """
        Extract data from buffer up to and including a specific pattern.
        
        Searches for the first occurrence of the specified pattern in the buffer
        and returns all data from the beginning up to and including the pattern.
        The returned data is removed from the buffer. This is useful for
        extracting complete messages or packets with known terminators.
        
        :param pattern: The byte sequence to search for (delimiter/terminator)
        :param max_size: Maximum bytes to search/return (None for no limit)
        :return: Data up to and including pattern, or None if pattern not found
        
        :raises TypeError: If pattern is not bytes or bytearray
        :raises ValueError: If pattern is empty or max_size < pattern length
        
        Example
        -------
        ```python
            >>> buffer = RingBuffer(256)
            >>> buffer.put(b"Hello\nWorld\nTest\n")
            >>> 
            >>> # Extract line by line
            >>> line1 = buffer.get_until(b'\n')
            >>> print(line1)  # b"Hello\n"
            >>> 
            >>> line2 = buffer.get_until(b'\n')
            >>> print(line2)  # b"World\n"
            >>> 
            >>> # Message protocol parsing
            >>> def parse_messages():
            ...     while True:
            ...         message = buffer.get_until(b'\r\n', max_size=200)
            ...         if message:
            ...             # Remove delimiter and process
            ...             content = message[:-2].decode('utf-8')
            ...             process_message(content)
            ...         else:
            ...             break  # No complete message available
        ```
        """
