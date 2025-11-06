"""
SLIP Protocol Implementation

SLIP (Serial Line Internet Protocol) encoder and decoder for reliable binary
data transmission over serial connections. Implements RFC 1055 with frame
boundary detection, escape sequence handling, and automatic error recovery.

Features:

- SLIP frame encoding and decoding
- Binary data transmission over serial links
- Frame boundary detection using END markers
- Escape sequence processing for special characters
- Stateful decoding with internal buffering
- Error recovery from invalid sequences
- Compatible with standard SLIP implementations
- Memory-efficient implementations for embedded systems

Protocol Details:

- END byte (0xC0): Marks frame boundaries
- ESC byte (0xDB): Escape character for special bytes
- ESC_END (0xDC): Escaped version of END byte
- ESC_ESC (0xDD): Escaped version of ESC byte

Encoding Rules:

- Frames are surrounded by END bytes
- END bytes in data become ESC + ESC_END
- ESC bytes in data become ESC + ESC_ESC
- All other bytes pass through unchanged

Decoding Rules:

- END bytes mark frame boundaries
- ESC + ESC_END becomes END in output
- ESC + ESC_ESC becomes ESC in output
- Invalid escape sequences cause frame reset
- Junk data before first frame is ignored

"""

import micropython


__version__ = "1.0.0"
__author__ = "PlanXLab Development Team"


class SlipEncoder:
    """
    SLIP (Serial Line Internet Protocol) encoder for reliable data transmission.
    
    This class implements the SLIP protocol encoding which allows reliable
    transmission of binary data over serial connections by using special
    escape sequences to frame data packets and handle control characters.
    
    SLIP Protocol Details:
        
        - END byte (0xC0): Marks frame boundaries
        - ESC byte (0xDB): Escape character for special bytes
        - ESC_END (0xDC): Escaped version of END byte
        - ESC_ESC (0xDD): Escaped version of ESC byte
    
    Features:
        
        - Reliable binary data transmission
        - Frame boundary detection
        - Escape sequence handling
        - Compatible with SLIP decoders
        - Stateless encoding (static methods)
    
    """
    END      = 0xC0
    ESC      = 0xDB
    ESC_END  = 0xDC
    ESC_ESC  = 0xDD

    @staticmethod
    def encode(payload: bytes) -> bytes:
        """
        Encode a byte array into a SLIP frame.
        
        Converts arbitrary binary data into a SLIP-encoded frame by adding
        frame delimiters and escaping special characters. The resulting
        frame can be safely transmitted over serial connections.
        
        :param payload: The byte array to encode (any binary data)
        :return: SLIP-encoded frame as bytes with delimiters and escaping
        
        :raises TypeError: If payload is not bytes or bytearray
        
        Encoding Rules:
        
            - Frames are surrounded by END bytes (0xC0)
            - END bytes (0xC0) in data are escaped as ESC + ESC_END (0xDB 0xDC)
            - ESC bytes (0xDB) in data are escaped as ESC + ESC_ESC (0xDB 0xDD)
        
        Example
        -------
        ```python
            >>> # Simple text encoding
            >>> text = b"Hello"
            >>> encoded = SlipEncoder.encode(text)
            >>> print(f"Encoded: {encoded.hex()}")  # c048656c6c6fc0
            >>> # Breakdown: C0 (END) + "Hello" + C0 (END)
            >>> 
            >>> # Binary data with special bytes
            >>> data = bytes([0x01, 0xC0, 0x02, 0xDB, 0x03])
            >>> encoded = SlipEncoder.encode(data)
            >>> print(f"Original: {data.hex()}")    # 01c002db03
            >>> print(f"Encoded:  {encoded.hex()}")  # c001dbdc02dbdd03c0
            >>> # Breakdown: C0 + 01 + DB DC (escaped C0) + 02 + DB DD (escaped DB) + 03 + C0
            >>> 
            >>> # JSON data encoding
            >>> import json
            >>> json_str = json.dumps({"temp": 25.5, "humidity": 67})
            >>> json_bytes = json_str.encode('utf-8')
            >>> encoded = SlipEncoder.encode(json_bytes)
            >>> 
            >>> # Struct data encoding  
            >>> import struct
            >>> # Pack sensor readings: temp(float), humidity(int), timestamp(int)
            >>> sensor_data = struct.pack('<fII', 25.5, 67, 1234567890)
            >>> encoded = SlipEncoder.encode(sensor_data)
            >>> 
            >>> # Multiple packet encoding
            >>> packets = [
            ...     b"PING",
            ...     b"DATA:12345", 
            ...     bytes([0x00, 0xFF, 0xC0, 0xDB])  # Test with special chars
            ... ]
            >>> 
            >>> encoded_packets = []
            >>> for packet in packets:
            ...     encoded = SlipEncoder.encode(packet)
            ...     encoded_packets.append(encoded)
            ...     print(f"Packet: {packet.hex() if isinstance(packet, bytes) else packet}")
            ...     print(f"Encoded: {encoded.hex()}")
            >>> 
            >>> # Protocol message encoding
            >>> def create_message(msg_type, msg_id, payload):
            ...     # Message format: [TYPE:1][ID:2][PAYLOAD_LEN:2][PAYLOAD]
            ...     header = struct.pack('<BHH', msg_type, msg_id, len(payload))
            ...     message = header + payload
            ...     return SlipEncoder.encode(message)
            >>> 
            >>> # Create different message types
            >>> ping_msg = create_message(0x01, 1, b"")
            >>> data_msg = create_message(0x02, 2, b"sensor_data")
            >>> config_msg = create_message(0x03, 3, json.dumps({"rate": 100}).encode())
        ```
        """


class SlipDecoder:
    """
    SLIP (Serial Line Internet Protocol) decoder for reliable data reception.
    
    This class implements the SLIP protocol decoding which allows reliable
    reception and reconstruction of binary data packets from serial connections.
    It handles frame boundary detection, escape sequence processing, and
    automatic error recovery from corrupted data streams.
    
    SLIP Protocol Details:
        
        - END byte (0xC0): Marks frame boundaries
        - ESC byte (0xDB): Escape character for special bytes
        - ESC_END (0xDC): Escaped version of END byte
        - ESC_ESC (0xDD): Escaped version of ESC byte
    
    Features:
        
        - Stateful decoding with internal buffering
        - Automatic frame boundary detection
        - Escape sequence processing
        - Error recovery from invalid sequences
        - Multiple frame extraction from single data chunk
        - Compatible with SlipEncoder output
    
    State Management:
        
        - Maintains internal buffer for incomplete frames
        - Tracks escape sequence state
        - Handles frame boundary detection
        - Provides reset capability for error recovery
    
    """    
    END      = 0xC0
    ESC      = 0xDB
    ESC_END  = 0xDC
    ESC_ESC  = 0xDD

    def __init__(self) -> None:
        """
        Initialize the SLIP decoder with empty state.
        
        Sets up the internal buffer and resets all state flags for processing
        SLIP frames. The decoder is ready to receive data immediately after
        initialization.
        
        Example
        -------
        ```python
            >>> # Create decoder for serial communication
            >>> decoder = SlipDecoder()
            >>> 
            >>> # Multiple decoders for different channels
            >>> control_decoder = SlipDecoder()  # For control messages
            >>> data_decoder = SlipDecoder()     # For data streams
        ```
        """

    def reset(self) -> None:
        """
        Reset the decoder state to initial conditions.
        
        Clears the internal buffer and resets all state flags. Use this method
        when you need to restart decoding after detecting errors or when
        switching to a new data stream.
        
        Example
        -------
        ```python
            >>> decoder = SlipDecoder()
            >>> 
            >>> # Process some data
            >>> frames = decoder.feed(b'\xc0Hello\xc0')
            >>> print(f"Frames received: {len(frames)}")
            >>> 
            >>> # Reset clears all internal state
            >>> decoder.reset()
            >>> 
            >>> # Error recovery scenario
            >>> def handle_communication_error():
            ...     print("Communication error detected")
            ...     decoder.reset()  # Clear any partial data
            ...     uart.flush()     # Clear hardware buffers
        ```
        """

    def feed(self, chunk: bytes) -> list[bytes]:
        """
        Feed a chunk of bytes to the decoder and extract complete frames.
        
        Processes incoming data and returns a list of complete SLIP frames.
        Incomplete frames are buffered internally until the next call.
        The method handles escape sequences, frame boundaries, and error
        recovery automatically.
        
        :param chunk: The chunk of bytes to process (any length)
        :return: List of complete SLIP frames as byte arrays
        
        :raises TypeError: If chunk is not bytes or bytearray
        
        Processing Rules:
        
            - END bytes mark frame boundaries
            - ESC+ESC_END sequences become END bytes in output
            - ESC+ESC_ESC sequences become ESC bytes in output
            - Invalid escape sequences cause frame reset
            - Junk data before first frame is ignored
        
        Example
        -------
        ```python
            >>> decoder = SlipDecoder()
            >>> 
            >>> # Single complete frame
            >>> chunk1 = b'\xc0Hello\xc0'
            >>> frames = decoder.feed(chunk1)
            >>> print(f"Frames: {frames}")  # [b'Hello']
            >>> 
            >>> # Partial frame (buffered internally)
            >>> chunk2 = b'\xc0Partial'
            >>> frames = decoder.feed(chunk2)
            >>> print(f"Frames: {frames}")  # [] - no complete frames yet
            >>> 
            >>> # Complete the partial frame
            >>> chunk3 = b' frame\xc0'
            >>> frames = decoder.feed(chunk3)
            >>> print(f"Frames: {frames}")  # [b'Partial frame']
            >>> 
            >>> # Multiple frames in one chunk
            >>> chunk4 = b'\xc0Frame1\xc0\xc0Frame2\xc0\xc0Frame3\xc0'
            >>> frames = decoder.feed(chunk4)
            >>> print(f"Frames: {frames}")  # [b'Frame1', b'Frame2', b'Frame3']
            >>> 
            >>> # Real-world serial receiver
            >>> def serial_receiver():
            ...     decoder = SlipDecoder()
            ...     while True:
            ...         if uart.any():
            ...             chunk = uart.read()
            ...             frames = decoder.feed(chunk)
            ...             for frame in frames:
            ...                 process_message(frame)
            ...         utime.sleep_ms(10)
        ```
        """
